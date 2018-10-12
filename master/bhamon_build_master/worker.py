import asyncio
import json
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
		self.active_asyncio_sleep = None


	def assign_build(self, job, build):
		executor = { "job": job, "build": build, "should_abort": False }
		self.executors.append(executor)


	def abort_build(self, build_identifier):
		for executor in self.executors:
			if executor["build"]["identifier"] == build_identifier:
				executor["should_abort"] = True


	async def run(self):
		builds_to_recover = await Worker._execute_remote_command(self._connection, self.identifier, "list", {})
		for build_information in builds_to_recover:
			executor = await self._recover_execution(**build_information)
			if executor is not None:
				self.executors.append(executor)

		while not self.should_disconnect and (not self.should_shutdown or len(self.executors) > 0):
			update_start = time.time()
			await self._connection.ping()
			all_executors = list(self.executors)
			for executor in all_executors:
				await self._process_executor(executor)
			update_end = time.time()

			try:
				self.active_asyncio_sleep = asyncio.ensure_future(asyncio.sleep(self.update_interval_seconds - (update_end - update_start)))
				await self.active_asyncio_sleep
				self.active_asyncio_sleep = None
			except asyncio.CancelledError:
				break

		if self.should_shutdown and len(self.executors) == 0:
			await Worker._execute_remote_command(self._connection, self.identifier, "shutdown", None)


	async def _process_executor(self, executor):
		try:
			if executor["build"]["status"] == "pending":
				await self._start_execution(executor["build"], executor["job"])
			if executor["should_abort"]:
				await self._abort_execution(executor["build"])
			if executor["build"]["status"] == "running":
				await self._update_execution(executor["build"])
			if executor["build"]["status"] != "running":
				await self._finish_execution(executor["build"])
				self.executors.remove(executor)
		except websockets.exceptions.ConnectionClosed:
			raise
		except:
			logger.error("(%s) Failed to execute build %s %s", self.identifier, executor["build"]["job"], executor["build"]["identifier"], exc_info = True)
			self._build_provider.update(executor["build"], status = "exception")
			self.executors.remove(executor)


	async def _recover_execution(self, job_identifier, build_identifier):
		logger.info("(%s) Recovering build %s %s", self.identifier, job_identifier, build_identifier)
		build_request = await self._retrieve_request(job_identifier, build_identifier)
		build = self._build_provider.get(build_identifier)
		return { "job": build_request["job"], "build": build, "should_abort": False }


	async def _start_execution(self, build, job):
		logger.info("(%s) Starting build %s %s", self.identifier, build["job"], build["identifier"])
		self._build_provider.update(build, worker = self.identifier, status = "running")
		execute_request = { "job_identifier": build["job"], "build_identifier": build["identifier"], "job": job, "parameters": build["parameters"] }
		await Worker._execute_remote_command(self._connection, self.identifier, "execute", execute_request)


	async def _abort_execution(self, build):
		logger.info("(%s) Aborting build %s %s", self.identifier, build["job"], build["identifier"])
		abort_request = { "job_identifier": build["job"], "build_identifier": build["identifier"] }
		await Worker._execute_remote_command(self._connection, self.identifier, "abort", abort_request)


	async def _update_execution(self, build):
		status_request = { "job_identifier": build["job"], "build_identifier": build["identifier"] }
		status_response = await Worker._execute_remote_command(self._connection, self.identifier, "status", status_request)
		if status_response:
			self._build_provider.update(build, status = status_response["status"])
			if "steps" in status_response:
				self._build_provider.update_steps(build["identifier"], status_response["steps"])
				await self._retrieve_logs(build, status_response["steps"])
				await self._retrieve_results(build)


	async def _finish_execution(self, build):
		all_steps = self._build_provider.get_all_steps(build["identifier"])
		await self._retrieve_logs(build, all_steps)
		await self._retrieve_results(build)
		clean_request = { "job_identifier": build["job"], "build_identifier": build["identifier"] }
		await Worker._execute_remote_command(self._connection, self.identifier, "clean", clean_request)
		logger.info("(%s) Completed build %s %s with status %s", self.identifier, build["job"], build["identifier"], build["status"])


	async def _retrieve_request(self, job_identifier, build_identifier):
		parameters = { "job_identifier": job_identifier, "build_identifier": build_identifier }
		return await Worker._execute_remote_command(self._connection, self.identifier, "request", parameters)


	async def _retrieve_logs(self, build, build_step_collection):
		for build_step in build_step_collection:
			is_completed = build_step["status"] not in [ "pending", "running" ]
			has_log = self._build_provider.has_step_log(build["identifier"], build_step["index"])
			if is_completed and not has_log:
				log_request = {
					"job_identifier": build["job"],
					"build_identifier": build["identifier"],
					"step_index": build_step["index"],
					"step_name": build_step["name"],
				}
				log_text = await Worker._execute_remote_command(self._connection, self.identifier, "log", log_request)
				self._build_provider.set_step_log(build["identifier"], build_step["index"], log_text)


	async def _retrieve_results(self, build):
		results_request = { "job_identifier": build["job"], "build_identifier": build["identifier"], }
		results = await Worker._execute_remote_command(self._connection, self.identifier, "results", results_request)
		self._build_provider.set_results(build["identifier"], results)


	@staticmethod
	async def authenticate(connection):
		return await Worker._execute_remote_command(connection, None, "authenticate", None)


	@staticmethod
	async def _execute_remote_command(connection, worker_identifier, command, parameters):
		request = { "command": command, "parameters": parameters }
		logger.debug("(%s) > %s", worker_identifier, request)
		await connection.send(json.dumps(request))
		response = json.loads(await connection.recv())
		logger.debug("(%s) < %s", worker_identifier, response)
		if "error" in response:
			raise RuntimeError("Worker error: " + response["error"])
		return response["result"]
