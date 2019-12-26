import asyncio
import base64
import json
import logging
import platform
import signal
import sys
import traceback

from bhamon_orchestra_model.network.websocket import WebSocketClient
from bhamon_orchestra_worker.executor_watcher import ExecutorWatcher
import bhamon_orchestra_worker.worker_logging as worker_logging
import bhamon_orchestra_worker.worker_storage as worker_storage


logger = logging.getLogger("Worker")


class Worker: # pylint: disable = too-few-public-methods


	def __init__(self, identifier, master_uri, user, secret, properties, executor_script):
		self._identifier = identifier
		self._master_uri = master_uri
		self._user = user
		self._secret = secret
		self._properties = properties
		self._executor_script = executor_script

		self._client_future = None
		self._active_executors = []
		self._asyncio_loop = None
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
		try:
			websocket_client_instance = WebSocketClient("master", self._master_uri)
			authentication_data = base64.b64encode(b"%s:%s" % (self._user.encode(), self._secret.encode())).decode()
			headers = { "Authorization": "Basic" + " " + authentication_data, "X-Orchestra-Worker": self._identifier }
			self._client_future = asyncio.ensure_future(websocket_client_instance.run_forever(self._process_connection, extra_headers = headers))
			await self._client_future
		except asyncio.CancelledError:
			pass
		except Exception: # pylint: disable = broad-except
			logger.error("Unhandled exception", exc_info = True)
		finally:
			self._client_future = None


	async def _process_connection(self, connection):
		while not self._should_shutdown:
			request = json.loads(await connection.receive())
			logger.debug("< %s", request)

			try:
				result = await self._execute_command(request["command"], request["parameters"])
				response = { "result": result }
			except Exception as exception: # pylint: disable=broad-except
				logger.error("Failed to process request %s", request, exc_info = True)
				response = { "error": "".join(traceback.format_exception_only(exception.__class__, exception)).strip() }

			logger.debug("> %s", response)
			await connection.send(json.dumps(response))


	def _terminate(self):
		all_futures = []
		for executor in self._active_executors:
			all_futures.append(executor.terminate(self.termination_timeout_seconds))
		self._asyncio_loop.run_until_complete(asyncio.gather(*all_futures))
		for executor in self._active_executors:
			if executor.is_running():
				logger.warning("%s %s is still running (Process: %s)", executor.job_identifier, executor.run_identifier, executor.process.pid)


	async def _execute_command(self, command, parameters): # pylint: disable=too-many-return-statements
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


	def _get_properties(self):
		return self._properties


	def _recover(self):
		all_runs = worker_storage.list_runs()
		for job_identifier, run_identifier in all_runs:
			logger.info("Recovering %s %s", job_identifier, run_identifier)
			for executor in self._active_executors:
				if executor.run_identifier == run_identifier:
					continue
			executor = ExecutorWatcher(job_identifier, run_identifier)
			self._active_executors.append(executor)


	def _list_runs(self):
		all_runs = []
		for executor in self._active_executors:
			all_runs.append({ "job_identifier": executor.job_identifier, "run_identifier": executor.run_identifier })
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

		executor = ExecutorWatcher(job_identifier, run_identifier)
		executor_command = [ sys.executable, self._executor_script, job_identifier, run_identifier ]
		self._active_executors.append(executor)
		await executor.start(executor_command)


	async def _clean(self, job_identifier, run_identifier):
		logger.info("Cleaning %s %s", job_identifier, run_identifier)
		executor = self._find_executor(run_identifier)
		if executor.is_running():
			raise RuntimeError("Executor is still running for run %s" % run_identifier)
		await executor.wait_futures()
		self._active_executors.remove(executor)
		worker_storage.delete_run(job_identifier, run_identifier)


	def _abort(self, job_identifier, run_identifier):
		logger.info("Aborting %s %s", job_identifier, run_identifier)
		executor = self._find_executor(run_identifier)
		if executor.is_running():
			executor.abort()


	def _find_executor(self, run_identifier):
		for executor in self._active_executors:
			if executor.run_identifier == run_identifier:
				return executor
		raise KeyError("Executor not found for %s" % run_identifier)


	def _request_shutdown(self):
		if len(self._active_executors) > 0:
			raise RuntimeError("Executors are still running")
		self._shutdown()


	def _shutdown(self):
		self._should_shutdown = True
		if self._client_future:
			self._client_future.cancel()


	def _retrieve_status(self, job_identifier, run_identifier):
		executor = self._find_executor(run_identifier)
		is_executor_running = executor.is_running()
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
