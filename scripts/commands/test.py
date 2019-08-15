import json
import logging
import os
import subprocess
import uuid

import scripts.workspace as workspace


logger = logging.getLogger("Main")


def configure_argument_parser(environment, configuration, subparsers): # pylint: disable = unused-argument
	parser = subparsers.add_parser("test", help = "run the test suite")
	parser.add_argument("--filter", help = "specify a string expression to select tests to run")
	return parser


def run(environment, configuration, arguments): # pylint: disable = unused-argument
	run_identifier = uuid.uuid4()

	try:
		test(environment["python3_executable"], run_identifier, arguments.filter, arguments.simulate)
	finally:
		save_results(run_identifier, arguments.results, arguments.simulate)


def test(python_executable, run_identifier, filter_expression, simulate):
	logger.info("Running test suite (RunIdentifier: %s)", run_identifier)

	os.makedirs("test_results", exist_ok = True)

	pytest_command = [ python_executable, "-m", "pytest", "test", "--verbose" ]
	pytest_command += [ "--collect-only" ] if simulate else []
	pytest_command += [ "--basetemp", os.path.join("test_results", str(run_identifier)) ]
	pytest_command += [ "--json", os.path.join("test_results", str(run_identifier) + ".json") ]
	pytest_command += [ "-k", filter_expression ] if filter_expression else []

	logger.info("+ %s", " ".join(pytest_command))
	subprocess.check_call(pytest_command)


def save_results(run_identifier, result_file_path, simulate):
	report_path = os.path.join("test_results", str(run_identifier) + ".json")
	with open(report_path) as report_file:
		report = json.load(report_file)

	test_results = {
		"run_identifier": str(run_identifier),
		"total": report["report"]["summary"].get("num_tests", 0),
		"total_succeeded": report["report"]["summary"].get("passed", 0),
		"total_failed": report["report"]["summary"].get("failed", 0),
		"total_skipped": report["report"]["summary"].get("skipped", 0),
	}

	if result_file_path:
		results = workspace.load_results(result_file_path)
		results["tests"].append(test_results)
		if not simulate:
			workspace.save_results(result_file_path, results)
