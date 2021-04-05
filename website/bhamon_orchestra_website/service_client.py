import json
import logging
from typing import Any, Optional, Tuple

import flask
import requests


logger = logging.getLogger("ServiceClient")


class ServiceClient:


	def __init__(self, service_url: str) -> None:
		self.service_url = service_url


	def get(self, route: str, parameters: Optional[dict] = None) -> Optional[Any]:
		return self.send_request("GET", route, parameters = parameters)


	def get_or_default(self, route: str, parameters: Optional[dict] = None, default_value: Optional[Any] = None) -> Optional[Any]:
		try:
			result = self.get(route, parameters = parameters)
			if result is not None:
				return result
		except requests.HTTPError as exception:
			if exception.response.status_code != "404":
				raise
		return default_value


	def post(self, route: str, parameters: Optional[dict] = None, data: Optional[Any] = None) -> Optional[Any]:
		return self.send_request("POST", route, parameters = parameters, data = data)


	def send_request(self, method: str, route: str, parameters: Optional[dict] = None, data: Optional[Any] = None) -> Optional[Any]:
		logger.debug("%s %s", method, self.service_url + route)

		authentication = self._get_authentication()
		headers = { "Accept": "application/json" }

		serialized_data = None
		if data is not None:
			headers["Content-Type"] = "application/json"
			serialized_data = json.dumps(data)

		response = requests.request(method, self.service_url + route, auth = authentication, headers = headers, params = parameters, data = serialized_data)

		response.raise_for_status()

		if response.status_code == 204:
			return None

		if response.headers["Content-Type"].split(";")[0] == "application/json":
			return json.loads(response.text)
		if response.headers["Content-Type"].split(";")[0] == "text/plain":
			return response.text

		raise RuntimeError("Unsupported response content-type '%s'" % response.headers["Content-Type"])


	def download(self, route: str, parameters: Optional[dict] = None) -> requests.Response:
		logger.debug("GET %s", self.service_url + route)

		authentication = self._get_authentication()

		response = requests.get(self.service_url + route, auth = authentication, params = parameters)
		response.raise_for_status()
		return response


	def proxy(self, route: str) -> requests.Response:
		logger.debug("%s %s", flask.request.method, self.service_url + route)

		authentication = self._get_authentication()

		headers = {}
		for header_key, header_value in flask.request.headers:
			if header_key in [ "Accept", "Content-Type" ] or header_key.startswith("X-Orchestra-"):
				headers[header_key] = header_value

		parameters = flask.request.args
		data = flask.request.get_data()

		return requests.request(flask.request.method, self.service_url + route, auth = authentication, headers = headers, params = parameters, data = data)


	def _get_authentication(self) -> Optional[Tuple[str,str]]: # pylint: disable = no-self-use
		if "token" not in flask.session:
			return None
		return flask.session["token"]["user_identifier"], flask.session["token"]["secret"]
