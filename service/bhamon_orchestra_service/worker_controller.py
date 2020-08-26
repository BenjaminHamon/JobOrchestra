import logging

import flask


logger = logging.getLogger("WorkerController")


def get_count():
	database_client = flask.request.database_client()
	return flask.jsonify(flask.current_app.worker_provider.count(database_client))


def get_collection():
	query_parameters = {
		"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
		"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
		"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
	}

	database_client = flask.request.database_client()
	return flask.jsonify(flask.current_app.worker_provider.get_list(database_client, **query_parameters))


def get(worker_identifier):
	database_client = flask.request.database_client()
	return flask.jsonify(flask.current_app.worker_provider.get(database_client, worker_identifier))


def get_job_collection(worker_identifier): # pylint: disable = unused-argument
	query_parameters = {
		"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
		"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
		"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
	}

	database_client = flask.request.database_client()
	return flask.jsonify(flask.current_app.job_provider.get_list(database_client, **query_parameters))


def get_run_count(worker_identifier):
	query_parameters = {
		"worker": worker_identifier,
		"project": flask.request.args.get("project", default = None),
		"status": flask.request.args.get("status", default = None),
	}

	database_client = flask.request.database_client()
	return flask.jsonify(flask.current_app.run_provider.count(database_client, **query_parameters))


def get_run_collection(worker_identifier):
	query_parameters = {
		"worker": worker_identifier,
		"project": flask.request.args.get("project", default = None),
		"status": flask.request.args.get("status", default = None),
		"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
		"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
		"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
	}

	database_client = flask.request.database_client()
	return flask.jsonify(flask.current_app.run_provider.get_list(database_client, **query_parameters))


def disconnect(worker_identifier):
	database_client = flask.request.database_client()
	flask.current_app.worker_provider.update_status(database_client, { "identifier": worker_identifier }, should_disconnect = True)
	return flask.jsonify({})


def enable(worker_identifier):
	database_client = flask.request.database_client()
	flask.current_app.worker_provider.update_status(database_client, { "identifier": worker_identifier }, is_enabled = True)
	return flask.jsonify({})


def disable(worker_identifier):
	database_client = flask.request.database_client()
	flask.current_app.worker_provider.update_status(database_client, { "identifier": worker_identifier }, is_enabled = False)
	return flask.jsonify({})
