import logging
import os
import uuid

import bhamon_development_toolkit.python.system
import bhamon_development_toolkit.python.test
import bhamon_development_toolkit.workspace

import development.commands.distribute
import development.commands.test


logger = logging.getLogger("Main")


def configure_argument_parser(environment, configuration, subparsers): # pylint: disable = unused-argument
	parser = subparsers.add_parser("test-distribution", help = "run the test suite on the distribution packages")
	parser.add_argument("--identifier", default = str(uuid.uuid4()), help = "specify a identifier for the run (default to a GUID)")
	parser.add_argument("--filter", help = "specify a string expression to select tests to run")
	parser.set_defaults(func = run)


def run(environment, configuration, arguments): # pylint: disable = unused-argument
	logger.info("Setting up python virtual environment")
	venv_directory = os.path.join("test_results", arguments.identifier + "_" + "venv")
	bhamon_development_toolkit.python.system.setup_virtual_environment(environment["python3_system_executable"], venv_directory, arguments.simulate)

	print("")

	python_executable = os.path.join(venv_directory, "scripts", "python")
	python_package_repository = environment.get("python_package_repository_web_url", None)
	development.commands.distribute.install_for_test(python_executable, python_package_repository, configuration, arguments.simulate)

	print("")

	try:
		development.commands.test.test(python_executable, arguments.identifier, arguments.filter, arguments.simulate)
	finally:
		development.commands.test.save_results(arguments.identifier, arguments.results, arguments.simulate)
