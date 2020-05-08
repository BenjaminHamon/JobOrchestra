import logging
import platform

import flask

import bhamon_orchestra_service


logger = logging.getLogger("AdminController")


def information():
	return flask.jsonify({
		"python_version": platform.python_version() + "+" + platform.python_revision(),
		"service_version": bhamon_orchestra_service.__version__,
		"service_version_date": bhamon_orchestra_service.__date__,
	})


def get_service_collection():
	return flask.jsonify(list(sorted(flask.current_app.external_services.keys())))


def get_service_status(service_identifier):
	service = flask.current_app.external_services.get(service_identifier, None)
	if service is None:
		flask.abort(404)
	return flask.jsonify(service.get_service_status())
