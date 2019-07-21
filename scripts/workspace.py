import json
import os


def load_results(result_file_path):
	results = {}

	if os.path.isfile(result_file_path):
		with open(result_file_path, "r") as result_file:
			results = json.load(result_file)

	results["artifacts"] = results.get("artifacts", [])
	results["distributions"] = results.get("distributions", [])

	return results


def save_results(result_file_path, result_data):
	if os.path.dirname(result_file_path):
		os.makedirs(os.path.dirname(result_file_path), exist_ok = True)
	with open(result_file_path, "w") as result_file:
		json.dump(result_data, result_file, indent = 4)
