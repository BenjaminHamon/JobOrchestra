import logging

import flask


logger = logging.getLogger("WorkerController")


def get_count():
	return flask.jsonify(flask.current_app.worker_provider.count())


def get_collection():
	query_parameters = {
		"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
		"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
		"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
	}

	return flask.jsonify(flask.current_app.worker_provider.get_list(**query_parameters))


def get(worker_identifier):
	return flask.jsonify(flask.current_app.worker_provider.get(worker_identifier))


def get_job_collection(worker_identifier): # pylint: disable = unused-argument
	query_parameters = {
		"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
		"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
		"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
	}

	return flask.jsonify(flask.current_app.job_provider.get_list(**query_parameters))


def get_run_count(worker_identifier):
	query_parameters = {
		"worker": worker_identifier,
		"project": flask.request.args.get("project", default = None),
		"status": flask.request.args.get("status", default = None),
	}

	return flask.jsonify(flask.current_app.run_provider.count(**query_parameters))


def get_run_collection(worker_identifier):
	query_parameters = {
		"worker": worker_identifier,
		"project": flask.request.args.get("project", default = None),
		"status": flask.request.args.get("status", default = None),
		"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
		"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
		"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
	}

	return flask.jsonify(flask.current_app.run_provider.get_list(**query_parameters))


def get_tasks(worker_identifier):
	query_parameters = {
		"worker": worker_identifier,
		"status": flask.request.args.get("status", default = None),
		"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
		"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
		"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
	}

	return flask.jsonify(flask.current_app.task_provider.get_list(**query_parameters))


def stop(worker_identifier):
	task = flask.current_app.task_provider.create("stop_worker", { "worker_identifier": worker_identifier })
	return flask.jsonify({ "worker_identifier": worker_identifier, "task_identifier": task["identifier"] })


def enable(worker_identifier):
	flask.current_app.worker_provider.update_status({ "identifier": worker_identifier }, is_enabled = True)
	return flask.jsonify({})


def disable(worker_identifier):
	flask.current_app.worker_provider.update_status({ "identifier": worker_identifier }, is_enabled = False)
	return flask.jsonify({})
