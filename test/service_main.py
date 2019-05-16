import argparse
import logging

import flask
import pymongo

import bhamon_build_model.build_provider as build_provider
import bhamon_build_model.file_storage as file_storage
import bhamon_build_model.job_provider as job_provider
import bhamon_build_model.json_database_client as json_database_client
import bhamon_build_model.mongo_database_client as mongo_database_client
import bhamon_build_model.task_provider as task_provider
import bhamon_build_model.worker_provider as worker_provider
import bhamon_build_service.service as service

import environment


def main():
	environment.configure_logging(logging.INFO)
	arguments = parse_arguments()

	database_client_instance = create_database_client(arguments.database)
	file_storage_instance = file_storage.FileStorage(".")

	application = flask.Flask(__name__)
	application.build_provider = build_provider.BuildProvider(database_client_instance, file_storage_instance)
	application.job_provider = job_provider.JobProvider(database_client_instance)
	application.task_provider = task_provider.TaskProvider(database_client_instance)
	application.worker_provider = worker_provider.WorkerProvider(database_client_instance)

	service.register_handlers(application)
	service.register_routes(application)

	application.run(host = arguments.address, port = arguments.port)


def parse_arguments():
	argument_parser = argparse.ArgumentParser()
	argument_parser.add_argument("--address", required = True, help = "Set the address for the server to listen to")
	argument_parser.add_argument("--port", required = True, type = int, help = "Set the port for the server to listen to")
	argument_parser.add_argument("--database", required = True, help = "Set the build database uri")
	return argument_parser.parse_args()


def create_database_client(database_uri):
	if database_uri == "json":
		return json_database_client.JsonDatabaseClient(".")
	if database_uri.startswith("mongodb://"):
		return mongo_database_client.MongoDatabaseClient(pymongo.MongoClient(database_uri).get_database())
	raise ValueError("Unsupported database uri '%s'" % database_uri)


if __name__ == "__main__":
	main()
