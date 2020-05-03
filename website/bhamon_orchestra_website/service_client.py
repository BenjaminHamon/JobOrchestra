import json

import flask
import requests


def proxy(route):
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


def get_or_default(route, parameters = None, default_value = None):
	try:
		result = get(route, parameters = parameters)
		if result is not None:
			return result
	except requests.HTTPError as exception:
		if exception.response.status_code != "404":
			raise
	return default_value


def get(route, parameters = None):
	return raw_get(route, headers = { "Content-Type": "application/json" }, parameters = parameters).json()


def post(route, data = None):
	return raw_post(route, headers = { "Content-Type": "application/json" }, data = data).json()


def raw_get(route, headers = None, parameters = None):
	authentication = _get_authentication()
	if parameters is None:
		parameters = {}

	response = requests.get(flask.current_app.service_url + route, auth = authentication, headers = headers, params = parameters)
	response.raise_for_status()
	return response


def raw_post(route, headers = None, data = None):
	authentication = _get_authentication()
	if data is None:
		data = {}

	response = requests.post(flask.current_app.service_url + route, auth = authentication, headers = headers, data = json.dumps(data))
	response.raise_for_status()
	return response


def _get_authentication():
	if "token" not in flask.session:
		return None
	return flask.session["token"]["user_identifier"], flask.session["token"]["secret"]
