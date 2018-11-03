import argparse
import logging

import bhamon_build_worker.controller as controller

import environment


# Rapid requests to reduce delays in tests
controller.wait_delay_seconds = 1


def parse_arguments():

	def parse_key_value_parameter(argument_value):
		key_value = argument_value.split("=")
		if len(key_value) != 2:
			raise argparse.ArgumentTypeError("invalid key value parameter: '%s'" % argument_value)
		return (key_value[0], key_value[1])

	main_parser = argparse.ArgumentParser()
	main_parser.add_argument("--service-url", required = True, help = "set the build service url to send requests to")
	main_parser.add_argument("--results", required = True, help = "set the file path where to store the build results")

	subparsers = main_parser.add_subparsers(title = "commands", metavar = "<command>")
	subparsers.required = True

	command_parser = subparsers.add_parser("trigger", help = "trigger a build")
	command_parser.add_argument("job_identifier", help = "set the job to trigger a build for")
	command_parser.add_argument("--parameters", nargs = "*", type = parse_key_value_parameter, default = [],
		metavar = "<key=value>", help = "set parameters for the artifact")
	command_parser.set_defaults(func = trigger_build)

	command_parser = subparsers.add_parser("wait", help = "wait for triggered builds")
	command_parser.set_defaults(func = wait_build)

	arguments = main_parser.parse_args()
	if hasattr(arguments, "parameters"):
		arguments.parameters = { key: value for key, value in arguments.parameters }

	return arguments


def trigger_build(arguments):
	controller.trigger_build(arguments.service_url, arguments.results, arguments.job_identifier, arguments.parameters)


def wait_build(arguments):
	controller.wait_build(arguments.service_url, arguments.results)


if __name__ == "__main__":
	environment.configure_logging(logging.INFO)
	arguments = parse_arguments()
	arguments.func(arguments)
