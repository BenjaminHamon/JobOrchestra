import asyncio
import logging
import time

import websockets


logger = logging.getLogger("Worker")


class Worker:


	def __init__(self, identifier, connection, build_provider):
		self.identifier = identifier
		self._connection = connection
		self._build_provider = build_provider
		self.should_disconnect = False
		self.should_shutdown = False
		self.executors = []
		self.update_interval_seconds = 10
		self._active_asyncio_sleep = None


	def assign_build(self, job, build):
		self._build_provider.update_status(build, worker = self.identifier)
		executor = { "job": job, "build": build, "local_status": "pending", "should_abort": False }
		self.executors.append(executor)


	def abort_build(self, build_identifier):
		for executor in self.executors:
			if executor["build"]["identifier"] == build_identifier:
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
			logger.error("(%s) Unhandled exception while recovering builds", self.identifier, exc_info = True)

		while not self.should_disconnect and (not self.should_shutdown or len(self.executors) > 0):
			update_start = time.time()
			await self._connection.ping()

			all_executors = list(self.executors)
			for executor in all_executors:
				try:
					await self._process_executor(executor)
				except websockets.exceptions.ConnectionClosed:
					raise
				except Exception: # pylint: disable = broad-except
					logger.error("(%s) Unhandled exception while executing build %s %s", self.identifier, executor["build"]["job"], executor["build"]["identifier"], exc_info = True)
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

		if self.should_shutdown and len(self.executors) == 0:
			await self._connection.execute_command(self.identifier, "shutdown")


	async def _recover_executors(self):
		recovered_executors = []
		builds_to_recover = await self._connection.execute_command(self.identifier, "list")
		for build_information in builds_to_recover:
			executor = await self._recover_execution(**build_information)
			recovered_executors.append(executor)
		return recovered_executors


	async def _process_executor(self, executor):
		if executor["local_status"] == "pending":
			await self._start_execution(executor["build"], executor["job"])
			executor["local_status"] = "running"

		elif executor["local_status"] == "running":
			await self._update_execution(executor["build"])

			if executor["build"]["status"] in [ "succeeded", "failed", "aborted", "exception" ]:
				await self._finish_execution(executor["build"])
				executor["local_status"] = "done"

			elif executor["should_abort"]:
				await self._abort_execution(executor["build"])
				executor["local_status"] = "aborting"

		elif executor["local_status"] == "aborting":
			await self._update_execution(executor["build"])

			if executor["build"]["status"] in [ "succeeded", "failed", "aborted", "exception" ]:
				await self._finish_execution(executor["build"])
				executor["local_status"] = "done"


	async def _recover_execution(self, job_identifier, build_identifier):
		logger.info("(%s) Recovering build %s %s", self.identifier, job_identifier, build_identifier)
		build_request = await self._retrieve_request(job_identifier, build_identifier)
		build = self._build_provider.get(build_identifier)
		return { "job": build_request["job"], "build": build, "local_status": "running", "should_abort": False }


	async def _start_execution(self, build, job):
		logger.info("(%s) Starting build %s %s", self.identifier, build["job"], build["identifier"])
		execute_request = { "job_identifier": build["job"], "build_identifier": build["identifier"], "job": job, "parameters": build["parameters"] }
		await self._connection.execute_command(self.identifier, "execute", execute_request)


	async def _abort_execution(self, build):
		logger.info("(%s) Aborting build %s %s", self.identifier, build["job"], build["identifier"])
		abort_request = { "job_identifier": build["job"], "build_identifier": build["identifier"] }
		await self._connection.execute_command(self.identifier, "abort", abort_request)


	async def _update_execution(self, build):
		status_request = { "job_identifier": build["job"], "build_identifier": build["identifier"] }
		status_response = await self._connection.execute_command(self.identifier, "status", status_request)
		if status_response["status"] != "unknown":
			properties_to_update = [ "status", "start_date", "completion_date" ]
			self._build_provider.update_status(build, ** { key: value for key, value in status_response.items() if key in properties_to_update })
			if "steps" in status_response:
				self._build_provider.update_steps(build, status_response["steps"])
				await self._retrieve_logs(build)
				await self._retrieve_results(build)


	async def _finish_execution(self, build):
		clean_request = { "job_identifier": build["job"], "build_identifier": build["identifier"] }
		await self._connection.execute_command(self.identifier, "clean", clean_request)
		logger.info("(%s) Completed build %s %s with status %s", self.identifier, build["job"], build["identifier"], build["status"])


	async def _retrieve_request(self, job_identifier, build_identifier):
		parameters = { "job_identifier": job_identifier, "build_identifier": build_identifier }
		return await self._connection.execute_command(self.identifier, "request", parameters)


	async def _retrieve_logs(self, build):
		for build_step in build["steps"]:
			is_completed = build_step["status"] not in [ "pending", "running" ]
			has_log = self._build_provider.has_step_log(build["identifier"], build_step["index"])
			if is_completed and not has_log:
				log_request = {
					"job_identifier": build["job"],
					"build_identifier": build["identifier"],
					"step_index": build_step["index"],
					"step_name": build_step["name"],
				}
				log_text = await self._connection.execute_command(self.identifier, "log", log_request)
				self._build_provider.set_step_log(build["identifier"], build_step["index"], log_text)


	async def _retrieve_results(self, build):
		results_request = { "job_identifier": build["job"], "build_identifier": build["identifier"], }
		results = await self._connection.execute_command(self.identifier, "results", results_request)
		self._build_provider.set_results(build, results)
