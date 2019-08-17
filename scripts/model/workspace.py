import json
import os
import shutil


def load_results(result_file_path):
	results = {}

	if os.path.isfile(result_file_path):
		with open(result_file_path, "r") as result_file:
			results = json.load(result_file)

	results["artifacts"] = results.get("artifacts", [])
	results["distributions"] = results.get("distributions", [])
	results["tests"] = results.get("tests", [])

	return results


def save_results(result_file_path, results):
	if os.path.dirname(result_file_path):
		os.makedirs(os.path.dirname(result_file_path), exist_ok = True)
	with open(result_file_path + ".tmp", "w") as result_file:
		json.dump(results, result_file, indent = 4)
	if os.path.isfile(result_file_path):
		os.remove(result_file_path)
	shutil.move(result_file_path + ".tmp", result_file_path)


def load_test_reports(result_file_path):
	results = []

	if os.path.isfile(result_file_path):
		with open(result_file_path, "r") as result_file:
			results = json.load(result_file)

	return results


def save_test_report(result_file_path, report):
	results = load_test_reports(result_file_path)
	results.append(report)

	if os.path.dirname(result_file_path):
		os.makedirs(os.path.dirname(result_file_path), exist_ok = True)
	with open(result_file_path + ".tmp", "w") as result_file:
		json.dump(results, result_file, indent = 4)
	if os.path.isfile(result_file_path):
		os.remove(result_file_path)
	shutil.move(result_file_path + ".tmp", result_file_path)
