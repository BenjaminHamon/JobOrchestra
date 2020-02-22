import json
import logging
import time

import requests

import bhamon_orchestra_worker.workspace as workspace


logger = logging.getLogger("Controller")


class Controller:


	def __init__(self, service_url, authorization):
		self.service_url = service_url
		self.authorization = authorization

		self.request_attempt_delay_collection = [ 10, 10, 10, 10, 10, 60, 60, 60, 300 ]
		self.wait_delay_seconds = 10


	def trigger_run(self, result_file_path, project_identifier, job_identifier, parameters):
		message = "Triggering run for job %s" % job_identifier
		route = "/project/{project_identifier}/job/{job_identifier}/trigger".format(**locals())
		response = self._try_request(message, lambda: self._service_post(route, data = parameters))
		logger.info("Run: %s", response["run_identifier"])

		results = workspace.load_results(result_file_path)
		results["child_runs"] = results.get("child_runs", [])
		results["child_runs"].append(response)
		workspace.save_results(result_file_path, results)


	def wait_run(self, result_file_path):
		results = workspace.load_results(result_file_path)

		for run in results["child_runs"]:
			run["run_status"] = "unknown"

		while any(run["run_status"] in [ "unknown", "pending", "running" ] for run in results["child_runs"]):
			time.sleep(self.wait_delay_seconds)

			for run in results["child_runs"]:
				if run["run_status"] in [ "unknown", "pending", "running" ]:
					response = self._try_request(None, lambda: self._service_get("/run/" + run["run_identifier"]))
					if run["run_status"] in [ "unknown", "pending" ] and response["status"] == "running":
						logger.info("run %s is running", response["identifier"])
					run["run_status"] = response["status"]
					if response["status"] not in [ "pending", "running" ]:
						logger.info("Run %s completed with status %s", response["identifier"], response["status"])

		if any(run["run_status"] != "succeeded" for run in results["child_runs"]):
			raise RuntimeError("One or more runs failed")


	def _try_request(self, message, send_request):
		request_attempt_counter = 0

		while True:
			try:
				request_attempt_counter += 1
				if message:
					logger.info("%s (Attempt: %s)", message, request_attempt_counter)
				return send_request()

			except requests.exceptions.ConnectionError as exception:
				try:
					request_attempt_delay = self.request_attempt_delay_collection[request_attempt_counter]
				except IndexError:
					request_attempt_delay = self.request_attempt_delay_collection[-1]
				if message:
					logger.warning("Request failed: %s (retrying in %s seconds)", exception, request_attempt_delay)
				time.sleep(request_attempt_delay)


	def _service_get(self, route, parameters = None):
		headers = { "Content-Type": "application/json" }
		if parameters is None:
			parameters = {}

		response = requests.get(self.service_url + route, auth = self.authorization, headers = headers, params = parameters)
		response.raise_for_status()
		return response.json()


	def _service_post(self, route, data = None):
		if data is None:
			data = {}

		headers = { "Content-Type": "application/json" }
		response = requests.post(self.service_url + route, auth = self.authorization, headers = headers, data = json.dumps(data))
		response.raise_for_status()
		return response.json()
