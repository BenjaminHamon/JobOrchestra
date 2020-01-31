import logging

import flask


logger = logging.getLogger("JobController")


def get_job_count():
	query_parameters = {
		"project": flask.request.args.get("project", default = None),
	}

	return flask.jsonify(flask.current_app.job_provider.count(**query_parameters))


def get_job_collection():
	query_parameters = {
		"project": flask.request.args.get("project", default = None),
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
	job = flask.current_app.job_provider.get(job_identifier)
	run = flask.current_app.run_provider.create(job["project"], job_identifier, parameters)
	return flask.jsonify({ "job_identifier": job_identifier, "run_identifier": run["identifier"] })


def enable_job(job_identifier):
	flask.current_app.job_provider.update_status({ "identifier": job_identifier }, is_enabled = True)
	return flask.jsonify({})


def disable_job(job_identifier):
	flask.current_app.job_provider.update_status({ "identifier": job_identifier }, is_enabled = False)
	return flask.jsonify({})
