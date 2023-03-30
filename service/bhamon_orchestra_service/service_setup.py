import datetime
import logging
from typing import Callable, List, Optional

import flask
import werkzeug.exceptions

import bhamon_orchestra_service
from bhamon_orchestra_model.database.database_client import DatabaseClient
from bhamon_orchestra_model.database.file_data_storage import FileDataStorage
from bhamon_orchestra_model.date_time_provider import DateTimeProvider
from bhamon_orchestra_model.job_provider import JobProvider
from bhamon_orchestra_model.project_provider import ProjectProvider
from bhamon_orchestra_model.run_provider import RunProvider
from bhamon_orchestra_model.schedule_provider import ScheduleProvider
from bhamon_orchestra_model.serialization.json_serializer import JsonSerializer
from bhamon_orchestra_model.users.authentication_provider import AuthenticationProvider
from bhamon_orchestra_model.users.authorization_provider import AuthorizationProvider
from bhamon_orchestra_model.users.user_provider import UserProvider
from bhamon_orchestra_model.worker_provider import WorkerProvider
from bhamon_orchestra_service.admin_controller import AdminController
from bhamon_orchestra_service.job_controller import JobController
from bhamon_orchestra_service.me_controller import MeController
from bhamon_orchestra_service.project_controller import ProjectController
from bhamon_orchestra_service.response_builder import ResponseBuilder
from bhamon_orchestra_service.run_controller import RunController
from bhamon_orchestra_service.schedule_controller import ScheduleController
from bhamon_orchestra_service.service import Service
from bhamon_orchestra_service.user_controller import UserController
from bhamon_orchestra_service.worker_controller import WorkerController


logger = logging.getLogger("ServiceSetup")


def create_application( # pylint: disable = too-many-locals
		flask_import_name: str, database_client_factory: Callable[[], DatabaseClient], file_storage_path: str, external_services: dict) -> Service:

	application = flask.Flask(flask_import_name)

	data_storage = FileDataStorage(file_storage_path)
	date_time_provider = DateTimeProvider()
	serializer = JsonSerializer()
	response_builder = ResponseBuilder(application, serializer)

	authentication_provider = AuthenticationProvider(date_time_provider)
	authorization_provider = AuthorizationProvider()
	job_provider = JobProvider(date_time_provider)
	project_provider = ProjectProvider(date_time_provider)
	run_provider = RunProvider(data_storage, date_time_provider)
	schedule_provider = ScheduleProvider(date_time_provider)
	user_provider = UserProvider(date_time_provider)
	worker_provider = WorkerProvider(date_time_provider)

	service = Service(
		application = application,
		response_builder = response_builder,
		database_client_factory = database_client_factory,
		authentication_provider = authentication_provider,
		authorization_provider = authorization_provider,
		user_provider = user_provider,
	)

	configure(application)
	register_handlers(application, service)
	register_root_routes(application, service)
	register_admin_controllers_and_routes(application, response_builder, external_services)
	register_user_controllers_and_routes(application, response_builder, authentication_provider, user_provider)
	register_project_controllers_and_routes(application, response_builder, job_provider, run_provider, project_provider, schedule_provider)
	register_worker_controllers_and_routes(application, response_builder, job_provider, run_provider, worker_provider)

	return service


def configure( # pylint: disable = redefined-builtin
		application: flask.Flask, title: Optional[str] = None,
		copyright: Optional[str] = None, version: Optional[str] = None, date: Optional[str] = None) -> None:

	application.config["SERVICE_TITLE"] = title if title is not None else bhamon_orchestra_service.__product__
	application.config["SERVICE_COPYRIGHT"] = copyright if copyright is not None else bhamon_orchestra_service.__copyright__
	application.config["SERVICE_VERSION"] = version if version is not None else bhamon_orchestra_service.__version__
	application.config["SERVICE_DATE"] = date if date is not None else bhamon_orchestra_service.__date__
	application.permanent_session_lifetime = datetime.timedelta(days = 7)


def register_handlers(application: flask.Flask, service: Service) -> None:
	application.log_exception = lambda exc_info: None
	application.before_request(service.log_request)
	application.before_request(service.setup_request_dependencies)
	application.before_request(service.authorize_request)
	application.teardown_request(service.teardown_request_dependencies)
	for exception in werkzeug.exceptions.default_exceptions:
		application.register_error_handler(exception, service.handle_error)


def register_root_routes(application: flask.Flask, service: Service) -> None:
	add_url_rule(application, "/", [ "GET" ], service.home)
	add_url_rule(application, "/routes", [ "GET" ], service.list_routes)


