import json

import flask
import requests


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
