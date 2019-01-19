import logging

import flask


logger = logging.getLogger("JobController")


def get_job_collection():
	return flask.jsonify(flask.current_app.job_provider.get_all())


def get_job(job_identifier):
	return flask.jsonify(flask.current_app.job_provider.get(job_identifier))


def trigger_job(job_identifier):
	parameters = flask.request.get_json()
	build = flask.current_app.build_provider.create(job_identifier, parameters)
	task = flask.current_app.task_provider.create("trigger_build", { "build_identifier": build["identifier"] })
	return flask.jsonify({ "job_identifier": job_identifier, "build_identifier": build["identifier"], "task_identifier": task["identifier"] })


def enable_job(job_identifier):
	flask.current_app.job_provider.update_status(job_identifier, is_enabled = True)
	return flask.jsonify({})


def disable_job(job_identifier):
	flask.current_app.job_provider.update_status(job_identifier, is_enabled = False)
	return flask.jsonify({})
