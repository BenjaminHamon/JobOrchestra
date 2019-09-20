import asyncio
import json
import logging
import os
import platform
import signal
import subprocess
import sys
import time

import websockets

import bhamon_build_worker.worker_logging as worker_logging
import bhamon_build_worker.worker_storage as worker_storage


logger = logging.getLogger("Worker")

shutdown_signal = signal.CTRL_BREAK_EVENT if platform.system() == "Windows" else signal.SIGINT # pylint: disable = no-member
subprocess_flags = subprocess.CREATE_NEW_PROCESS_GROUP if platform.system() == "Windows" else 0

connection_attempt_delay_collection = [ 10, 10, 10, 10, 10, 60, 60, 60, 300, 3600 ]
termination_timeout_seconds = 30


def run(master_uri, worker_identifier, executor_script):
	logger.info("Starting build worker")

	worker_data = {
		"identifier": worker_identifier,
		"executor_script": executor_script,
		"active_connection_task": None,
		"active_executors": [],
		"should_shutdown": False,
	}

	if platform.system() == "Windows":
		signal.signal(signal.SIGBREAK, lambda signal_number, frame: _shutdown(worker_data)) # pylint: disable = no-member
	signal.signal(signal.SIGINT, lambda signal_number, frame: _shutdown(worker_data))
	signal.signal(signal.SIGTERM, lambda signal_number, frame: _shutdown(worker_data))

	if platform.system() == "Windows":
		asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

	worker_logging.configure_logging_handlers()

	main_loop = asyncio.get_event_loop()
	worker_data["asyncio_loop"] = main_loop

	_recover(worker_data)
	main_future = asyncio.gather(_run_client(master_uri, worker_data), _check_signals(worker_data))
	main_loop.run_until_complete(main_future)
	_terminate(worker_data)
	main_loop.close()

	logger.info("Exiting build worker")


# Ensure Windows signals are processed even when the asyncio event loop is blocking with nothing happening
async def _check_signals(worker_data):
	while not worker_data["should_shutdown"]:
		await asyncio.sleep(1)


async def _run_client(master_uri, worker_data):
	connection_attempt_counter = 0

	while not worker_data["should_shutdown"]:
		try:
			connection_attempt_counter += 1
			logger.info("Connecting to master on %s (Attempt: %s)", master_uri, connection_attempt_counter)
			try:
				async with websockets.connect(master_uri) as connection:
					logger.info("Connected to master, waiting for commands")
					connection_attempt_counter = 0
					await _process_connection(connection, worker_data)
			except websockets.exceptions.ConnectionClosed as exception:
				if exception.code not in [ 1000, 1001 ]:
					raise
			logger.info("Closed connection to master")

		except OSError:
			logger.error("Failed to connect to master", exc_info = True)
		except (websockets.exceptions.ConnectionClosed, websockets.exceptions.InvalidStatusCode):
			logger.error("Lost connection to master", exc_info = True)

		if not worker_data["should_shutdown"]:
			try:
				connection_attempt_delay = connection_attempt_delay_collection[connection_attempt_counter]
			except IndexError:
				connection_attempt_delay = connection_attempt_delay_collection[-1]
			logger.info("Retrying connection in %s seconds", connection_attempt_delay)
			delay_start_time = time.time()
			while not worker_data["should_shutdown"] and (time.time() - delay_start_time < connection_attempt_delay):
				await asyncio.sleep(1)


async def _process_connection(connection, worker_data):
	while not worker_data["should_shutdown"]:
		try:
			worker_data["active_connection_task"] = asyncio.ensure_future(connection.recv())
			request = json.loads(await worker_data["active_connection_task"])
			worker_data["active_connection_task"] = None
		except asyncio.CancelledError:
			break

		logger.debug("< %s", request)

		try:
			result = await _execute_command(worker_data, request["command"], request["parameters"])
			response = { "result": result }
		except Exception as exception: # pylint: disable=broad-except
			logger.error("Failed to process request %s", request, exc_info = True)
			response = { "error": str(exception) }

		logger.debug("> %s", response)

		try:
			worker_data["active_connection_task"] = asyncio.ensure_future(connection.send(json.dumps(response)))
			await worker_data["active_connection_task"]
			worker_data["active_connection_task"] = None
		except asyncio.CancelledError:
			break


def _terminate(worker_data):
	all_futures = []
	for executor in worker_data["active_executors"]:
		all_futures.append(_terminate_executor(executor, termination_timeout_seconds))
	worker_data["asyncio_loop"].run_until_complete(asyncio.gather(*all_futures))
	for executor in worker_data["active_executors"]:
		if "process" in executor and executor["process"].returncode is None:
			logger.warning("%s %s is still running (Process: %s)", executor["job_identifier"], executor["build_identifier"], executor["process"].pid)


