import io
import logging
import os

from bhamon_orchestra_model.network.messenger import Messenger
from bhamon_orchestra_worker.worker_storage import WorkerStorage


logger = logging.getLogger("Synchronization")


class Synchronization:
	""" Responsible for pushing data from an executor to the master """


	def __init__(self, storage: WorkerStorage, run_request: dict) -> None:
		self._storage = storage
		self.run_identifier = run_request["run_identifier"]

		self.internal_status = "paused"
		self.run_status = "unknown"
		self.log_file = None
		self.status_last_timestamp = None
		self.results_last_timestamp = None


	def resume(self) -> None:
		if self.internal_status == "paused":
			self.internal_status = "running"


	def pause(self) -> None:
		if self.internal_status == "running":
			self.internal_status = "paused"


	def dispose(self) -> None:
		if self.log_file is not None:
			self.log_file.close()
			self.log_file = None
		self.internal_status = "disposed"


	def reset(self, log_cursor: int) -> None:
		if self.log_file is None:
			log_file_path = self._storage.get_log_path(self.run_identifier)
			if os.path.exists(log_file_path):
				self.log_file = open(log_file_path, mode = "r", encoding = "utf-8") # pylint: disable = consider-using-with

		# The log cursor is computed on the text size instead of the binary size
		# to take into account encoding and end-of-lines differences.
		if self.log_file is not None:
			self.log_file.seek(0)
			self.log_file.read(log_cursor)


	def update(self, messenger: Messenger) -> None:
		if self.internal_status == "running":
			try:
				self._send_updates(messenger)
				self._send_log_updates(messenger)
			except Exception: # pylint: disable = broad-except
				logger.warning("(%s) Failed to send updates", self.run_identifier, exc_info = True)

			if self.run_status in [ "succeeded", "failed", "aborted", "exception" ] and self.log_file is None:
				self.internal_status = "done"


	def _send_updates(self, messenger: Messenger) -> None:
		status_timestamp = self._storage.get_status_timestamp(self.run_identifier)
		if status_timestamp != self.status_last_timestamp:
			status = self._storage.load_status(self.run_identifier)
			if status is not None:
				messenger.send_update({ "run": self.run_identifier, "status": status })
				self.run_status = status["status"]
			self.status_last_timestamp = status_timestamp

		results_timestamp = self._storage.get_results_timestamp(self.run_identifier)
		if results_timestamp != self.results_last_timestamp:
			results = self._storage.load_results(self.run_identifier)
			if results is not None:
				messenger.send_update({ "run": self.run_identifier, "results": results })
			self.results_last_timestamp = results_timestamp


	def _send_log_updates(self, messenger: Messenger) -> None:
		if self.log_file is None:
			log_file_path = self._storage.get_log_path(self.run_identifier)
			if os.path.exists(log_file_path):
				self.log_file = open(log_file_path, mode = "r", encoding = "utf-8") # pylint: disable = consider-using-with

		if self.log_file is not None:
			log_lines = self._read_lines(self.log_file, 1024)

			if len(log_lines) > 0:
				messenger.send_update({ "run": self.run_identifier, "log_chunk": "".join(log_lines) })

			if self.run_status in [ "succeeded", "failed", "aborted", "exception" ] and len(log_lines) == 0:
				self.log_file.close()
				self.log_file = None


	def _read_lines(self, log_file: io.TextIOWrapper, limit: int) -> str: # pylint: disable = no-self-use
		all_lines = []

		while len(all_lines) < limit:
			last_position = log_file.tell()
			next_line = log_file.readline()

			if not next_line:
				break

			if not next_line.endswith("\n"):
				log_file.seek(last_position)
				break

			all_lines.append(next_line)

		return all_lines
