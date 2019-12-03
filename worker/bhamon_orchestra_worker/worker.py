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

import bhamon_orchestra_worker.worker_logging as worker_logging
import bhamon_orchestra_worker.worker_storage as worker_storage


logger = logging.getLogger("Worker")

shutdown_signal = signal.CTRL_BREAK_EVENT if platform.system() == "Windows" else signal.SIGINT # pylint: disable = no-member
subprocess_flags = subprocess.CREATE_NEW_PROCESS_GROUP if platform.system() == "Windows" else 0


class Worker: # pylint: disable = too-few-public-methods


	def __init__(self, identifier, master_uri, user, secret, properties, executor_script):
		self._identifier = identifier
		self._master_uri = master_uri
		self._user = user
		self._secret = secret
		self._properties = properties
		self._executor_script = executor_script

		self._active_executors = []
		self._asyncio_loop = None
		self._active_connection_task = None
		self._should_shutdown = False

		self.connection_attempt_delay_collection = [ 10, 10, 10, 10, 10, 60, 60, 60, 300, 3600 ]
		self.termination_timeout_seconds = 30


	def run(self):
		logger.info("Starting worker")

		if platform.system() == "Windows":
			signal.signal(signal.SIGBREAK, lambda signal_number, frame: self._shutdown()) # pylint: disable = no-member
		signal.signal(signal.SIGINT, lambda signal_number, frame: self._shutdown())
		signal.signal(signal.SIGTERM, lambda signal_number, frame: self._shutdown())

		if platform.system() == "Windows":
			asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy()) # pylint: disable = no-member

		worker_logging.configure_logging_handlers()

		self._asyncio_loop = asyncio.get_event_loop()

		self._recover()
		main_future = asyncio.gather(self._run_client(), self._check_signals())
		self._asyncio_loop.run_until_complete(main_future)
		self._terminate()
		self._asyncio_loop.close()

		logger.info("Exiting worker")


	# Ensure Windows signals are processed even when the asyncio event loop is blocking with nothing happening
	async def _check_signals(self):
		while not self._should_shutdown:
			await asyncio.sleep(1)


	async def _run_client(self):
		connection_attempt_counter = 0

		while not self._should_shutdown:
			try:
				connection_attempt_counter += 1
				logger.info("Connecting to master on %s (Attempt: %s)", self._master_uri, connection_attempt_counter)
				try:
					async with websockets.connect(self._master_uri) as connection:
						logger.info("Connected to master, waiting for commands")
						connection_attempt_counter = 0
						await self._process_connection(connection)
				except websockets.exceptions.ConnectionClosed as exception:
					if exception.code not in [ 1000, 1001 ]:
						raise
				logger.info("Closed connection to master")

			except OSError:
				logger.error("Failed to connect to master", exc_info = True)
			except (websockets.exceptions.ConnectionClosed, websockets.exceptions.InvalidStatusCode):
				logger.error("Lost connection to master", exc_info = True)

			if not self._should_shutdown:
				try:
					connection_attempt_delay = self.connection_attempt_delay_collection[connection_attempt_counter]
				except IndexError:
					connection_attempt_delay = self.connection_attempt_delay_collection[-1]
				logger.info("Retrying connection in %s seconds", connection_attempt_delay)
				delay_start_time = time.time()
				while not self._should_shutdown and (time.time() - delay_start_time < connection_attempt_delay):
					await asyncio.sleep(1)


	async def _process_connection(self, connection):
		while not self._should_shutdown:
			try:
				self._active_connection_task = asyncio.ensure_future(connection.recv())
				request = json.loads(await self._active_connection_task)
				self._active_connection_task = None
			except asyncio.CancelledError:
				break

			logger.debug("< %s", request)

			try:
				result = await self._execute_command(request["command"], request["parameters"])
				response = { "result": result }
			except Exception as exception: # pylint: disable=broad-except
				logger.error("Failed to process request %s", request, exc_info = True)
				response = { "error": str(exception) }

			logger.debug("> %s", response)

			try:
				self._active_connection_task = asyncio.ensure_future(connection.send(json.dumps(response)))
				await self._active_connection_task
				self._active_connection_task = None
			except asyncio.CancelledError:
				break


	def _terminate(self):
		all_futures = []
		for executor in self._active_executors:
			all_futures.append(self._terminate_executor(executor, self.termination_timeout_seconds))
		self._asyncio_loop.run_until_complete(asyncio.gather(*all_futures))
		for executor in self._active_executors:
			if "process" in executor and executor["process"].returncode is None:
				logger.warning("%s %s is still running (Process: %s)", executor["job_identifier"], executor["run_identifier"], executor["process"].pid)


	async def _terminate_executor(self, executor, timeout_seconds):
		if "process" in executor and executor["process"].returncode is None:
			logger.info("Aborting %s %s", executor["job_identifier"], executor["run_identifier"])
			os.kill(executor["process"].pid, shutdown_signal)

			try:
				await asyncio.wait_for(executor["process"].wait(), timeout_seconds)
			except asyncio.TimeoutError:
				logger.warning("Forcing termination for %s %s", executor["job_identifier"], executor["run_identifier"])
				executor["process"].kill()


	async def _execute_command(self, command, parameters): # pylint: disable=too-many-return-statements
		if command == "authenticate":
			return self._authenticate()
		if command == "properties":
			return self._get_properties()
		if command == "list":
			return self._list_runs()
		if command == "execute":
			return await self._execute(**parameters)
		if command == "clean":
			return await self._clean(**parameters)
		if command == "abort":
			return self._abort(**parameters)
		if command == "status":
			return self._retrieve_status(**parameters)
		if command == "request":
			return self._retrieve_request(**parameters)
		if command == "log":
			return self._retrieve_log(**parameters)
		if command == "results":
			return self._retrieve_results(**parameters)
		if command == "shutdown":
			return self._request_shutdown()
		raise ValueError("Unknown command '%s'" % command)


	def _authenticate(self):
		return {
			"worker": self._identifier,
			"user": self._user,
			"secret": self._secret,
		}


	def _get_properties(self):
		return self._properties


	def _recover(self):
		all_runs = worker_storage.list_runs()
		for job_identifier, run_identifier in all_runs:
			logger.info("Recovering %s %s", job_identifier, run_identifier)
			for executor in self._active_executors:
				if executor["run_identifier"] == run_identifier:
					continue
			executor = { "job_identifier": job_identifier, "run_identifier": run_identifier }
			self._active_executors.append(executor)


	def _list_runs(self):
		all_runs = []
		for executor in self._active_executors:
			all_runs.append({ "job_identifier": executor["job_identifier"], "run_identifier": executor["run_identifier"] })
		return all_runs


	async def _execute(self, job_identifier, run_identifier, job, parameters):
		logger.info("Executing %s %s", job_identifier, run_identifier)

		run_request = {
			"job_identifier": job_identifier,
			"run_identifier": run_identifier,
			"job": job,
			"parameters": parameters,
		}

		worker_storage.create_run(job_identifier, run_identifier)
		worker_storage.save_request(job_identifier, run_identifier, run_request)

		executor_command = [ sys.executable, self._executor_script, job_identifier, run_identifier ]
		executor_process = await asyncio.create_subprocess_exec(*executor_command, stdout = subprocess.PIPE, stderr = subprocess.STDOUT, creationflags = subprocess_flags)
		executor_watcher = self._asyncio_loop.create_task(self._watch_executor(executor_process))

		executor = {
			"job_identifier": job_identifier,
			"run_identifier": run_identifier,
			"process": executor_process,
			"watcher": executor_watcher,
		}

		self._active_executors.append(executor)


	async def _clean(self, job_identifier, run_identifier):
		logger.info("Cleaning %s %s", job_identifier, run_identifier)
		executor = self._find_executor(run_identifier)
		if "watcher" in executor:
			await asyncio.wait_for(executor["watcher"], 1)
		if "process" in executor and executor["process"].returncode is None:
			raise RuntimeError("Executor is still running for run %s" % run_identifier)
		self._active_executors.remove(executor)
		worker_storage.delete_run(job_identifier, run_identifier)


	def _abort(self, job_identifier, run_identifier):
		logger.info("Aborting %s %s", job_identifier, run_identifier)
		executor = self._find_executor(run_identifier)
		if executor["process"].returncode is None:
			os.kill(executor["process"].pid, shutdown_signal)
		# The executor should terminate nicely, if it does not it will stays as running and should be investigated
		# Forcing termination here would leave orphan processes and the status as running


	def _find_executor(self, run_identifier):
		for executor in self._active_executors:
			if executor["run_identifier"] == run_identifier:
				return executor
		raise KeyError("Executor not found for %s" % run_identifier)


	def _request_shutdown(self):
		if len(self._active_executors) > 0:
			raise RuntimeError("Executors are still running")
		self._shutdown()


	def _shutdown(self):
		self._should_shutdown = True
		if self._active_connection_task:
			self._active_connection_task.cancel()


	def _retrieve_status(self, job_identifier, run_identifier):
		executor = self._find_executor(run_identifier)
		is_executor_running = "process" in executor and executor["process"].returncode is None
		status = worker_storage.load_status(job_identifier, run_identifier)
		if not is_executor_running and (status["status"] in [ "unknown", "running" ]):
			logger.error("Run '%s' terminated before completion", run_identifier)
			status["status"] = "exception"
			worker_storage.save_status(job_identifier, run_identifier, status)
		return status


	def _retrieve_request(self, job_identifier, run_identifier): # pylint: disable = no-self-use
		return worker_storage.load_request(job_identifier, run_identifier)


	def _retrieve_log(self, job_identifier, run_identifier, step_index, step_name): # pylint: disable = no-self-use
		return worker_storage.load_log(job_identifier, run_identifier, step_index, step_name)


	def _retrieve_results(self, job_identifier, run_identifier): # pylint: disable = no-self-use
		return worker_storage.load_results(job_identifier, run_identifier)


	async def _watch_executor(self, executor_process):
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
