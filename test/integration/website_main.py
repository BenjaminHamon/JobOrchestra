import argparse
import logging

from bhamon_orchestra_website import website_setup
from bhamon_orchestra_website.website import Website

from . import environment


logger = logging.getLogger("Main")


def main() -> None:
	arguments = parse_arguments()
	environment_instance = environment.load_environment()
	environment.configure_logging(environment_instance, arguments)

	application = create_application(environment_instance)
	application.run(address = arguments.address, port = arguments.port)


def parse_arguments() -> argparse.Namespace:
	argument_parser = argparse.ArgumentParser()
	argument_parser.add_argument("--address", required = True, help = "Set the address for the server to listen to")
	argument_parser.add_argument("--port", required = True, type = int, help = "Set the port for the server to listen to")
	return argument_parser.parse_args()


def create_application(environment_instance: dict) -> Website:
	return website_setup.create_application(
		flask_import_name = __name__,
		flask_secret_key = "secret",
		orchestra_service_url = environment_instance["orchestra_service_url"])


if __name__ == "__main__":
	main()
