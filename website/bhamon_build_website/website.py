import logging
import os

import flask
import jinja2
import werkzeug

import bhamon_build_website.build_controller as build_controller
import bhamon_build_website.job_controller as job_controller
import bhamon_build_website.task_controller as task_controller
import bhamon_build_website.worker_controller as worker_controller


logger = logging.getLogger("Website")


def register_routes(application):
	application.add_url_rule("/", methods = [ "GET" ], view_func = home)
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
	application.add_url_rule("/worker_collection", methods = [ "GET" ], view_func = worker_controller.worker_collection_index)
	application.add_url_rule("/worker/<worker_identifier>", methods = [ "GET" ], view_func = worker_controller.worker_index)
	application.add_url_rule("/worker/<worker_identifier>/stop", methods = [ "POST" ], view_func = worker_controller.stop_worker)
	application.add_url_rule("/worker/<worker_identifier>/enable", methods = [ "POST" ], view_func = worker_controller.enable_worker)
	application.add_url_rule("/worker/<worker_identifier>/disable", methods = [ "POST" ], view_func = worker_controller.disable_worker)


def register_resources(application):
	package_path = os.path.join(os.path.dirname(__file__))

	# This requires that Flask is initialized with 'static_folder = None',
	# otherwise it raises an AssertionError about overwriting the static endpoint
	application.static_folder = os.path.join(application.root_path, "static")
	application.static_folder_default = os.path.join(package_path, "static")
	application.add_url_rule("/static/<path:filename>", view_func = send_static_file, endpoint = "static")

	local_loader = jinja2.FileSystemLoader(os.path.join(application.root_path, "templates"))
	default_loader = jinja2.FileSystemLoader(os.path.join(package_path, "templates"))
	application.jinja_loader = jinja2.ChoiceLoader([ local_loader, default_loader ])


def log_request():
	logger.info("%s %s from %s", flask.request.method, flask.request.base_url, flask.request.environ["REMOTE_ADDR"])


def handle_error(exception):
	logger.error("Failed to process request on %s", flask.request.path, exc_info = True)
	error_code = 500
	if isinstance(exception, werkzeug.exceptions.HTTPException):
		error_code = exception.code
	# return flask.jsonify(str(exception)), error_code
	return flask.render_template("error.html", title = "Error", message = str(exception)), error_code


# Override Flask send_static_file to add a default static directory
def send_static_file(filename):
	if not flask.current_app.has_static_folder:
		raise RuntimeError('No static folder for this object')

	# Ensure get_send_file_max_age is called in all cases.
	# Here, we ensure get_send_file_max_age is called for Blueprints.
	cache_timeout = flask.current_app.get_send_file_max_age(filename)

	try:
		return flask.helpers.send_from_directory(flask.current_app.static_folder, filename, cache_timeout = cache_timeout)
	except werkzeug.exceptions.NotFound:
		return flask.helpers.send_from_directory(flask.current_app.static_folder_default, filename, cache_timeout = cache_timeout)


def home():
	return flask.render_template("home.html", title = "Home")


def artifact_storage_index():
	return flask.redirect(flask.current_app.artifact_storage_url)
