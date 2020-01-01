import logging

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


	def update(self, messenger):
		if self.internal_status == "running":
			try:
				self._send_updates(messenger)
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

		for step in self.run_steps:
			step_status = status["steps"][step["index"]]["status"]
			if step["log_status"] == "pending":
				if step_status == "skipped":
					step["log_status"] = "done"
				elif step_status in [ "succeeded", "failed", "aborted", "exception" ]:
					log_text = worker_storage.load_log(self.job_identifier, self.run_identifier, step["index"], step["name"])
					messenger.send_update({ "run": self.run_identifier, "step_index": step["index"], "step_name": step["name"], "log_text": log_text })
					step["status"] = "done"
