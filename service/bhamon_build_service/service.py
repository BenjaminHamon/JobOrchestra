import logging

import flask
import werkzeug

import bhamon_build_service.admin_controller as admin_controller
import bhamon_build_service.build_controller as build_controller
import bhamon_build_service.job_controller as job_controller
import bhamon_build_service.task_controller as task_controller
import bhamon_build_service.worker_controller as worker_controller


logger = logging.getLogger("Service")


def register_routes(application):
	application.add_url_rule("/", methods = [ "GET" ], view_func = home)
	application.add_url_rule("/help", methods = [ "GET" ], view_func = help)
	application.add_url_rule("/admin/reload", methods = [ "POST" ], view_func = admin_controller.reload)
	application.add_url_rule("/build_count", methods = [ "GET" ], view_func = build_controller.get_build_count)
	application.add_url_rule("/build_collection", methods = [ "GET" ], view_func = build_controller.get_build_collection)
	application.add_url_rule("/build/<build_identifier>", methods = [ "GET" ], view_func = build_controller.get_build)
	application.add_url_rule("/build/<build_identifier>/step_collection", methods = [ "GET" ], view_func = build_controller.get_build_step_collection)
	application.add_url_rule("/build/<build_identifier>/step/<int:step_index>", methods = [ "GET" ], view_func = build_controller.get_build_step)
	application.add_url_rule("/build/<build_identifier>/step/<int:step_index>/log", methods = [ "GET" ], view_func = build_controller.get_build_step_log)
	application.add_url_rule("/build/<build_identifier>/results", methods = [ "GET" ], view_func = build_controller.get_build_results)
	application.add_url_rule("/build/<build_identifier>/tasks", methods = [ "GET" ], view_func = build_controller.get_build_tasks)
	application.add_url_rule("/build/<build_identifier>/abort", methods = [ "POST" ], view_func = build_controller.abort_build)
	application.add_url_rule("/job_count", methods = [ "GET" ], view_func = job_controller.get_job_count)
	application.add_url_rule("/job_collection", methods = [ "GET" ], view_func = job_controller.get_job_collection)
	application.add_url_rule("/job/<job_identifier>", methods = [ "GET" ], view_func = job_controller.get_job)
	application.add_url_rule("/job/<job_identifier>/builds", methods = [ "GET" ], view_func = job_controller.get_job_builds)
	application.add_url_rule("/job/<job_identifier>/trigger", methods = [ "POST" ], view_func = job_controller.trigger_job)
	application.add_url_rule("/job/<job_identifier>/enable", methods = [ "POST" ], view_func = job_controller.enable_job)
	application.add_url_rule("/job/<job_identifier>/disable", methods = [ "POST" ], view_func = job_controller.disable_job)
	application.add_url_rule("/task_count", methods = [ "GET" ], view_func = task_controller.get_task_count)
	application.add_url_rule("/task_collection", methods = [ "GET" ], view_func = task_controller.get_task_collection)
	application.add_url_rule("/task/<task_identifier>", methods = [ "GET" ], view_func = task_controller.get_task)
	application.add_url_rule("/task/<task_identifier>/cancel", methods = [ "POST" ], view_func = task_controller.cancel_task)
	application.add_url_rule("/worker_count", methods = [ "GET" ], view_func = worker_controller.get_worker_count)
	application.add_url_rule("/worker_collection", methods = [ "GET" ], view_func = worker_controller.get_worker_collection)
	application.add_url_rule("/worker/<worker_identifier>", methods = [ "GET" ], view_func = worker_controller.get_worker)
	application.add_url_rule("/worker/<worker_identifier>/builds", methods = [ "GET" ], view_func = worker_controller.get_worker_builds)
	application.add_url_rule("/worker/<worker_identifier>/tasks", methods = [ "GET" ], view_func = worker_controller.get_worker_tasks)
	application.add_url_rule("/worker/<worker_identifier>/stop", methods = [ "POST" ], view_func = worker_controller.stop_worker)
	application.add_url_rule("/worker/<worker_identifier>/enable", methods = [ "POST" ], view_func = worker_controller.enable_worker)
	application.add_url_rule("/worker/<worker_identifier>/disable", methods = [ "POST" ], view_func = worker_controller.disable_worker)


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


def help(): # pylint: disable=redefined-builtin
	route_collection = []
	for rule in flask.current_app.url_map.iter_rules():
		if not rule.rule.startswith("/static/"):
			route_collection.append(rule.rule)
	route_collection.sort()
	return flask.jsonify(route_collection)
