import asyncio
import logging

from typing import List, Optional

from bhamon_orchestra_model.network.messenger import Messenger
from bhamon_orchestra_model.run_provider import RunProvider


logger = logging.getLogger("Worker")


class WorkerError(Exception):
	""" Exception class for worker errors occuring in normal operations """


class Worker:
	""" Watcher for a remote worker process """


	def __init__(self, identifier: str, messenger: Messenger, run_provider: RunProvider) -> None:
		self.identifier = identifier
		self._messenger = messenger
		self._run_provider = run_provider

		self.should_disconnect = False
		self.executors = []


	def assign_run(self, job: dict, run: dict) -> None:
		""" Assign a pending run to the worker """
		self._run_provider.update_status(run, worker = self.identifier)
		executor = { "job": job, "run": run, "local_status": "pending", "synchronization": "unknown", "should_abort": False }
		self.executors.append(executor)


	def abort_run(self, run_identifier: str) -> None:
		""" Request a run to be aborted """
		for executor in self.executors:
			if executor["run"]["identifier"] == run_identifier:
				executor["should_abort"] = True


	async def run(self) -> None:
		""" Perform updates until cancelled """

		try:
			self.executors += await self._recover_executors()
		except asyncio.CancelledError: # pylint: disable = try-except-raise
			raise
		except Exception: # pylint: disable = broad-except
			logger.error("(%s) Unhandled exception while recovering runs", self.identifier, exc_info = True)

		while not self.should_disconnect:
			all_executors = list(self.executors)
			for executor in all_executors:
				try:
					await self._process_executor(executor)
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


	async def _recover_executors(self) -> List[dict]:
		""" Retrieve the executor list from the remote worker """

		recovered_executors = []
		runs_to_recover = await self._execute_remote_command("list")
		for run_information in runs_to_recover:
			executor = await self._recover_execution(**run_information)
			recovered_executors.append(executor)
		return recovered_executors


	async def _process_executor(self, executor: dict) -> None:
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


	async def _recover_execution(self, run_identifier: str) -> dict:
		""" Recover the state for an executor from the remote worker """

		logger.info("(%s) Recovering run %s", self.identifier, run_identifier)
		run_request = await self._retrieve_request(run_identifier)
		run = self._run_provider.get(run_request["job"]["project"], run_identifier)
		return { "job": run_request["job"], "run": run, "local_status": "running", "synchronization": "unknown", "should_abort": False }


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

		reset = { "steps": [] }

		for step in self._run_provider.get_all_steps(run["project"], run["identifier"]):
			if self._run_provider.has_step_log(run["project"], run["identifier"], step["index"]):
				log_size = self._run_provider.get_step_log_size(run["project"], run["identifier"], step["index"])
				reset["steps"].append({ "index": step["index"], "log_file_cursor": log_size })

		resynchronization_request = { "run_identifier": run["identifier"], "reset": reset }
		await self._execute_remote_command("resynchronize", resynchronization_request)


	async def _retrieve_request(self, run_identifier: str) -> dict:
		""" Retrieves the run request stored on the remote worker """
		parameters = { "run_identifier": run_identifier }
		return await self._execute_remote_command("request", parameters)


	async def handle_update(self, update: dict) -> None:
		""" Process an incoming update from the remote worker """

		executor = self._find_executor(update["run"])

		if executor["local_status"] == "finishing":
			raise RuntimeError("Update received after completion and verification")

		if "status" in update:
			self._update_status(executor["run"], update["status"])
		if "results" in update:
			self._update_results(executor["run"], update["results"])
		if "log_chunk" in update:
			self._update_log_file(executor["run"], update["step_index"], update["log_chunk"])
		if "event" in update:
			self._handle_event(executor, update["event"])


	def _find_executor(self, run_identifier: str) -> dict:
		""" Retrieve the local object for an active executor """

		for executor in self.executors:
			if executor["run"]["identifier"] == run_identifier:
				return executor

		raise KeyError("Executor not found for %s" % run_identifier)


	def _update_status(self, run: dict, status: dict) -> None:
		""" Process an update for the run status """

		properties_to_update = [ "status", "start_date", "completion_date" ]
		self._run_provider.update_status(run, ** { key: value for key, value in status.items() if key in properties_to_update })

		step_properties_to_update = [ "name", "index", "status" ]
		step_collection = [ { key: value for key, value in step.items() if key in step_properties_to_update } for step in status.get("steps", []) ]
		self._run_provider.update_steps(run, step_collection)


	def _update_results(self, run: dict, results: dict) -> None:
		""" Process an update for the run results """
		self._run_provider.set_results(run, results)


	def _update_log_file(self, run: str, step_index: int, log_chunk: str) -> None:
		""" Process an update for the run log files """
		self._run_provider.append_step_log(run["project"], run["identifier"], step_index, log_chunk)


	def _handle_event(self, executor: dict, event: str) -> None: # pylint: disable = no-self-use
		""" Process an event update """
		if event == "synchronization_completed":
			executor["synchronization"] = "done"
