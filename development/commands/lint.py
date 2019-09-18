import logging
import uuid

import bhamon_development_toolkit.python.lint
import bhamon_development_toolkit.workspace


logger = logging.getLogger("Main")


def configure_argument_parser(environment, configuration, subparsers): # pylint: disable = unused-argument
	return subparsers.add_parser("lint", help = "run linter")


def run(environment, configuration, arguments): # pylint: disable = unused-argument
	run_identifier = uuid.uuid4()

	try:
		lint_packages(environment["python3_executable"], run_identifier, configuration["components"], arguments.simulate)
		lint_tests(environment["python3_executable"], run_identifier, "./test", arguments.simulate)
	finally:
		save_results(run_identifier, arguments.results, arguments.simulate)


def lint_packages(python_executable, run_identifier, component_collection, simulate):
	logger.info("Running linter for packages (RunIdentifier: %s)", run_identifier)
	print("")

	all_results = []

	for component in component_collection:
		pylint_results = bhamon_development_toolkit.python.lint.run_pylint(python_executable, "test_results", run_identifier, component["packages"][0], simulate)
		print("")

		component_results = { "name": component["name"] }
		component_results.update(pylint_results)
		all_results.append(component_results)

	if any(not result["success"] for result in all_results):
		raise RuntimeError("Linting failed")


def lint_tests(python_executable, run_identifier, test_directory, simulate):
	logger.info("Running linter for tests (RunIdentifier: %s)", run_identifier)
	print("")

	pylint_results = bhamon_development_toolkit.python.lint.run_pylint(python_executable, "test_results", run_identifier, test_directory, simulate)
	if not pylint_results["success"]:
		raise RuntimeError("Linting failed")


def save_results(run_identifier, result_file_path, simulate):
	test_results = bhamon_development_toolkit.python.lint.get_aggregated_results("test_results", run_identifier)

	if result_file_path:
		results = bhamon_development_toolkit.workspace.load_results(result_file_path)
		results["tests"] = results.get("tests", [])
		results["tests"].append(test_results)
		if not simulate:
			bhamon_development_toolkit.workspace.save_results(result_file_path, results)
