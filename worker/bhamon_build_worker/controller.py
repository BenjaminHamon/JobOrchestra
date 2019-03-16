import json
import logging
import time

import requests

import bhamon_build_worker.workspace as workspace


logger = logging.getLogger("Controller")

request_attempt_delay_collection = [ 10, 10, 10, 10, 10, 60, 60, 60, 300 ]
wait_delay_seconds = 10


def trigger_build(service_url, result_file_path, job_identifier, parameters):
	message = "Triggering build for job %s" % job_identifier
	response = _try_request(message, lambda: _service_post(service_url, "/job/" + job_identifier + "/trigger", parameters))
	logger.info("Build: %s, Task: %s", response["build_identifier"], response["task_identifier"])

	results = workspace.load_results(result_file_path)
	results["child_builds"] = results.get("child_builds", [])
	results["child_builds"].append(response)
	workspace.save_results(result_file_path, results)


def wait_build(service_url, result_file_path):
	results = workspace.load_results(result_file_path)

	for build in results["child_builds"]:
		build["build_status"] = "unknown"

	while any(build["build_status"] in [ "unknown", "pending", "running" ] for build in results["child_builds"]):
		time.sleep(wait_delay_seconds)

		for build in results["child_builds"]:
			if build["build_status"] in [ "unknown", "pending", "running" ]:
				response = _try_request(None, lambda: _service_get(service_url, "/build/" + build["build_identifier"]))
				if build["build_status"] in [ "unknown", "pending" ] and response["status"] == "running":
					logger.info("Build %s is running", response["identifier"])
				build["build_status"] = response["status"]
				if response["status"] not in [ "pending", "running" ]:
					logger.info("Build %s completed with status %s", response["identifier"], response["status"])

	if any(build["build_status"] != "succeeded" for build in results["child_builds"]):
		raise RuntimeError("One or more builds failed")


def _try_request(message, send_request):
	request_attempt_counter = 0

	while True:
		try:
			request_attempt_counter += 1
			if message:
				logger.info("%s (Attempt: %s)", message, request_attempt_counter)
			return send_request()

		except requests.exceptions.ConnectionError as exception:
			try:
				request_attempt_delay = request_attempt_delay_collection[request_attempt_counter]
			except IndexError:
				request_attempt_delay = request_attempt_delay_collection[-1]
			if message:
				logger.warning("Request failed: %s (retrying in %s seconds)", exception, request_attempt_delay)
			time.sleep(request_attempt_delay)


def _service_get(service_url, route, parameters = None):
	headers = { "Content-Type": "application/json" }
	if parameters is None:
		parameters = {}

	response = requests.get(service_url + route, headers = headers, params = parameters)
	response.raise_for_status()
	return response.json()


def _service_post(service_url, route, data = None):
	if data is None:
		data = {}

	headers = { "Content-Type": "application/json" }
	response = requests.post(service_url + route, headers = headers, data = json.dumps(data))
	response.raise_for_status()
	return response.json()
