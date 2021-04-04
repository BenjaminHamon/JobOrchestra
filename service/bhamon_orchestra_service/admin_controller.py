import logging
import platform

import flask


logger = logging.getLogger("AdminController")


def information():
	return flask.jsonify({
		"python_version": platform.python_version() + "+" + platform.python_revision(),
		"service_version": flask.current_app.config["SERVICE_VERSION"],
		"service_date": flask.current_app.config["SERVICE_DATE"],
	})


def get_service_collection():
	return flask.jsonify(list(sorted(flask.current_app.external_services.keys())))


def get_service_status(service_identifier):
	service = flask.current_app.external_services.get(service_identifier, None)
	if service is None:
		flask.abort(404)
	return flask.jsonify(service.get_service_status())
