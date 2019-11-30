import logging
import uuid

import bhamon_development_toolkit.python.test
import bhamon_development_toolkit.workspace


logger = logging.getLogger("Main")


def configure_argument_parser(environment, configuration, subparsers): # pylint: disable = unused-argument
	parser = subparsers.add_parser("test", help = "run the test suite")
	parser.add_argument("--identifier", default = str(uuid.uuid4()), help = "specify a identifier for the run (default to a GUID)")
	parser.add_argument("--filter", help = "specify a string expression to select tests to run")
	return parser


def run(environment, configuration, arguments): # pylint: disable = unused-argument
	try:
		test(environment["python3_executable"], arguments.identifier, arguments.filter, arguments.simulate)
	finally:
		save_results(arguments.identifier, arguments.results, arguments.simulate)


def test(python_executable, run_identifier, filter_expression, simulate):
	logger.info("Running test suite (RunIdentifier: '%s', Filter: '%s')", run_identifier, filter_expression)
	print("")

	report = bhamon_development_toolkit.python.test.run_pytest(python_executable, "test_results", run_identifier, "./test", filter_expression, simulate)
	if not report["success"]:
		raise RuntimeError("Test run failed")


def save_results(run_identifier, result_file_path, simulate):
	test_results = bhamon_development_toolkit.python.test.get_aggregated_results("test_results", run_identifier)

	if result_file_path:
		results = bhamon_development_toolkit.workspace.load_results(result_file_path)
		results["tests"] = results.get("tests", [])
		results["tests"].append(test_results)
		if not simulate:
			bhamon_development_toolkit.workspace.save_results(result_file_path, results)
