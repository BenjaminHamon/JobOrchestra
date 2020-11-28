import asyncio
import logging
import os
import platform
import signal
import subprocess
from typing import List

from bhamon_orchestra_model.network.messenger import Messenger
from bhamon_orchestra_worker.worker_storage import WorkerStorage


logger = logging.getLogger("ExecutorWatcher")

shutdown_signal = signal.CTRL_BREAK_EVENT if platform.system() == "Windows" else signal.SIGTERM # pylint: disable = no-member
subprocess_flags = subprocess.CREATE_NEW_PROCESS_GROUP if platform.system() == "Windows" else 0


class ExecutorWatcher:


	def __init__(self, storage: WorkerStorage, run_identifier: str) -> None:
		self._storage = storage
		self.run_identifier = run_identifier

		self.process = None
		self.synchronization = None
		self.stdout_future = None


	async def start(self, command: List[str]) -> None:
		process_environment = os.environ.copy()
		process_environment["PYTHONIOENCODING"] = "utf-8" # Force executor to use utf-8 instead of the default stdout encoding

		self.process = await asyncio.create_subprocess_exec(*command,
				stdout = subprocess.PIPE, stderr = subprocess.STDOUT, env = process_environment, creationflags = subprocess_flags)
		self.stdout_future = asyncio.ensure_future(self.watch_stdout())


	async def terminate(self, timeout_seconds: int) -> None:
		if self.is_running():
			logger.info("(%s) Aborting", self.run_identifier)
			os.kill(self.process.pid, shutdown_signal)

			try:
				await asyncio.wait_for(self.process.wait(), timeout_seconds)
			except asyncio.TimeoutError:
				logger.warning("(%s) Forcing termination", self.run_identifier)
				self.process.kill()

		if self.stdout_future is not None:
			try:
				await asyncio.wait_for(self.stdout_future, timeout = 1)
			except asyncio.TimeoutError:
				logger.warning("(%s) Timeout on stdout future", self.run_identifier)


	def abort(self) -> None:
		os.kill(self.process.pid, shutdown_signal)
		# The executor should terminate nicely, if it does not it will stays as running and should be investigated
		# Forcing termination here would leave orphan processes and the status as running


	def is_running(self) -> bool:
		return self.process is not None and self.process.returncode is None


	async def watch_stdout(self) -> None:
		raw_logger = logging.getLogger("raw")

		while True:
			line = await self.process.stdout.readline()
			if not line:
				break

			line = line.decode("utf-8").rstrip()
			raw_logger.info(line)


	def update(self, messenger: Messenger) -> None:
		self._check_termination()

		if self.synchronization is not None:
			self.synchronization.update(messenger)


	async def complete(self) -> None:
		if self.is_running():
			raise RuntimeError("Run '%s' is still active" % self.run_identifier)

		if self.stdout_future is not None:
			try:
				await asyncio.wait_for(self.stdout_future, 1)
			except asyncio.TimeoutError:
				logger.warning("(%s) Timeout on stdout future", self.run_identifier)


	def _check_termination(self) -> None:
		if self.is_running():
			return

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
