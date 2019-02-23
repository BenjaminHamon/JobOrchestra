import logging
import subprocess


def configure_argument_parser(environment, configuration, subparsers): # pylint: disable=unused-argument
	return subparsers.add_parser("lint", help = "run linter")


def run(environment, configuration, arguments): # pylint: disable=unused-argument
	lint(environment, configuration["components"])


def lint(environment, component_collection):
	logging.info("Running linter")
	logging.info("")

	pylint_command = [ environment["python3_executable"], "-m", "pylint" ]
	pylint_command += [ component["path"] for component in component_collection ]

	logging.info("+ %s", " ".join(pylint_command))
	subprocess.check_call(pylint_command)
