import logging

import flask


logger = logging.getLogger("WorkerController")


def get_worker_count():
	return flask.jsonify(flask.current_app.worker_provider.count())


def get_worker_collection():
	query_parameters = {
		"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
		"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
		"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
	}
	
	return flask.jsonify(flask.current_app.worker_provider.get_list(**query_parameters))


def get_worker(worker_identifier):
	return flask.jsonify(flask.current_app.worker_provider.get(worker_identifier))


def get_worker_builds(worker_identifier):
	query_parameters = {
		"worker": worker_identifier,
		"status": flask.request.args.get("status", default = None),
		"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
		"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
		"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
	}

	return flask.jsonify(flask.current_app.build_provider.get_list(**query_parameters))


def get_worker_tasks(worker_identifier):
	query_parameters = {
		"worker": worker_identifier,
		"status": flask.request.args.get("status", default = None),
		"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
		"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
		"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
	}

	return flask.jsonify(flask.current_app.task_provider.get_list(**query_parameters))


def stop_worker(worker_identifier):
	task = flask.current_app.task_provider.create("stop_worker", { "worker_identifier": worker_identifier })
	return flask.jsonify({ "worker_identifier": worker_identifier, "task_identifier": task["identifier"] })


def enable_worker(worker_identifier):
	flask.current_app.worker_provider.update_status({ "identifier": worker_identifier }, is_enabled = True)
	return flask.jsonify({})


def disable_worker(worker_identifier):
	flask.current_app.worker_provider.update_status({ "identifier": worker_identifier }, is_enabled = False)
	return flask.jsonify({})
