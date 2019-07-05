import logging
import os

import flask
import jinja2
import werkzeug

import bhamon_build_website.admin_controller as admin_controller
import bhamon_build_website.build_controller as build_controller
import bhamon_build_website.helpers as helpers
import bhamon_build_website.job_controller as job_controller
import bhamon_build_website.task_controller as task_controller
import bhamon_build_website.user_controller as user_controller
import bhamon_build_website.worker_controller as worker_controller


main_logger = logging.getLogger("Website")
request_logger = logging.getLogger("Request")


def configure(application):
	application.jinja_env.trim_blocks = True
	application.jinja_env.lstrip_blocks = True
	application.jinja_env.filters['strip_pagination_arguments'] = helpers.strip_pagination_arguments


def register_handlers(application):
	application.log_exception = lambda exc_info: None
	application.before_request(log_request)
	for exception in werkzeug.exceptions.default_exceptions:
		application.register_error_handler(exception, handle_error)


def register_routes(application):
	application.add_url_rule("/", methods = [ "GET" ], view_func = home)
	application.add_url_rule("/admin", methods = [ "GET" ], view_func = admin_controller.administration_index)
	application.add_url_rule("/admin/reload", methods = [ "POST" ], view_func = admin_controller.reload_service)
	application.add_url_rule("/artifact_storage", methods = [ "GET" ], view_func = artifact_storage_index)
	application.add_url_rule("/build_collection", methods = [ "GET" ], view_func = build_controller.build_collection_index)
	application.add_url_rule("/build/<build_identifier>", methods = [ "GET" ], view_func = build_controller.build_index)
	application.add_url_rule("/build/<build_identifier>/step/<int:step_index>/log", methods = [ "GET" ], view_func = build_controller.build_step_log)
	application.add_url_rule("/build/<build_identifier>/abort", methods = [ "POST" ], view_func = build_controller.abort_build)
	application.add_url_rule("/job_collection", methods = [ "GET" ], view_func = job_controller.job_collection_index)
	application.add_url_rule("/job/<job_identifier>", methods = [ "GET" ], view_func = job_controller.job_index)
	application.add_url_rule("/job/<job_identifier>/trigger", methods = [ "POST" ], view_func = job_controller.trigger_job)
	application.add_url_rule("/job/<job_identifier>/enable", methods = [ "POST" ], view_func = job_controller.enable_job)
	application.add_url_rule("/job/<job_identifier>/disable", methods = [ "POST" ], view_func = job_controller.disable_job)
	application.add_url_rule("/task_collection", methods = [ "GET" ], view_func = task_controller.task_collection_index)
	application.add_url_rule("/task/<task_identifier>/cancel", methods = [ "POST" ], view_func = task_controller.cancel_task)
	application.add_url_rule("/user_collection", methods = [ "GET" ], view_func = user_controller.user_collection_index)
	application.add_url_rule("/user_create", methods = [ "GET", "POST" ], view_func = user_controller.create_user)
	application.add_url_rule("/user/<user_identifier>", methods = [ "GET" ], view_func = user_controller.user_index)
	application.add_url_rule("/user/<user_identifier>/edit", methods = [ "GET", "POST" ], view_func = user_controller.edit_user)
	application.add_url_rule("/user/<user_identifier>/enable", methods = [ "POST" ], view_func = user_controller.enable_user)
	application.add_url_rule("/user/<user_identifier>/disable", methods = [ "POST" ], view_func = user_controller.disable_user)
	application.add_url_rule("/worker_collection", methods = [ "GET" ], view_func = worker_controller.worker_collection_index)
	application.add_url_rule("/worker/<worker_identifier>", methods = [ "GET" ], view_func = worker_controller.worker_index)
	application.add_url_rule("/worker/<worker_identifier>/stop", methods = [ "POST" ], view_func = worker_controller.stop_worker)
	application.add_url_rule("/worker/<worker_identifier>/enable", methods = [ "POST" ], view_func = worker_controller.enable_worker)
	application.add_url_rule("/worker/<worker_identifier>/disable", methods = [ "POST" ], view_func = worker_controller.disable_worker)


def register_resources(application, path_collection = None):
	if application.static_folder is not None:
		raise ValueError("Flask application should be initialized with static_folder set to None")

	if path_collection is None:
		path_collection = [ os.path.dirname(__file__) ]

	application.static_directories = [ os.path.join(path, "static") for path in path_collection ]
	application.add_url_rule("/static/<path:filename>", view_func = send_static_file, endpoint = "static")
	application.jinja_loader = jinja2.ChoiceLoader([ jinja2.FileSystemLoader(os.path.join(path, "templates")) for path in path_collection ])


def log_request():
	request_logger.info("(%s) %s %s", flask.request.environ["REMOTE_ADDR"], flask.request.method, flask.request.base_url)


def handle_error(exception):
	status_code = exception.code if isinstance(exception, werkzeug.exceptions.HTTPException) else 500
	status_message = get_error_message(status_code)
	request_logger.error("(%s) %s %s (StatusCode: %s)", flask.request.environ["REMOTE_ADDR"], flask.request.method, flask.request.base_url, status_code, exc_info = True)
	if flask.request.headers.get("Content-Type") == "application/json":
		return flask.jsonify({ "status_code": status_code, "status_message": status_message }), status_code
	return flask.render_template("error.html", title = "Error", status_message = status_message, status_code = status_code), status_code


def get_error_message(status_code): # pylint: disable = too-many-return-statements
	if status_code == 400:
		return "Bad request"
	if status_code == 401:
		return "Unauthorized"
	if status_code == 403:
		return "Forbidden"
	if status_code == 404:
		return "Page not found"
	if status_code == 405:
		return "Method not allowed"

	if status_code == 500:
		return "Internal server error"

	if 400 <= status_code < 500:
		return "Client error"
	if 500 <= status_code < 600:
		return "Server error"
	return "Unknown error"


# Override Flask send_static_file to support several static directories
def send_static_file(filename):
	if not flask.current_app.static_directories:
		raise RuntimeError('Flask application has no static directory')

	# Ensure get_send_file_max_age is called in all cases.
	# Here, we ensure get_send_file_max_age is called for Blueprints.
	cache_timeout = flask.current_app.get_send_file_max_age(filename)

	for directory in flask.current_app.static_directories:
		try:
			return flask.helpers.send_from_directory(directory, filename, cache_timeout = cache_timeout)
		except werkzeug.exceptions.NotFound:
			pass

	raise werkzeug.exceptions.NotFound


def home():
	return flask.render_template("home.html", title = "Home")


def artifact_storage_index():
	return flask.redirect(flask.current_app.artifact_storage_url)
