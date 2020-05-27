import asyncio
import logging
import os
import platform
import signal
import subprocess

import bhamon_orchestra_worker.worker_storage as worker_storage


logger = logging.getLogger("ExecutorWatcher")

shutdown_signal = signal.CTRL_BREAK_EVENT if platform.system() == "Windows" else signal.SIGINT # pylint: disable = no-member
subprocess_flags = subprocess.CREATE_NEW_PROCESS_GROUP if platform.system() == "Windows" else 0


class ExecutorWatcher:


	def __init__(self, run_identifier):
		self.run_identifier = run_identifier
		self.process = None
		self.synchronization = None
		self.stdout_future = None


	async def start(self, command):
		self.process = await asyncio.create_subprocess_exec(*command, stdout = subprocess.PIPE, stderr = subprocess.STDOUT, creationflags = subprocess_flags)
		self.stdout_future = asyncio.ensure_future(self.watch_stdout())


	async def terminate(self, timeout_seconds):
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


	def abort(self):
		os.kill(self.process.pid, shutdown_signal)
		# The executor should terminate nicely, if it does not it will stays as running and should be investigated
		# Forcing termination here would leave orphan processes and the status as running


	def is_running(self):
		return self.process is not None and self.process.returncode is None


	async def watch_stdout(self):
		raw_logger = logging.getLogger("raw")

		while True:
			line = await self.process.stdout.readline()
			if not line:
				break

			line = line.decode("utf-8").strip()
			raw_logger.info(line)


	def update(self, messenger):
		self._check_termination()

		if self.synchronization is not None:
			self.synchronization.update(messenger)


	async def complete(self):
		if self.is_running():
			raise RuntimeError("Run '%s' is still active" % self.run_identifier)

		if self.stdout_future is not None:
			try:
				await asyncio.wait_for(self.stdout_future, 1)
			except asyncio.TimeoutError:
				logger.warning("(%s) Timeout on stdout future", self.run_identifier)


	def _check_termination(self):
		if self.is_running():
			return

		status = worker_storage.load_status(self.run_identifier)
		if status["status"] in [ "unknown", "running" ]:
			logger.error("(%s) Run terminated before completion", self.run_identifier)
			status["status"] = "exception"
			worker_storage.save_status(self.run_identifier, status)
