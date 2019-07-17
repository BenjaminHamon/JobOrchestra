import argparse
import json
import logging
import types

import bhamon_build_cli.admin_controller as admin_controller
import bhamon_build_model.authentication_provider as authentication_provider
import bhamon_build_model.authorization_provider as authorization_provider
import bhamon_build_model.build_provider as build_provider
import bhamon_build_model.file_storage as file_storage
import bhamon_build_model.job_provider as job_provider
import bhamon_build_model.task_provider as task_provider
import bhamon_build_model.user_provider as user_provider
import bhamon_build_model.worker_provider as worker_provider

import environment


def main():
	environment.configure_logging(logging.INFO)
	arguments = parse_arguments()

	database_client_instance = environment.create_database_client(arguments.database)
	file_storage_instance = file_storage.FileStorage(".")

	application = types.SimpleNamespace()
	application.authentication_provider = authentication_provider.AuthenticationProvider(database_client_instance)
	application.authorization_provider = authorization_provider.AuthorizationProvider()
	application.build_provider = build_provider.BuildProvider(database_client_instance, file_storage_instance)
	application.job_provider = job_provider.JobProvider(database_client_instance)
	application.task_provider = task_provider.TaskProvider(database_client_instance)
	application.user_provider = user_provider.UserProvider(database_client_instance)
	application.worker_provider = worker_provider.WorkerProvider(database_client_instance)

	result = arguments.handler(application, arguments)
	print(json.dumps(result, indent = 4))


def parse_arguments():
	main_parser = argparse.ArgumentParser()
	main_parser.add_argument("--database", required = True, metavar = "<uri>", help = "set the build database uri")

	subparsers = main_parser.add_subparsers(title = "commands", metavar = "<command>")
	subparsers.required = True

	admin_controller.register_commands(subparsers)

	return main_parser.parse_args()


if __name__ == "__main__":
	main()
