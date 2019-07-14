import argparse
import importlib
import logging

import filelock

import bhamon_build_master.master as master
import bhamon_build_master.supervisor as supervisor
import bhamon_build_master.task_processor as task_processor
import bhamon_build_model.build_provider as build_provider
import bhamon_build_model.file_storage as file_storage
import bhamon_build_model.job_provider as job_provider
import bhamon_build_model.task_provider as task_provider
import bhamon_build_model.worker_provider as worker_provider

import configuration
import configuration_extensions
import environment


def main():
	environment.configure_logging(logging.INFO)
	arguments = parse_arguments()

	with filelock.FileLock("build_master.lock", 5):
		database_client_instance = environment.create_database_client(arguments.database)
		file_storage_instance = file_storage.FileStorage(".")

		build_provider_instance = build_provider.BuildProvider(database_client_instance, file_storage_instance)
		job_provider_instance = job_provider.JobProvider(database_client_instance)
		task_provider_instance = task_provider.TaskProvider(database_client_instance)
		worker_provider_instance = worker_provider.WorkerProvider(database_client_instance)

		task_processor_instance = task_processor.TaskProcessor(
			task_provider = task_provider_instance,
		)

		worker_selector_instance = configuration_extensions.WorkerSelector(
			worker_provider = worker_provider_instance,
		)

		supervisor_instance = supervisor.Supervisor(
			host = arguments.address,
			port = arguments.port,
			worker_provider = worker_provider_instance,
			job_provider = job_provider_instance,
			build_provider = build_provider_instance,
			worker_selector = worker_selector_instance,
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


def reload_configuration():
	importlib.reload(configuration)
	return configuration.configure()


if __name__ == "__main__":
	main()
