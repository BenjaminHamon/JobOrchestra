import json
import os


def load_results(result_file_path: str) -> dict:
	if not os.path.isfile(result_file_path):
		return {}
	with open(result_file_path, mode = "r", encoding = "utf-8") as result_file:
		return json.load(result_file)


def save_results(result_file_path: str, results: dict) -> None:
	os.makedirs(os.path.dirname(result_file_path), exist_ok = True)
	with open(result_file_path + ".tmp", mode = "w", encoding = "utf-8") as result_file:
		json.dump(results, result_file, indent = 4)
	if os.path.isfile(result_file_path):
		os.remove(result_file_path)
	os.replace(result_file_path + ".tmp", result_file_path)
