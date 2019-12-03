import logging

import flask


logger = logging.getLogger("JobController")


def get_job_count():
	return flask.jsonify(flask.current_app.job_provider.count())


def get_job_collection():
	query_parameters = {
		"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
		"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
		"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
	}

	return flask.jsonify(flask.current_app.job_provider.get_list(**query_parameters))


def get_job(job_identifier):
	return flask.jsonify(flask.current_app.job_provider.get(job_identifier))


def get_job_runs(job_identifier):
	query_parameters = {
		"job": job_identifier,
		"status": flask.request.args.get("status", default = None),
		"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
		"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
		"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
	}

	return flask.jsonify(flask.current_app.run_provider.get_list(**query_parameters))


def trigger_job(job_identifier):
	parameters = flask.request.get_json()
	run = flask.current_app.run_provider.create(job_identifier, parameters)
	task = flask.current_app.task_provider.create("trigger_run", { "run_identifier": run["identifier"] })
	return flask.jsonify({ "job_identifier": job_identifier, "run_identifier": run["identifier"], "task_identifier": task["identifier"] })


def enable_job(job_identifier):
	flask.current_app.job_provider.update_status({ "identifier": job_identifier }, is_enabled = True)
	return flask.jsonify({})


def disable_job(job_identifier):
	flask.current_app.job_provider.update_status({ "identifier": job_identifier }, is_enabled = False)
	return flask.jsonify({})
