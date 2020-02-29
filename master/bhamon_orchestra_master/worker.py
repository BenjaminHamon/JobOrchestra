import asyncio
import logging


logger = logging.getLogger("Worker")


class WorkerError(Exception):
	pass


class Worker:


	def __init__(self, identifier, messenger, run_provider):
		self.identifier = identifier
		self._messenger = messenger
		self._run_provider = run_provider

		self.should_disconnect = False
		self.executors = []


	def assign_run(self, job, run):
		self._run_provider.update_status(run, worker = self.identifier)
		executor = { "job": job, "run": run, "local_status": "pending", "synchronization": "unknown", "should_abort": False }
		self.executors.append(executor)


	def abort_run(self, run_identifier):
		for executor in self.executors:
			if executor["run"]["identifier"] == run_identifier:
				executor["should_abort"] = True


	async def run(self):
		try:
			self.executors += await self._recover_executors()
		except asyncio.CancelledError: # pylint: disable = try-except-raise
			raise
		except Exception: # pylint: disable = broad-except
			logger.error("(%s) Unhandled exception while recovering runs", self.identifier, exc_info = True)

		while not self.should_disconnect:
			all_executors = list(self.executors)
			for executor in all_executors:
				try:
					await self._process_executor(executor)
				except asyncio.CancelledError: # pylint: disable = try-except-raise
					raise
				except Exception: # pylint: disable = broad-except
					logger.error("(%s) Unhandled exception while executing run %s", self.identifier, executor["run"]["identifier"], exc_info = True)
					executor["local_status"] = "exception"

				if executor["local_status"] in [ "done", "exception" ]:
					self.executors.remove(executor)

			await asyncio.sleep(0.1)


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

			if executor["synchronization"] == "unknown":
				await self._resynchronize(executor["run"])
				executor["synchronization"] = "running"

		elif executor["local_status"] == "aborting":
			if executor["run"]["status"] in [ "succeeded", "failed", "aborted", "exception" ]:
				executor["local_status"] = "verifying"

		elif executor["local_status"] == "verifying":
			if executor["synchronization"] == "done":
				executor["local_status"] = "finishing"

		elif executor["local_status"] == "finishing":
			await self._finish_execution(executor["run"])
			executor["local_status"] = "done"


	async def _recover_execution(self, run_identifier):
		logger.info("(%s) Recovering run %s", self.identifier, run_identifier)
		run_request = await self._retrieve_request(run_identifier)
		run = self._run_provider.get(run_request["job"]["project"], run_identifier)
		return { "job": run_request["job"], "run": run, "local_status": "running", "synchronization": "unknown", "should_abort": False }


	async def _start_execution(self, run, job):
		logger.info("(%s) Starting run %s", self.identifier, run["identifier"])
		execute_request = { "run_identifier": run["identifier"], "job": job, "parameters": run["parameters"] }
		await self._execute_remote_command("execute", execute_request)


	async def _abort_execution(self, run):
		logger.info("(%s) Aborting run %s", self.identifier, run["identifier"])
		abort_request = { "run_identifier": run["identifier"] }
		await self._execute_remote_command("abort", abort_request)


	async def _finish_execution(self, run):
		clean_request = { "run_identifier": run["identifier"] }
		await self._execute_remote_command("clean", clean_request)
		logger.info("(%s) Completed run %s with status %s", self.identifier, run["identifier"], run["status"])


	async def _resynchronize(self, run):
		reset = { "steps": [] }

		for step in self._run_provider.get_all_steps(run["project"], run["identifier"]):
			if self._run_provider.has_step_log(run["project"], run["identifier"], step["index"]):
				log_size = self._run_provider.get_step_log_size(run["project"], run["identifier"], step["index"])
				reset["steps"].append({ "index": step["index"], "log_file_cursor": log_size })

		resynchronization_request = { "run_identifier": run["identifier"], "reset": reset }
		await self._execute_remote_command("resynchronize", resynchronization_request)


	async def _retrieve_request(self, run_identifier):
		parameters = { "run_identifier": run_identifier }
		return await self._execute_remote_command("request", parameters)


	async def handle_update(self, update):
		executor = self._find_executor(update["run"])

		if executor["local_status"] == "finishing":
			raise RuntimeError("Update received after completion and verification")

		if "status" in update:
			self._update_status(executor["run"], update["status"])
		if "results" in update:
			self._update_results(executor["run"], update["results"])
		if "log_chunk" in update:
			self._update_log_file(executor["run"], update["step_index"], update["log_chunk"])
		if "event" in update:
			self._handle_event(executor, update["event"])


	def _find_executor(self, run_identifier):
		for executor in self.executors:
			if executor["run"]["identifier"] == run_identifier:
				return executor
		raise KeyError("Executor not found for %s" % run_identifier)


	def _update_status(self, run, status):
		properties_to_update = [ "status", "start_date", "completion_date" ]
		self._run_provider.update_status(run, ** { key: value for key, value in status.items() if key in properties_to_update })

		step_properties_to_update = [ "name", "index", "status" ]
		step_collection = [ { key: value for key, value in step.items() if key in step_properties_to_update } for step in status.get("steps", []) ]
		self._run_provider.update_steps(run, step_collection)


	def _update_results(self, run, results):
		self._run_provider.set_results(run, results)


	def _update_log_file(self, run, step_index, log_chunk):
		self._run_provider.append_step_log(run["project"], run["identifier"], step_index, log_chunk)


	def _handle_event(self, executor, event): # pylint: disable = no-self-use
		if event == "synchronization_completed":
			executor["synchronization"] = "done"
