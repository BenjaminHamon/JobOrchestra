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


	def __init__(self, job_identifier, run_identifier):
		self.job_identifier = job_identifier
		self.run_identifier = run_identifier
		self.process = None
		self.futures = []
		self.status = "unknown"
		self.synchronization = "unknown"
		self.status_last_timestamp = None
		self.results_last_timestamp = None


	async def start(self, command):
		self.process = await asyncio.create_subprocess_exec(*command, stdout = subprocess.PIPE, stderr = subprocess.STDOUT, creationflags = subprocess_flags)
		self.futures.append(asyncio.ensure_future(self.watch_stdout()))
		self.synchronization = "running"


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


	def update(self, messenger):
		self._check_termination()

		if self.synchronization == "running":
			try:
				self._send_updates(messenger)
			except Exception: # pylint: disable = broad-except
				logger.warning("%s %s failed to send updates", self.job_identifier, self.run_identifier, exc_info = True)

			if self.status in [ "succeeded", "failed", "aborted", "exception" ]:
				self.synchronization = "done"
				messenger.send_update({ "run": self.run_identifier, "event": "synchronization_completed" })


	def _send_updates(self, messenger):
		status_timestamp = worker_storage.get_status_timestamp(self.job_identifier, self.run_identifier)
		if status_timestamp != self.status_last_timestamp:
			status = worker_storage.load_status(self.job_identifier, self.run_identifier)
			if status["status"] != "unknown":
				messenger.send_update({ "run": self.run_identifier, "status": status })
			self.status = status["status"]
			self.status_last_timestamp = status_timestamp

		results_timestamp = worker_storage.get_results_timestamp(self.job_identifier, self.run_identifier)
		if results_timestamp != self.results_last_timestamp:
			results = worker_storage.load_results(self.job_identifier, self.run_identifier)
			messenger.send_update({ "run": self.run_identifier, "results": results })
			self.results_last_timestamp = results_timestamp


	def _check_termination(self):
		if self.is_running():
			return

		status = worker_storage.load_status(self.job_identifier, self.run_identifier)
		if status["status"] in [ "unknown", "running" ]:
			logger.error("Run '%s' terminated before completion", self.run_identifier)
			status["status"] = "exception"
			worker_storage.save_status(self.job_identifier, self.run_identifier, status)
