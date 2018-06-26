import json
import logging
import os
import signal
import subprocess
import time


logger = logging.getLogger("Executor")

termination_timeout_seconds = 30

should_exit = False


def run(build_identifier, environment):
	signal.signal(signal.SIGINT, _handle_termination)
	signal.signal(signal.SIGBREAK, _handle_termination)
	signal.signal(signal.SIGTERM, _handle_termination)

	logger.info("Executing %s", build_identifier)
	build_directory = os.path.join("builds", build_identifier)
	with open(os.path.join(build_directory, "request.json")) as build_request_file:
		build_request = json.load(build_request_file)

	build_status = {
		"job_identifier": build_request["job_identifier"],
		"build_identifier": build_request["build_identifier"],
		"status": "running",
		"steps": [],
	}
	for step_index, step in enumerate(build_request["job"]["steps"]):
		build_status["steps"].append({
			"index": step_index,
			"name": step["name"],
			"command": step["command"],
			"status": "pending",
		})
	_save_status(build_directory, build_status)

	try:

		workspace = os.path.join("workspaces", build_request["job"]["workspace"])
		if not os.path.exists(workspace):
			os.makedirs(workspace)

		def update_step_status(step_index, status):
			build_status["steps"][step_index]["status"] = status
			_save_status(build_directory, build_status)

		build_final_status = "succeeded"
		is_skipping = False
		for step_index, step in enumerate(build_request["job"]["steps"]):
			step_status = _execute_step(build_directory, workspace, step_index, step, environment, build_request["parameters"], is_skipping, update_step_status)
			if not is_skipping and step_status in [ "failed", "aborted", "exception" ]:
				build_final_status = step_status
				is_skipping = True
		build_status["status"] = build_final_status
		_save_status(build_directory, build_status)

	except:
		logger.error("Failed to execute build", exc_info = True)
		build_status["status"] = "exception"
		_save_status(build_directory, build_status)

	logger.info("Build completed with status %s", build_status["status"])


def _execute_step(build_directory, workspace, step_index, step, environment, parameters, is_skipping, update_status_handler):
	logger.info("Step %s running", step["name"])
	step_status = "running"
	update_status_handler(step_index, step_status)

	log_file_name = "step_{index}_{name}.log".format(index = step_index, name = step["name"])

	try:
		if is_skipping:
			step_status = "skipped"
		else:
			step_command = [ argument.format(env = environment, parameters = parameters) for argument in step["command"] ]
			logger.info("Step command: %s", " ".join(step_command))
			with open(os.path.join(build_directory, log_file_name), "w") as log_file:
				child_process = subprocess.Popen(step_command, cwd = workspace, stdout = log_file, stderr = subprocess.STDOUT,
					creationflags = subprocess.CREATE_NEW_PROCESS_GROUP)
				step_status = _wait_process(child_process)

	except:
		logger.error("Failed to execute step", exc_info = True)
		step_status = "exception"

	update_status_handler(step_index, step_status)
	logger.info("Step %s completed with status %s", step["name"], step_status)
	return step_status


def _wait_process(child_process):
	result = None
	while result is None:
		if should_exit:
			logger.info("Terminating child process")
			os.kill(child_process.pid, signal.CTRL_BREAK_EVENT)
			try:
				result = child_process.wait(timeout = termination_timeout_seconds)
			except subprocess.TimeoutExpired:
				logger.warning("Terminating child process (force)")
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
