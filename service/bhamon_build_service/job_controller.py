import logging

import flask


logger = logging.getLogger("JobController")


def get_job_count():
	return flask.jsonify(flask.current_app.job_provider.count())


def get_job_collection():
	skip = max(flask.request.args.get("skip", default = 0, type = int), 0)
	limit = max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0)
	order_by = [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ]
	return flask.jsonify(flask.current_app.job_provider.get_list(skip = skip, limit = limit, order_by = order_by))


def get_job(job_identifier):
	return flask.jsonify(flask.current_app.job_provider.get(job_identifier))


def get_job_builds(job_identifier):
	skip = max(flask.request.args.get("skip", default = 0, type = int), 0)
	limit = max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0)
	order_by = [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ]
	return flask.jsonify(flask.current_app.build_provider.get_list_for_job(job_identifier, skip = skip, limit = limit, order_by = order_by))


def trigger_job(job_identifier):
	parameters = flask.request.get_json()
	build = flask.current_app.build_provider.create(job_identifier, parameters)
	task = flask.current_app.task_provider.create("trigger_build", { "build_identifier": build["identifier"] })
	return flask.jsonify({ "job_identifier": job_identifier, "build_identifier": build["identifier"], "task_identifier": task["identifier"] })


def enable_job(job_identifier):
	flask.current_app.job_provider.update_status({ "identifier": job_identifier }, is_enabled = True)
	return flask.jsonify({})


def disable_job(job_identifier):
	flask.current_app.job_provider.update_status({ "identifier": job_identifier }, is_enabled = False)
	return flask.jsonify({})
