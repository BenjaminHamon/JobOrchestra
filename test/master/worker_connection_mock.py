class WorkerConnectionMock:
	""" Mock a connection to a remote worker """


	def __init__(self, worker):
		self.worker = worker


	async def ping(self):
		return None


	async def execute_command(self, worker_identifier, command, parameters = None): # pylint: disable = unused-argument
		if parameters is None:
			parameters = {}
		return self.worker.execute_command(command, parameters)
