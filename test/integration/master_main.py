import argparse
import functools
import importlib
import logging

import filelock

from bhamon_orchestra_master.job_scheduler import JobScheduler
from bhamon_orchestra_master.master import Master
from bhamon_orchestra_master.protocol import WebSocketServerProtocol
from bhamon_orchestra_master.supervisor import Supervisor
from bhamon_orchestra_master.worker_selector import WorkerSelector
from bhamon_orchestra_model.authentication_provider import AuthenticationProvider
from bhamon_orchestra_model.authorization_provider import AuthorizationProvider
from bhamon_orchestra_model.database.file_data_storage import FileDataStorage
from bhamon_orchestra_model.date_time_provider import DateTimeProvider
from bhamon_orchestra_model.job_provider import JobProvider
from bhamon_orchestra_model.project_provider import ProjectProvider
from bhamon_orchestra_model.run_provider import RunProvider
from bhamon_orchestra_model.schedule_provider import ScheduleProvider
from bhamon_orchestra_model.user_provider import UserProvider
from bhamon_orchestra_model.worker_provider import WorkerProvider

import configuration
import environment
import factory


logger = logging.getLogger("Master")


def main():
	arguments = parse_arguments()
	environment_instance = environment.load_environment()
	environment.configure_logging(environment_instance, arguments)

	with filelock.FileLock("master.lock", 5):
		application = create_application(arguments)
		application.run()


def parse_arguments():
	argument_parser = argparse.ArgumentParser()
	argument_parser.add_argument("--address", required = True, help = "Set the address for the server to listen to")
	argument_parser.add_argument("--port", required = True, type = int, help = "Set the port for the server to listen to")
	argument_parser.add_argument("--database", required = True, help = "Set the database uri")
	return argument_parser.parse_args()


def create_application(arguments): # pylint: disable = too-many-locals
	database_metadata = None
	if arguments.database.startswith("postgresql://"):
		database_metadata = importlib.import_module("bhamon_orchestra_model.database.sql_database_model").metadata

	database_client_factory = factory.create_database_client_factory(arguments.database, database_metadata)
	data_storage_instance = FileDataStorage(".")
	date_time_provider_instance = DateTimeProvider()

	authentication_provider_instance = AuthenticationProvider(date_time_provider_instance)
	authorization_provider_instance = AuthorizationProvider()
	job_provider_instance = JobProvider(date_time_provider_instance)
	project_provider_instance = ProjectProvider(date_time_provider_instance)
	run_provider_instance = RunProvider(data_storage_instance, date_time_provider_instance)
	schedule_provider_instance = ScheduleProvider(date_time_provider_instance)
	user_provider_instance = UserProvider(date_time_provider_instance)
	worker_provider_instance = WorkerProvider(date_time_provider_instance)

	protocol_factory = functools.partial(
		WebSocketServerProtocol,
		database_client_factory = database_client_factory,
		user_provider = user_provider_instance,
		authentication_provider = authentication_provider_instance,
		authorization_provider = authorization_provider_instance,
	)

	supervisor_instance = Supervisor(
		host = arguments.address,
		port = arguments.port,
		protocol_factory = protocol_factory,
		database_client_factory = database_client_factory,
		worker_provider = worker_provider_instance,
		run_provider = run_provider_instance,
	)

	worker_selector_instance = WorkerSelector(
		database_client_factory = database_client_factory,
		worker_provider = worker_provider_instance,
		supervisor = supervisor_instance,
	)

	job_scheduler_instance = JobScheduler(
		database_client_factory = database_client_factory,
		job_provider = job_provider_instance,
		run_provider = run_provider_instance,
		schedule_provider = schedule_provider_instance,
		supervisor = supervisor_instance,
		worker_selector = worker_selector_instance,
		date_time_provider = date_time_provider_instance,
	)

	master_instance = Master(
		database_client_factory = database_client_factory,
		project_provider = project_provider_instance,
		job_provider = job_provider_instance,
		schedule_provider = schedule_provider_instance,
		worker_provider = worker_provider_instance,
		job_scheduler = job_scheduler_instance,
		supervisor = supervisor_instance,
	)

	# Rapid updates to reduce delays in tests
	job_scheduler_instance.update_interval_seconds = 1
	supervisor_instance.update_interval_seconds = 1

	master_instance.apply_configuration(configuration.configure())

	return master_instance


if __name__ == "__main__":
	main()
