import json
import logging


logger = logging.getLogger("WorkerConnection")


class WorkerConnection:


	def __init__(self, connection):
		self.connection = connection


	async def ping(self):
		return await self.connection.ping()


	async def execute_command(self, worker_identifier, command, parameters = None):
		if parameters is None:
			parameters = {}

		request = { "command": command, "parameters": parameters }
		logger.debug("(%s) > %s", worker_identifier, request)
		await self.connection.send(json.dumps(request))
		response = json.loads(await self.connection.receive())
		logger.debug("(%s) < %s", worker_identifier, response)
		if "error" in response:
			raise RuntimeError("Worker error: " + response["error"])
		return response["result"]
