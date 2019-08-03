import logging

import flask
import werkzeug

import bhamon_build_service
import bhamon_build_service.helpers as helpers

import bhamon_build_service.admin_controller as admin_controller
import bhamon_build_service.build_controller as build_controller
import bhamon_build_service.job_controller as job_controller
import bhamon_build_service.me_controller as me_controller
import bhamon_build_service.task_controller as task_controller
import bhamon_build_service.user_controller as user_controller
import bhamon_build_service.worker_controller as worker_controller


main_logger = logging.getLogger("Service")
request_logger = logging.getLogger("Request")


def configure(application, title = None, copyright = None, version = None, date = None): # pylint: disable = redefined-builtin
	application.config["SERVICE_TITLE"] = title if title is not None else "Build Service"
	application.config["SERVICE_COPYRIGHT"] = copyright if copyright is not None else bhamon_build_service.__copyright__
	application.config["SERVICE_VERSION"] = version if version is not None else bhamon_build_service.__version__
	application.config["SERVICE_DATE"] = date if date is not None else bhamon_build_service.__date__


def register_handlers(application):
	application.log_exception = lambda exc_info: None
	application.before_request(log_request)
	application.before_request(authorize_request)
	for exception in werkzeug.exceptions.default_exceptions:
		application.register_error_handler(exception, handle_error)


def register_routes(application): # pylint: disable = too-many-statements
	application.add_url_rule("/", methods = [ "GET" ], view_func = home)
	application.add_url_rule("/help", methods = [ "GET" ], view_func = help)
	application.add_url_rule("/admin/information", methods = [ "GET" ], view_func = admin_controller.information)
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
	application.add_url_rule("/me", methods = [ "GET" ], view_func = me_controller.get_my_user)
	application.add_url_rule("/me/login", methods = [ "POST" ], view_func = me_controller.login)
	application.add_url_rule("/me/logout", methods = [ "POST" ], view_func = me_controller.logout)
	application.add_url_rule("/me/change_password", methods = [ "POST" ], view_func = me_controller.change_password)
	application.add_url_rule("/me/token_collection", methods = [ "GET" ], view_func = me_controller.get_my_token_list)
	application.add_url_rule("/me/token_create", methods = [ "POST" ], view_func = me_controller.create_my_token)
	application.add_url_rule("/me/token/<token_identifier>/delete", methods = [ "POST" ], view_func = me_controller.delete_my_token)
	application.add_url_rule("/task_count", methods = [ "GET" ], view_func = task_controller.get_task_count)
	application.add_url_rule("/task_collection", methods = [ "GET" ], view_func = task_controller.get_task_collection)
	application.add_url_rule("/task/<task_identifier>", methods = [ "GET" ], view_func = task_controller.get_task)
	application.add_url_rule("/task/<task_identifier>/cancel", methods = [ "POST" ], view_func = task_controller.cancel_task)
	application.add_url_rule("/user_count", methods = [ "GET" ], view_func = user_controller.get_user_count)
	application.add_url_rule("/user_collection", methods = [ "GET" ], view_func = user_controller.get_user_collection)
	application.add_url_rule("/user/<user_identifier>", methods = [ "GET" ], view_func = user_controller.get_user)
	application.add_url_rule("/user/<user_identifier>/create", methods = [ "POST" ], view_func = user_controller.create_user)
	application.add_url_rule("/user/<user_identifier>/update_identity", methods = [ "POST" ], view_func = user_controller.update_user_identity)
	application.add_url_rule("/user/<user_identifier>/update_roles", methods = [ "POST" ], view_func = user_controller.update_user_roles)
	application.add_url_rule("/user/<user_identifier>/reset_password", methods = [ "POST" ], view_func = user_controller.reset_password)
	application.add_url_rule("/user/<user_identifier>/enable", methods = [ "POST" ], view_func = user_controller.enable_user)
	application.add_url_rule("/user/<user_identifier>/disable", methods = [ "POST" ], view_func = user_controller.disable_user)
	application.add_url_rule("/user/<user_identifier>/token_count", methods = [ "GET" ], view_func = user_controller.get_user_token_count)
	application.add_url_rule("/user/<user_identifier>/token_collection", methods = [ "GET" ], view_func = user_controller.get_user_token_list)
	application.add_url_rule("/user/<user_identifier>/token_create", methods = [ "POST" ], view_func = user_controller.create_user_token)
	application.add_url_rule("/user/<user_identifier>/token/<token_identifier>/refresh", methods = [ "POST" ], view_func = user_controller.refresh_user_token)
	application.add_url_rule("/user/<user_identifier>/token/<token_identifier>/delete", methods = [ "POST" ], view_func = user_controller.delete_user_token)
	application.add_url_rule("/worker_count", methods = [ "GET" ], view_func = worker_controller.get_worker_count)
	application.add_url_rule("/worker_collection", methods = [ "GET" ], view_func = worker_controller.get_worker_collection)
	application.add_url_rule("/worker/<worker_identifier>", methods = [ "GET" ], view_func = worker_controller.get_worker)
	application.add_url_rule("/worker/<worker_identifier>/builds", methods = [ "GET" ], view_func = worker_controller.get_worker_builds)
	application.add_url_rule("/worker/<worker_identifier>/tasks", methods = [ "GET" ], view_func = worker_controller.get_worker_tasks)
	application.add_url_rule("/worker/<worker_identifier>/stop", methods = [ "POST" ], view_func = worker_controller.stop_worker)
	application.add_url_rule("/worker/<worker_identifier>/enable", methods = [ "POST" ], view_func = worker_controller.enable_worker)
	application.add_url_rule("/worker/<worker_identifier>/disable", methods = [ "POST" ], view_func = worker_controller.disable_worker)


def log_request():
	request_logger.info("(%s) %s %s", flask.request.environ["REMOTE_ADDR"], flask.request.method, flask.request.base_url)


def authorize_request():
	if flask.request.url_rule is None:
		return
	if flask.current_app.authorization_provider.is_public_route(flask.request.method, flask.request.url_rule.rule):
		return

	user = None
	if flask.request.authorization is not None:
		is_authenticated = flask.current_app.authentication_provider.authenticate_with_token(flask.request.authorization.username, flask.request.authorization.password)
		user = flask.current_app.user_provider.get(flask.request.authorization.username) if is_authenticated else None

	is_authorized = flask.current_app.authorization_provider.authorize_request(user, flask.request.method, flask.request.url_rule.rule)
	if not is_authorized:
		flask.abort(403)


def handle_error(exception):
	status_code = exception.code if isinstance(exception, werkzeug.exceptions.HTTPException) else 500
	status_message = helpers.get_error_message(status_code)
	request_logger.error("(%s) %s %s (StatusCode: %s)", flask.request.environ["REMOTE_ADDR"], flask.request.method, flask.request.base_url, status_code, exc_info = True)
	return flask.jsonify({ "status_code": status_code, "status_message": status_message }), status_code


def home():
	return flask.jsonify({
		"title": flask.current_app.config["SERVICE_TITLE"],
		"copyright": flask.current_app.config["SERVICE_COPYRIGHT"],
		"version": flask.current_app.config["SERVICE_VERSION"],
		"date": flask.current_app.config["SERVICE_DATE"],
	})


def help(): # pylint: disable = redefined-builtin
	route_collection = []
	for rule in flask.current_app.url_map.iter_rules():
		if not rule.rule.startswith("/static/"):
			route_collection.append(rule.rule)
	route_collection.sort()
	return flask.jsonify(route_collection)
