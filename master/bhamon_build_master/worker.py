import asyncio
import json
import logging


logger = logging.getLogger("Worker")

run_interval_seconds = 5
status_interval_seconds = 5


class Worker:


	def __init__(self, identifier, connection, database):
		self.identifier = identifier
		self._connection = connection
		self._database = database
		self.build = None
		self.job = None
		self._should_abort = False


	def is_idle(self):
		return self.build is None


	def assign_build(self, job, build):
		if self.build is not None:
			raise RuntimeError("Worker %s is already building %s %s" % (self.identifier, self.build["job"], self.build["identifier"]))
		self.job = job
		self.build = build
		self._should_abort = False


	def abort_build(self):
		self._should_abort = True


	async def run(self):
		while True:
			if self.build is None:
				await self._connection.ping()
				await asyncio.sleep(run_interval_seconds)
			else:
				await self._process_build()


	async def _process_build(self):
		logger.info("(%s) Starting build %s %s", self.identifier, self.build["job"], self.build["identifier"])

		try:
			self.build["worker"] = self.identifier
			self.build["status"] = "running"
			self._database.update_build(self.build)

			execute_request = {
				"job_identifier": self.build["job"],
				"build_identifier": self.build["identifier"],
				"job": self.job,
				"parameters": self.build["parameters"],
			}
			await Worker._execute_remote_command(self._connection, self.identifier, "execute", execute_request)

			while self.build["status"] == "running":

				if self._should_abort:
					abort_request = { "job_identifier": self.build["job"], "build_identifier": self.build["identifier"] }
					await Worker._execute_remote_command(self._connection, self.identifier, "abort", abort_request)

				await asyncio.sleep(status_interval_seconds)

				status_request = { "job_identifier": self.build["job"], "build_identifier": self.build["identifier"] }
				status_response = await Worker._execute_remote_command(self._connection, self.identifier, "status", status_request)
				self.build["status"] = status_response["status"]
				build_steps = status_response["steps"]
				self._database.update_build(self.build)
				self._database.update_build_steps(self.build["identifier"], build_steps)
				await self._retrieve_logs(build_steps)

			await self._retrieve_logs(build_steps)

			clean_request = { "job_identifier": self.build["job"], "build_identifier": self.build["identifier"] }
			await Worker._execute_remote_command(self._connection, self.identifier, "clean", clean_request)

		except:
			logger.error("(%s) Failed to process build %s %s", self.identifier, self.build["job"], self.build["identifier"], exc_info = True)
			self.build["status"] = "exception"
			self._database.update_build(self.build)

		logger.info("(%s) Completed build %s %s with status %s", self.identifier, self.build["job"], self.build["identifier"], self.build["status"])
		self.job = None
		self.build = None


	async def _retrieve_logs(self, build_step_collection):
		for build_step in build_step_collection:
			is_completed = build_step["status"] not in [ "pending", "running" ]
			has_log = self._database.has_build_step_log(self.build["identifier"], build_step["index"])
			if is_completed and not has_log:
				log_request = {
					"job_identifier": self.build["job"],
					"build_identifier": self.build["identifier"],
					"step_index": build_step["index"],
					"step_name": build_step["name"],
				}
				log_text = await Worker._execute_remote_command(self._connection, self.identifier, "log", log_request)
				self._database.set_build_step_log(self.build["identifier"], build_step["index"], log_text)


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