def register_admin_controllers_and_routes(
		application: flask.Flask, response_builder: ResponseBuilder, external_services: dict) -> None:

	admin_controller = AdminController(response_builder, external_services)

	add_url_rule(application, "/admin/information", [ "GET" ], admin_controller.information)
	add_url_rule(application, "/admin/service_collection", [ "GET" ], admin_controller.get_service_collection)
	add_url_rule(application, "/admin/service/<service_identifier>", [ "GET" ], admin_controller.get_service)
	add_url_rule(application, "/admin/service/<service_identifier>/status", [ "GET" ], admin_controller.get_service_status)


def register_user_controllers_and_routes(
		application: flask.Flask, response_builder: ResponseBuilder,
		authentication_provider: AuthenticationProvider, user_provider: UserProvider) -> None:

	user_controller = UserController(response_builder, authentication_provider, user_provider)
	me_controller = MeController(response_builder, authentication_provider, user_provider, user_controller)

	add_url_rule(application, "/me", [ "GET" ], me_controller.get_user)
	add_url_rule(application, "/me/login", [ "POST" ], me_controller.login)
	add_url_rule(application, "/me/logout", [ "POST" ], me_controller.logout)
	add_url_rule(application, "/me/refresh_session", [ "POST" ], me_controller.refresh_session)
	add_url_rule(application, "/me/change_password", [ "POST" ], me_controller.change_password)
	add_url_rule(application, "/me/token_collection", [ "GET" ], me_controller.get_token_list)
	add_url_rule(application, "/me/token_create", [ "POST" ], me_controller.create_token)
	add_url_rule(application, "/me/token/<token_identifier>/delete", [ "POST" ], me_controller.delete_token)

	add_url_rule(application, "/user_count", [ "GET" ], user_controller.get_count)
	add_url_rule(application, "/user_collection", [ "GET" ], user_controller.get_collection)
	add_url_rule(application, "/user/<user_identifier>", [ "GET" ], user_controller.get)
	add_url_rule(application, "/user/<user_identifier>/create", [ "POST" ], user_controller.create)
	add_url_rule(application, "/user/<user_identifier>/update_identity", [ "POST" ], user_controller.update_identity)
	add_url_rule(application, "/user/<user_identifier>/update_roles", [ "POST" ], user_controller.update_roles)
	add_url_rule(application, "/user/<user_identifier>/reset_password", [ "POST" ], user_controller.reset_password)
	add_url_rule(application, "/user/<user_identifier>/enable", [ "POST" ], user_controller.enable)
	add_url_rule(application, "/user/<user_identifier>/disable", [ "POST" ], user_controller.disable)
	add_url_rule(application, "/user/<user_identifier>/token_count", [ "GET" ], user_controller.get_token_count)
	add_url_rule(application, "/user/<user_identifier>/token_collection", [ "GET" ], user_controller.get_token_list)
	add_url_rule(application, "/user/<user_identifier>/token_create", [ "POST" ], user_controller.create_token)
	add_url_rule(application, "/user/<user_identifier>/token/<token_identifier>/set_expiration", [ "POST" ], user_controller.set_token_expiration)
	add_url_rule(application, "/user/<user_identifier>/token/<token_identifier>/delete", [ "POST" ], user_controller.delete_token)


