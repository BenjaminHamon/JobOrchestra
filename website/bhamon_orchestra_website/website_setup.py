import datetime
import logging
import os
from typing import Any, Callable, List, Optional

import flask
import jinja2
import werkzeug

import bhamon_orchestra_website
from bhamon_orchestra_website import helpers as website_helpers
from bhamon_orchestra_website.admin_controller import AdminController
from bhamon_orchestra_website.job_controller import JobController
from bhamon_orchestra_website.me_controller import MeController
from bhamon_orchestra_website.pipeline_view import build_pipeline_view
from bhamon_orchestra_website.project_controller import ProjectController
from bhamon_orchestra_website.run_controller import RunController
from bhamon_orchestra_website.schedule_controller import ScheduleController
from bhamon_orchestra_website.user_controller import UserController
from bhamon_orchestra_website.website import Website
from bhamon_orchestra_website.worker_controller import WorkerController


logger = logging.getLogger("WebsiteSetup")


def configure( # pylint: disable = redefined-builtin, too-many-arguments
		application: flask.Flask, website: Website, title: Optional[str] = None,
		copyright: Optional[str] = None, version: Optional[str] = None, date: Optional[str] = None) -> None:

	application.config["WEBSITE_TITLE"] = title if title is not None else bhamon_orchestra_website.__product__
	application.config["WEBSITE_COPYRIGHT"] = copyright if copyright is not None else bhamon_orchestra_website.__copyright__
	application.config["WEBSITE_VERSION"] = version if version is not None else bhamon_orchestra_website.__version__
	application.config["WEBSITE_DATE"] = date if date is not None else bhamon_orchestra_website.__date__

	application.jinja_env.undefined = jinja2.StrictUndefined()
	application.jinja_env.trim_blocks = True
	application.jinja_env.lstrip_blocks = True
	application.jinja_env.filters["build_pipeline_view"] = build_pipeline_view
	application.jinja_env.filters["format_date"] = website_helpers.format_date
	application.jinja_env.filters["describe_cron_expression"] = website_helpers.describe_cron_expression
	application.jinja_env.filters["truncate_text"] = website_helpers.truncate_text
	application.jinja_env.globals["authorize_view"] = website.authorize_view
	application.permanent_session_lifetime = datetime.timedelta(days = 7)


def register_handlers(application: flask.Flask, website: Website) -> None:
	application.log_exception = lambda exc_info: None
	application.before_request(website.log_request)
	application.before_request(website.refresh_session)
	application.before_request(website.authorize_request)
	for exception in werkzeug.exceptions.default_exceptions:
		application.register_error_handler(exception, website.handle_error)


