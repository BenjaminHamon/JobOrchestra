from typing import Any, Optional, Tuple

import flask
import requests


def proxy(route: str) -> requests.Response:
	method = flask.request.method
	url = flask.current_app.service_url + route

	headers = {}
	for header_key, header_value in flask.request.headers:
		if header_key in [ "Accept", "Content-Type" ] or header_key.startswith("X-Orchestra-"):
			headers[header_key] = header_value

	parameters = flask.request.args
	data = flask.request.get_data()
	authentication = _get_authentication()

	return requests.request(method, url, auth = authentication, headers = headers, params = parameters, data = data)


def get_or_default(route: str, parameters: Optional[dict] = None, default_value: Optional[Any] = None) -> Optional[Any]:
	try:
		result = get(route, parameters = parameters)
		if result is not None:
			return result
	except requests.HTTPError as exception:
		if exception.response.status_code != "404":
			raise
	return default_value


def get(route: str, parameters: Optional[dict] = None) -> Optional[Any]:
	return send_request("GET", route, headers = { "Accept": "application/json" }, parameters = parameters).json()


def post(route: str, data: Optional[Any] = None) -> Optional[Any]:
	return send_request("POST", route, headers = { "Accept": "application/json" }, data = data).json()


def send_request(method: str, route: str, headers: Optional[dict] = None,
		parameters: Optional[dict] = None, data: Optional[dict] = None) -> requests.Response:

	authentication = _get_authentication()
	if parameters is None:
		parameters = {}

	response = requests.request(method, flask.current_app.service_url + route, auth = authentication, headers = headers, params = parameters, json = data)
	response.raise_for_status()
	return response


def _get_authentication() -> Optional[Tuple[str,str]]:
	if "token" not in flask.session:
		return None
	return flask.session["token"]["user_identifier"], flask.session["token"]["secret"]
