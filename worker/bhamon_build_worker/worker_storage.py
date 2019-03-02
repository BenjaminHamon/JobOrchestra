import json
import os
import shutil

import filelock


filelock_timeout_seconds = 5


def list_builds():
	if not os.path.isdir("builds"):
		return []

	all_builds = []
	for child_directory in os.listdir("builds"):
		build_directory = os.path.join("builds", child_directory)
		if os.path.isdir(build_directory):
			request_file_path = os.path.join(build_directory, "request.json")
			with open(request_file_path, "r") as request_file:
				build_request = json.load(request_file)
				all_builds.append((build_request["job_identifier"], build_request["build_identifier"]))
	return all_builds


def create_build(job_identifier, build_identifier):
	build_directory = os.path.join("builds", job_identifier + "_" + build_identifier)
	os.makedirs(build_directory)


def delete_build(job_identifier, build_identifier):
	build_directory = os.path.join("builds", job_identifier + "_" + build_identifier)
	shutil.rmtree(build_directory)


def load_request(job_identifier, build_identifier):
	request_file_path = get_file_path(job_identifier, build_identifier, "request.json")
	with filelock.FileLock(request_file_path + ".lock", filelock_timeout_seconds):
		return _load_data(request_file_path)


def save_request(job_identifier, build_identifier, build_request):
	request_file_path = get_file_path(job_identifier, build_identifier, "request.json")
	with filelock.FileLock(request_file_path + ".lock", filelock_timeout_seconds):
		_save_data(request_file_path, build_request)


def load_status(job_identifier, build_identifier):
	status_file_path = get_file_path(job_identifier, build_identifier, "status.json")
	with filelock.FileLock(status_file_path + ".lock", filelock_timeout_seconds):
		if not os.path.isfile(status_file_path):
			return { "job_identifier": job_identifier, "build_identifier": build_identifier, "status": "unknown" }
		return _load_data(status_file_path)


def save_status(job_identifier, build_identifier, status):
	status_file_path = get_file_path(job_identifier, build_identifier, "status.json")
	with filelock.FileLock(status_file_path + ".lock", filelock_timeout_seconds):
		_save_data(status_file_path, status)


def load_results(job_identifier, build_identifier):
	results_file_path = get_file_path(job_identifier, build_identifier, "results.json")
	with filelock.FileLock(results_file_path + ".lock", filelock_timeout_seconds):
		if not os.path.isfile(results_file_path):
			return {}
		return _load_data(results_file_path)


def save_results(job_identifier, build_identifier, results):
	results_file_path = get_file_path(job_identifier, build_identifier, "results.json")
	with filelock.FileLock(results_file_path + ".lock", filelock_timeout_seconds):
		_save_data(results_file_path, results)


def get_file_path(job_identifier, build_identifier, file_name):
	build_directory = os.path.join("builds", job_identifier + "_" + build_identifier)
	return os.path.join(build_directory, file_name)


def get_log_path(job_identifier, build_identifier, step_index, step_name):
	build_directory = os.path.join("builds", job_identifier + "_" + build_identifier)
	log_file_name = "step_{index}_{name}.log".format(index = step_index, name = step_name)
	return os.path.join(build_directory, log_file_name)


def load_log(job_identifier, build_identifier, step_index, step_name):
	log_fith_path = get_log_path(job_identifier, build_identifier, step_index, step_name)
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
