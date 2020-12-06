import asyncio
import logging
from typing import Callable, List, Optional

import websockets

from bhamon_orchestra_model.database.database_client import DatabaseClient
from bhamon_orchestra_model.network.messenger import Messenger
from bhamon_orchestra_model.run_provider import RunProvider
from bhamon_orchestra_model.worker_provider import WorkerProvider


logger = logging.getLogger("Worker")


class Worker:
	""" Watcher for a remote worker process """


	def __init__(self, # pylint: disable = too-many-arguments
			identifier: str, messenger: Messenger,
			database_client_factory: Callable[[], DatabaseClient],
			run_provider: RunProvider, worker_provider: WorkerProvider) -> None:

		self.identifier = identifier
		self._messenger = messenger
		self._database_client_factory = database_client_factory
		self._run_provider = run_provider
		self._worker_provider = worker_provider

		self.should_disconnect = False
		self.executors = []


	def assign_run(self, job: dict, run: dict) -> None:
		""" Assign a pending run to the worker """

		with self._database_client_factory() as database_client:
			self._run_provider.update_status(database_client, run, worker = self.identifier)

		executor = {
			"job": job,
			"run": run,
			"local_status": "pending",
			"synchronization": "unknown",
			"received_updates": [],
			"should_abort": False,
		}

		self.executors.append(executor)


	def abort_run(self, run_identifier: str) -> None:
		""" Request a run to be aborted """
		for executor in self.executors:
			if executor["run"]["identifier"] == run_identifier:
				executor["should_abort"] = True


	async def run(self) -> None:
		""" Perform updates until cancelled """

		messenger_future = asyncio.ensure_future(self._messenger.run())
		worker_future = asyncio.ensure_future(self._run_worker())

		try:
			await asyncio.wait([ messenger_future, worker_future ], return_when = asyncio.FIRST_COMPLETED)

		finally:
			worker_future.cancel()
			messenger_future.cancel()

			self._messenger.dispose()

			try:
				await worker_future
			except asyncio.CancelledError:
				pass
			except Exception: # pylint: disable = broad-except
				logger.error("(%s) Unhandled exception", self.identifier, exc_info = True)

			try:
				await messenger_future
			except websockets.exceptions.ConnectionClosed as exception:
				if exception.code not in [ 1000, 1001 ] and not isinstance(exception.__cause__, asyncio.CancelledError):
					logger.error("(%s) Lost connection with remote", self.identifier, exc_info = True)
			except asyncio.CancelledError:
				pass
			except Exception as exception: # pylint: disable = broad-except
				logger.error("(%s) Unhandled exception from messenger", self.identifier, exc_info = True)


	async def _run_worker(self) -> None:
		with self._database_client_factory() as database_client:
			await self._update_properties(database_client)

		try:
			with self._database_client_factory() as database_client:
				self.executors += await self._recover_executors(database_client)
		except asyncio.CancelledError: # pylint: disable = try-except-raise
			raise
		except Exception: # pylint: disable = broad-except
			logger.error("(%s) Unhandled exception while recovering runs", self.identifier, exc_info = True)

		while not self.should_disconnect:
			all_executors = list(self.executors)
			for executor in all_executors:
				try:
					with self._database_client_factory() as database_client:
						await self._process_executor(database_client, executor)
				except asyncio.CancelledError: # pylint: disable = try-except-raise
					raise
				except Exception: # pylint: disable = broad-except
					logger.error("(%s) Unhandled exception while executing run %s", self.identifier, executor["run"]["identifier"], exc_info = True)
					executor["local_status"] = "exception"

				if executor["local_status"] in [ "done", "exception" ]:
					self.executors.remove(executor)

			await asyncio.sleep(0.1)


	async def _execute_remote_command(self, command: str, parameters: Optional[dict] = None) -> Optional[dict]:
		""" Execute a command on the remote worker """
		return await self._messenger.send_request({ "command": command, "parameters": parameters if parameters is not None else {} })


	def _find_executor(self, run_identifier: str) -> dict:
		""" Retrieve the local object for an active executor """

		for executor in self.executors:
			if executor["run"]["identifier"] == run_identifier:
				return executor

		raise KeyError("Executor not found for %s" % run_identifier)


	async def _update_properties(self, database_client: DatabaseClient) -> None:
		worker_properties = await self._execute_remote_command("describe")
		self._worker_provider.update_properties(database_client, { "identifier": self.identifier }, **worker_properties)


	async def _recover_executors(self, database_client: DatabaseClient) -> List[dict]:
		""" Retrieve the executor list from the remote worker """

		recovered_executors = []
		runs_to_recover = await self._execute_remote_command("list")
		for run_information in runs_to_recover:
			executor = await self._recover_execution(database_client, **run_information)
			recovered_executors.append(executor)
		return recovered_executors


	async def _process_executor(self, database_client: DatabaseClient, executor: dict) -> None:
		""" Perform a update for a single executor """

		if executor["local_status"] == "pending":
			await self._start_execution(executor["run"], executor["job"])
			executor["local_status"] = "running"

		elif executor["local_status"] == "running":
			if executor["run"]["status"] in [ "succeeded", "failed", "aborted", "exception" ]:
				executor["local_status"] = "verifying"

			elif executor["should_abort"]:
				await self._abort_execution(executor["run"])
				executor["local_status"] = "aborting"

			if executor["synchronization"] == "unknown":
				await self._resynchronize(executor["run"])
				executor["synchronization"] = "running"

		elif executor["local_status"] == "aborting":
			if executor["run"]["status"] in [ "succeeded", "failed", "aborted", "exception" ]:
				executor["local_status"] = "verifying"

		elif executor["local_status"] == "verifying":
			if executor["synchronization"] == "done":
				executor["local_status"] = "finishing"

		elif executor["local_status"] == "finishing":
			await self._finish_execution(executor["run"])
			executor["local_status"] = "done"

		for update in executor["received_updates"]:
			await self._process_update(database_client, executor, update)
		executor["received_updates"].clear()


	async def _recover_execution(self, database_client: DatabaseClient, run_identifier: str) -> dict:
		""" Recover the state for an executor from the remote worker """

		logger.info("(%s) Recovering run %s", self.identifier, run_identifier)
		run_request = await self._retrieve_request(run_identifier)
		run = self._run_provider.get(database_client, run_request["project_identifier"], run_identifier)

		return {
			"job": run_request["job_definition"],
			"run": run,
			"local_status": "running",
			"synchronization": "unknown",
			"received_updates": [],
			"should_abort": False,
		}


	async def _start_execution(self, run: dict, job: dict) -> None:
		""" Trigger a run execution on the remote worker """

		logger.info("(%s) Starting run %s", self.identifier, run["identifier"])
		execute_request = { "run_identifier": run["identifier"], "job": job, "parameters": run["parameters"] }
		await self._execute_remote_command("execute", execute_request)


	async def _abort_execution(self, run: dict) -> None:
		""" Request a run to be aborted on the remote worker """

		logger.info("(%s) Aborting run %s", self.identifier, run["identifier"])
		abort_request = { "run_identifier": run["identifier"] }
		await self._execute_remote_command("abort", abort_request)


	async def _finish_execution(self, run: dict) -> None:
		""" Perform cleanup on the remote worker after the run has completed and data synchronization is done """

		clean_request = { "run_identifier": run["identifier"] }
		await self._execute_remote_command("clean", clean_request)
		logger.info("(%s) Completed run %s with status %s", self.identifier, run["identifier"], run["status"])


	async def _resynchronize(self, run: dict) -> None:
		""" Resumes data synchronization with the remote worker for the specified run """

		# The log cursor is computed on the text size instead of the binary size
		# to take into account encoding and end-of-lines differences.
		log_cursor = len(self._run_provider.get_log(run["project"], run["identifier"])[0])
		resynchronization_request = { "run_identifier": run["identifier"], "log_cursor": log_cursor }
		await self._execute_remote_command("resynchronize", resynchronization_request)


	async def _retrieve_request(self, run_identifier: str) -> dict:
		""" Retrieves the run request stored on the remote worker """
		parameters = { "run_identifier": run_identifier }
		return await self._execute_remote_command("request", parameters)


	async def receive_update(self, update: dict) -> None:
		""" Process an incoming update from the remote worker """

		executor = self._find_executor(update["run"])

		if executor["local_status"] == "finishing":
			raise RuntimeError("Update received after completion and verification")

		executor["received_updates"].append(update)


	async def _process_update(self, database_client: DatabaseClient, executor: dict, update: dict) -> None:
		if "status" in update:
			self._update_status(database_client, executor["run"], update["status"])
		if "results" in update:
			self._update_results(database_client, executor["run"], update["results"])
		if "log_chunk" in update:
			self._update_log_file(executor["run"], update["log_chunk"])
		if "event" in update:
			self._handle_event(executor, update["event"])


	def _update_status(self, database_client: DatabaseClient, run: dict, status: dict) -> None:
		""" Process an update for the run status """

		properties_to_update = [ "status", "start_date", "completion_date" ]
		self._run_provider.update_status(database_client, run, ** { key: value for key, value in status.items() if key in properties_to_update })


	def _update_results(self, database_client: DatabaseClient, run: dict, results: dict) -> None:
		""" Process an update for the run results """
		self._run_provider.set_results(database_client, run, results)


	def _update_log_file(self, run: dict, log_chunk: str) -> None:
		""" Process an update for the run log files """
		self._run_provider.append_log_chunk(run["project"], run["identifier"], log_chunk)


	def _handle_event(self, executor: dict, event: str) -> None: # pylint: disable = no-self-use
		""" Process an event update """
		if event == "synchronization_completed":
			executor["synchronization"] = "done"
