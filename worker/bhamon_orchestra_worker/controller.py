import logging
import time

import requests

from bhamon_orchestra_worker import workspace
from bhamon_orchestra_worker.service_client import ServiceClient


logger = logging.getLogger("Controller")


class Controller:


	def __init__(self, service_client: ServiceClient, trigger_source: dict, result_file_path: str) -> None:
		self.service_client = service_client
		self.trigger_source = trigger_source
		self.result_file_path = result_file_path

		self.all_inner_runs = []

		self.wait_delay_seconds = 10


	def reload(self) -> None:
		results = workspace.load_results(self.result_file_path)
		self.all_inner_runs = results.get("inner_runs", [])


	def trigger(self, project_identifier: str, job_identifier: str, parameters: dict) -> None:
		logger.info("Triggering run for project '%s' and job '%s'", project_identifier, job_identifier)

		trigger_response = self.service_client.trigger_job(project_identifier, job_identifier, parameters, self.trigger_source)

		inner_run = {
			"project": trigger_response["project_identifier"],
			"job": trigger_response["job_identifier"],
			"identifier": trigger_response["run_identifier"],
			"status": "pending",
		}

		self.all_inner_runs.append(inner_run)

		logger.info("Triggered run '%s'", inner_run["identifier"])

		self._save_results()


	def wait(self) -> None:
		while not self.is_completed():
			time.sleep(self.wait_delay_seconds)

			try:
				for inner_run in self.all_inner_runs:
					self._update_inner_run(inner_run)
			except requests.ConnectionError:
				logger.warning("Connection error during update", exc_info = True)

		status = self.compute_status()

		if status == "failed":
			raise RuntimeError("One or more runs failed")
		if status == "aborted":
			raise RuntimeError("One or more runs was aborted or cancelled")


	def is_completed(self) -> bool:
		return all(inner_run["status"] in [ "succeeded", "failed", "exception", "aborted", "cancelled" ] for inner_run in self.all_inner_runs)


	def compute_status(self) -> str:
		if any(inner_run["status"] in [ "pending", "running" ] for inner_run in self.all_inner_runs):
			return "running"
		if any(inner_run["status"] in [ "failed", "exception" ] for inner_run in self.all_inner_runs):
			return "failed"
		if any(inner_run["status"] in [ "cancelled", "aborted" ] for inner_run in self.all_inner_runs):
			return "aborted"
		return "succeeded"


	def _update_inner_run(self, inner_run: dict) -> None:
		logger.debug("Updating '%s'", inner_run["identifier"])

		last_status = inner_run["status"]
		if last_status in [ "unknown", "pending", "running" ]:
			run_record = self.service_client.get_run(inner_run["project"], inner_run["identifier"])
			inner_run["status"] = run_record["status"]

		if last_status in [ "unknown", "pending" ] and inner_run["status"] == "running":
			logger.info("Started run '%s'", inner_run["identifier"])
		if last_status in [ "unknown", "pending", "running" ] and inner_run["status"] not in [ "pending", "running" ]:
			logger.info("Completed run '%s' with status '%s'", inner_run["identifier"], inner_run["status"])


	def _save_results(self) -> None:
		results = workspace.load_results(self.result_file_path)
		results["inner_runs"] = self.all_inner_runs
		workspace.save_results(self.result_file_path, results)
