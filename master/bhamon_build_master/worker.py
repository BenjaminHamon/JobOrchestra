import asyncio
import json
import logging


logger = logging.getLogger("Worker")

run_interval_seconds = 5


class Worker:


	def __init__(self, identifier, connection, build_provider):
		self.identifier = identifier
		self._connection = connection
		self._build_provider = build_provider
		self._should_shutdown = False
		self.executors = []


	def can_assign_build(self):
		return not self._should_shutdown


	def assign_build(self, job, build):
		executor = { "job": job, "build": build, "should_abort": False }
		self.executors.append(executor)


	def abort_build(self, build_identifier):
		for executor in self.executors:
			if executor["build"]["identifier"] == build_identifier:
				executor["should_abort"] = True


	def shutdown(self):
		self._should_shutdown = True


	async def run(self):
		while not self._should_shutdown or len(self.executors) > 0:
			await self._connection.ping()
			all_executors = list(self.executors)
			for executor in all_executors:
				await self._process_executor(executor)
			await asyncio.sleep(run_interval_seconds)


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
		except:
			logger.error("(%s) Failed to execute build %s %s", self.identifier, executor["build"]["job"], executor["build"]["identifier"], exc_info = True)
			self._build_provider.update(executor["build"], status = "exception")
			self.executors.remove(executor)


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
