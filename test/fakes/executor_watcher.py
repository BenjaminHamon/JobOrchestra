class FakeExecutorWatcher:


	def __init__(self, run_identifier):
		self.run_identifier = run_identifier
		self.is_running = False
		self.synchronization = None

		self.status = {
			"run_identifier": run_identifier,
			"status": "pending",
		}


	async def start(self, context, command): # pylint: disable = unused-argument
		if self.is_running:
			raise RuntimeError("Executor is already running")
		self.status["status"] = "running"
		self.is_running = True


	async def terminate(self, reason): # pylint: disable = unused-argument
		if not self.is_running:
			raise RuntimeError("Executor is not running")
		self.status["status"] = "aborted"
		self.is_running = False


	def abort(self):
		if not self.is_running:
			raise RuntimeError("Executor is not running")
		self.status["status"] = "aborted"
		self.is_running = False


	def succeed(self):
		self.status["status"] = "succeeded"
		self.is_running = False
