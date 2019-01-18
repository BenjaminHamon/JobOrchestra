import json

import flask
import requests


def get(route, parameters = {}):
	headers = { "Content-Type": "application/json" }
	response = requests.get(flask.current_app.service_url + route, headers = headers, params = parameters)
	response.raise_for_status()
	return response.json()


def get_text(route, parameters = {}):
	response = requests.get(flask.current_app.service_url + route, params = parameters)
	response.raise_for_status()
	return response.text


def post(route, data = {}):
	headers = { "Content-Type": "application/json" }
	response = requests.post(flask.current_app.service_url + route, headers = headers, data = json.dumps(data))
	response.raise_for_status()
	return response.json()
