import logging
from typing import Any, Optional, Tuple

import requests

from bhamon_orchestra_worker.service_client import ServiceClient


logger = logging.getLogger("WebServiceClient")


class WebServiceClient(ServiceClient):
	""" Implementation of ServiceClient for a web service """


	def __init__(self, service_url: str, authorization: Optional[Tuple[str,str]]) -> None:
		self.service_url = service_url
		self.authorization = authorization


	def get_run(self, project_identifier: str, run_identifier: str) -> dict: # pylint: disable = unused-argument
		route = "/project/{project_identifier}/run/{run_identifier}".format(**locals())
		return self.send_request("GET", route)


	def trigger_job(self, project_identifier: str, job_identifier: str, parameters: dict, source: dict) -> dict: # pylint: disable = unused-argument
		route = "/project/{project_identifier}/job/{job_identifier}/trigger".format(**locals())
		trigger_data = { "parameters": parameters, "source": source }
		return self.send_request("POST", route, data = trigger_data)


	def cancel_run(self, project_identifier: str, run_identifier: str) -> None: # pylint: disable = unused-argument
		route = "/project/{project_identifier}/run/{run_identifier}/cancel".format(**locals())
		self.send_request("POST", route)


	def abort_run(self, project_identifier: str, run_identifier: str) -> None: # pylint: disable = unused-argument
		route = "/project/{project_identifier}/run/{run_identifier}/abort".format(**locals())
		self.send_request("POST", route)


	def send_request(self, method: str, route: str, parameters: Optional[dict] = None, data: Optional[dict] = None) -> Any:
		logger.debug("%s %s", method, self.service_url + route)

		headers = { "Accept": "application/json" }
		if parameters is None:
			parameters = {}

		response = requests.request(method, self.service_url + route, auth = self.authorization, headers = headers, params = parameters, json = data)
		response.raise_for_status()
		return response.json()
