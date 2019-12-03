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


def reload():
	task = flask.current_app.task_provider.create("reload_configuration", {})
	return flask.jsonify({ "task_identifier": task["identifier"] })
