import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
import time

import websockets

import bhamon_build_worker.worker_storage as worker_storage


logger = logging.getLogger("Worker")

connection_attempt_delay_collection = [ 10, 10, 10, 10, 10, 60, 60, 60, 300, 3600 ]
termination_timeout_seconds = 30


def run(master_address, worker_identifier, executor_script):
	worker_data = {
		"identifier": worker_identifier,
		"executor_script": executor_script,
		"active_executors": [],
		"should_shutdown": False,
	}

	signal.signal(signal.SIGBREAK, lambda signal_number, frame: _shutdown(worker_data))
	signal.signal(signal.SIGINT, lambda signal_number, frame: _shutdown(worker_data))
	signal.signal(signal.SIGTERM, lambda signal_number, frame: _shutdown(worker_data))

	logger.info("Starting build worker")
	main_future = asyncio.gather(_run_client(master_address, worker_data), _handle_shutdown(worker_data))
	asyncio.get_event_loop().run_until_complete(main_future)
	logger.info("Exiting build worker")


async def _run_client(master_address, worker_data):
	connection_attempt_counter = 0

	while not worker_data["should_shutdown"]:
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
			logger.info("Closed connection to master")

		except OSError:
			logger.error("Failed to connect to master", exc_info = True)
		except websockets.exceptions.ConnectionClosed:
			logger.error("Lost connection to master", exc_info = True)

		if not worker_data["should_shutdown"]:
			try:
				connection_attempt_delay = connection_attempt_delay_collection[connection_attempt_counter]
			except IndexError:
				connection_attempt_delay = connection_attempt_delay_collection[-1]
			logger.info("Retrying connection in %s seconds", connection_attempt_delay)
			await asyncio.sleep(connection_attempt_delay)


async def _process_connection(connection, worker_data):
	# When terminating, the connection is kept opened until all the builds are aborted and cleaned
	while not worker_data["should_shutdown"] or len(worker_data["active_executors"]) > 0:
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


async def _handle_shutdown(worker_data):
	while not worker_data["should_shutdown"]:
		await asyncio.sleep(1)

	logger.info("Terminating build worker")
	termination_start_time = time.time()
	for executor in worker_data["active_executors"]:
		_abort(worker_data, executor["job_identifier"], executor["build_identifier"])
	while (len(worker_data["active_executors"]) > 0) and (time.time() - termination_start_time < termination_timeout_seconds):
		await asyncio.sleep(1)
	for executor in worker_data["active_executors"]:
		logger.warning("Build %s was not cleaned", executor["build_identifier"])
		if executor["process"].poll() is None:
			logger.warning("Build %s executor is still running (Process: %s)", executor["build_identifier"], executor["process"].pid)
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
		return _check_status(worker_data, **parameters)
	elif command == "log":
		return _retrieve_log(**parameters)
	elif command == "results":
		return _retrieve_results(**parameters)
	elif command == "shutdown":
		return _request_shutdown(worker_data)
	else:
		raise ValueError("Unknown command %s" % command)


def _authenticate(worker_data):
	return { "identifier": worker_data["identifier"] }


def _execute(worker_data, job_identifier, build_identifier, job, parameters):
	logger.info("Executing %s %s", job_identifier, build_identifier)
	build_request = { "job_identifier": job_identifier, "build_identifier": build_identifier, "job": job, "parameters": parameters }
	worker_storage.create_build(job_identifier, build_identifier)
	worker_storage.save_request(job_identifier, build_identifier, build_request)
	executor_command = [ sys.executable, worker_data["executor_script"], job_identifier, build_identifier ]
	executor_process = subprocess.Popen(executor_command, creationflags = subprocess.CREATE_NEW_PROCESS_GROUP)
	executor = { "job_identifier": job_identifier, "build_identifier": build_identifier, "process": executor_process }
	worker_data["active_executors"].append(executor)


def _clean(worker_data, job_identifier, build_identifier):
	logger.info("Cleaning %s %s", job_identifier, build_identifier)
	executor = _find_executor(worker_data, build_identifier)
	if executor["process"].poll() is None:
		raise RuntimeError("Executor is still running for build %s" % build_identifier)
	worker_data["active_executors"].remove(executor)
	worker_storage.delete_build(job_identifier, build_identifier)


def _abort(worker_data, job_identifier, build_identifier):
	logger.info("Aborting %s %s", job_identifier, build_identifier)
	executor = _find_executor(worker_data, build_identifier)
	os.kill(executor["process"].pid, signal.CTRL_BREAK_EVENT)
	# The executor should terminate nicely, if it does not it will stays as running and should be investigated
	# Forcing termination here would leave orphan processes and the status as running


def _find_executor(worker_data, build_identifier):
	for executor in worker_data["active_executors"]:
		if executor["build_identifier"] == build_identifier:
			return executor
	raise KeyError("Executor not found for %s" % build_identifier)


def _request_shutdown(worker_data):
	if len(worker_data["active_executors"]) > 0:
		raise RuntimeError("Executors are still running")
	_shutdown(worker_data)


def _shutdown(worker_data):
	worker_data["should_shutdown"] = True


def _check_status(worker_data, job_identifier, build_identifier):
	executor = _find_executor(worker_data, build_identifier)
	is_executor_running = executor["process"].poll() is None
	status = worker_storage.load_status(job_identifier, build_identifier)
	if not is_executor_running and (not status or status["status"] == "running"):
		logger.error('Build %s executor terminated before completion', build_identifier)
		status["status"] = "exception"
		worker_storage.save_status(job_identifier, build_identifier, status)
	return status


def _retrieve_log(job_identifier, build_identifier, step_index, step_name):
	return worker_storage.load_log(job_identifier, build_identifier, step_index, step_name)


def _retrieve_results(job_identifier, build_identifier):
	return worker_storage.load_results(job_identifier, build_identifier)