def register_project_controllers_and_routes( # pylint: disable = too-many-arguments
		application: flask.Flask, response_builder: ResponseBuilder,
		job_provider: JobProvider, run_provider: RunProvider, project_provider: ProjectProvider, schedule_provider: ScheduleProvider) -> None:

	run_controller_serializer = JsonSerializer(indent = 4)

	job_controller = JobController(response_builder, job_provider, run_provider)
	project_controller = ProjectController(application, response_builder, project_provider, run_provider)
	run_controller = RunController(response_builder, run_controller_serializer, run_provider)
	schedule_controller = ScheduleController(response_builder, schedule_provider)

	add_url_rule(application, "/project_count", [ "GET" ], project_controller.get_count)
	add_url_rule(application, "/project_collection", [ "GET" ], project_controller.get_collection)
	add_url_rule(application, "/project/<project_identifier>", [ "GET" ], project_controller.get)
	add_url_rule(application, "/project/<project_identifier>/job_count", [ "GET" ], job_controller.get_count)
	add_url_rule(application, "/project/<project_identifier>/job_collection", [ "GET" ], job_controller.get_collection)
	add_url_rule(application, "/project/<project_identifier>/job/<job_identifier>", [ "GET" ], job_controller.get)
	add_url_rule(application, "/project/<project_identifier>/job/<job_identifier>/runs", [ "GET" ], job_controller.get_runs)
	add_url_rule(application, "/project/<project_identifier>/job/<job_identifier>/trigger", [ "POST" ], job_controller.trigger)
	add_url_rule(application, "/project/<project_identifier>/job/<job_identifier>/enable", [ "POST" ], job_controller.enable)
	add_url_rule(application, "/project/<project_identifier>/job/<job_identifier>/disable", [ "POST" ], job_controller.disable)
	add_url_rule(application, "/project/<project_identifier>/run_count", [ "GET" ], run_controller.get_count)
	add_url_rule(application, "/project/<project_identifier>/run_collection", [ "GET" ], run_controller.get_collection)
	add_url_rule(application, "/project/<project_identifier>/run/<run_identifier>", [ "GET" ], run_controller.get)
	add_url_rule(application, "/project/<project_identifier>/run/<run_identifier>/log", [ "GET" ], run_controller.get_log)
	add_url_rule(application, "/project/<project_identifier>/run/<run_identifier>/log_chunk", [ "GET" ], run_controller.get_log_chunk)
	add_url_rule(application, "/project/<project_identifier>/run/<run_identifier>/results", [ "GET" ], run_controller.get_results)
	add_url_rule(application, "/project/<project_identifier>/run/<run_identifier>/cancel", [ "POST" ], run_controller.cancel)
	add_url_rule(application, "/project/<project_identifier>/run/<run_identifier>/abort", [ "POST" ], run_controller.abort)
	add_url_rule(application, "/project/<project_identifier>/run/<run_identifier>/download", [ "GET" ], run_controller.download_archive)
	add_url_rule(application, "/project/<project_identifier>/schedule_count", [ "GET" ], schedule_controller.get_count)
	add_url_rule(application, "/project/<project_identifier>/schedule_collection", [ "GET" ], schedule_controller.get_collection)
	add_url_rule(application, "/project/<project_identifier>/schedule/<schedule_identifier>", [ "GET" ], schedule_controller.get)
	add_url_rule(application, "/project/<project_identifier>/schedule/<schedule_identifier>/enable", [ "POST" ], schedule_controller.enable)
	add_url_rule(application, "/project/<project_identifier>/schedule/<schedule_identifier>/disable", [ "POST" ], schedule_controller.disable)
	add_url_rule(application, "/project/<project_identifier>/repository", [ "GET" ], project_controller.get_repository)
	add_url_rule(application, "/project/<project_identifier>/repository/branch_collection", [ "GET" ], project_controller.get_branch_collection)
	add_url_rule(application, "/project/<project_identifier>/repository/revision_collection", [ "GET" ], project_controller.get_revision_collection)
	add_url_rule(application, "/project/<project_identifier>/repository/revision/<reference>", [ "GET" ], project_controller.get_revision)
	add_url_rule(application, "/project/<project_identifier>/repository/revision/<reference>/status", [ "GET" ], project_controller.get_revision_status)
	add_url_rule(application, "/project/<project_identifier>/status", [ "GET" ], project_controller.get_project_status)


def register_worker_controllers_and_routes(
		application: flask.Flask, response_builder: ResponseBuilder,
		job_provider: JobProvider, run_provider: RunProvider, worker_provider: WorkerProvider) -> None:

	worker_controller = WorkerController(response_builder, job_provider, run_provider, worker_provider)

	add_url_rule(application, "/worker_count", [ "GET" ], worker_controller.get_count)
	add_url_rule(application, "/worker_collection", [ "GET" ], worker_controller.get_collection)
	add_url_rule(application, "/worker/<worker_identifier>", [ "GET" ], worker_controller.get)
	add_url_rule(application, "/worker/<worker_identifier>/job_collection", [ "GET" ], worker_controller.get_job_collection)
	add_url_rule(application, "/worker/<worker_identifier>/run_count", [ "GET" ], worker_controller.get_run_count)
	add_url_rule(application, "/worker/<worker_identifier>/run_collection", [ "GET" ], worker_controller.get_run_collection)
	add_url_rule(application, "/worker/<worker_identifier>/disconnect", [ "POST" ], worker_controller.disconnect)
	add_url_rule(application, "/worker/<worker_identifier>/enable", [ "POST" ], worker_controller.enable)
	add_url_rule(application, "/worker/<worker_identifier>/disable", [ "POST" ], worker_controller.disable)


def add_url_rule(application: flask.Flask, path: str, methods: List[str], handler: Callable, **kwargs) -> None:
	endpoint = ".".join(handler.__module__.split(".")[1:]) + "." + handler.__name__
	application.add_url_rule(path, methods = methods, endpoint = endpoint, view_func = handler, **kwargs)
