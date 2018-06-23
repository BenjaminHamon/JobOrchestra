import logging

import flask
import werkzeug


logger = logging.getLogger("Service")
logging.getLogger("werkzeug").setLevel(logging.WARNING)

logger.info("Starting build master service")

application = flask.Flask(__name__)
application.database = None
application.task_provider = None


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
	return ""


@application.route("/job_collection", methods = [ "GET" ])
def get_job_collection():
	return flask.jsonify(application.database.get_job_collection())


@application.route("/job/<identifier>", methods = [ "GET" ])
def get_job(identifier):
	return flask.jsonify(application.database.get_job(identifier))


@application.route("/job/<identifier>/trigger", methods = [ "POST" ])
def trigger_job(identifier):
	logger.info("TriggerJob %s", identifier)
	parameters = flask.request.get_json()
	build_identifier = application.database.create_build(identifier, parameters)
	task_identifier = application.task_provider.create("trigger_build", { "build_identifier": build_identifier })
	return flask.jsonify({ "build_identifier": build_identifier, "task_identifier": task_identifier })


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


@application.route("/worker_collection", methods = [ "GET" ])
def get_worker_collection():
	return flask.jsonify(application.database.get_worker_collection())


@application.route("/worker/<identifier>", methods = [ "GET" ])
def get_worker(identifier):
	return flask.jsonify(application.database.get_worker(identifier))
