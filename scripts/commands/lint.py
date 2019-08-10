import logging
import os
import subprocess


logger = logging.getLogger("Main")


def configure_argument_parser(environment, configuration, subparsers): # pylint: disable = unused-argument
	return subparsers.add_parser("lint", help = "run linter")


def run(environment, configuration, arguments): # pylint: disable = unused-argument
	lint_packages(environment["python3_executable"], configuration["components"])
	lint_tests(environment["python3_executable"], "test")


def lint_packages(python_executable, component_collection):
	logger.info("Running linter in python packages")

	pylint_command = [ python_executable, "-m", "pylint" ]
	pylint_command += [ os.path.join(component["path"], component["packages"][0]) for component in component_collection ]

	logger.info("+ %s", " ".join(pylint_command))
	subprocess.check_call(pylint_command)


def lint_tests(python_executable, test_directory):
	logger.info("Running linter in python tests")

	pylint_command = [ python_executable, "-m", "pylint", test_directory ]

	logger.info("+ %s", " ".join(pylint_command))
	subprocess.check_call(pylint_command)
