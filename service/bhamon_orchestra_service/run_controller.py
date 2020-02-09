import logging

import flask


logger = logging.getLogger("RunController")


def get_count():
	query_parameters = {
		"project": flask.request.args.get("project", default = None),
		"job": flask.request.args.get("job", default = None),
		"worker": flask.request.args.get("worker", default = None),
		"status": flask.request.args.get("status", default = None),
	}

	return flask.jsonify(flask.current_app.run_provider.count(**query_parameters))


def get_collection():
	query_parameters = {
		"project": flask.request.args.get("project", default = None),
		"job": flask.request.args.get("job", default = None),
		"worker": flask.request.args.get("worker", default = None),
		"status": flask.request.args.get("status", default = None),
		"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
		"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
		"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
	}

	return flask.jsonify(flask.current_app.run_provider.get_list(**query_parameters))


def get(run_identifier):
	return flask.jsonify(flask.current_app.run_provider.get(run_identifier))


def get_step_collection(run_identifier):
	return flask.jsonify(flask.current_app.run_provider.get_all_steps(run_identifier))


def get_step(run_identifier, step_index):
	return flask.jsonify(flask.current_app.run_provider.get_step(run_identifier, step_index))


def get_step_log(run_identifier, step_index):
	log_text, log_cursor = flask.current_app.run_provider.get_step_log(run_identifier, step_index)
	return flask.Response(log_text, mimetype = "text/plain", headers = { "X-Orchestra-FileCursor": log_cursor })


def get_step_log_chunk(run_identifier, step_index):
	query_parameters = {
		"run_identifier": run_identifier,
		"step_index": step_index,
		"skip": max(flask.request.headers.get("X-Orchestra-FileCursor", default = 0, type = int), 0),
		"limit": max(flask.request.args.get("limit", default = 1024 * 1024, type = int), 0),
	}

	log_text, log_cursor = flask.current_app.run_provider.get_step_log_chunk(**query_parameters)
	return flask.Response(log_text, mimetype = "text/plain", headers = { "X-Orchestra-FileCursor": log_cursor })


def get_results(run_identifier):
	return flask.jsonify(flask.current_app.run_provider.get_results(run_identifier))


def get_tasks(run_identifier):
	query_parameters = {
		"run": run_identifier,
		"status": flask.request.args.get("status", default = None),
		"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
		"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
		"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
	}

	return flask.jsonify(flask.current_app.task_provider.get_list(**query_parameters))


def cancel(run_identifier):
	task = flask.current_app.task_provider.create("cancel_run", { "run_identifier": run_identifier })
	return flask.jsonify({ "run_identifier": run_identifier, "task_identifier": task["identifier"] })


def abort(run_identifier):
	task = flask.current_app.task_provider.create("abort_run", { "run_identifier": run_identifier })
	return flask.jsonify({ "run_identifier": run_identifier, "task_identifier": task["identifier"] })


def download_archive(run_identifier):
	archive = flask.current_app.run_provider.get_archive(run_identifier)
	headers = { "Content-Disposition": "attachment;filename=" + '"' + archive["file_name"] + '"' }
	return flask.Response(archive["data"], headers = headers, mimetype = "application/" + archive["type"])
