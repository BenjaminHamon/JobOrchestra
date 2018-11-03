import argparse
import logging

import bhamon_build_master.build_provider as build_provider
import bhamon_build_master.file_storage as file_storage
import bhamon_build_master.job_provider as job_provider
import bhamon_build_master.json_database_client as json_database_client
import bhamon_build_master.task_provider as task_provider
import bhamon_build_master.worker_provider as worker_provider

import environment


def parse_arguments():
	argument_parser = argparse.ArgumentParser()
	argument_parser.add_argument("--address", required = True, help = "Set the address for the server to listen to")
	argument_parser.add_argument("--port", required = True, type = int, help = "Set the port for the server to listen to")
	return argument_parser.parse_args()


if __name__ == "__main__":
	environment.configure_logging(logging.INFO)
	arguments = parse_arguments()

	from bhamon_build_master.service import application

	database_client_instance = json_database_client.JsonDatabaseClient(".")
	file_storage_instance = file_storage.FileStorage(".")

	application.build_provider = build_provider.BuildProvider(database_client_instance, file_storage_instance)
	application.job_provider = job_provider.JobProvider(database_client_instance)
	application.task_provider = task_provider.TaskProvider(database_client_instance)
	application.worker_provider = worker_provider.WorkerProvider(database_client_instance)

	application.run(host = arguments.address, port = arguments.port)
