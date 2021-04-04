import logging
from typing import Any

import flask


logger = logging.getLogger("RunController")


def get_count(project_identifier: str) -> Any:
	query_parameters = {
		"project": project_identifier,
		"job": flask.request.args.get("job", default = None),
		"worker": flask.request.args.get("worker", default = None),
		"status": flask.request.args.get("status", default = None),
	}

	database_client = flask.request.database_client()
	return flask.jsonify(flask.current_app.run_provider.count(database_client, **query_parameters))


def get_collection(project_identifier: str) -> Any:
	query_parameters = {
		"project": project_identifier,
		"job": flask.request.args.get("job", default = None),
		"worker": flask.request.args.get("worker", default = None),
		"status": flask.request.args.get("status", default = None),
		"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
		"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
		"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
	}

	database_client = flask.request.database_client()
	return flask.jsonify(flask.current_app.run_provider.get_list(database_client, **query_parameters))


def get(project_identifier: str, run_identifier: str) -> Any:
	database_client = flask.request.database_client()
	return flask.jsonify(flask.current_app.run_provider.get(database_client, project_identifier, run_identifier))


def get_log(project_identifier: str, run_identifier: str) -> Any:
	log_text, log_cursor = flask.current_app.run_provider.get_log(project_identifier, run_identifier)
	return flask.Response(log_text, mimetype = "text/plain", headers = { "X-Orchestra-FileCursor": log_cursor })


def get_log_chunk(project_identifier: str, run_identifier: str) -> Any:
	query_parameters = {
		"project": project_identifier,
		"run_identifier": run_identifier,
		"skip": max(flask.request.headers.get("X-Orchestra-FileCursor", default = 0, type = int), 0),
		"limit": max(flask.request.args.get("limit", default = 1024 * 1024, type = int), 0),
	}

	log_text, log_cursor = flask.current_app.run_provider.get_log_chunk(**query_parameters)
	return flask.Response(log_text, mimetype = "text/plain", headers = { "X-Orchestra-FileCursor": log_cursor })


def get_results(project_identifier: str, run_identifier: str) -> Any:
	database_client = flask.request.database_client()
	run_results = flask.current_app.run_provider.get_results(database_client, project_identifier, run_identifier)
	run_results = flask.current_app.run_result_transformer(project_identifier, run_identifier, run_results)
	return flask.jsonify(run_results)


def cancel(project_identifier: str, run_identifier: str) -> Any:
	database_client = flask.request.database_client()
	flask.current_app.run_provider.update_status(database_client, { "project": project_identifier, "identifier": run_identifier }, should_cancel = True)
	return flask.jsonify({})


def abort(project_identifier: str, run_identifier: str) -> Any:
	database_client = flask.request.database_client()
	flask.current_app.run_provider.update_status(database_client, { "project": project_identifier, "identifier": run_identifier }, should_abort = True)
	return flask.jsonify({})


def download_archive(project_identifier: str, run_identifier: str) -> Any:
	database_client = flask.request.database_client()
	archive = flask.current_app.run_provider.get_archive(database_client, project_identifier, run_identifier)
	headers = { "Content-Disposition": "attachment;filename=" + '"' + archive["file_name"] + '"' }
	return flask.Response(archive["data"], headers = headers, mimetype = "application/" + archive["type"])
