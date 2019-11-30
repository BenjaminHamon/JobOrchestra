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


def parse_arguments():
	argument_parser = argparse.ArgumentParser()
	argument_parser.add_argument("--address", required = True, help = "Set the address for the server to listen to")
	argument_parser.add_argument("--port", required = True, type = int, help = "Set the port for the server to listen to")
	return argument_parser.parse_args()


def create_application(environment_instance):
	application = flask.Flask(__name__, static_folder = None)
	application.authorization_provider = AuthorizationProvider()
	application.service_url = environment_instance["build_service_url"]
	application.secret_key = "secret"

	website.configure(application)
	website.register_handlers(application)
	website.register_routes(application)
	website.register_resources(application)

	application.add_url_rule("/me/routes", methods = [ "GET" ], view_func = list_routes)

	return application


def list_routes():
	route_collection = []
	for rule in flask.current_app.url_map.iter_rules():
		if "GET" in rule.methods and not rule.rule.startswith("/static/"):
			is_authorized = flask.current_app.authorization_provider.authorize_request(flask.request.user, "GET", rule.rule)
			if is_authorized:
				route_collection.append(rule.rule)
	route_collection.sort()
	return flask.jsonify(route_collection)


if __name__ == "__main__":
	main()
