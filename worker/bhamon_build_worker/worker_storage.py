import json
import os
import shutil


def create_build(job_identifier, build_identifier):
	build_directory = os.path.join("builds", job_identifier + "_" + build_identifier)
	os.makedirs(build_directory)


def delete_build(job_identifier, build_identifier):
	build_directory = os.path.join("builds", job_identifier + "_" + build_identifier)
	shutil.rmtree(build_directory)


def load_request(job_identifier, build_identifier):
	build_directory = os.path.join("builds", job_identifier + "_" + build_identifier)
	request_file_path = os.path.join(build_directory, "request.json")
	with open(request_file_path, "r") as request_file:
		return json.load(request_file)


def save_request(job_identifier, build_identifier, build_request):
	build_directory = os.path.join("builds", job_identifier + "_" + build_identifier)
	request_file_path = os.path.join(build_directory, "request.json")
	with open(request_file_path + ".tmp", "w") as request_file:
		json.dump(build_request, request_file, indent = 4)
	if os.path.exists(request_file_path):
		os.remove(request_file_path)
	os.rename(request_file_path + ".tmp", request_file_path)


def load_status(job_identifier, build_identifier):
	build_directory = os.path.join("builds", job_identifier + "_" + build_identifier)
	status_file_path = os.path.join(build_directory, "status.json")
	if not os.path.isfile(status_file_path):
		return {}
	with open(status_file_path, "r") as status_file:
		return json.load(status_file)


def save_status(job_identifier, build_identifier, status):
	build_directory = os.path.join("builds", job_identifier + "_" + build_identifier)
	status_file_path = os.path.join(build_directory, "status.json")
	with open(status_file_path + ".tmp", "w") as status_file:
		json.dump(status, status_file, indent = 4)
	if os.path.exists(status_file_path):
		os.remove(status_file_path)
	os.rename(status_file_path + ".tmp", status_file_path)


def load_results(job_identifier, build_identifier):
	build_directory = os.path.join("builds", job_identifier + "_" + build_identifier)
	result_file_path = os.path.join(build_directory, "results.json")
	if not os.path.isfile(result_file_path):
		return {}
	with open(result_file_path, "r") as result_file:
		return json.load(result_file)


def save_results(job_identifier, build_identifier, source):
	build_directory = os.path.join("builds", job_identifier + "_" + build_identifier)
	result_file_path = os.path.join(build_directory, "results.json")
	shutil.copyfile(source, result_file_path + ".tmp")
	if os.path.isfile(result_file_path):
		os.remove(result_file_path)
	shutil.move(result_file_path + ".tmp", result_file_path)


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
