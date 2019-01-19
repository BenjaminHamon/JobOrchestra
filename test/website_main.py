import argparse
import logging

import flask
import werkzeug

import bhamon_build_website.website as website

import environment


def parse_arguments():
	argument_parser = argparse.ArgumentParser()
	argument_parser.add_argument("--address", required = True, help = "Set the address for the server to listen to")
	argument_parser.add_argument("--port", required = True, type = int, help = "Set the port for the server to listen to")
	return argument_parser.parse_args()


if __name__ == "__main__":
	environment.configure_logging(logging.INFO)
	arguments = parse_arguments()

	application = flask.Flask(__name__, static_folder = None)
	application.service_url = "http://%s:%s" % (environment.service_address, environment.service_port)
	application.artifact_storage_path = None
	application.artifact_storage_url = None

	application.before_request(website.log_request)
	for exception in werkzeug.exceptions.default_exceptions:
		application.register_error_handler(exception, website.handle_error)

	website.register_routes(application)
	website.register_resources(application)

	application.run(host = arguments.address, port = arguments.port)
