import logging

import flask


logger = logging.getLogger("TaskController")


def get_count():
	query_parameters = {
		"type": flask.request.args.get("type", default = None),
		"status": flask.request.args.get("status", default = None),
		"run": flask.request.args.get("run", default = None),
		"worker": flask.request.args.get("worker", default = None),
	}

	return flask.jsonify(flask.current_app.task_provider.count(**query_parameters))


def get_collection():
	query_parameters = {
		"type": flask.request.args.get("type", default = None),
		"status": flask.request.args.get("status", default = None),
		"run": flask.request.args.get("run", default = None),
		"worker": flask.request.args.get("worker", default = None),
		"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
		"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
		"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
	}

	return flask.jsonify(flask.current_app.task_provider.get_list(**query_parameters))


def get(task_identifier):
	return flask.jsonify(flask.current_app.task_provider.get(task_identifier))


def cancel(task_identifier):
	task = flask.current_app.task_provider.get(task_identifier)
	if task["status"] == "pending":
		flask.current_app.task_provider.update_status(task, should_cancel = True)
	return flask.jsonify({})
