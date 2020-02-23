import argparse
import json
import logging
import types

from bhamon_orchestra_model.authentication_provider import AuthenticationProvider
from bhamon_orchestra_model.authorization_provider import AuthorizationProvider
from bhamon_orchestra_model.database.file_storage import FileStorage
from bhamon_orchestra_model.date_time_provider import DateTimeProvider
from bhamon_orchestra_model.job_provider import JobProvider
from bhamon_orchestra_model.project_provider import ProjectProvider
from bhamon_orchestra_model.run_provider import RunProvider
from bhamon_orchestra_model.schedule_provider import ScheduleProvider
from bhamon_orchestra_model.task_provider import TaskProvider
from bhamon_orchestra_model.user_provider import UserProvider
from bhamon_orchestra_model.worker_provider import WorkerProvider

import bhamon_orchestra_cli.admin_controller as admin_controller
import bhamon_orchestra_cli.database_controller as database_controller

import environment


def main():
	environment.configure_logging(logging.INFO)
	arguments = parse_arguments()

	application = create_application(arguments)
	result = arguments.handler(application, arguments)
	print(json.dumps(result, indent = 4))


def parse_arguments():
	main_parser = argparse.ArgumentParser()
	main_parser.add_argument("--database", required = True, metavar = "<uri>", help = "set the database uri")

	subparsers = main_parser.add_subparsers(title = "commands", metavar = "<command>")
	subparsers.required = True

	admin_controller.register_commands(subparsers)
	database_controller.register_commands(subparsers)

	return main_parser.parse_args()


def create_application(arguments):
	database_client_instance = environment.create_database_client(arguments.database)
	file_storage_instance = FileStorage(".")
	date_time_provider_instance = DateTimeProvider()

	application = types.SimpleNamespace()
	application.authentication_provider = AuthenticationProvider(database_client_instance, date_time_provider_instance)
	application.authorization_provider = AuthorizationProvider()
	application.job_provider = JobProvider(database_client_instance, date_time_provider_instance)
	application.project_provider = ProjectProvider(database_client_instance, date_time_provider_instance)
	application.run_provider = RunProvider(database_client_instance, file_storage_instance, date_time_provider_instance)
	application.schedule_provider = ScheduleProvider(database_client_instance, date_time_provider_instance)
	application.task_provider = TaskProvider(database_client_instance, date_time_provider_instance)
	application.user_provider = UserProvider(database_client_instance, date_time_provider_instance)
	application.worker_provider = WorkerProvider(database_client_instance, date_time_provider_instance)

	return application


if __name__ == "__main__":
	main()
