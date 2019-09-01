import logging

import flask


logger = logging.getLogger("BuildController")


def get_build_count():
	query_parameters = {
		"job": flask.request.args.get("job", default = None),
		"worker": flask.request.args.get("worker", default = None),
		"status": flask.request.args.get("status", default = None),
	}

	return flask.jsonify(flask.current_app.build_provider.count(**query_parameters))


def get_build_collection():
	query_parameters = {
		"job": flask.request.args.get("job", default = None),
		"worker": flask.request.args.get("worker", default = None),
		"status": flask.request.args.get("status", default = None),
		"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
		"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
		"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
	}

	return flask.jsonify(flask.current_app.build_provider.get_list(**query_parameters))


def get_build(build_identifier):
	return flask.jsonify(flask.current_app.build_provider.get(build_identifier))


def get_build_step_collection(build_identifier):
	return flask.jsonify(flask.current_app.build_provider.get_all_steps(build_identifier))


def get_build_step(build_identifier, step_index):
	return flask.jsonify(flask.current_app.build_provider.get_step(build_identifier, step_index))


def get_build_step_log(build_identifier, step_index):
	log_text = flask.current_app.build_provider.get_step_log(build_identifier, step_index)
	return flask.Response(log_text, mimetype = "text/plain")


def get_build_results(build_identifier):
	return flask.jsonify(flask.current_app.build_provider.get_results(build_identifier))


def get_build_tasks(build_identifier):
	query_parameters = {
		"build": build_identifier,
		"status": flask.request.args.get("status", default = None),
		"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
		"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
		"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
	}

	return flask.jsonify(flask.current_app.task_provider.get_list(**query_parameters))


def abort_build(build_identifier):
	task = flask.current_app.task_provider.create("abort_build", { "build_identifier": build_identifier })
	return flask.jsonify({ "build_identifier": build_identifier, "task_identifier": task["identifier"] })


def download_build_archive(build_identifier):
	archive = flask.current_app.build_provider.get_archive(build_identifier)
	headers = { "Content-Disposition": "attachment;filename=" + '"' + archive["file_name"] + '"' }
	return flask.Response(archive["data"], headers = headers, mimetype = "application/" + archive["type"])
