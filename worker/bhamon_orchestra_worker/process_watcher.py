import asyncio
import logging
import os
import platform
import signal
import subprocess
import sys
from typing import List

from bhamon_orchestra_worker.process_exception import ProcessException


logger = logging.getLogger("ProcessWatcher")


class ProcessWatcher:


	def __init__(self) -> None:
		self.process = None
		self.output_future = None
		self.output_handler = None

		self.termination_timeout_seconds = 10

		self.termination_signal = signal.CTRL_BREAK_EVENT if platform.system() == "Windows" else signal.SIGTERM # pylint: disable = no-member
		self.subprocess_flags = subprocess.CREATE_NEW_PROCESS_GROUP if platform.system() == "Windows" else 0


	async def run(self, command: List[str]) -> None:
		try:
			await self.start(command)
			await self.wait()
			await self.complete()

		except:
			if self.is_running():
				await self.terminate(sys.exc_info()[0].__name__)

			raise


	async def start(self, command: List[str]):
		process_environment = os.environ.copy()
		process_environment["PYTHONIOENCODING"] = "utf-8" # Force executor to use utf-8 instead of the default stdout encoding

		self.process = await asyncio.create_subprocess_exec(*command,
				stdout = subprocess.PIPE, stderr = subprocess.STDOUT, env = process_environment, creationflags = self.subprocess_flags)

		logger.info("New subprocess (PID: %s)", self.process.pid)

		self.output_future = asyncio.ensure_future(self._watch_output())


	async def wait(self) -> None:
		await self.process.wait()

		try:
			await asyncio.wait_for(self.output_future, 1)
		except asyncio.TimeoutError:
			logger.warning("Timeout on stdout future (PID: %s)", self.process.pid)


	async def complete(self) -> None:
		if self.process.returncode != 0:
			raise ProcessException("Subprocess failed (ExitCode: %s)" % self.process.returncode, self.process.returncode)


	async def terminate(self, reason: str) -> None:
		logger.info("Terminating subprocess (PID: %s, Reason: '%s')", self.process.pid, reason)

		if self.is_running():
			logger.info("Requesting subprocess termination (PID: %s)", self.process.pid)
			self.process.send_signal(self.termination_signal)

			try:
				await asyncio.wait_for(self.process.wait(), self.termination_timeout_seconds)
			except asyncio.TimeoutError:
				pass

		if self.is_running():
			logger.error("Forcing subprocess termination (PID: %s)", self.process.pid)
			self.process.kill()

			try:
				await asyncio.wait_for(self.process.wait(), self.termination_timeout_seconds)
			except asyncio.TimeoutError:
				pass

		if self.output_future is not None:
			try:
				await asyncio.wait_for(self.output_future, 1)
			except asyncio.TimeoutError:
				logger.warning("Timeout on stdout future (PID: %s)", self.process.pid)

		if self.is_running():
			logger.error("Terminating subprocess failed (PID: %s)", self.process.pid)

		if not self.is_running():
			logger.info("Terminating subprocess succeeded (PID: %s)", self.process.pid)


	def is_running(self) -> bool:
		return self.process is not None and self.process.returncode is None


	async def _watch_output(self) -> None:
		while True:
			line = await self.process.stdout.readline()
			if not line:
				break

			line = line.decode("utf-8").rstrip()

			if self.output_handler is not None:
				self.output_handler(line) # pylint: disable = not-callable
