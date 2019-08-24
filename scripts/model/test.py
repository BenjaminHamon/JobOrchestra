import datetime
import json
import logging
import os
import subprocess

import scripts.model.workspace


logger = logging.getLogger("Test")

pytest_status_collection = [ "error", "failed", "passed", "skipped", "xfailed", "xpassed" ]


def run_pytest(python_executable, output_directory, run_identifier, target, filter_expression, simulate): # pylint: disable = too-many-locals
	intermediate_report_file_path = os.path.join(output_directory, str(run_identifier) + "_intermediate.json")

	pytest_command = [ python_executable, "-m", "pytest", target, "--verbose" ]
	pytest_command += [ "--collect-only" ] if simulate else []
	pytest_command += [ "--basetemp", os.path.join(output_directory, str(run_identifier)) ]
	pytest_command += [ "-k", filter_expression ] if filter_expression else []
	report_options = [ "--json", intermediate_report_file_path ]

	start_date = datetime.datetime.utcnow().replace(microsecond = 0).isoformat() + "Z"

	logger.info("+ %s", " ".join(pytest_command))

	if simulate:
		result_code = subprocess.call(pytest_command)
	else:
		os.makedirs(output_directory, exist_ok = True)
		result_code = subprocess.call(pytest_command + report_options)

	success = result_code == 0
	completion_date = datetime.datetime.utcnow().replace(microsecond = 0).isoformat() + "Z"

	if simulate:
		intermediate_report = _simulate_intermediate_report()
	else:
		with open(intermediate_report_file_path, "r") as intermediate_report_file:
			intermediate_report = json.load(intermediate_report_file)["report"]

	job_parameters = { "target": target, "filter_expression": filter_expression }
	report = _generate_report(run_identifier, job_parameters, intermediate_report, success, start_date, completion_date)

	result_file_path = os.path.join(output_directory, str(run_identifier) + ".json")
	if not simulate:
		scripts.model.workspace.save_test_report(result_file_path, report)

	if not simulate:
		os.remove(intermediate_report_file_path)

	return report


def get_aggregated_results(output_directory, run_identifier):
	result_file_path = os.path.join(output_directory, str(run_identifier) + ".json")
	all_reports = scripts.model.workspace.load_test_reports(result_file_path)

	success = True
	summary = { "total": 0 }
	summary.update({ status: 0 for status in pytest_status_collection })

	for report in all_reports:
		if report["job"] == "pytest":
			success = success and report["success"]
			summary["total"] += report["summary"]["total"]
			for status in pytest_status_collection:
				summary[status] += report["summary"][status]

	return {
		"run_identifier": str(run_identifier),
		"run_type": "pytest",
		"success": success,
		"summary": summary,
	}


def _simulate_intermediate_report():
	return {
		"tests": [],
		"summary": {
			"num_tests": 0,
		},
	}


def _generate_report(run_identifier, job_parameters, intermediate_report, success, start_date, completion_date):
	summary = { "total": intermediate_report["summary"]["num_tests"] }
	for status in pytest_status_collection:
		summary[status] = intermediate_report["summary"].get(status, 0)

	all_tests = []
	for test in intermediate_report["tests"]:
		all_tests.append({
			"name": test["name"],
			"status": test["outcome"],
			"duration": test["duration"],
		})

	return {
		"run_identifier": str(run_identifier),
		"job": "pytest",
		"job_parameters": job_parameters,
		"success": success,
		"summary": summary,
		"results": all_tests,
		"start_date": start_date,
		"completion_date": completion_date,
	}
