import logging

import flask
import werkzeug


logger = logging.getLogger("Service")


def register_routes(application):
	application.add_url_rule("/", methods = [ "GET" ], view_func = home)
	application.add_url_rule("/help", methods = [ "GET" ], view_func = help)
	application.add_url_rule("/admin/reload", methods = [ "POST" ], view_func = reload)
	application.add_url_rule("/job_collection", methods = [ "GET" ], view_func = get_job_collection)
	application.add_url_rule("/job/<job_identifier>", methods = [ "GET" ], view_func = get_job)
	application.add_url_rule("/job/<job_identifier>/trigger", methods = [ "POST" ], view_func = trigger_job)
	application.add_url_rule("/job/<job_identifier>/enable", methods = [ "POST" ], view_func = enable_job)
	application.add_url_rule("/job/<job_identifier>/disable", methods = [ "POST" ], view_func = disable_job)
	application.add_url_rule("/build_collection", methods = [ "GET" ], view_func = get_build_collection)
	application.add_url_rule("/build/<build_identifier>", methods = [ "GET" ], view_func = get_build)
	application.add_url_rule("/build/<build_identifier>/step_collection", methods = [ "GET" ], view_func = get_build_step_collection)
	application.add_url_rule("/build/<build_identifier>/step/<int:step_index>", methods = [ "GET" ], view_func = get_build_step)
	application.add_url_rule("/build/<build_identifier>/step/<int:step_index>/log", methods = [ "GET" ], view_func = get_build_step_log)
	application.add_url_rule("/build/<build_identifier>/results", methods = [ "GET" ], view_func = get_build_results)
	application.add_url_rule("/build/<build_identifier>/abort", methods = [ "POST" ], view_func = abort_build)
	application.add_url_rule("/worker_collection", methods = [ "GET" ], view_func = get_worker_collection)
	application.add_url_rule("/worker/<worker_identifier>", methods = [ "GET" ], view_func = get_worker)
	application.add_url_rule("/worker/<worker_identifier>/stop", methods = [ "POST" ], view_func = stop_worker)
	application.add_url_rule("/task_collection", methods = [ "GET" ], view_func = get_task_collection)
	application.add_url_rule("/task/<task_identifier>", methods = [ "GET" ], view_func = get_task)
	application.add_url_rule("/task/<task_identifier>/cancel", methods = [ "POST" ], view_func = cancel_task)


def log_request():
	logger.info("%s %s from %s", flask.request.method, flask.request.base_url, flask.request.environ["REMOTE_ADDR"])


def handle_error(exception):
	logger.error("Failed to process request on %s", flask.request.path, exc_info = True)
	error_code = 500
	if isinstance(exception, werkzeug.exceptions.HTTPException):
		error_code = exception.code
	return flask.jsonify(str(exception)), error_code


def home():
	return flask.jsonify({})


def help():
	route_collection = []
	for rule in flask.current_app.url_map.iter_rules():
		if not rule.rule.startswith("/static/"):
			route_collection.append(rule.rule)
	route_collection.sort()
	return flask.jsonify(route_collection)


def reload():
	task = flask.current_app.task_provider.create("reload_configuration", {})
	return flask.jsonify({ "task_identifier": task["identifier"] })


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


def get_build_collection():
	return flask.jsonify(flask.current_app.build_provider.get_all())


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


def abort_build(build_identifier):
	task = flask.current_app.task_provider.create("abort_build", { "build_identifier": build_identifier })
	return flask.jsonify({ "build_identifier": build_identifier, "task_identifier": task["identifier"] })


def get_worker_collection():
	return flask.jsonify(flask.current_app.worker_provider.get_all())


def get_worker(worker_identifier):
	return flask.jsonify(flask.current_app.worker_provider.get(worker_identifier))


def stop_worker(worker_identifier):
	task = flask.current_app.task_provider.create("stop_worker", { "worker_identifier": worker_identifier })
	return flask.jsonify({ "worker_identifier": worker_identifier, "task_identifier": task["identifier"] })


def get_task_collection():
	return flask.jsonify(flask.current_app.task_provider.get_all())


def get_task(task_identifier):
	task = flask.current_app.task_provider.get(task_identifier)
	return flask.jsonify(task)


def cancel_task(task_identifier):
	task = flask.current_app.task_provider.get(task_identifier)
	if task["status"] == "pending":
		flask.current_app.task_provider.update(task, should_cancel = True)
	return flask.jsonify(task)
