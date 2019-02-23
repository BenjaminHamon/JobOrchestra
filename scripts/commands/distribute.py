import logging
import os
import subprocess


def configure_argument_parser(environment, configuration, subparsers): # pylint: disable=unused-argument
	return subparsers.add_parser("distribute", help = "create distribution packages")


def run(environment, configuration, arguments): # pylint: disable=unused-argument
	for component in configuration["components"]:
		create_distribution(environment, component, arguments.verbosity == "debug", arguments.simulate)


def create_distribution(environment, component, verbose, simulate):
	logging.info("Creating distribution for '%s'", component["name"])
	logging.info("")

	output_directory = os.path.join("..", ".build", component["path"])

	setup_command = [ environment["python3_executable"], "setup.py" ]
	setup_command += [ "--quiet" ] if not verbose else []
	setup_command += [ "--dry-run" ] if simulate else []
	setup_command += [ "sdist", "--dist-dir", output_directory, "--format", "zip" ]

	logging.info("+ %s", " ".join(setup_command))
	subprocess.check_call(setup_command, cwd = component["path"])
