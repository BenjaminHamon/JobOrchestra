import logging
import os

import bhamon_orchestra_worker.worker_storage as worker_storage


logger = logging.getLogger("Synchronization")


class Synchronization:
	""" Responsible for pushing data from an executor to the master """


	def __init__(self, run_request):
		self.job_identifier = run_request["job_identifier"]
		self.run_identifier = run_request["run_identifier"]

		self.internal_status = "paused"
		self.run_status = "unknown"
		self.run_steps = []

		for step_index, step in enumerate(run_request["job"]["steps"]):
			self.run_steps.append({ "index": step_index, "name": step["name"], "log_status": "pending" })

		self.status_last_timestamp = None
		self.results_last_timestamp = None


	def resume(self):
		if self.internal_status == "paused":
			self.internal_status = "running"


	def pause(self):
		if self.internal_status == "running":
			self.internal_status = "paused"


	def dispose(self):
		for step in self.run_steps:
			if "log_file" in step:
				step["log_file"].close()
		self.internal_status = "disposed"


	def reset(self, step_collection):
		for step in step_collection:
			self.run_steps[step["index"]]["log_file_cursor"] = step["log_file_cursor"]


	def update(self, messenger):
		if self.internal_status == "running":
			try:
				self._send_updates(messenger)
				self._send_log_updates(messenger)
			except Exception: # pylint: disable = broad-except
				logger.warning("%s %s failed to send updates", self.job_identifier, self.run_identifier, exc_info = True)

			if self.run_status in [ "succeeded", "failed", "aborted", "exception" ]:
				messenger.send_update({ "run": self.run_identifier, "event": "synchronization_completed" })
				self.internal_status = "done"


	def _send_updates(self, messenger):
		status_timestamp = worker_storage.get_status_timestamp(self.job_identifier, self.run_identifier)
		status = worker_storage.load_status(self.job_identifier, self.run_identifier)
		if status_timestamp != self.status_last_timestamp:
			if status["status"] != "unknown":
				messenger.send_update({ "run": self.run_identifier, "status": status })
			self.run_status = status["status"]
			self.status_last_timestamp = status_timestamp

		results_timestamp = worker_storage.get_results_timestamp(self.job_identifier, self.run_identifier)
		if results_timestamp != self.results_last_timestamp:
			results = worker_storage.load_results(self.job_identifier, self.run_identifier)
			messenger.send_update({ "run": self.run_identifier, "results": results })
			self.results_last_timestamp = results_timestamp


	def _send_log_updates(self, messenger):
		status = worker_storage.load_status(self.job_identifier, self.run_identifier)

		for step in self.run_steps:
			step_status = status["steps"][step["index"]]["status"]

			if step["log_status"] == "pending" and step_status not in [ "pending", "skipped" ]:
				log_file_path = worker_storage.get_log_path(self.job_identifier, self.run_identifier, step["index"], step["name"])
				if os.path.exists(log_file_path):
					step["log_file"] = open(log_file_path, mode = "r")
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


	def _read_lines(self, log_file, limit): # pylint: disable = no-self-use
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
