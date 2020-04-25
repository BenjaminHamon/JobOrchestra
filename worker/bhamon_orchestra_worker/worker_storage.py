import json
import os
import shutil

import filelock


filelock_timeout_seconds = 5


def list_runs():
	if not os.path.isdir("runs"):
		return []

	all_runs = []
	for child_directory in os.listdir("runs"):
		run_directory = os.path.join("runs", child_directory)
		if os.path.isdir(run_directory):
			request_file_path = os.path.join(run_directory, "request.json")
			with open(request_file_path, "r") as request_file:
				run_request = json.load(request_file)
				all_runs.append(run_request["run_identifier"])
	return all_runs


def create_run(run_identifier):
	run_directory = os.path.join("runs", run_identifier)
	os.makedirs(run_directory)


def delete_run(run_identifier):
	run_directory = os.path.join("runs", run_identifier)
	shutil.rmtree(run_directory)


def load_request(run_identifier):
	request_file_path = get_file_path(run_identifier, "request.json")
	with filelock.FileLock(request_file_path + ".lock", filelock_timeout_seconds):
		return _load_data(request_file_path)


def save_request(run_identifier, run_request):
	request_file_path = get_file_path(run_identifier, "request.json")
	with filelock.FileLock(request_file_path + ".lock", filelock_timeout_seconds):
		_save_data(request_file_path, run_request)


def get_status_timestamp(run_identifier):
	status_file_path = get_file_path(run_identifier, "status.json")
	with filelock.FileLock(status_file_path + ".lock", filelock_timeout_seconds):
		if not os.path.isfile(status_file_path):
			return None
		return os.path.getmtime(status_file_path)


def load_status(run_identifier):
	status_file_path = get_file_path(run_identifier, "status.json")
	with filelock.FileLock(status_file_path + ".lock", filelock_timeout_seconds):
		if not os.path.isfile(status_file_path):
			return { "run_identifier": run_identifier, "status": "unknown" }
		return _load_data(status_file_path)


def save_status(run_identifier, status):
	status_file_path = get_file_path(run_identifier, "status.json")
	with filelock.FileLock(status_file_path + ".lock", filelock_timeout_seconds):
		_save_data(status_file_path, status)


def get_results_timestamp(run_identifier):
	result_file_path = get_file_path(run_identifier, "results.json")
	with filelock.FileLock(result_file_path + ".lock", filelock_timeout_seconds):
		if not os.path.isfile(result_file_path):
			return None
		return os.path.getmtime(result_file_path)



def load_results(run_identifier):
	result_file_path = get_file_path(run_identifier, "results.json")
	with filelock.FileLock(result_file_path + ".lock", filelock_timeout_seconds):
		if not os.path.isfile(result_file_path):
			return {}
		return _load_data(result_file_path)


def save_results(run_identifier, results):
	result_file_path = get_file_path(run_identifier, "results.json")
	with filelock.FileLock(result_file_path + ".lock", filelock_timeout_seconds):
		_save_data(result_file_path, results)


def get_file_path(run_identifier, file_name):
	run_directory = os.path.join("runs", run_identifier)
	return os.path.join(run_directory, file_name)


def get_log_path(run_identifier, step_index, step_name):
	run_directory = os.path.join("runs", run_identifier)
	log_file_name = "step_{index}_{name}.log".format(index = step_index, name = step_name)
	return os.path.join(run_directory, log_file_name)


def load_log(run_identifier, step_index, step_name):
	log_fith_path = get_log_path(run_identifier, step_index, step_name)
	if not os.path.isfile(log_fith_path):
		return ""
	with open(log_fith_path) as log_file:
		return log_file.read()


def _load_data(file_path):
	with open(file_path, "r") as data_file:
		return json.load(data_file)


def _save_data(file_path, data):
	with open(file_path + ".tmp", "w") as data_file:
		json.dump(data, data_file, indent = 4)
	if os.path.isfile(file_path):
		os.remove(file_path)
	shutil.move(file_path + ".tmp", file_path)
