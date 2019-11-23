import argparse
import json
import logging
import types

from bhamon_build_model.authentication_provider import AuthenticationProvider
from bhamon_build_model.authorization_provider import AuthorizationProvider
from bhamon_build_model.build_provider import BuildProvider
from bhamon_build_model.file_storage import FileStorage
from bhamon_build_model.job_provider import JobProvider
from bhamon_build_model.task_provider import TaskProvider
from bhamon_build_model.user_provider import UserProvider
from bhamon_build_model.worker_provider import WorkerProvider

import bhamon_build_cli.admin_controller as admin_controller

import environment


def main():
	environment.configure_logging(logging.INFO)
	arguments = parse_arguments()

	application = create_application(arguments)
	result = arguments.handler(application, arguments)
	print(json.dumps(result, indent = 4))


def parse_arguments():
	main_parser = argparse.ArgumentParser()
	main_parser.add_argument("--database", required = True, metavar = "<uri>", help = "set the build database uri")

	subparsers = main_parser.add_subparsers(title = "commands", metavar = "<command>")
	subparsers.required = True

	admin_controller.register_commands(subparsers)

	return main_parser.parse_args()


def create_application(arguments):
	database_client_instance = environment.create_database_client(arguments.database)
	file_storage_instance = FileStorage(".")

	application = types.SimpleNamespace()
	application.authentication_provider = AuthenticationProvider(database_client_instance)
	application.authorization_provider = AuthorizationProvider()
	application.build_provider = BuildProvider(database_client_instance, file_storage_instance)
	application.job_provider = JobProvider(database_client_instance)
	application.task_provider = TaskProvider(database_client_instance)
	application.user_provider = UserProvider(database_client_instance)
	application.worker_provider = WorkerProvider(database_client_instance)

	return application


if __name__ == "__main__":
	main()
