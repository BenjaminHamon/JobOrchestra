import argparse
import logging

import flask

from bhamon_orchestra_model.date_time_provider import DateTimeProvider
from bhamon_orchestra_model.serialization.json_serializer import JsonSerializer
from bhamon_orchestra_model.users.authorization_provider import AuthorizationProvider

import bhamon_orchestra_website.website_setup as website_setup
from bhamon_orchestra_website.admin_controller import AdminController
from bhamon_orchestra_website.job_controller import JobController
from bhamon_orchestra_website.me_controller import MeController
from bhamon_orchestra_website.project_controller import ProjectController
from bhamon_orchestra_website.run_controller import RunController
from bhamon_orchestra_website.schedule_controller import ScheduleController
from bhamon_orchestra_website.service_client import ServiceClient
from bhamon_orchestra_website.user_controller import UserController
from bhamon_orchestra_website.website import Website
from bhamon_orchestra_website.worker_controller import WorkerController

from . import environment


logger = logging.getLogger("Main")


def main():
	arguments = parse_arguments()
	environment_instance = environment.load_environment()
	environment.configure_logging(environment_instance, arguments)

	application = create_application(environment_instance)
	application.run(host = arguments.address, port = arguments.port)


def parse_arguments():
	argument_parser = argparse.ArgumentParser()
	argument_parser.add_argument("--address", required = True, help = "Set the address for the server to listen to")
	argument_parser.add_argument("--port", required = True, type = int, help = "Set the port for the server to listen to")
	return argument_parser.parse_args()


def create_application(environment_instance):
	application = flask.Flask(__name__, static_folder = None)
	application.secret_key = "secret"

	date_time_provider_instance = DateTimeProvider()
	serializer_instance = JsonSerializer(indent = 4)
	authorization_provider_instance = AuthorizationProvider()
	service_client_instance = ServiceClient(serializer_instance, environment_instance["orchestra_service_url"])

	website_instance = Website(application, date_time_provider_instance, authorization_provider_instance, service_client_instance)
	admin_controller_instance = AdminController(application, service_client_instance)
	job_controller_instance = JobController(service_client_instance)
	me_controller_instance = MeController(date_time_provider_instance, service_client_instance)
	project_controller_instance = ProjectController(service_client_instance)
	run_controller_instance = RunController(service_client_instance)
	schedule_controller_instance = ScheduleController(service_client_instance)
	user_controller_instance = UserController(date_time_provider_instance, authorization_provider_instance, service_client_instance)
	worker_controller_instance = WorkerController(service_client_instance)

	website_setup.configure(application, website_instance)
	website_setup.register_handlers(application, website_instance)
	website_setup.register_resources(application)

	website_setup.register_routes(
		application = application,
		website = website_instance,
		admin_controller = admin_controller_instance,
		job_controller = job_controller_instance,
		me_controller = me_controller_instance,
		project_controller = project_controller_instance,
		run_controller = run_controller_instance,
		schedule_controller = schedule_controller_instance,
		user_controller = user_controller_instance,
		worker_controller = worker_controller_instance,
	)

	return application


if __name__ == "__main__":
	main()
