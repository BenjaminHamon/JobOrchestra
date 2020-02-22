import argparse
import json
import logging

from bhamon_orchestra_worker.controller import Controller

import environment


def main():
	environment.configure_logging(logging.INFO)
	arguments = parse_arguments()

	with open(arguments.authentication, "r") as authentication_file:
		authentication = json.load(authentication_file)

	controller_instance = Controller(arguments.service_url, (authentication["user"], authentication["secret"]))

	# Rapid requests to reduce delays in tests
	controller_instance.wait_delay_seconds = 1

	arguments.func(controller_instance, arguments)


def parse_arguments():

	def parse_key_value_parameter(argument_value):
		key_value = argument_value.split("=")
		if len(key_value) != 2:
			raise argparse.ArgumentTypeError("invalid key value parameter: '%s'" % argument_value)
		return (key_value[0], key_value[1])

	main_parser = argparse.ArgumentParser()
	main_parser.add_argument("--service-url", required = True, help = "set the service url to send requests to")
	main_parser.add_argument("--authentication", required = True, help = "set the file path containing credentials to communicate with the service")
	main_parser.add_argument("--results", required = True, help = "set the file path where to store the run results")

	subparsers = main_parser.add_subparsers(title = "commands", metavar = "<command>")
	subparsers.required = True

	command_parser = subparsers.add_parser("trigger", help = "trigger a run")
	command_parser.add_argument("project_identifier", help = "set the project to trigger a run for")
	command_parser.add_argument("job_identifier", help = "set the job to trigger a run for")
	command_parser.add_argument("--parameters", nargs = "*", type = parse_key_value_parameter, default = [],
		metavar = "<key=value>", help = "set parameters for the job")
	command_parser.set_defaults(func = trigger_run)

	command_parser = subparsers.add_parser("wait", help = "wait for triggered runs")
	command_parser.set_defaults(func = wait_run)

	arguments = main_parser.parse_args()
	if hasattr(arguments, "parameters"):
		arguments.parameters = dict(arguments.parameters)

	return arguments


def trigger_run(controller_instance, arguments):
	controller_instance.trigger_run(arguments.results, arguments.project_identifier, arguments.job_identifier, arguments.parameters)


def wait_run(controller_instance, arguments):
	controller_instance.wait_run(arguments.results)


if __name__ == "__main__":
	main()
