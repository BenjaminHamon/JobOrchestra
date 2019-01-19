import logging

import flask


logger = logging.getLogger("TaskController")


def get_task_collection():
	return flask.jsonify(flask.current_app.task_provider.get_all())


def get_task(task_identifier):
	task = flask.current_app.task_provider.get(task_identifier)
	return flask.jsonify(task)


def cancel_task(task_identifier):
	task = flask.current_app.task_provider.get(task_identifier)
	if task["status"] == "pending":
		flask.current_app.task_provider.update(task, should_cancel = True)
	return flask.jsonify(task)
