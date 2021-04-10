import logging
from typing import Any

import flask


logger = logging.getLogger("JobController")


def get_count(project_identifier: str) -> Any:
	query_parameters = {
		"project": project_identifier,
	}

	return flask.jsonify(flask.current_app.job_provider.count(flask.request.database_client(), **query_parameters))


def get_collection(project_identifier: str) -> Any:
	query_parameters = {
		"project": project_identifier,
		"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
		"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
		"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
	}

	return flask.jsonify(flask.current_app.job_provider.get_list(flask.request.database_client(), **query_parameters))


def get(project_identifier: str, job_identifier: str) -> Any:
	return flask.jsonify(flask.current_app.job_provider.get(flask.request.database_client(), project_identifier, job_identifier))


def get_runs(project_identifier: str, job_identifier: str) -> Any:
	query_parameters = {
		"project": project_identifier,
		"job": job_identifier,
		"status": flask.request.args.get("status", default = None),
		"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
		"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
		"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
	}

	return flask.jsonify(flask.current_app.run_provider.get_list(flask.request.database_client(), **query_parameters))


def trigger(project_identifier: str, job_identifier: str) -> Any:
	trigger_data = flask.request.get_json()
	job = flask.current_app.job_provider.get(flask.request.database_client(), project_identifier, job_identifier)
	run = flask.current_app.run_provider.create(flask.request.database_client(), job["project"], job_identifier, **trigger_data)
	return flask.jsonify({ "project_identifier": project_identifier, "job_identifier": job_identifier, "run_identifier": run["identifier"] })


def enable(project_identifier: str, job_identifier: str) -> Any:
	flask.current_app.job_provider.update_status(flask.request.database_client(), { "project": project_identifier, "identifier": job_identifier }, is_enabled = True)
	return flask.jsonify({})


def disable(project_identifier: str, job_identifier: str) -> Any:
	flask.current_app.job_provider.update_status(flask.request.database_client(), { "project": project_identifier, "identifier": job_identifier }, is_enabled = False)
	return flask.jsonify({})
