import json
import logging
import os
import shutil
import signal
import subprocess
import time


logger = logging.getLogger("Executor")

termination_timeout_seconds = 30

should_exit = False


def run(job_identifier, build_identifier, environment):
	signal.signal(signal.SIGINT, _handle_termination)
	signal.signal(signal.SIGBREAK, _handle_termination)
	signal.signal(signal.SIGTERM, _handle_termination)

	logger.info("(%s) Executing %s", build_identifier, job_identifier)
	executor_build_directory = os.path.join("builds", job_identifier + "_" + build_identifier)
	with open(os.path.join(executor_build_directory, "request.json")) as build_request_file:
		build_request = json.load(build_request_file)

	build_status = {
		"job_identifier": build_request["job_identifier"],
		"build_identifier": build_request["build_identifier"],
		"status": "pending",
		"steps": [
			{
				"index": step_index,
				"name": step["name"],
				"command": step["command"],
				"status": "pending",
			}
			for step_index, step in enumerate(build_request["job"]["steps"])
		],
	}

	logger.info("(%s) Build is starting", build_identifier)

	try:
		
		build_status["status"] = "running"
		_save_status(executor_build_directory, build_status)

		workspace = os.path.join("workspaces", build_request["job"]["workspace"])
		if not os.path.exists(workspace):
			os.makedirs(workspace)

		def update_step_status(step_index, status):
			build_status["steps"][step_index]["status"] = status
			_save_status(executor_build_directory, build_status)

		build_final_status = "succeeded"
		is_skipping = False
		for step_index, step in enumerate(build_request["job"]["steps"]):
			step_status = _execute_step(workspace, step_index, step, job_identifier, build_identifier,
					environment, build_request["parameters"], is_skipping, update_step_status)
			if not is_skipping and step_status in [ "failed", "aborted", "exception" ]:
				build_final_status = step_status
				is_skipping = True
		build_status["status"] = build_final_status
		_save_status(executor_build_directory, build_status)

	except:
		logger.error("(%s) Build raised an exception", build_identifier, exc_info = True)
		build_status["status"] = "exception"
		_save_status(executor_build_directory, build_status)

	logger.info("(%s) Build completed with status %s", build_identifier, build_status["status"])


def _execute_step(workspace, step_index, step, job_identifier, build_identifier, environment, parameters, is_skipping, update_status_handler):
	logger.info("(%s) Step %s is starting", build_identifier, step["name"])
	step_status = "running"
	update_status_handler(step_index, step_status)

	log_file_name = "step_{index}_{name}.log".format(index = step_index, name = step["name"])
	executor_build_directory = os.path.join("builds", job_identifier + "_" + build_identifier)
	workspace_result_file_path = os.path.join(".build_results", job_identifier + "_" + build_identifier, "results.json")

	try:
		if is_skipping:
			step_status = "skipped"
		else:
			step_parameters = {
				"result_file_path": workspace_result_file_path,
				"environment": environment,
				"parameters": parameters,
			}
			step_command = [ argument.format(**step_parameters) for argument in step["command"] ]
			logger.info("(%s) + %s", build_identifier, " ".join(step_command))
			with open(os.path.join(executor_build_directory, log_file_name), "w") as log_file:
				child_process = subprocess.Popen(step_command, cwd = workspace, stdout = log_file, stderr = subprocess.STDOUT,
						creationflags = subprocess.CREATE_NEW_PROCESS_GROUP)
				step_status = _wait_process(build_identifier, child_process)

	except:
		logger.error("(%s) Step %s raised an exception", build_identifier, step["name"], exc_info = True)
		step_status = "exception"

	build_result_file_path = os.path.join(executor_build_directory, "results.json")
	if os.path.isfile(os.path.join(workspace, workspace_result_file_path)):
		shutil.copyfile(os.path.join(workspace, workspace_result_file_path), build_result_file_path + ".tmp")
		if os.path.isfile(build_result_file_path):
			os.remove(build_result_file_path)
		shutil.move(build_result_file_path + ".tmp", build_result_file_path)

	update_status_handler(step_index, step_status)
	logger.info("(%s) Step %s completed with status %s", build_identifier, step["name"], step_status)
	return step_status


def _wait_process(build_identifier, child_process):
	result = None
	while result is None:
		if should_exit:
			logger.info("(%s) Terminating child process", build_identifier)
			os.kill(child_process.pid, signal.CTRL_BREAK_EVENT)
			try:
				result = child_process.wait(timeout = termination_timeout_seconds)
			except subprocess.TimeoutExpired:
				logger.warning("(%s) Terminating child process (force)", build_identifier)
				child_process.kill()
			return "aborted"
		time.sleep(1)
		result = child_process.poll()
	return "succeeded" if result == 0 else "failed"


def _save_status(build_directory, build_status):
	status_file_path = os.path.join(build_directory, "status.json")
	with open(status_file_path + ".tmp", "w") as status_file:
		json.dump(build_status, status_file, indent = 4)
	if os.path.exists(status_file_path):
		os.remove(status_file_path)
	os.rename(status_file_path + ".tmp", status_file_path)


def _handle_termination(signal_number, frame):
	global should_exit
	should_exit = True
