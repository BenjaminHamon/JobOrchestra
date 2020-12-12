import logging
from typing import List

from bhamon_orchestra_model.network.messenger import Messenger
from bhamon_orchestra_worker.process_exception import ProcessException
from bhamon_orchestra_worker.worker_storage import WorkerStorage


logger = logging.getLogger("ExecutorWatcher")


class ExecutorWatcher:


	def __init__(self, storage: WorkerStorage, run_identifier: str) -> None:
		self._storage = storage
		self.run_identifier = run_identifier

		self.is_running = False
		self.process_watcher = None
		self.synchronization = None


	async def start(self, context: str, command: List[str]) -> None:
		self.is_running = True
		await self.process_watcher.start(context, command)


	def recover(self) -> None:
		self.is_running = True


	async def update(self, messenger: Messenger) -> None:
		if self.is_running:
			await self._check_completion()

		if self.synchronization is not None:
			self.synchronization.update(messenger)

			if not self.is_running and self.synchronization.internal_status == "done":
				messenger.send_update({ "run": self.run_identifier, "event": "synchronization_completed" })
				self.synchronization.dispose()
				self.synchronization = None


	async def terminate(self, reason: str) -> None:
		if self.process_watcher is not None:
			await self.process_watcher.terminate(reason)


	def abort(self) -> None:
		logger.info("Requesting subprocess termination (PID: %s)", self.process_watcher.process.pid)
		self.process_watcher.process.send_signal(self.process_watcher.termination_signal)


	async def _check_completion(self) -> None:
		if self.process_watcher is not None:
			if not self.process_watcher.is_running():
				await self.process_watcher.wait()

				try:
					await self.process_watcher.complete()
				except ProcessException:
					logger.error("Run '%s' exited with an error", self.run_identifier, exc_info = True)

				self.is_running = False

		else:
			status = self._storage.load_status(self.run_identifier)

			if status is None:
				status = {
					"run_identifier": self.run_identifier,
					"status": "unknown",
				}

			if status["status"] in [ "pending", "running", "unknown" ]:
				logger.error("Run '%s' exited before completion", self.run_identifier)
				status["status"] = "exception"
				self._storage.save_status(self.run_identifier, status)

			if status["status"] in [ "succeeded", "failed", "aborted", "exception" ]:
				self.is_running = False
