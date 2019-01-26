import logging

import flask


logger = logging.getLogger("TaskController")


def get_task_count():
	return flask.jsonify(flask.current_app.task_provider.count())


def get_task_collection():
	skip = max(flask.request.args.get("skip", default = 0, type = int), 0)
	limit = max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0)
	order_by = [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ]
	return flask.jsonify(flask.current_app.task_provider.get_list(skip = skip, limit = limit, order_by = order_by))


def get_task(task_identifier):
	task = flask.current_app.task_provider.get(task_identifier)
	return flask.jsonify(task)


def cancel_task(task_identifier):
	task = flask.current_app.task_provider.get(task_identifier)
	if task["status"] == "pending":
		flask.current_app.task_provider.update(task, should_cancel = True)
	return flask.jsonify({})
