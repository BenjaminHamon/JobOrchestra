import argparse
import importlib
import logging

import filelock

from bhamon_build_master.job_scheduler import JobScheduler
from bhamon_build_master.master import Master
from bhamon_build_master.supervisor import Supervisor
from bhamon_build_master.task_processor import TaskProcessor
from bhamon_build_model.authentication_provider import AuthenticationProvider
from bhamon_build_model.authorization_provider import AuthorizationProvider
from bhamon_build_model.build_provider import BuildProvider
from bhamon_build_model.database.file_storage import FileStorage
from bhamon_build_model.job_provider import JobProvider
from bhamon_build_model.task_provider import TaskProvider
from bhamon_build_model.user_provider import UserProvider
from bhamon_build_model.worker_provider import WorkerProvider

import configuration
import configuration_extensions
import environment


def main():
	environment.configure_logging(logging.INFO)
	arguments = parse_arguments()

	with filelock.FileLock("build_master.lock", 5):
		application = create_application(arguments)
		application.run()


def parse_arguments():
	argument_parser = argparse.ArgumentParser()
	argument_parser.add_argument("--address", required = True, help = "Set the address for the server to listen to")
	argument_parser.add_argument("--port", required = True, type = int, help = "Set the port for the server to listen to")
	argument_parser.add_argument("--database", required = True, help = "Set the build database uri")
	return argument_parser.parse_args()


def create_application(arguments):
	database_client_instance = environment.create_database_client(arguments.database)
	file_storage_instance = FileStorage(".")

	authentication_provider_instance = AuthenticationProvider(database_client_instance)
	authorization_provider_instance = AuthorizationProvider()
	build_provider_instance = BuildProvider(database_client_instance, file_storage_instance)
	job_provider_instance = JobProvider(database_client_instance)
	task_provider_instance = TaskProvider(database_client_instance)
	user_provider_instance = UserProvider(database_client_instance)
	worker_provider_instance = WorkerProvider(database_client_instance)

	task_processor_instance = TaskProcessor(
		task_provider = task_provider_instance,
	)

	worker_selector_instance = configuration_extensions.WorkerSelector(
		worker_provider = worker_provider_instance,
	)

	supervisor_instance = Supervisor(
		host = arguments.address,
		port = arguments.port,
		worker_provider = worker_provider_instance,
		build_provider = build_provider_instance,
		user_provider = user_provider_instance,
		authentication_provider = authentication_provider_instance,
		authorization_provider = authorization_provider_instance,
	)

	job_scheduler_instance = JobScheduler(
		supervisor = supervisor_instance,
		job_provider = job_provider_instance,
		build_provider = build_provider_instance,
		worker_selector = worker_selector_instance,
	)

	master_instance = Master(
		job_scheduler = job_scheduler_instance,
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

	return master_instance


def reload_configuration():
	importlib.reload(configuration)
	return configuration.configure()


if __name__ == "__main__":
	main()
