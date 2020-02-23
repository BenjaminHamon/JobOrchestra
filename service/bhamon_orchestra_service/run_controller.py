import logging

import flask


logger = logging.getLogger("RunController")


def get_count(project_identifier):
	query_parameters = {
		"project": project_identifier,
		"job": flask.request.args.get("job", default = None),
		"worker": flask.request.args.get("worker", default = None),
		"status": flask.request.args.get("status", default = None),
	}

	return flask.jsonify(flask.current_app.run_provider.count(**query_parameters))


def get_collection(project_identifier):
	query_parameters = {
		"project": project_identifier,
		"job": flask.request.args.get("job", default = None),
		"worker": flask.request.args.get("worker", default = None),
		"status": flask.request.args.get("status", default = None),
		"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
		"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
		"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
	}

	return flask.jsonify(flask.current_app.run_provider.get_list(**query_parameters))


def get(project_identifier, run_identifier):
	return flask.jsonify(flask.current_app.run_provider.get(project_identifier, run_identifier))


def get_step_collection(project_identifier, run_identifier):
	return flask.jsonify(flask.current_app.run_provider.get_all_steps(project_identifier, run_identifier))


def get_step(project_identifier, run_identifier, step_index):
	return flask.jsonify(flask.current_app.run_provider.get_step(project_identifier, run_identifier, step_index))


def get_step_log(project_identifier, run_identifier, step_index):
	log_text, log_cursor = flask.current_app.run_provider.get_step_log(project_identifier, run_identifier, step_index)
	return flask.Response(log_text, mimetype = "text/plain", headers = { "X-Orchestra-FileCursor": log_cursor })


def get_step_log_chunk(project_identifier, run_identifier, step_index):
	query_parameters = {
		"project": project_identifier,
		"run_identifier": run_identifier,
		"step_index": step_index,
		"skip": max(flask.request.headers.get("X-Orchestra-FileCursor", default = 0, type = int), 0),
		"limit": max(flask.request.args.get("limit", default = 1024 * 1024, type = int), 0),
	}

	log_text, log_cursor = flask.current_app.run_provider.get_step_log_chunk(**query_parameters)
	return flask.Response(log_text, mimetype = "text/plain", headers = { "X-Orchestra-FileCursor": log_cursor })


def get_results(project_identifier, run_identifier):
	run_results = flask.current_app.run_provider.get_results(project_identifier, run_identifier)
	run_results = flask.current_app.run_result_transformer(project_identifier, run_identifier, run_results)
	return flask.jsonify(run_results)


def get_tasks(project_identifier, run_identifier):
	query_parameters = {
		"project": project_identifier,
		"run": run_identifier,
		"status": flask.request.args.get("status", default = None),
		"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
		"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
		"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
	}

	return flask.jsonify(flask.current_app.task_provider.get_list(**query_parameters))


def cancel(project_identifier, run_identifier):
	task = flask.current_app.task_provider.create("cancel_run", { "project_identifier": project_identifier, "run_identifier": run_identifier })
	return flask.jsonify({ "project_identifier": project_identifier, "run_identifier": run_identifier, "task_identifier": task["identifier"] })


def abort(project_identifier, run_identifier):
	task = flask.current_app.task_provider.create("abort_run", { "project_identifier": project_identifier, "run_identifier": run_identifier })
	return flask.jsonify({ "project_identifier": project_identifier, "run_identifier": run_identifier, "task_identifier": task["identifier"] })


def download_archive(project_identifier, run_identifier):
	archive = flask.current_app.run_provider.get_archive(project_identifier, run_identifier)
	headers = { "Content-Disposition": "attachment;filename=" + '"' + archive["file_name"] + '"' }
	return flask.Response(archive["data"], headers = headers, mimetype = "application/" + archive["type"])
