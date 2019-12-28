import asyncio
import logging
import time

import websockets


logger = logging.getLogger("Worker")


class WorkerError(Exception):
	pass


class Worker:


	def __init__(self, identifier, messenger, run_provider):
		self.identifier = identifier
		self._messenger = messenger
		self._run_provider = run_provider

		self.should_disconnect = False
		self.should_shutdown = False
		self.executors = []
		self.update_interval_seconds = 10
		self._active_asyncio_sleep = None


	def assign_run(self, job, run):
		self._run_provider.update_status(run, worker = self.identifier)
		executor = { "job": job, "run": run, "local_status": "pending", "should_abort": False }
		self.executors.append(executor)


	def abort_run(self, run_identifier):
		for executor in self.executors:
			if executor["run"]["identifier"] == run_identifier:
				executor["should_abort"] = True


	def wake_up(self):
		if self._active_asyncio_sleep:
			self._active_asyncio_sleep.cancel()


	async def run(self):
		try:
			self.executors += await self._recover_executors()
		except websockets.exceptions.ConnectionClosed:
			raise
		except Exception: # pylint: disable = broad-except
			logger.error("(%s) Unhandled exception while recovering runs", self.identifier, exc_info = True)

		while not self.should_disconnect and not self._messenger.is_disposed and (not self.should_shutdown or len(self.executors) > 0):
			update_start = time.time()
			await self._messenger.connection.ping()

			all_executors = list(self.executors)
			for executor in all_executors:
				try:
					await self._process_executor(executor)
				except websockets.exceptions.ConnectionClosed:
					raise
				except Exception: # pylint: disable = broad-except
					logger.error("(%s) Unhandled exception while executing run %s %s", self.identifier, executor["run"]["job"], executor["run"]["identifier"], exc_info = True)
					executor["local_status"] = "exception"

				if executor["local_status"] in [ "done", "exception" ]:
					self.executors.remove(executor)

			update_end = time.time()

			try:
				self._active_asyncio_sleep = asyncio.ensure_future(asyncio.sleep(self.update_interval_seconds - (update_end - update_start)))
				await self._active_asyncio_sleep
				self._active_asyncio_sleep = None
			except asyncio.CancelledError:
				break

		if self.should_shutdown and not self._messenger.is_disposed and len(self.executors) == 0:
			await self._execute_remote_command("shutdown")


	async def _execute_remote_command(self, command, parameters = None):
		return await self._messenger.send_request({ "command": command, "parameters": parameters if parameters is not None else {} })


	async def _recover_executors(self):
		recovered_executors = []
		runs_to_recover = await self._execute_remote_command("list")
		for run_information in runs_to_recover:
			executor = await self._recover_execution(**run_information)
			recovered_executors.append(executor)
		return recovered_executors


	async def _process_executor(self, executor):
		if executor["local_status"] == "pending":
			await self._start_execution(executor["run"], executor["job"])
			executor["local_status"] = "running"

		elif executor["local_status"] == "running":
			if executor["run"]["status"] in [ "succeeded", "failed", "aborted", "exception" ]:
				executor["local_status"] = "verifying"

			elif executor["should_abort"]:
				await self._abort_execution(executor["run"])
				executor["local_status"] = "aborting"

		elif executor["local_status"] == "aborting":
			if executor["run"]["status"] in [ "succeeded", "failed", "aborted", "exception" ]:
				executor["local_status"] = "verifying"

		elif executor["local_status"] == "verifying":
			await self._retrieve_logs(executor["run"])
			executor["local_status"] = "finishing"

		elif executor["local_status"] == "finishing":
			await self._finish_execution(executor["run"])
			executor["local_status"] = "done"


	async def _recover_execution(self, job_identifier, run_identifier):
		logger.info("(%s) Recovering run %s %s", self.identifier, job_identifier, run_identifier)
		run_request = await self._retrieve_request(job_identifier, run_identifier)
		run = self._run_provider.get(run_identifier)
		return { "job": run_request["job"], "run": run, "local_status": "running", "should_abort": False }


	async def _start_execution(self, run, job):
		logger.info("(%s) Starting run %s %s", self.identifier, run["job"], run["identifier"])
		execute_request = { "job_identifier": run["job"], "run_identifier": run["identifier"], "job": job, "parameters": run["parameters"] }
		await self._execute_remote_command("execute", execute_request)


	async def _abort_execution(self, run):
		logger.info("(%s) Aborting run %s %s", self.identifier, run["job"], run["identifier"])
		abort_request = { "job_identifier": run["job"], "run_identifier": run["identifier"] }
		await self._execute_remote_command("abort", abort_request)


	async def _finish_execution(self, run):
		clean_request = { "job_identifier": run["job"], "run_identifier": run["identifier"] }
		await self._execute_remote_command("clean", clean_request)
		logger.info("(%s) Completed run %s %s with status %s", self.identifier, run["job"], run["identifier"], run["status"])


	async def _retrieve_request(self, job_identifier, run_identifier):
		parameters = { "job_identifier": job_identifier, "run_identifier": run_identifier }
		return await self._execute_remote_command("request", parameters)


	async def _retrieve_logs(self, run):
		for run_step in run["steps"]:
			is_completed = run_step["status"] not in [ "pending", "running" ]
			has_log = self._run_provider.has_step_log(run["identifier"], run_step["index"])
			if is_completed and not has_log:
				log_request = {
					"job_identifier": run["job"],
					"run_identifier": run["identifier"],
					"step_index": run_step["index"],
					"step_name": run_step["name"],
				}
				log_text = await self._execute_remote_command("log", log_request)
				self._run_provider.set_step_log(run["identifier"], run_step["index"], log_text)


	async def handle_update(self, update):
		executor = self._find_executor(update["run"])

		if executor["local_status"] == "finishing":
			raise RuntimeError("Update received after completion and verification")

		if "status" in update:
			self._update_status(executor["run"], update["status"])
		if "results" in update:
			self._update_results(executor["run"], update["results"])


	def _find_executor(self, run_identifier):
		for executor in self.executors:
			if executor["run"]["identifier"] == run_identifier:
				return executor
		raise KeyError("Executor not found for %s" % run_identifier)


	def _update_status(self, run, status):
		properties_to_update = [ "status", "start_date", "completion_date" ]
		self._run_provider.update_status(run, ** { key: value for key, value in status.items() if key in properties_to_update })
		self._run_provider.update_steps(run, status.get("steps", []))


	def _update_results(self, run, results):
		self._run_provider.set_results(run, results)
