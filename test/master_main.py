import argparse
import importlib
import logging

import filelock
import pymongo

import bhamon_build_master.master as master
import bhamon_build_master.supervisor as supervisor
import bhamon_build_master.task_processor as task_processor
import bhamon_build_model.build_provider as build_provider
import bhamon_build_model.file_storage as file_storage
import bhamon_build_model.job_provider as job_provider
import bhamon_build_model.json_database_client as json_database_client
import bhamon_build_model.mongo_database_client as mongo_database_client
import bhamon_build_model.task_provider as task_provider
import bhamon_build_model.worker_provider as worker_provider

import configuration
import environment


def main():
	environment.configure_logging(logging.INFO)
	arguments = parse_arguments()

	with filelock.FileLock("build_master.lock", 5):
		database_client_instance = create_database_client(arguments.database)
		file_storage_instance = file_storage.FileStorage(".")

		build_provider_instance = build_provider.BuildProvider(database_client_instance, file_storage_instance)
		job_provider_instance = job_provider.JobProvider(database_client_instance)
		task_provider_instance = task_provider.TaskProvider(database_client_instance)
		worker_provider_instance = worker_provider.WorkerProvider(database_client_instance)

		task_processor_instance = task_processor.TaskProcessor(
			task_provider = task_provider_instance,
		)

		supervisor_instance = supervisor.Supervisor(
			host = arguments.address,
			port = arguments.port,
			worker_provider = worker_provider_instance,
			job_provider = job_provider_instance,
			build_provider = build_provider_instance,
			worker_selector = select_worker,
		)

		master_instance = master.Master(
			supervisor = supervisor_instance,
			task_processor = task_processor_instance,
			job_provider = job_provider_instance,
			worker_provider = worker_provider_instance,
			configuration_loader = reload_configuration,
		)

		# Rapid updates to reduce delays in tests
		supervisor_instance.update_interval_seconds = 1
		task_processor_instance.update_interval_seconds = 1

		master_instance.register_default_tasks()

		master_instance.run()


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


def reload_configuration():
	importlib.reload(configuration)
	return configuration.configure()


def select_worker(job, all_available_workers):
	return configuration.select_worker(job, all_available_workers)


if __name__ == "__main__":
	main()
