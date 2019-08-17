import logging

import scripts.model.linting


logger = logging.getLogger("Main")


def configure_argument_parser(environment, configuration, subparsers): # pylint: disable = unused-argument
	return subparsers.add_parser("lint", help = "run linter")


def run(environment, configuration, arguments): # pylint: disable = unused-argument
	lint_packages(environment["python3_executable"], configuration["components"])
	lint_tests(environment["python3_executable"], "./test")


def lint_packages(python_executable, component_collection):
	logger.info("Running linter in python packages")
	print("")

	all_results = []

	for component in component_collection:
		pylint_results = scripts.model.linting.run_pylint(python_executable, component["packages"][0])
		print("")

		component_results = { "name": component["name"] }
		component_results.update(pylint_results)
		all_results.append(component_results)

	if any(not result["success"] for result in all_results):
		raise RuntimeError("Linting failed")


def lint_tests(python_executable, test_directory):
	logger.info("Running linter in python tests")
	print("")

	pylint_results = scripts.model.linting.run_pylint(python_executable, test_directory)
	if not pylint_results["success"]:
		raise RuntimeError("Linting failed")
