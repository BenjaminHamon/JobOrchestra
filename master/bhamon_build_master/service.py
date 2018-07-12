import logging

import flask
import werkzeug


logger = logging.getLogger("Service")
logging.getLogger("werkzeug").setLevel(logging.WARNING)

logger.info("Starting build master service")

application = flask.Flask(__name__)
application.database = None
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


@application.route("/job_collection", methods = [ "GET" ])
def get_job_collection():
	return flask.jsonify(list(application.job_provider.get_all().values()))


@application.route("/job/<job_identifier>", methods = [ "GET" ])
def get_job(job_identifier):
	return flask.jsonify(application.job_provider.get(job_identifier))


@application.route("/job/<job_identifier>/trigger", methods = [ "POST" ])
def trigger_job(job_identifier):
	parameters = flask.request.get_json()
	build_identifier = application.database.create_build(job_identifier, parameters)
	task = application.task_provider.create("trigger_build", { "build_identifier": build_identifier })
	return flask.jsonify({ "build_identifier": build_identifier, "task_identifier": task["identifier"] })


@application.route("/build_collection", methods = [ "GET" ])
def get_build_collection():
	sort_by_date = flask.request.args.get("sort_by_date", True, bool)
	limit = flask.request.args.get("limit", 50, int)
	return flask.jsonify(application.database.get_build_collection(sort_by_date, limit))


@application.route("/build/<identifier>", methods = [ "GET" ])
def get_build(identifier):
	return flask.jsonify(application.database.get_build(identifier))


@application.route("/build/<identifier>/step_collection", methods = [ "GET" ])
def get_build_step_collection(identifier):
	return flask.jsonify(application.database.get_build_step_collection(identifier))


@application.route("/build/<build_identifier>/step/<int:step_index>", methods = [ "GET" ])
def get_build_step(build_identifier, step_index):
	return flask.jsonify(application.database.get_build_step(build_identifier, step_index))


@application.route("/build/<build_identifier>/step/<int:step_index>/log", methods = [ "GET" ])
def get_build_step_log(build_identifier, step_index):
	log_text = application.database.get_build_step_log(build_identifier, step_index)
	return flask.Response(log_text, mimetype = "text/plain")


@application.route("/build/<build_identifier>/abort", methods = [ "POST" ])
def abort_build(build_identifier):
	task = application.task_provider.create("abort_build", { "build_identifier": build_identifier })
	return flask.jsonify({ "build_identifier": build_identifier, "task_identifier": task["identifier"] })


@application.route("/worker_collection", methods = [ "GET" ])
def get_worker_collection():
	return flask.jsonify(list(application.worker_provider.get_all().values()))


@application.route("/worker/<worker_identifier>", methods = [ "GET" ])
def get_worker(worker_identifier):
	return flask.jsonify(application.worker_provider.get(worker_identifier))


@application.route("/worker/<worker_identifier>/stop", methods = [ "POST" ])
def stop_worker(worker_identifier):
	task = application.task_provider.create("stop_worker", { "worker_identifier": worker_identifier })
	return flask.jsonify({ "worker_identifier": worker_identifier, "task_identifier": task["identifier"] })


@application.route("/task_collection", methods = [ "GET" ])
def get_task_collection():
	task_collection = list(application.task_provider.get_all().values())
	task_collection.sort(key = lambda task: task["update_date"], reverse = True)
	return flask.jsonify(task_collection)


@application.route("/task/<task_identifier>", methods = [ "GET" ])
def get_task(task_identifier):
	task = application.task_provider.get(task_identifier)
	return flask.jsonify(task)


@application.route("/task/<task_identifier>/cancel", methods = [ "POST" ])
def cancel_task(task_identifier):
	task = application.task_provider.get(task_identifier)
	if task["status"] == "pending":
		task = application.task_provider.update(task_identifier, "cancelled")
	return flask.jsonify(task)
