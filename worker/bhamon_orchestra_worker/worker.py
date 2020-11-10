import asyncio
import logging
import sys
from typing import Any, List, Optional

from bhamon_orchestra_model.network.connection import NetworkConnection
from bhamon_orchestra_model.network.messenger import Messenger
from bhamon_orchestra_worker.executor_watcher import ExecutorWatcher
from bhamon_orchestra_worker.master_client import MasterClient
from bhamon_orchestra_worker.synchronization import Synchronization
import bhamon_orchestra_worker.worker_logging as worker_logging
from bhamon_orchestra_worker.worker_storage import WorkerStorage


logger = logging.getLogger("Worker")


class Worker: # pylint: disable = too-few-public-methods


	def __init__(self, # pylint: disable = too-many-arguments
			storage: WorkerStorage, master_client: MasterClient,
			display_name: str, properties: dict, executor_script: str) -> None:

		self._storage = storage
		self._master_client = master_client
		self._display_name = display_name
		self._properties = properties
		self._executor_script = executor_script

		self._active_executors = []
		self._messenger = None

		self.termination_timeout_seconds = 30


	async def run(self) -> None:
		logger.info("Starting worker")

		worker_logging.configure_logging_handlers()

		self._recover()

		executors_future = asyncio.ensure_future(self._run_executors())
		master_client_future = asyncio.ensure_future(self._master_client.run(self._process_connection))

		try:
			await asyncio.wait([ executors_future, master_client_future ], return_when = asyncio.FIRST_COMPLETED)

		finally:
			executors_future.cancel()
			master_client_future.cancel()

			try:
				await executors_future
			except asyncio.CancelledError:
				pass
			except Exception: # pylint: disable = broad-except
				logger.error("Unhandled exception from executors", exc_info = True)

			try:
				await master_client_future
			except asyncio.CancelledError:
				pass
			except Exception: # pylint: disable = broad-except
				logger.error("Unhandled exception from master client", exc_info = True)

			await self._terminate()

			logger.info("Exiting worker")


	async def _run_executors(self) -> None:
		while True:
			for executor in self._active_executors:
				executor.update(self._messenger)
			await asyncio.sleep(1)


	async def _process_connection(self, connection: NetworkConnection) -> None:
		messenger_instance = Messenger(connection.remote_address, connection)
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


	async def _handle_request(self, request: dict) -> Optional[Any]:
		return await self._execute_command(request["command"], request.get("parameters", {}))


	def _recover(self) -> None:
		all_runs = self._storage.list_runs()
		for run_identifier in all_runs:
			logger.info("Recovering run %s", run_identifier)
			for executor in self._active_executors:
				if executor.run_identifier == run_identifier:
					continue
			executor = self._instantiate_executor(run_identifier)
			self._active_executors.append(executor)


	async def _terminate(self) -> None:
		all_futures = []
		for executor in self._active_executors:
			all_futures.append(asyncio.ensure_future(executor.terminate(self.termination_timeout_seconds)))

		if len(all_futures) > 0:
			await asyncio.wait(all_futures, return_when = asyncio.ALL_COMPLETED)

		for future in all_futures:
			try:
				await future
			except Exception: # pylint: disable = broad-except
				logger.error("Unhandled exception from executor termination", exc_info = True)

		for executor in self._active_executors:
			if executor.is_running():
				logger.warning("Run %s is still active (Process: %s)", executor.run_identifier, executor.process.pid)


	async def _execute_command(self, command: str, parameters: dict) -> Optional[Any]: # pylint: disable=too-many-return-statements
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
		raise ValueError("Unknown command '%s'" % command)


	def _instantiate_executor(self, run_identifier: str) -> ExecutorWatcher:
		return ExecutorWatcher(self._storage, run_identifier)


	def _find_executor(self, run_identifier: str) -> ExecutorWatcher:
		for executor in self._active_executors:
			if executor.run_identifier == run_identifier:
				return executor
		raise KeyError("Executor not found for %s" % run_identifier)


	def _describe(self) -> dict:
		return {
			"display_name": self._display_name,
			"properties": self._properties,
		}


	def _list_runs(self) -> List[dict]:
		all_runs = []
		for executor in self._active_executors:
			all_runs.append({ "run_identifier": executor.run_identifier })
		return all_runs


	async def _execute(self, run_identifier: str, job: dict, parameters: dict) -> None:
		logger.info("Executing run %s", run_identifier)

		run_request = {
			"project_identifier": job["project"],
			"job_identifier": job["identifier"],
			"run_identifier": run_identifier,
			"job_definition": job,
			"parameters": parameters,
		}

		self._storage.create_run(run_identifier)
		self._storage.save_request(run_identifier, run_request)

		executor = self._instantiate_executor(run_identifier)
		executor_command = [ sys.executable, self._executor_script, run_identifier ]

		try:
			await executor.start(executor_command)
		except OSError:
			logger.error("Failed to start run %s", run_identifier, exc_info = True)

		self._active_executors.append(executor)


	async def _clean(self, run_identifier: str) -> None:
		logger.info("Cleaning run %s", run_identifier)
		executor = self._find_executor(run_identifier)
		await executor.complete()

		if executor.synchronization is not None:
			executor.synchronization.dispose()
			executor.synchronization = None

		self._active_executors.remove(executor)
		self._storage.delete_run(run_identifier)


	def _abort(self, run_identifier: str) -> None:
		logger.info("Aborting run %s", run_identifier)
		executor = self._find_executor(run_identifier)
		if executor.is_running():
			executor.abort()


	def _retrieve_request(self, run_identifier: str) -> dict: # pylint: disable = no-self-use
		return self._storage.load_request(run_identifier)


	def _resynchronize(self, run_identifier: str, reset: dict) -> None:
		executor = self._find_executor(run_identifier)
		run_request = self._storage.load_request(run_identifier)

		if executor.synchronization is not None:
			executor.synchronization.dispose()
			executor.synchronization = None

		executor.synchronization = Synchronization(self._storage, run_request)
		executor.synchronization.reset(reset["steps"])
		executor.synchronization.resume()
