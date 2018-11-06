import logging

import flask
import werkzeug


logger = logging.getLogger("Service")

logger.info("Starting build master service")

application = flask.Flask(__name__)
application.build_provider = None
application.job_provider = None
application.task_provider = None
application.worker_provider = None


@application.before_request
def log_request():
	logger.info("%s %s from %s", flask.request.method, flask.request.base_url, flask.request.environ["REMOTE_ADDR"])


@application.errorhandler(Exception)
def error(exception):
	logger.error("Failed to process request on %s", flask.request.path, exc_info = True)
	error_code = 500
	if isinstance(exception, werkzeug.exceptions.HTTPException):
		error_code = exception.code
	return flask.jsonify(str(exception)), error_code


for exception in werkzeug.exceptions.default_exceptions:
	application.register_error_handler(exception, error)


@application.route("/", methods = [ "GET" ])
def home():
	return flask.jsonify({})


@application.route("/help", methods = [ "GET" ])
def help():
	route_collection = []
	for rule in application.url_map.iter_rules():
		if not rule.rule.startswith("/static/"):
			route_collection.append(rule.rule)
	route_collection.sort()
	return flask.jsonify(route_collection)


@application.route("/admin/reload", methods = [ "POST" ])
def reload():
	task = application.task_provider.create("reload_configuration", {})
	return flask.jsonify({ "task_identifier": task["identifier"] })


@application.route("/job_collection", methods = [ "GET" ])
def get_job_collection():
	return flask.jsonify(application.job_provider.get_all())


@application.route("/job/<job_identifier>", methods = [ "GET" ])
def get_job(job_identifier):
	return flask.jsonify(application.job_provider.get(job_identifier))


@application.route("/job/<job_identifier>/trigger", methods = [ "POST" ])
def trigger_job(job_identifier):
	parameters = flask.request.get_json()
	build = application.build_provider.create(job_identifier, parameters)
	task = application.task_provider.create("trigger_build", { "build_identifier": build["identifier"] })
	return flask.jsonify({ "job_identifier": job_identifier, "build_identifier": build["identifier"], "task_identifier": task["identifier"] })


@application.route("/job/<job_identifier>/enable", methods = [ "POST" ])
def enable_job(job_identifier):
	application.job_provider.update_status(job_identifier, is_enabled = True)
	return flask.jsonify({})


@application.route("/job/<job_identifier>/disable", methods = [ "POST" ])
def disable_job(job_identifier):
	application.job_provider.update_status(job_identifier, is_enabled = False)
	return flask.jsonify({})


@application.route("/build_collection", methods = [ "GET" ])
def get_build_collection():
	return flask.jsonify(application.build_provider.get_all())


@application.route("/build/<build_identifier>", methods = [ "GET" ])
def get_build(build_identifier):
	return flask.jsonify(application.build_provider.get(build_identifier))


@application.route("/build/<build_identifier>/step_collection", methods = [ "GET" ])
def get_build_step_collection(build_identifier):
	return flask.jsonify(application.build_provider.get_all_steps(build_identifier))


@application.route("/build/<build_identifier>/step/<int:step_index>", methods = [ "GET" ])
def get_build_step(build_identifier, step_index):
	return flask.jsonify(application.build_provider.get_step(build_identifier, step_index))


@application.route("/build/<build_identifier>/step/<int:step_index>/log", methods = [ "GET" ])
def get_build_step_log(build_identifier, step_index):
	log_text = application.build_provider.get_step_log(build_identifier, step_index)
	return flask.Response(log_text, mimetype = "text/plain")


@application.route("/build/<build_identifier>/results", methods = [ "GET" ])
def get_build_results(build_identifier):
	return flask.jsonify(application.build_provider.get_results(build_identifier))


@application.route("/build/<build_identifier>/abort", methods = [ "POST" ])
def abort_build(build_identifier):
	task = application.task_provider.create("abort_build", { "build_identifier": build_identifier })
	return flask.jsonify({ "build_identifier": build_identifier, "task_identifier": task["identifier"] })


@application.route("/worker_collection", methods = [ "GET" ])
def get_worker_collection():
	return flask.jsonify(application.worker_provider.get_all())


@application.route("/worker/<worker_identifier>", methods = [ "GET" ])
def get_worker(worker_identifier):
	return flask.jsonify(application.worker_provider.get(worker_identifier))


@application.route("/worker/<worker_identifier>/stop", methods = [ "POST" ])
def stop_worker(worker_identifier):
	task = application.task_provider.create("stop_worker", { "worker_identifier": worker_identifier })
	return flask.jsonify({ "worker_identifier": worker_identifier, "task_identifier": task["identifier"] })


@application.route("/task_collection", methods = [ "GET" ])
def get_task_collection():
	return flask.jsonify(application.task_provider.get_all())


@application.route("/task/<task_identifier>", methods = [ "GET" ])
def get_task(task_identifier):
	task = application.task_provider.get(task_identifier)
	return flask.jsonify(task)


@application.route("/task/<task_identifier>/cancel", methods = [ "POST" ])
def cancel_task(task_identifier):
	task = application.task_provider.get(task_identifier)
	if task["status"] == "pending":
		application.task_provider.update(task, should_cancel = True)
	return flask.jsonify(task)
