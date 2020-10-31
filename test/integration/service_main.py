import argparse
import importlib
import logging

import flask

from bhamon_orchestra_model.authentication_provider import AuthenticationProvider
from bhamon_orchestra_model.authorization_provider import AuthorizationProvider
from bhamon_orchestra_model.database.file_storage import FileStorage
from bhamon_orchestra_model.date_time_provider import DateTimeProvider
from bhamon_orchestra_model.job_provider import JobProvider
from bhamon_orchestra_model.project_provider import ProjectProvider
from bhamon_orchestra_model.run_provider import RunProvider
from bhamon_orchestra_model.schedule_provider import ScheduleProvider
from bhamon_orchestra_model.user_provider import UserProvider
from bhamon_orchestra_model.worker_provider import WorkerProvider

import bhamon_orchestra_service.service as service

import environment


logger = logging.getLogger("Service")


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


def create_application(arguments):
	database_metadata = None
	if arguments.database.startswith("postgresql://"):
		database_metadata = importlib.import_module("bhamon_orchestra_model.database.sql_database_model").metadata

	database_client_factory = environment.create_database_client_factory(arguments.database, database_metadata)
	file_storage_instance = FileStorage(".")
	date_time_provider_instance = DateTimeProvider()

	application = flask.Flask(__name__)
	application.database_client_factory = database_client_factory
	application.authentication_provider = AuthenticationProvider(date_time_provider_instance)
	application.authorization_provider = AuthorizationProvider()
	application.job_provider = JobProvider(date_time_provider_instance)
	application.project_provider = ProjectProvider(date_time_provider_instance)
	application.run_provider = RunProvider(file_storage_instance, date_time_provider_instance)
	application.schedule_provider = ScheduleProvider(date_time_provider_instance)
	application.user_provider = UserProvider(date_time_provider_instance)
	application.worker_provider = WorkerProvider(date_time_provider_instance)

	application.run_result_transformer = transform_run_results

	application.external_services = {}

	service.configure(application)
	service.register_handlers(application)
	service.register_routes(application)

	application.add_url_rule("/me/routes", methods = [ "GET" ], view_func = list_routes)

	return application


def transform_run_results(project_identifier, run_identifier, run_results): # pylint: disable = unused-argument
	return run_results


def list_routes():
	route_collection = []
	for rule in flask.current_app.url_map.iter_rules():
		if "GET" in rule.methods and not rule.rule.startswith("/static/"):
			if flask.current_app.authorization_provider.authorize_request(flask.request.user, "GET", rule.rule):
				route_collection.append(rule.rule)

	route_collection.sort()

	return flask.jsonify(route_collection)


if __name__ == "__main__":
	main()
