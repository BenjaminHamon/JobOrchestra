import datetime
import json
import logging
import os
import platform
import signal
import subprocess
import time
import traceback

import bhamon_orchestra_worker.worker_storage as worker_storage


logger = logging.getLogger("Executor")

shutdown_signal = signal.CTRL_BREAK_EVENT if platform.system() == "Windows" else signal.SIGINT # pylint: disable = no-member
subprocess_flags = subprocess.CREATE_NEW_PROCESS_GROUP if platform.system() == "Windows" else 0

termination_timeout_seconds = 30


def run(job_identifier, run_identifier, environment):
	executor_data = {
		"should_shutdown": False,
	}

	if platform.system() == "Windows":
		signal.signal(signal.SIGBREAK, lambda signal_number, frame: _shutdown(executor_data)) # pylint: disable = no-member
	signal.signal(signal.SIGINT, lambda signal_number, frame: _shutdown(executor_data))
	signal.signal(signal.SIGTERM, lambda signal_number, frame: _shutdown(executor_data))

	logger.info("(%s) Executing %s", run_identifier, job_identifier)
	run_request = worker_storage.load_request(job_identifier, run_identifier)

	run_status = {
		"job_identifier": run_request["job_identifier"],
		"run_identifier": run_request["run_identifier"],
		"workspace": os.path.join("workspaces", run_request["job"]["workspace"]),
		"environment": environment,
		"parameters": run_request["parameters"],
		"status": "running",
		"steps": [
			{
				"index": step_index,
				"name": step["name"],
				"command": step["command"],
				"status": "pending",
			}
			for step_index, step in enumerate(run_request["job"]["steps"])
		],

		"start_date": datetime.datetime.utcnow().replace(microsecond = 0).isoformat() + "Z",
		"completion_date": None,
	}

	logger.info("(%s) Run is starting", run_identifier)

	try:
		worker_storage.save_status(job_identifier, run_identifier, run_status)

		if not os.path.exists(run_status["workspace"]):
			os.makedirs(run_status["workspace"])

		# Prevent executor pyvenv from overriding a python executable specified in a command
		if "__PYVENV_LAUNCHER__" in os.environ:
			del os.environ["__PYVENV_LAUNCHER__"]

		run_final_status = "succeeded"
		is_skipping = False

		for step_index, step in enumerate(run_status["steps"]):
			if not is_skipping and executor_data["should_shutdown"]:
				run_final_status = "aborted"
				is_skipping = True
			_execute_step(executor_data, job_identifier, run_identifier, run_status, step_index, step, is_skipping)
			if not is_skipping and step["status"] != "succeeded":
				run_final_status = step["status"]
				is_skipping = True

		run_status["status"] = run_final_status
		run_status["completion_date"] = datetime.datetime.utcnow().replace(microsecond = 0).isoformat() + "Z"
		worker_storage.save_status(job_identifier, run_identifier, run_status)

	except: # pylint: disable = bare-except
		logger.error("(%s) Run raised an exception", run_identifier, exc_info = True)
		run_status["status"] = "exception"
		run_status["completion_date"] = datetime.datetime.utcnow().replace(microsecond = 0).isoformat() + "Z"
		worker_storage.save_status(job_identifier, run_identifier, run_status)

	logger.info("(%s) Run completed with status %s", run_identifier, run_status["status"])


def _execute_step( # pylint: disable = too-many-arguments
		executor_data, job_identifier, run_identifier, run_status, step_index, step, is_skipping):
	logger.info("(%s) Step %s is starting", run_identifier, step["name"])

	try:
		step["status"] = "running"
		worker_storage.save_status(job_identifier, run_identifier, run_status)

		log_file_path = worker_storage.get_log_path(job_identifier, run_identifier, step_index, step["name"])
		result_file_path = os.path.join(run_status["workspace"], "run_results", run_identifier, "results.json")

		if is_skipping:
			step["status"] = "skipped"

		else:
			step_command = _format_command(step["command"], run_status, result_file_path, log_file_path)
			logger.info("(%s) + %s", run_identifier, " ".join(step_command))
			step["status"] = _execute_command(executor_data, run_identifier, step_command, run_status["workspace"], log_file_path)

			if os.path.isfile(result_file_path):
				with open(result_file_path, "r") as result_file:
					results = json.load(result_file)
				worker_storage.save_results(job_identifier, run_identifier, results)

		worker_storage.save_status(job_identifier, run_identifier, run_status)

	except: # pylint: disable = bare-except
		logger.error("(%s) Step %s raised an exception", run_identifier, step["name"], exc_info = True)
		step["status"] = "exception"
		worker_storage.save_status(job_identifier, run_identifier, run_status)

	logger.info("(%s) Step %s completed with status %s", run_identifier, step["name"], step["status"])


def _format_command(command, run_status, result_file_path, log_file_path):
	results = {}
	if os.path.isfile(result_file_path):
		with open(result_file_path, "r") as result_file:
			results = json.load(result_file)

	format_parameters = {
		"environment": run_status["environment"],
		"parameters": run_status["parameters"],
		"results": results,
		"result_file_path": os.path.relpath(result_file_path, run_status["workspace"]),
	}

	try:
		return [ argument.format(**format_parameters) for argument in command ]
	except KeyError:
		with open(log_file_path, "w") as log_file:
			log_file.write("# Workspace: %s\n" % os.path.abspath(run_status["workspace"]))
			log_file.write("# Command: %s\n" % " ".join(command))
			log_file.write("\n")
			log_file.write("Exception while formatting the step command\n")
			log_file.write("\n")
			log_file.write(traceback.format_exc())
		raise


def _execute_command(executor_data, run_identifier, command, workspace, log_file_path):
	with open(log_file_path, "w") as log_file:
		log_file.write("# Workspace: %s\n" % os.path.abspath(workspace))
		log_file.write("# Command: %s\n" % " ".join(command))
		log_file.write("\n")
		log_file.flush()

		executor_directory = os.getcwd()
		os.chdir(workspace)

		try:
			child_process = subprocess.Popen(command, stdout = log_file, stderr = subprocess.STDOUT, creationflags = subprocess_flags)
		finally:
			os.chdir(executor_directory)

		return _wait_process(executor_data, run_identifier, child_process)


def _wait_process(executor_data, run_identifier, child_process):
	result = None
	while result is None:
		if executor_data["should_shutdown"]:
			logger.info("(%s) Terminating child process", run_identifier)
			os.kill(child_process.pid, shutdown_signal)
			try:
				result = child_process.wait(timeout = termination_timeout_seconds)
			except subprocess.TimeoutExpired:
				logger.warning("(%s) Terminating child process (force)", run_identifier)
				child_process.kill()
			return "aborted"
		time.sleep(1)
		result = child_process.poll()
	return "succeeded" if result == 0 else "failed"


def _shutdown(executor_data):
	executor_data["should_shutdown"] = True
