import json

import flask
import requests


def get(route, parameters = None):
	authentication = (flask.session["token"]["user_identifier"], flask.session["token"]["secret"]) if "token" in flask.session else None
	headers = { "Content-Type": "application/json" }
	if parameters is None:
		parameters = {}

	response = requests.get(flask.current_app.service_url + route, auth = authentication, headers = headers, params = parameters)
	response.raise_for_status()
	return response.json()


def get_text(route, parameters = None):
	authentication = (flask.session["token"]["user_identifier"], flask.session["token"]["secret"]) if "token" in flask.session else None
	if parameters is None:
		parameters = {}

	response = requests.get(flask.current_app.service_url + route, auth = authentication, params = parameters)
	response.raise_for_status()
	return response.text


def post(route, data = None):
	authentication = (flask.session["token"]["user_identifier"], flask.session["token"]["secret"]) if "token" in flask.session else None
	headers = { "Content-Type": "application/json" }
	if data is None:
		data = {}

	response = requests.post(flask.current_app.service_url + route, auth = authentication, headers = headers, data = json.dumps(data))
	response.raise_for_status()
	return response.json()
