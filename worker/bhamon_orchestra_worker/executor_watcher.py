import logging
from typing import List

from bhamon_orchestra_model.network.messenger import Messenger
from bhamon_orchestra_worker.worker_storage import WorkerStorage


logger = logging.getLogger("ExecutorWatcher")


class ExecutorWatcher:


	def __init__(self, storage: WorkerStorage, run_identifier: str) -> None:
		self._storage = storage
		self.run_identifier = run_identifier

		self.process_watcher = None
		self.synchronization = None


	async def start(self, command: List[str]) -> None:
		await self.process_watcher.start(command)


	async def update(self, messenger: Messenger) -> None:
		await self._check_termination()

		if self.synchronization is not None:
			self.synchronization.update(messenger)


	async def complete(self) -> None:
		if self.is_running():
			raise RuntimeError("Run '%s' is still active" % self.run_identifier)


	async def terminate(self, reason: str) -> None:
		await self.process_watcher.terminate(reason)


	def abort(self) -> None:
		logger.info("Requesting subprocess termination (PID: %s)", self.process_watcher.process.pid)
		self.process_watcher.process.send_signal(self.process_watcher.termination_signal)


	def is_running(self) -> bool:
		if self.process_watcher is not None:
			return self.process_watcher.is_running()

		status = self._storage.load_status(self.run_identifier)

		return status is not None and status["status"] in [ "pending", "running" ]


	async def _check_termination(self) -> None:
		if self.is_running():
			return

		if self.process_watcher is not None:
			await self.process_watcher.wait()

		status = self._storage.load_status(self.run_identifier)

		if status is None:
			status = {
				"run_identifier": self.run_identifier,
				"status": "unknown",
			}

		if status["status"] in [ "pending", "running", "unknown" ]:
			logger.error("(%s) Run terminated before completion", self.run_identifier)
			status["status"] = "exception"
			self._storage.save_status(self.run_identifier, status)
