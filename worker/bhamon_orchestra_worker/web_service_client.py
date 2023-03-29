import datetime
import logging
from typing import Any, Optional, Tuple

import requests

from bhamon_orchestra_model.serialization.serializer import Serializer
from bhamon_orchestra_worker.service_client import ServiceClient


logger = logging.getLogger("WebServiceClient")


class WebServiceClient(ServiceClient):
	""" Implementation of ServiceClient for a web service """


	def __init__(self, serializer: Serializer, service_url: str, authorization: Optional[Tuple[str,str]]) -> None:
		self._serializer = serializer
		self.service_url = service_url
		self.authorization = authorization
		self.timeout = datetime.timedelta(seconds = 30)


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


	def send_request(self, method: str, route: str, parameters: Optional[dict] = None, data: Optional[Any] = None) -> Optional[Any]:
		logger.debug("%s %s", method, self.service_url + route)

		headers = { "Accept": self._serializer.get_content_type() }

		serialized_data = None
		if data is not None:
			headers["Content-Type"] = self._serializer.get_content_type()
			serialized_data = self._serializer.serialize_to_string(data)

		response = requests.request(method, self.service_url + route,
			auth = self.authorization, headers = headers, params = parameters, data = serialized_data, timeout = self.timeout.total_seconds())

		response.raise_for_status()

		if response.status_code == 204:
			return None

		if response.headers["Content-Type"].split(";")[0] == self._serializer.get_content_type():
			return self._serializer.deserialize_from_string(response.text)

		raise RuntimeError("Unsupported response content-type '%s'" % response.headers["Content-Type"])
