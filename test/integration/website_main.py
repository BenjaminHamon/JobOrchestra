import argparse
import logging

import flask

import bhamon_build_website.website as website

import environment


def main():
	environment.configure_logging(logging.INFO)
	arguments = parse_arguments()

	application = flask.Flask(__name__, static_folder = None)
	application.service_url = "http://%s:%s" % (environment.service_address, environment.service_port)
	application.artifact_storage_path = None
	application.artifact_storage_url = None

	website.configure(application)
	website.register_handlers(application)
	website.register_routes(application)
	website.register_resources(application)

	application.run(host = arguments.address, port = arguments.port)


def parse_arguments():
	argument_parser = argparse.ArgumentParser()
	argument_parser.add_argument("--address", required = True, help = "Set the address for the server to listen to")
	argument_parser.add_argument("--port", required = True, type = int, help = "Set the port for the server to listen to")
	return argument_parser.parse_args()


if __name__ == "__main__":
	main()