def register_routes( # pylint: disable = too-many-arguments
		application: flask.Flask, website: Website,
		admin_controller: AdminController, job_controller: JobController, me_controller: MeController,
		project_controller: ProjectController, run_controller: RunController, schedule_controller: ScheduleController,
		user_controller: UserController, worker_controller: WorkerController) -> None:

	add_url_rule(application, "/", [ "GET" ], website.home)
	add_url_rule(application, "/routes", [ "GET" ], website.list_routes)
	add_url_rule(application, "/admin", [ "GET" ], admin_controller.index)
	add_url_rule(application, "/me", [ "GET" ], me_controller.show_profile)
	add_url_rule(application, "/me/login", [ "GET", "POST" ], me_controller.login)
	add_url_rule(application, "/me/logout", [ "GET", "POST" ], me_controller.logout)
	add_url_rule(application, "/me/refresh_session", [ "POST" ], me_controller.refresh_session)
	add_url_rule(application, "/me/change_password", [ "GET", "POST" ], me_controller.change_password)
	add_url_rule(application, "/me/token_create", [ "GET", "POST" ], me_controller.create_token)
	add_url_rule(application, "/me/token/<token_identifier>/delete", [ "POST" ], me_controller.delete_token)
	add_url_rule(application, "/project_collection", [ "GET" ], project_controller.show_collection)
	add_url_rule(application, "/project/<project_identifier>", [ "GET" ], project_controller.show)
	add_url_rule(application, "/project/<project_identifier>/status", [ "GET" ], project_controller.show_status)
	add_url_rule(application, "/project/<project_identifier>/job_collection", [ "GET" ], job_controller.show_collection)
	add_url_rule(application, "/project/<project_identifier>/job/<job_identifier>", [ "GET" ], job_controller.show)
	add_url_rule(application, "/project/<project_identifier>/job/<job_identifier>/trigger", [ "POST" ], job_controller.trigger)
	add_url_rule(application, "/project/<project_identifier>/job/<job_identifier>/enable", [ "POST" ], job_controller.enable)
	add_url_rule(application, "/project/<project_identifier>/job/<job_identifier>/disable", [ "POST" ], job_controller.disable)
	add_url_rule(application, "/project/<project_identifier>/run_collection", [ "GET" ], run_controller.show_collection)
	add_url_rule(application, "/project/<project_identifier>/run/<run_identifier>", [ "GET" ], run_controller.show)
	add_url_rule(application, "/project/<project_identifier>/run/<run_identifier>/log", [ "GET" ], run_controller.show_log)
	add_url_rule(application, "/project/<project_identifier>/run/<run_identifier>/log_raw", [ "GET" ], run_controller.show_log_raw)
	add_url_rule(application, "/project/<project_identifier>/run/<run_identifier>/cancel", [ "POST" ], run_controller.cancel)
	add_url_rule(application, "/project/<project_identifier>/run/<run_identifier>/abort", [ "POST" ], run_controller.abort)
	add_url_rule(application, "/project/<project_identifier>/run/<run_identifier>/download", [ "GET" ], run_controller.download_archive)
	add_url_rule(application, "/project/<project_identifier>/schedule_collection", [ "GET" ], schedule_controller.show_collection)
	add_url_rule(application, "/project/<project_identifier>/schedule/<schedule_identifier>", [ "GET" ], schedule_controller.show)
	add_url_rule(application, "/project/<project_identifier>/schedule/<schedule_identifier>/enable", [ "POST" ], schedule_controller.enable)
	add_url_rule(application, "/project/<project_identifier>/schedule/<schedule_identifier>/disable", [ "POST" ], schedule_controller.disable)
	add_url_rule(application, "/user_collection", [ "GET" ], user_controller.show_collection)
	add_url_rule(application, "/user_create", [ "GET", "POST" ], user_controller.create)
	add_url_rule(application, "/user/<user_identifier>", [ "GET" ], user_controller.show)
	add_url_rule(application, "/user/<user_identifier>/edit", [ "GET" ], user_controller.edit)
	add_url_rule(application, "/user/<user_identifier>/update_identity", [ "POST" ], user_controller.update_identity)
	add_url_rule(application, "/user/<user_identifier>/update_roles", [ "POST" ], user_controller.update_roles)
	add_url_rule(application, "/user/<user_identifier>/enable", [ "POST" ], user_controller.enable)
	add_url_rule(application, "/user/<user_identifier>/disable", [ "POST" ], user_controller.disable)
	add_url_rule(application, "/user/<user_identifier>/reset_password", [ "GET", "POST" ], user_controller.reset_password)
	add_url_rule(application, "/user/<user_identifier>/token_create", [ "GET", "POST" ], user_controller.create_token)
	add_url_rule(application, "/user/<user_identifier>/token/<token_identifier>/delete", [ "POST" ], user_controller.delete_token)
	add_url_rule(application, "/worker_collection", [ "GET" ], worker_controller.show_collection)
	add_url_rule(application, "/worker/<worker_identifier>", [ "GET" ], worker_controller.show)
	add_url_rule(application, "/worker/<worker_identifier>/runs", [ "GET" ], worker_controller.show_runs)
	add_url_rule(application, "/worker/<worker_identifier>/disconnect", [ "POST" ], worker_controller.disconnect)
	add_url_rule(application, "/worker/<worker_identifier>/enable", [ "POST" ], worker_controller.enable)
	add_url_rule(application, "/worker/<worker_identifier>/disable", [ "POST" ], worker_controller.disable)
	add_url_rule(application, "/service_proxy", [ "GET", "POST" ], website.proxy_to_service, defaults = { "route": "" })
	add_url_rule(application, "/service_proxy/<path:route>", [ "GET", "POST" ], website.proxy_to_service)


def add_url_rule(application: flask.Flask, path: str, methods: List[str], handler: Callable, **kwargs) -> None:
	endpoint = ".".join(handler.__module__.split(".")[1:]) + "." + handler.__name__
	application.add_url_rule(path, methods = methods, endpoint = endpoint, view_func = handler, **kwargs)


def register_resources(application: flask.Flask, path_collection: Optional[List[str]] = None) -> None:
	if application.static_folder is not None:
		raise ValueError("Flask application should be initialized with static_folder set to None")

	if path_collection is None:
		path_collection = [ os.path.dirname(__file__) ]

	application.static_directories = [ os.path.join(path, "static") for path in path_collection ]
	application.add_url_rule("/static/<path:filename>", view_func = send_static_file, endpoint = "static")
	application.jinja_loader = jinja2.ChoiceLoader([ jinja2.FileSystemLoader(os.path.join(path, "templates")) for path in path_collection ])


# Override Flask send_static_file to support several static directories
def send_static_file(filename: str) -> Any:
	if not flask.current_app.static_directories:
		raise RuntimeError("Flask application has no static directory")

	# Ensure get_send_file_max_age is called in all cases.
	# Here, we ensure get_send_file_max_age is called for Blueprints.
	cache_timeout = flask.current_app.get_send_file_max_age(filename)

	for directory in flask.current_app.static_directories:
		try:
			return flask.helpers.send_from_directory(directory, filename, cache_timeout = cache_timeout)
		except werkzeug.exceptions.NotFound:
			pass

	raise werkzeug.exceptions.NotFound
