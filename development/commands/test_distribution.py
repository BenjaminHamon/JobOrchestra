import logging
import os
import shutil
import uuid

import bhamon_development_toolkit.python.system as python_system
import bhamon_development_toolkit.python.test as python_test

import development.commands.distribute
import development.commands.test


logger = logging.getLogger("Main")


def configure_argument_parser(environment, configuration, subparsers): # pylint: disable = unused-argument
	parser = subparsers.add_parser("test-distribution", help = "run the test suite on the distribution packages")
	parser.add_argument("--identifier", default = str(uuid.uuid4()), metavar = "<identifier>", help = "specify a identifier for the run (default to a GUID)")
	parser.add_argument("--filter", metavar = "<expression>", help = "specify a string expression to select tests to run")
	parser.set_defaults(func = run)


def run(environment, configuration, arguments): # pylint: disable = unused-argument
	logger.info("Setting up python virtual environment")
	venv_directory = os.path.join(configuration["artifact_directory"], "test_results", arguments.identifier + "_" + "venv")

	if not arguments.simulate and os.path.exists(venv_directory):
		shutil.rmtree(venv_directory)

	python_system.setup_virtual_environment(environment["python3_system_executable"], venv_directory, arguments.simulate)

	print("")

	python_executable = os.path.join(venv_directory, "scripts", "python")
	python_package_repository = environment.get("python_package_repository_web_url", None)
	package_directory = os.path.join(configuration["artifact_directory"], "distributions")
	development.commands.distribute.install_for_test(python_executable, python_package_repository, configuration, package_directory, arguments.simulate)

	print("")

	result_directory = os.path.join(configuration["artifact_directory"], "test_results")
	report = python_test.run_pytest(python_executable, result_directory, arguments.identifier, "./test",  arguments.filter, simulate = arguments.simulate)

	if arguments.results:
		development.commands.test.save_results(arguments.results, report, simulate = arguments.simulate)

	if not report["success"]:
		raise RuntimeError("Test run failed")
