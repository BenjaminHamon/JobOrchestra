import json

import flask
import requests


def get(route, parameters = None):
	headers = { "Content-Type": "application/json" }
	if parameters is None:
		parameters = {}

	response = requests.get(flask.current_app.service_url + route, headers = headers, params = parameters)
	response.raise_for_status()
	return response.json()


def get_text(route, parameters = None):
	if parameters is None:
		parameters = {}

	response = requests.get(flask.current_app.service_url + route, params = parameters)
	response.raise_for_status()
	return response.text


def post(route, data = None):
	headers = { "Content-Type": "application/json" }
	if data is None:
		data = {}

	response = requests.post(flask.current_app.service_url + route, headers = headers, data = json.dumps(data))
	response.raise_for_status()
	return response.json()