async def _terminate_executor(executor, timeout_seconds):
	if "process" in executor and executor["process"].returncode is None:
		logger.info("Aborting %s %s", executor["job_identifier"], executor["build_identifier"])
		os.kill(executor["process"].pid, shutdown_signal)

		try:
			await asyncio.wait_for(executor["process"].wait(), timeout_seconds)
		except asyncio.TimeoutError:
			logger.warning("Forcing termination for %s %s", executor["job_identifier"], executor["build_identifier"])
			executor["process"].kill()


async def _execute_command(worker_data, command, parameters): # pylint: disable=too-many-return-statements
	if command == "authenticate":
		return _authenticate(worker_data)
	if command == "list":
		return _list_builds(worker_data)
	if command == "execute":
		return await _execute(worker_data, **parameters)
	if command == "clean":
		return await _clean(worker_data, **parameters)
	if command == "abort":
		return _abort(worker_data, **parameters)
	if command == "status":
		return _retrieve_status(worker_data, **parameters)
	if command == "request":
		return _retrieve_request(**parameters)
	if command == "log":
		return _retrieve_log(**parameters)
	if command == "results":
		return _retrieve_results(**parameters)
	if command == "shutdown":
		return _request_shutdown(worker_data)
	raise ValueError("Unknown command '%s'" % command)


def _authenticate(worker_data):
	return { "identifier": worker_data["identifier"] }


def _recover(worker_data):
	all_builds = worker_storage.list_builds()
	for job_identifier, build_identifier in all_builds:
		logger.info("Recovering %s %s", job_identifier, build_identifier)
		for executor in worker_data["active_executors"]:
			if executor["build_identifier"] == build_identifier:
				continue
		executor = { "job_identifier": job_identifier, "build_identifier": build_identifier }
		worker_data["active_executors"].append(executor)


def _list_builds(worker_data):
	all_builds = []
	for executor in worker_data["active_executors"]:
		all_builds.append({ "job_identifier": executor["job_identifier"], "build_identifier": executor["build_identifier"] })
	return all_builds


async def _execute(worker_data, job_identifier, build_identifier, job, parameters):
	logger.info("Executing %s %s", job_identifier, build_identifier)

	build_request = {
		"job_identifier": job_identifier,
		"build_identifier": build_identifier,
		"job": job,
		"parameters": parameters,
	}

	worker_storage.create_build(job_identifier, build_identifier)
	worker_storage.save_request(job_identifier, build_identifier, build_request)

	executor_command = [ sys.executable, worker_data["executor_script"], job_identifier, build_identifier ]
	executor_process = await asyncio.create_subprocess_exec(*executor_command, stdout = subprocess.PIPE, stderr = subprocess.STDOUT, creationflags = subprocess_flags)
	executor_watcher = worker_data["asyncio_loop"].create_task(_watch_executor(executor_process))

	executor = {
		"job_identifier": job_identifier,
		"build_identifier": build_identifier,
		"process": executor_process,
		"watcher": executor_watcher,
	}

	worker_data["active_executors"].append(executor)


async def _clean(worker_data, job_identifier, build_identifier):
	logger.info("Cleaning %s %s", job_identifier, build_identifier)
	executor = _find_executor(worker_data, build_identifier)
	if "watcher" in executor:
		await asyncio.wait_for(executor["watcher"], 1)
	if "process" in executor and executor["process"].returncode is None:
		raise RuntimeError("Executor is still running for build %s" % build_identifier)
	worker_data["active_executors"].remove(executor)
	worker_storage.delete_build(job_identifier, build_identifier)


def _abort(worker_data, job_identifier, build_identifier):
	logger.info("Aborting %s %s", job_identifier, build_identifier)
	executor = _find_executor(worker_data, build_identifier)
	if executor["process"].returncode is None:
		os.kill(executor["process"].pid, shutdown_signal)
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
	if worker_data["active_connection_task"]:
		worker_data["active_connection_task"].cancel()


def _retrieve_status(worker_data, job_identifier, build_identifier):
	executor = _find_executor(worker_data, build_identifier)
	is_executor_running = "process" in executor and executor["process"].returncode is None
	status = worker_storage.load_status(job_identifier, build_identifier)
	if not is_executor_running and (status["status"] in [ "unknown", "running" ]):
		logger.error('Build %s executor terminated before completion', build_identifier)
		status["status"] = "exception"
		worker_storage.save_status(job_identifier, build_identifier, status)
	return status


def _retrieve_request(job_identifier, build_identifier):
	return worker_storage.load_request(job_identifier, build_identifier)


def _retrieve_log(job_identifier, build_identifier, step_index, step_name):
	return worker_storage.load_log(job_identifier, build_identifier, step_index, step_name)


def _retrieve_results(job_identifier, build_identifier):
	return worker_storage.load_results(job_identifier, build_identifier)


async def _watch_executor(executor_process):
	raw_logger = logging.getLogger("raw")

	while True:
		try:
			line = await asyncio.wait_for(executor_process.stdout.readline(), 1)
		except asyncio.TimeoutError:
			continue

		if not line:
			break

		line = line.decode("utf-8").strip()
		raw_logger.info(line)
