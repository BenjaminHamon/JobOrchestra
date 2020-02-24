import asyncio
import base64
import logging
import platform
import signal
import sys

from bhamon_orchestra_model.network.messenger import Messenger
from bhamon_orchestra_model.network.websocket import WebSocketClient
from bhamon_orchestra_worker.executor_watcher import ExecutorWatcher
from bhamon_orchestra_worker.synchronization import Synchronization
import bhamon_orchestra_worker.worker_logging as worker_logging
import bhamon_orchestra_worker.worker_storage as worker_storage


logger = logging.getLogger("Worker")


class Worker: # pylint: disable = too-many-instance-attributes


	def __init__( # pylint: disable = too-many-arguments
			self, identifier, master_uri, user, secret, display_name, properties, executor_script):
		self._identifier = identifier
		self._master_uri = master_uri
		self._user = user
		self._secret = secret
		self._display_name = display_name
		self._properties = properties
		self._executor_script = executor_script

		self._active_executors = []
		self._messenger = None
		self._should_shutdown = False

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

		asyncio_loop = asyncio.get_event_loop()
		asyncio_loop.run_until_complete(self.run_async())
		asyncio_loop.close()

		logger.info("Exiting worker")


	async def run_async(self):
		self._recover()

		executors_future = asyncio.ensure_future(self._run_executors())
		messenger_future = asyncio.ensure_future(self._run_messenger())

		try:
			await asyncio.wait([ executors_future, messenger_future ], return_when = asyncio.FIRST_COMPLETED)

		finally:
			executors_future.cancel()
			messenger_future.cancel()

			try:
				await executors_future
			except asyncio.CancelledError:
				pass
			except Exception: # pylint: disable = broad-except
				logger.error("Unhandled exception from executors", exc_info = True)

			try:
				await messenger_future
			except asyncio.CancelledError:
				pass
			except Exception: # pylint: disable = broad-except
				logger.error("Unhandled exception from messenger", exc_info = True)

			await self._terminate()


	async def _run_executors(self):
		while not self._should_shutdown:
			for executor in self._active_executors:
				executor.update(self._messenger)
			await asyncio.sleep(1)


	async def _run_messenger(self):
		websocket_client_instance = WebSocketClient("master", self._master_uri)
		authentication_data = base64.b64encode(b"%s:%s" % (self._user.encode(), self._secret.encode())).decode()
		headers = { "Authorization": "Basic" + " " + authentication_data, "X-Orchestra-Worker": self._identifier }
		await websocket_client_instance.run_forever(self._process_connection, extra_headers = headers)


	async def _process_connection(self, connection):
		messenger_instance = Messenger(connection)
		messenger_instance.identifier = connection.connection.remote_address
		messenger_instance.request_handler = self._handle_request

		self._messenger = messenger_instance

		try:
			await messenger_instance.run()
		finally:
			messenger_instance.dispose()
			self._messenger = None

			for executor in self._active_executors:
				if executor.synchronization is not None:
					executor.synchronization.pause()


	async def _handle_request(self, request):
		return await self._execute_command(request["command"], request.get("parameters", {}))


	async def _terminate(self):
		all_futures = []
		for executor in self._active_executors:
			all_futures.append(executor.terminate(self.termination_timeout_seconds))
		if len(all_futures) > 0:
			await asyncio.wait(all_futures)
		for executor in self._active_executors:
			if executor.is_running():
				logger.warning("Run %s is still active (Process: %s)", executor.run_identifier, executor.process.pid)


	async def _execute_command(self, command, parameters): # pylint: disable=too-many-return-statements
		if command == "describe":
			return self._describe()
		if command == "list":
			return self._list_runs()
		if command == "execute":
			return await self._execute(**parameters)
		if command == "clean":
			return await self._clean(**parameters)
		if command == "abort":
			return self._abort(**parameters)
		if command == "request":
			return self._retrieve_request(**parameters)
		if command == "resynchronize":
			return self._resynchronize(**parameters)
		if command == "shutdown":
			return self._request_shutdown()
		raise ValueError("Unknown command '%s'" % command)


	def _describe(self):
		return { "display_name": self._display_name, "properties": self._properties }


	def _recover(self):
		all_runs = worker_storage.list_runs()
		for run_identifier in all_runs:
			logger.info("Recovering run %s", run_identifier)
			for executor in self._active_executors:
				if executor.run_identifier == run_identifier:
					continue
			executor = ExecutorWatcher(run_identifier)
			self._active_executors.append(executor)


	def _list_runs(self):
		all_runs = []
		for executor in self._active_executors:
			all_runs.append({ "run_identifier": executor.run_identifier })
		return all_runs


	async def _execute(self, run_identifier, job, parameters):
		logger.info("Executing run %s", run_identifier)

		run_request = {
			"run_identifier": run_identifier,
			"job": job,
			"parameters": parameters,
		}

		worker_storage.create_run(run_identifier)
		worker_storage.save_request(run_identifier, run_request)

		executor = ExecutorWatcher(run_identifier)
		executor_command = [ sys.executable, self._executor_script, run_identifier ]
		await executor.start(executor_command)
		self._active_executors.append(executor)


	async def _clean(self, run_identifier):
		logger.info("Cleaning run %s", run_identifier)
		executor = self._find_executor(run_identifier)
		if executor.is_running():
			raise RuntimeError("Executor is still running for run %s" % run_identifier)
		await executor.wait_futures()
		if executor.synchronization is not None:
			executor.synchronization.dispose()
		self._active_executors.remove(executor)
		worker_storage.delete_run(run_identifier)


	def _abort(self, run_identifier):
		logger.info("Aborting run %s", run_identifier)
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


	def _retrieve_request(self, run_identifier): # pylint: disable = no-self-use
		return worker_storage.load_request(run_identifier)


	def _resynchronize(self, run_identifier, reset):
		executor = self._find_executor(run_identifier)
		run_request = worker_storage.load_request(run_identifier)

		if executor.synchronization is not None:
			executor.synchronization.dispose()
			executor.synchronization = None

		executor.synchronization = Synchronization(run_request)
		executor.synchronization.reset(reset["steps"])
		executor.synchronization.resume()
