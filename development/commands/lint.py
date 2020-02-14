import glob
import logging
import os
import uuid

import jinja2

import bhamon_development_toolkit.python.lint
import bhamon_development_toolkit.workspace


logger = logging.getLogger("Main")


def configure_argument_parser(environment, configuration, subparsers): # pylint: disable = unused-argument
	parser = subparsers.add_parser("lint", help = "run linter")
	parser.add_argument("--identifier", default = str(uuid.uuid4()), help = "specify a identifier for the run (default to a GUID)")
	parser.set_defaults(func = run)


def run(environment, configuration, arguments): # pylint: disable = unused-argument
	try:
		lint_packages(environment["python3_executable"], arguments.identifier, configuration["components"], arguments.simulate)
		lint_templates(arguments.identifier, configuration["components"], arguments.simulate)
		lint_tests(environment["python3_executable"], arguments.identifier, "./test", arguments.simulate)
	finally:
		save_results(arguments.identifier, arguments.results, arguments.simulate)


def lint_packages(python_executable, run_identifier, component_collection, simulate):
	logger.info("Running linter for packages (RunIdentifier: %s)", run_identifier)
	print("")

	all_results = []

	for component in component_collection:
		pylint_results = bhamon_development_toolkit.python.lint.run_pylint(python_executable, "test_results", run_identifier, component["name"].replace("-", "_"), simulate)
		print("")

		component_results = { "name": component["name"] }
		component_results.update(pylint_results)
		all_results.append(component_results)

	if any(not result["success"] for result in all_results):
		raise RuntimeError("Linting failed")


def lint_templates(run_identifier, component_collection, simulate):
	logger.info("Running linter for templates (RunIdentifier: %s)", run_identifier)
	print("")

	all_results = []

	for component in component_collection:
		template_directory = os.path.join(component["path"], component["name"].replace("-", "_"), "templates")

		if os.path.isdir(template_directory):
			validation_result = validate_html_templates(template_directory, simulate)
			print("")
			all_results.append({ "name": component["name"], "success": validation_result })

	if any(not result["success"] for result in all_results):
		raise RuntimeError("Linting failed")


def validate_html_templates(template_directory, simulate):
	logger.info("Validating HTML templates in '%s'", template_directory)

	jinja_environment = jinja2.Environment()
	jinja_environment.autoescape = True

	success = True

	for template_path in glob.glob(os.path.join(template_directory, "**", "*.html"), recursive = True):
		try:
			with open(template_path, mode = "r") as template_file:
				if not simulate:
					jinja_environment.parse(template_file.read())
		except jinja2.TemplateSyntaxError as exception:
			success = False
			logger.error("(%s) TemplateSyntaxError: %s", template_path, exception)

	if success:
		logger.info("Linting succeeded for '%s'", template_directory)
	else:
		logger.error("Linting failed for '%s'", template_directory)

	return success


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
