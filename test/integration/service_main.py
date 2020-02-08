import argparse
import logging

import flask

from bhamon_orchestra_model.authentication_provider import AuthenticationProvider
from bhamon_orchestra_model.authorization_provider import AuthorizationProvider
from bhamon_orchestra_model.database.file_storage import FileStorage
from bhamon_orchestra_model.job_provider import JobProvider
from bhamon_orchestra_model.project_provider import ProjectProvider
from bhamon_orchestra_model.run_provider import RunProvider
from bhamon_orchestra_model.schedule_provider import ScheduleProvider
from bhamon_orchestra_model.task_provider import TaskProvider
from bhamon_orchestra_model.user_provider import UserProvider
from bhamon_orchestra_model.worker_provider import WorkerProvider

import bhamon_orchestra_service.service as service

import environment


def main():
	environment.configure_logging(logging.INFO)
	arguments = parse_arguments()

	application = create_application(arguments)
	application.run(host = arguments.address, port = arguments.port)


def parse_arguments():
	argument_parser = argparse.ArgumentParser()
	argument_parser.add_argument("--address", required = True, help = "Set the address for the server to listen to")
	argument_parser.add_argument("--port", required = True, type = int, help = "Set the port for the server to listen to")
	argument_parser.add_argument("--database", required = True, help = "Set the database uri")
	return argument_parser.parse_args()


def create_application(arguments):
	database_client_instance = environment.create_database_client(arguments.database)
	file_storage_instance = FileStorage(".")

	application = flask.Flask(__name__)
	application.authentication_provider = AuthenticationProvider(database_client_instance)
	application.authorization_provider = AuthorizationProvider()
	application.job_provider = JobProvider(database_client_instance)
	application.project_provider = ProjectProvider(database_client_instance)
	application.run_provider = RunProvider(database_client_instance, file_storage_instance)
	application.schedule_provider = ScheduleProvider(database_client_instance)
	application.task_provider = TaskProvider(database_client_instance)
	application.user_provider = UserProvider(database_client_instance)
	application.worker_provider = WorkerProvider(database_client_instance)

	application.external_services = {}

	service.configure(application)
	service.register_handlers(application)
	service.register_routes(application)

	application.add_url_rule("/me/routes", methods = [ "GET" ], view_func = list_routes)

	return application


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
