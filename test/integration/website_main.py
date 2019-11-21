import argparse
import logging

import flask

from bhamon_build_model.authorization_provider import AuthorizationProvider

import bhamon_build_website.website as website

import environment


def main():
	environment.configure_logging(logging.INFO)
	environment_instance = environment.load_environment()
	arguments = parse_arguments()

	application = create_application(environment_instance)
	application.run(host = arguments.address, port = arguments.port)


def create_application(environment_instance):
	application = flask.Flask(__name__, static_folder = None)
	application.authorization_provider = AuthorizationProvider()
	application.service_url = environment_instance["build_service_url"]
	application.secret_key = "secret"

	website.configure(application)
	website.register_handlers(application)
	website.register_routes(application)
	website.register_resources(application)

	return application


def parse_arguments():
	argument_parser = argparse.ArgumentParser()
	argument_parser.add_argument("--address", required = True, help = "Set the address for the server to listen to")
	argument_parser.add_argument("--port", required = True, type = int, help = "Set the port for the server to listen to")
	return argument_parser.parse_args()


if __name__ == "__main__":
	main()
