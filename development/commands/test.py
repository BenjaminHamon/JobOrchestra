import logging
import os
import uuid

import bhamon_development_toolkit.python.test as python_test
from bhamon_development_toolkit import workspace


logger = logging.getLogger("Main")


def configure_argument_parser(environment, configuration, subparsers): # pylint: disable = unused-argument
	parser = subparsers.add_parser("test", help = "run the test suite")
	parser.add_argument("--identifier", default = str(uuid.uuid4()), metavar = "<identifier>", help = "specify a identifier for the run (default to a GUID)")
	parser.add_argument("--filter", metavar = "<expression>", help = "specify a string expression to select tests to run")
	parser.add_argument("--filter-directory", default = ".", metavar = "<path>", help = "specify a directory to select tests to run")
	parser.set_defaults(func = run)


def run(environment, configuration, arguments): # pylint: disable = unused-argument
	python_executable = environment["python3_executable"]
	result_directory = os.path.join(configuration["artifact_directory"], "test_results")
	test_directory = os.path.normpath(os.path.join("test", arguments.filter_directory))

	report = python_test.run_pytest(python_executable, result_directory, arguments.identifier, test_directory, arguments.filter, simulate = arguments.simulate)

	if arguments.results:
		save_results(arguments.results, report, simulate = arguments.simulate)

	if not report["success"]:
		raise RuntimeError("Test run failed")


def save_results(result_file_path, report, simulate):
	report_as_results = {
		"run_identifier": report["run_identifier"],
		"run_type": "pytest",
		"success": report["success"],
		"summary": report["summary"],
	}

	results = workspace.load_results(result_file_path)
	results["tests"] = results.get("tests", [])
	results["tests"].append(report_as_results)

	if not simulate:
		workspace.save_results(result_file_path, results)
