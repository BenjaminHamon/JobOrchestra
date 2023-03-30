import argparse
import importlib
import logging

from bhamon_orchestra_service import service_setup
from bhamon_orchestra_service.service import Service

from . import environment
from . import factory


logger = logging.getLogger("Main")


def main() -> None:
	arguments = parse_arguments()
	environment_instance = environment.load_environment()
	environment.configure_logging(environment_instance, arguments)

	application = create_application(arguments)
	application.run(address = arguments.address, port = arguments.port)


def parse_arguments() -> argparse.Namespace:
	argument_parser = argparse.ArgumentParser()
	argument_parser.add_argument("--address", required = True, help = "Set the address for the server to listen to")
	argument_parser.add_argument("--port", required = True, type = int, help = "Set the port for the server to listen to")
	argument_parser.add_argument("--database", required = True, help = "Set the database uri")
	return argument_parser.parse_args()


def create_application(arguments: argparse.Namespace) -> Service:
	database_metadata = None
	if arguments.database.startswith("postgresql://"):
		database_metadata = importlib.import_module("bhamon_orchestra_model.database.sql_database_model").metadata

	database_client_factory = factory.create_database_client_factory(arguments.database, database_metadata)

	external_services = {}
	file_storage_path = "."

	return service_setup.create_application(
		flask_import_name = __name__,
		database_client_factory = database_client_factory,
		file_storage_path = file_storage_path,
		external_services = external_services)


if __name__ == "__main__":
	main()
