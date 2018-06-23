import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
import time

import websockets


logger = logging.getLogger("Worker")

connection_attempt_delay_collection = [ 10, 10, 10, 10, 10, 60, 60, 60, 300, 3600 ]


def run(master_address, worker_identifier, executor_script):
	worker_data = {
		"identifier": worker_identifier,
		"executor_script": executor_script,
		"active_executors": {}
	}

	async def run_client():
		is_running = True
		connection_attempt_index = 0

		while is_running:
			try:
				connection_attempt_index += 1
				logger.info("Connecting to master on %s (Attempt: %s)", master_address, connection_attempt_index)
				async with websockets.connect("ws://" + master_address) as connection:
					logger.info("Connected to master, waiting for commands")
					connection_attempt_index = 0
					while True:
						await _process_message(connection, worker_data)
				logger.info("Closed connection to master")
				is_running = False

			except (OSError, websockets.exceptions.ConnectionClosed):
				try:
					connection_attempt_delay = connection_attempt_delay_collection[connection_attempt_index]
				except IndexError:
					connection_attempt_delay = connection_attempt_delay_collection[-1]
				logger.error("Connection to master failed, retrying in %s seconds", connection_attempt_delay, exc_info = True)
				time.sleep(connection_attempt_delay)

	logger.info("Starting build worker")
	asyncio.get_event_loop().run_until_complete(run_client())
	logger.info("Exiting build worker")


async def _process_message(connection, worker_data):
	request = json.loads(await connection.recv())
	logger.debug("< %s", request)

	try:
		result = _execute_command(worker_data, request["command"], request["parameters"])
		response = { "result": result }
	except Exception as exception:
		logger.error("Failed to process request %s", request, exc_info = True)
		response = { "error": str(exception) }
	logger.debug("> %s", response)
	await connection.send(json.dumps(response))


def _execute_command(worker_data, command, parameters):
	if command == "authenticate":
		return _authenticate(worker_data)
	elif command == "execute":
		return _execute(worker_data, **parameters)
	elif command == "abort":
		return _abort(worker_data, **parameters)
	elif command == "status":
		return _get_status(**parameters)
	elif command == "log":
		return _retrieve_log(**parameters)
	else:
		raise ValueError("Unknown command " + command)


def _authenticate(worker_data):
	return { "identifier": worker_data["identifier"] }


def _execute(worker_data, job_identifier, build_identifier, job, parameters):
	logger.info("Executing %s %s", job_identifier, build_identifier)
	build_directory = os.path.join("builds", job_identifier + "_" + build_identifier)
	os.makedirs(build_directory)
	build_request = { "job_identifier": job_identifier, "build_identifier": build_identifier, "job": job, "parameters": parameters }
	with open(os.path.join(build_directory, "request.json"), "w") as request_file:
		json.dump(build_request, request_file, indent = 4)
	executor_command = [ sys.executable, worker_data["executor_script"], job_identifier + "_" + build_identifier ]
	executor_process = subprocess.Popen(executor_command, creationflags = subprocess.CREATE_NEW_PROCESS_GROUP)
	worker_data["active_executors"][build_identifier] = executor_process


def _abort(worker_data, job_identifier, build_identifier):
	logger.info("Aborting %s %s", job_identifier, build_identifier)
	executor_process = worker_data["active_executors"][build_identifier]
	os.kill(executor_process.pid, signal.CTRL_BREAK_EVENT)


def _get_status(job_identifier, build_identifier):
	build_directory = os.path.join("builds", job_identifier + "_" + build_identifier)
	status_file_path = os.path.join(build_directory, "status.json")
	with open(status_file_path) as status_file:
		return json.load(status_file)


def _retrieve_log(job_identifier, build_identifier, step_index, step_name):
	build_directory = os.path.join("builds", job_identifier + "_" + build_identifier)
	log_file_name = "step_{index}_{name}.log".format(index = step_index, name = step_name)
	log_fith_path = os.path.join(build_directory, log_file_name)
	if not os.path.isfile(log_fith_path):
		return ""
	with open(log_fith_path) as log_file:
		return log_file.read()
