import logging

import flask


logger = logging.getLogger("WorkerController")


def get_worker_count():
	return flask.jsonify(flask.current_app.worker_provider.count())


def get_worker_collection():
	skip = max(flask.request.args.get("skip", default = 0, type = int), 0)
	limit = max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0)
	return flask.jsonify(flask.current_app.worker_provider.get_list(skip = skip, limit = limit))


def get_worker(worker_identifier):
	return flask.jsonify(flask.current_app.worker_provider.get(worker_identifier))


def get_worker_builds(worker_identifier):
	skip = max(flask.request.args.get("skip", default = 0, type = int), 0)
	limit = max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0)
	return flask.jsonify(flask.current_app.build_provider.get_list_for_worker(worker_identifier, skip = skip, limit = limit))


def get_worker_tasks(worker_identifier):
	skip = max(flask.request.args.get("skip", default = 0, type = int), 0)
	limit = max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0)
	return flask.jsonify(flask.current_app.task_provider.get_list_for_worker(worker_identifier, skip = skip, limit = limit))


def stop_worker(worker_identifier):
	task = flask.current_app.task_provider.create("stop_worker", { "worker_identifier": worker_identifier })
	return flask.jsonify({ "worker_identifier": worker_identifier, "task_identifier": task["identifier"] })


def enable_worker(worker_identifier):
	flask.current_app.worker_provider.update_status({ "identifier": worker_identifier }, is_enabled = True)
	return flask.jsonify({})


def disable_worker(worker_identifier):
	flask.current_app.worker_provider.update_status({ "identifier": worker_identifier }, is_enabled = False)
	return flask.jsonify({})
