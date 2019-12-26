import asyncio
import logging
import os
import platform
import signal
import subprocess


logger = logging.getLogger("ExecutorWatcher")

shutdown_signal = signal.CTRL_BREAK_EVENT if platform.system() == "Windows" else signal.SIGINT # pylint: disable = no-member
subprocess_flags = subprocess.CREATE_NEW_PROCESS_GROUP if platform.system() == "Windows" else 0


class ExecutorWatcher:


	def __init__(self, job_identifier, run_identifier):
		self.job_identifier = job_identifier
		self.run_identifier = run_identifier
		self.process = None
		self.futures = []


	async def start(self, command):
		self.process = await asyncio.create_subprocess_exec(*command, stdout = subprocess.PIPE, stderr = subprocess.STDOUT, creationflags = subprocess_flags)
		self.futures.append(asyncio.ensure_future(self.watch_stdout()))


	async def terminate(self, timeout_seconds):
		if self.is_running():
			logger.info("Aborting %s %s", self.job_identifier, self.run_identifier)
			os.kill(self.process.pid, shutdown_signal)

			try:
				await asyncio.wait_for(self.process.wait(), timeout_seconds)
			except asyncio.TimeoutError:
				logger.warning("Forcing termination for %s %s", self.job_identifier, self.run_identifier)
				self.process.kill()

			try:
				await self.wait_futures()
			except asyncio.TimeoutError:
				logger.warning("Timeout on futures for %s %s", self.job_identifier, self.run_identifier)


	def abort(self):
		os.kill(self.process.pid, shutdown_signal)
		# The executor should terminate nicely, if it does not it will stays as running and should be investigated
		# Forcing termination here would leave orphan processes and the status as running


	def is_running(self):
		return self.process is not None and self.process.returncode is None


	async def watch_stdout(self):
		raw_logger = logging.getLogger("raw")

		while True:
			try:
				line = await asyncio.wait_for(self.process.stdout.readline(), 1)
			except asyncio.TimeoutError:
				continue

			if not line:
				break

			line = line.decode("utf-8").strip()
			raw_logger.info(line)


	async def wait_futures(self):
		if len(self.futures) > 0:
			await asyncio.wait(self.futures, timeout = 1)
