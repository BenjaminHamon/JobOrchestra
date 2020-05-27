import glob
import logging
import os
import shutil
import uuid

import jinja2

import bhamon_development_toolkit.python.lint as python_lint
import bhamon_development_toolkit.workspace as workspace


logger = logging.getLogger("Main")


def configure_argument_parser(environment, configuration, subparsers): # pylint: disable = unused-argument
	parser = subparsers.add_parser("lint", help = "run linter")
	parser.add_argument("--identifier", default = str(uuid.uuid4()), metavar = "<identifier>", help = "specify a identifier for the run (default to a GUID)")
	parser.set_defaults(func = run)


def run(environment, configuration, arguments): # pylint: disable = unused-argument
	session_success = True
	result_directory = os.path.join(configuration["artifact_directory"], "lint_results")

	if not arguments.simulate:
		if os.path.exists(os.path.join(result_directory, arguments.identifier)):
			shutil.rmtree(os.path.join(result_directory, arguments.identifier))
		os.makedirs(os.path.join(result_directory, arguments.identifier))

	for component in configuration["components"]:
		pylint_results = python_lint.run_pylint(environment["python3_executable"], result_directory, arguments.identifier,
				component["name"].replace("-", "_"), simulate = arguments.simulate)
		if not pylint_results["success"]:
			session_success = False

		print("")

	for component in configuration["components"]:
		template_directory = os.path.join(component["path"], component["name"].replace("-", "_"), "templates")

		if os.path.isdir(template_directory):
			validation_result = validate_html_templates(template_directory, simulate = arguments.simulate)
			if not validation_result:
				session_success = False

			print("")

	pylint_results = python_lint.run_pylint(environment["python3_executable"], result_directory, arguments.identifier, "./test", simulate = arguments.simulate)
	if not pylint_results["success"]:
		session_success = False

	print("")

	if arguments.results:
		save_results(arguments.results, result_directory, arguments.identifier, simulate = arguments.simulate)

	if not session_success:
		raise RuntimeError("Linting failed")


def validate_html_templates(template_directory, simulate):
	logger.info("Validating HTML templates in '%s'", template_directory)

	jinja_environment = jinja2.Environment()
	jinja_environment.autoescape = True

	success = True

	for template_path in glob.glob(os.path.join(template_directory, "**", "*.html"), recursive = True):
		try:
			with open(template_path, mode = "r", encoding = "utf-8") as template_file:
				if not simulate:
					jinja_environment.parse(template_file.read())
		except jinja2.TemplateSyntaxError as exception:
			success = False
			logger.error("(%s) TemplateSyntaxError: %s", template_path, exception)

	if success:
		logger.info("Validation succeeded for '%s'", template_directory)
	else:
		logger.error("Validation failed for '%s'", template_directory)

	return success


def save_results(result_file_path, result_directory, run_identifier, simulate):
	all_report_file_paths = glob.glob(os.path.join(result_directory, run_identifier, "*.json"))
	reports_as_results = python_lint.get_aggregated_results(all_report_file_paths)
	reports_as_results["run_identifier"] = run_identifier

	results = workspace.load_results(result_file_path)
	results["tests"] = results.get("tests", [])
	results["tests"].append(reports_as_results)

	if not simulate:
		workspace.save_results(result_file_path, results)
