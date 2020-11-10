import io
import logging
import os
from typing import List

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
		self.run_steps = []

		for step_index, step in enumerate(run_request["job_definition"]["steps"]):
			self.run_steps.append({ "index": step_index, "name": step["name"], "log_status": "pending" })

		self.status_last_timestamp = None
		self.results_last_timestamp = None


	def resume(self) -> None:
		if self.internal_status == "paused":
			self.internal_status = "running"


	def pause(self) -> None:
		if self.internal_status == "running":
			self.internal_status = "paused"


	def dispose(self) -> None:
		for step in self.run_steps:
			if "log_file" in step:
				step["log_file"].close()
		self.internal_status = "disposed"


	def reset(self, step_collection: List[dict]) -> None:
		for step in step_collection:
			self.run_steps[step["index"]]["log_file_cursor"] = step["log_file_cursor"]


	def update(self, messenger: Messenger) -> None:
		if self.internal_status == "running":
			try:
				self._send_updates(messenger)
				self._send_log_updates(messenger)
			except Exception: # pylint: disable = broad-except
				logger.warning("(%s) Failed to send updates", self.run_identifier, exc_info = True)

			if self.run_status in [ "succeeded", "failed", "aborted", "exception" ]:
				messenger.send_update({ "run": self.run_identifier, "event": "synchronization_completed" })
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
		status = self._storage.load_status(self.run_identifier)
		if status is None or "steps" not in status:
			return

		for step in self.run_steps:
			step_status = status["steps"][step["index"]]["status"]

			if step["log_status"] == "pending" and step_status not in [ "pending", "skipped" ]:
				log_file_path = self._storage.get_log_path(self.run_identifier, step["index"], step["name"])
				if os.path.exists(log_file_path):
					step["log_file"] = open(log_file_path, mode = "r", encoding = "utf-8")
					step["log_status"] = "running"

			while step["log_status"] == "running":
				if "log_file_cursor" in step:
					# The cursor is based on a universal size (to support universal newlines), so we have to use read instead of seek
					step["log_file"].seek(0)
					step["log_file"].read(step["log_file_cursor"])
					del step["log_file_cursor"]

				log_lines = self._read_lines(step["log_file"], 1024)

				if len(log_lines) > 0:
					messenger.send_update({ "run": self.run_identifier, "step_index": step["index"], "log_chunk": "".join(log_lines) })

				if step_status == "running":
					break
				if len(log_lines) == 0:
					step["log_status"] = "finishing"

			if step["log_status"] == "finishing":
				step["log_file"].close()
				step["log_status"] = "done"


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
