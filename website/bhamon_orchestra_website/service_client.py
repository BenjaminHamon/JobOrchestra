from typing import Any, Optional, Tuple

import flask
import requests


class ServiceClient:


	def __init__(self, service_url: str) -> None:
		self.service_url = service_url


	def proxy(self, route: str) -> requests.Response:
		method = flask.request.method
		url = self.service_url + route

		headers = {}
		for header_key, header_value in flask.request.headers:
			if header_key in [ "Accept", "Content-Type" ] or header_key.startswith("X-Orchestra-"):
				headers[header_key] = header_value

		parameters = flask.request.args
		data = flask.request.get_data()
		authentication = self._get_authentication()

		return requests.request(method, url, auth = authentication, headers = headers, params = parameters, data = data)


	def get_or_default(self, route: str, parameters: Optional[dict] = None, default_value: Optional[Any] = None) -> Optional[Any]:
		try:
			result = self.get(route, parameters = parameters)
			if result is not None:
				return result
		except requests.HTTPError as exception:
			if exception.response.status_code != "404":
				raise
		return default_value


	def get(self, route: str, parameters: Optional[dict] = None) -> Optional[Any]:
		return self.send_request("GET", route, headers = { "Accept": "application/json" }, parameters = parameters).json()


	def post(self, route: str, data: Optional[Any] = None) -> Optional[Any]:
		return self.send_request("POST", route, headers = { "Accept": "application/json" }, data = data).json()


	def send_request(self, # pylint: disable = too-many-arguments
			method: str, route: str, headers: Optional[dict] = None,
			parameters: Optional[dict] = None, data: Optional[dict] = None) -> requests.Response:

		authentication = self._get_authentication()
		if parameters is None:
			parameters = {}

		response = requests.request(method, self.service_url + route, auth = authentication, headers = headers, params = parameters, json = data)
		response.raise_for_status()
		return response


	def _get_authentication(self) -> Optional[Tuple[str,str]]: # pylint: disable = no-self-use
		if "token" not in flask.session:
			return None
		return flask.session["token"]["user_identifier"], flask.session["token"]["secret"]
