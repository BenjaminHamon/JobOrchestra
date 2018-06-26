import asyncio
import datetime
import json
import logging
import os
import shutil
import signal
import subprocess
import sys

import websockets


logger = logging.getLogger("Worker")

connection_attempt_delay_collection = [ 10, 10, 10, 10, 10, 60, 60, 60, 300, 3600 ]
termination_delay_seconds = 5
termination_timeout_seconds = 30


def run(master_address, worker_identifier, executor_script):
	worker_data = {
		"identifier": worker_identifier,
		"executor_script": executor_script,
		"active_executors": {},
		"should_exit": False,
	}

	signal.signal(signal.SIGBREAK, lambda signal_number, frame: _shutdown(worker_data))
	signal.signal(signal.SIGINT, lambda signal_number, frame: _shutdown(worker_data))
	signal.signal(signal.SIGTERM, lambda signal_number, frame: _shutdown(worker_data))

	logger.info("Starting build worker")
	coroutine_set = asyncio.wait([ _run_client(master_address, worker_data), _handle_termination(worker_data) ])
	asyncio.get_event_loop().run_until_complete(coroutine_set)
	logger.info("Exiting build worker")


async def _run_client(master_address, worker_data):
	connection_attempt_counter = 0

	while not worker_data["should_exit"]:
		try:
			connection_attempt_counter += 1
			logger.info("Connecting to master on %s (Attempt: %s)", master_address, connection_attempt_counter)
			try:
				async with websockets.connect("ws://" + master_address) as connection:
					logger.info("Connected to master, waiting for commands")
					connection_attempt_counter = 0
					await _process_connection(connection, worker_data)
			except websockets.exceptions.ConnectionClosed as exception:
				if exception.code not in [ 1000, 1001 ]:
					raise
				worker_data["should_exit"] = True
			logger.info("Closed connection to master")

		except (OSError, websockets.exceptions.ConnectionClosed):
			try:
				connection_attempt_delay = connection_attempt_delay_collection[connection_attempt_counter]
			except IndexError:
				connection_attempt_delay = connection_attempt_delay_collection[-1]
			logger.error("Connection to master failed, retrying in %s seconds", connection_attempt_delay, exc_info = True)
			await asyncio.sleep(connection_attempt_delay)


async def _process_connection(connection, worker_data):
	# When terminating, the connection is kept opened until all the builds are aborted and cleaned
	while not worker_data["should_exit"] or len(worker_data["active_executors"]) > 0:
		try:
			# Timeout to ensure the loop condition is checked once in a while
			request = json.loads(await asyncio.wait_for(connection.recv(), timeout = 10))
		except asyncio.TimeoutError:
			await asyncio.wait_for(await connection.ping(), timeout = 10)
			continue
		logger.debug("< %s", request)

		try:
			result = _execute_command(worker_data, request["command"], request["parameters"])
			response = { "result": result }
		except Exception as exception:
			logger.error("Failed to process request %s", request, exc_info = True)
			response = { "error": str(exception) }

		logger.debug("> %s", response)
		await connection.send(json.dumps(response))


async def _handle_termination(worker_data):
	while not worker_data["should_exit"]:
		await asyncio.sleep(termination_delay_seconds)

	logger.info("Terminating build worker")
	termination_start_time = datetime.datetime.utcnow()
	for build_identifier in worker_data["active_executors"]:
		_abort(worker_data, build_identifier)
	while (len(worker_data["active_executors"]) > 0) and ((datetime.datetime.utcnow() - termination_start_time).total_seconds() < termination_timeout_seconds):
		await asyncio.sleep(termination_delay_seconds)
	for build_identifier, executor_process in worker_data["active_executors"].items():
		logger.warning("Executor is still running (Build: %s, Process: %s)", build_identifier, executor_process.pid)
	# Force the connection to close by discarding remaining executors
	worker_data["active_executors"].clear()


def _execute_command(worker_data, command, parameters):
	if command == "authenticate":
		return _authenticate(worker_data)
	elif command == "execute":
		return _execute(worker_data, **parameters)
	elif command == "clean":
		return _clean(worker_data, **parameters)
	elif command == "abort":
		return _abort(worker_data, **parameters)
	elif command == "status":
		return _get_status(**parameters)
	elif command == "log":
		return _retrieve_log(**parameters)
	elif command == "shutdown":
		return _shutdown(worker_data)
	else:
		raise ValueError("Unknown command %s" % command)


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


def _clean(worker_data, job_identifier, build_identifier):
	logger.info("Cleaning %s %s", job_identifier, build_identifier)

	if build_identifier in worker_data["active_executors"]:
		executor_process = worker_data["active_executors"][build_identifier]
		if executor_process.poll() is None:
			raise RuntimeError("Executor is still running for build %s" % build_identifier)
		del worker_data["active_executors"][build_identifier]

	build_directory = os.path.join("builds", job_identifier + "_" + build_identifier)
	shutil.rmtree(build_directory)


def _abort(worker_data, build_identifier):
	logger.info("Aborting %s", build_identifier)
	executor_process = worker_data["active_executors"][build_identifier]
	os.kill(executor_process.pid, signal.CTRL_BREAK_EVENT)
	# The executor should terminate nicely, if it does not it will stays as running and should be investigated
	# Forcing termination here would leave orphan processes and the status as running


def _shutdown(worker_data):
	worker_data["should_exit"] = True


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
