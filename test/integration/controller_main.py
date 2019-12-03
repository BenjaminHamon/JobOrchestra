import argparse
import json
import logging

import bhamon_orchestra_worker.controller as controller

import environment


# Rapid requests to reduce delays in tests
controller.wait_delay_seconds = 1


def main():
	environment.configure_logging(logging.INFO)
	arguments = parse_arguments()

	with open(arguments.authentication, "r") as authentication_file:
		authentication = json.load(authentication_file)

	arguments.func(arguments, (authentication["user"], authentication["secret"]))


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


def trigger_run(arguments, authorization):
	controller.trigger_run(arguments.service_url, arguments.results, arguments.job_identifier, arguments.parameters, authorization)


def wait_run(arguments, authorization):
	controller.wait_run(arguments.service_url, arguments.results, authorization)


if __name__ == "__main__":
	main()
