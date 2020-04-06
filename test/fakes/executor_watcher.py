class FakeExecutorWatcher:


	def __init__(self, run_identifier):
		self.run_identifier = run_identifier
		self.synchronization = None

		self.request = {
			"run_identifier": run_identifier,
		}

		self.status = {
			"run_identifier": run_identifier,
			"status": "pending",
			"steps": [
				{ "index": 0, "name": "first", "status": "pending" },
				{ "index": 1, "name": "second", "status": "pending" },
				{ "index": 2, "name": "third", "status": "pending" },
			],
		}


	async def start(self, command): # pylint: disable = unused-argument
		if self.is_running():
			raise RuntimeError("Executor is already running")
		self.status["status"] = "running"


	async def terminate(self, timeout_seconds):
		if not self.is_running():
			raise RuntimeError("Executor is not running")
		self.status["status"] = "aborted"


	def abort(self):
		if not self.is_running():
			raise RuntimeError("Executor is not running")
		self.status["status"] = "aborted"


	def is_running(self):
		return self.status["status"] == "running"


	async def wait_futures(self):
		pass
