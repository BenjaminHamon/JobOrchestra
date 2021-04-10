import argparse
import importlib
import logging
from typing import Any

import flask

from bhamon_orchestra_model.authentication_provider import AuthenticationProvider
from bhamon_orchestra_model.authorization_provider import AuthorizationProvider
from bhamon_orchestra_model.database.file_data_storage import FileDataStorage
from bhamon_orchestra_model.date_time_provider import DateTimeProvider
from bhamon_orchestra_model.job_provider import JobProvider
from bhamon_orchestra_model.project_provider import ProjectProvider
from bhamon_orchestra_model.run_provider import RunProvider
from bhamon_orchestra_model.schedule_provider import ScheduleProvider
from bhamon_orchestra_model.serialization.json_serializer import JsonSerializer
from bhamon_orchestra_model.user_provider import UserProvider
from bhamon_orchestra_model.worker_provider import WorkerProvider

import bhamon_orchestra_service.service_setup as service_setup
from bhamon_orchestra_service.admin_controller import AdminController
from bhamon_orchestra_service.job_controller import JobController
from bhamon_orchestra_service.me_controller import MeController
from bhamon_orchestra_service.project_controller import ProjectController
from bhamon_orchestra_service.response_builder import ResponseBuilder
from bhamon_orchestra_service.run_controller import RunController
from bhamon_orchestra_service.schedule_controller import ScheduleController
from bhamon_orchestra_service.user_controller import UserController
from bhamon_orchestra_service.service import Service
from bhamon_orchestra_service.worker_controller import WorkerController

from . import environment
from . import factory


logger = logging.getLogger("Main")


def main():
	arguments = parse_arguments()
	environment_instance = environment.load_environment()
	environment.configure_logging(environment_instance, arguments)

	application = create_application(arguments)
	application.run(host = arguments.address, port = arguments.port)


def parse_arguments():
	argument_parser = argparse.ArgumentParser()
	argument_parser.add_argument("--address", required = True, help = "Set the address for the server to listen to")
	argument_parser.add_argument("--port", required = True, type = int, help = "Set the port for the server to listen to")
	argument_parser.add_argument("--database", required = True, help = "Set the database uri")
	return argument_parser.parse_args()


def create_application(arguments): # pylint: disable = too-many-locals
	application = flask.Flask(__name__)

	external_services = {}

	database_metadata = None
	if arguments.database.startswith("postgresql://"):
		database_metadata = importlib.import_module("bhamon_orchestra_model.database.sql_database_model").metadata

	database_client_factory = factory.create_database_client_factory(arguments.database, database_metadata)
	data_storage_instance = FileDataStorage(".")
	date_time_provider_instance = DateTimeProvider()
	serializer_instance = JsonSerializer(indent = 4)
	response_builder_instance = ResponseBuilder(application, serializer_instance)

	authentication_provider_instance = AuthenticationProvider(date_time_provider_instance)
	authorization_provider_instance = AuthorizationProvider()
	job_provider_instance = JobProvider(date_time_provider_instance)
	project_provider_instance = ProjectProvider(date_time_provider_instance)
	run_provider_instance = RunProvider(data_storage_instance, date_time_provider_instance)
	schedule_provider_instance = ScheduleProvider(date_time_provider_instance)
	user_provider_instance = UserProvider(date_time_provider_instance)
	worker_provider_instance = WorkerProvider(date_time_provider_instance)

	service_instance = Service(
		application = application,
		response_builder = response_builder_instance,
		database_client_factory = database_client_factory,
		authentication_provider = authentication_provider_instance,
		authorization_provider = authorization_provider_instance,
		user_provider = user_provider_instance,
	)

	admin_controller_instance = AdminController(response_builder_instance, external_services)
	job_controller_instance = JobController(response_builder_instance, job_provider_instance, run_provider_instance)
	project_controller_instance = ProjectController(application, response_builder_instance, project_provider_instance, run_provider_instance)
	run_controller_instance = RunController(response_builder_instance, serializer_instance, run_provider_instance)
	schedule_controller_instance = ScheduleController(response_builder_instance, schedule_provider_instance)
	user_controller_instance = UserController(response_builder_instance, authentication_provider_instance, user_provider_instance)
	worker_controller_instance = WorkerController(response_builder_instance, job_provider_instance, run_provider_instance, worker_provider_instance)
	me_controller_instance = MeController(response_builder_instance, authentication_provider_instance, user_provider_instance, user_controller_instance)

	service_setup.configure(application)
	service_setup.register_handlers(application, service_instance)

	service_setup.register_routes(
		application = application,
		service = service_instance,
		admin_controller = admin_controller_instance,
		job_controller = job_controller_instance,
		me_controller = me_controller_instance,
		project_controller = project_controller_instance,
		run_controller = run_controller_instance,
		schedule_controller = schedule_controller_instance,
		user_controller = user_controller_instance,
		worker_controller = worker_controller_instance,
	)

	application.add_url_rule("/me/routes", methods = [ "GET" ], view_func = lambda: list_routes(response_builder_instance, authorization_provider_instance))

	return application


def list_routes(response_builder: ResponseBuilder, authorization_provider: AuthorizationProvider) -> Any:
	route_collection = []
	for rule in flask.current_app.url_map.iter_rules():
		if "GET" in rule.methods and not rule.rule.startswith("/static/"):
			if authorization_provider.authorize_request(flask.request.user, "GET", rule.rule):
				route_collection.append(rule.rule)

	route_collection.sort()

	return response_builder.create_data_response(route_collection)


if __name__ == "__main__":
	main()
