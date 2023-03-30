import argparse
import importlib
import logging

import filelock

import bhamon_orchestra_master
from bhamon_orchestra_master import master_setup
from bhamon_orchestra_master.master import Master
from bhamon_orchestra_model.application import AsyncioApplication

from . import configuration
from . import environment
from . import factory


logger = logging.getLogger("Main")


def main() -> None:
	arguments = parse_arguments()
	environment_instance = environment.load_environment()
	environment.configure_logging(environment_instance, arguments)

	application_title = bhamon_orchestra_master.__product__ + " " + "Master"
	application_version = bhamon_orchestra_master.__version__

	with filelock.FileLock("master.lock", 5):
		master_application = create_application(arguments)
		master_application.apply_configuration(configuration.configure())
		asyncio_application = AsyncioApplication(application_title, application_version)
		asyncio_application.run_as_standalone(master_application.run(arguments.address, arguments.port))


def parse_arguments() -> argparse.Namespace:
	argument_parser = argparse.ArgumentParser()
	argument_parser.add_argument("--address", required = True, help = "Set the address for the server to listen to")
	argument_parser.add_argument("--port", required = True, type = int, help = "Set the port for the server to listen to")
	argument_parser.add_argument("--database", required = True, help = "Set the database uri")
	return argument_parser.parse_args()


def create_application(arguments: argparse.Namespace) -> Master:
	database_metadata = None
	if arguments.database.startswith("postgresql://"):
		database_metadata = importlib.import_module("bhamon_orchestra_model.database.sql_database_model").metadata

	database_client_factory = factory.create_database_client_factory(arguments.database, database_metadata)

	master_instance = master_setup.create_application(
		database_client_factory = database_client_factory,
		file_storage_path = ".")

	# Rapid updates to reduce delays in tests
	master_instance._job_scheduler.update_interval_seconds = 1 # pylint: disable = protected-access
	master_instance._supervisor.update_interval_seconds = 1 # pylint: disable = protected-access

	return master_instance


if __name__ == "__main__":
	main()
