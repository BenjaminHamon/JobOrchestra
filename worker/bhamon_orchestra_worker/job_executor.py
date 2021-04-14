import logging
import os
from typing import List

from bhamon_orchestra_model.date_time_provider import DateTimeProvider
from bhamon_orchestra_model.serialization.serializer import Serializer
from bhamon_orchestra_worker.executor import Executor
from bhamon_orchestra_worker.process_exception import ProcessException
from bhamon_orchestra_worker.process_watcher import ProcessWatcher
from bhamon_orchestra_worker.worker_storage import WorkerStorage


logger = logging.getLogger("Executor")


class JobExecutor(Executor):


	def __init__(self, storage: WorkerStorage, date_time_provider: DateTimeProvider, serializer: Serializer) -> None:
		super().__init__(storage, date_time_provider)

		self._serializer = serializer

		self.result_file_path = None

		self.termination_timeout_seconds = 30


	async def initialize(self, environment: dict) -> None:
		await super().initialize(environment)

		self.result_file_path = os.path.join(self.workspace, ".orchestra", "runs", self.run_identifier, "results.json")


	async def execute_implementation(self) -> None:
		await self.execute_setup()
		try:
			success = await self.execute_all_commands()
		finally:
			await self.execute_teardown()

		self.run_status = "succeeded" if success else "failed"


	async def execute_setup(self) -> None:
		for command in self.job_definition.get("setup_commands", []):
			success = await self.execute_command(command)
			if not success:
				raise RuntimeError("Setup failed")


	async def execute_all_commands(self) -> bool:
		for command in self.job_definition.get("commands", []):
			success = await self.execute_command(command)
			if not success:
				return False

		return True


	async def execute_teardown(self) -> None:
		for command in self.job_definition.get("teardown_commands", []):
			success = await self.execute_command(command)
			if not success:
				raise RuntimeError("Teardown failed")


	async def execute_command(self, command: List[str]) -> bool:
		process_watcher_instance = ProcessWatcher()
		process_watcher_instance.output_handler = self._log_process_output

		command = self.format_command(command)
		logger.info("(%s) + %s", self.run_identifier, " ".join(("'" + x + "'") if " " in x else x for x in command))

		self.run_logger.info("+ %s", " ".join(("'" + x + "'") if " " in x else x for x in command))
		self.run_logging_handler.stream.write("\n")
		self.run_logging_handler.stream.write("-" * 80 + "\n")
		self.run_logging_handler.stream.write("\n")
		self.run_logging_handler.flush()

		executor_directory = os.getcwd()
		os.chdir(self.workspace)

		try:
			await process_watcher_instance.run(self.run_identifier, command)
		except ProcessException:
			pass
		finally:
			os.chdir(executor_directory)

			self.run_logging_handler.stream.write("\n")
			self.run_logging_handler.stream.write("-" * 80 + "\n")
			self.run_logging_handler.stream.write("\n")
			self.run_logging_handler.flush()

		if os.path.isfile(self.result_file_path):
			results = self._serializer.deserialize_from_file(self.result_file_path)
			self._storage.save_results(self.run_identifier, results)

		return process_watcher_instance.process.returncode == 0


	def format_command(self, command: List[str]) -> List[str]:
		extra_parameters = {
			"result_file_path": os.path.relpath(self.result_file_path, self.workspace),
		}

		return [ self.format_value(argument, extra_parameters) for argument in command ]


	def _log_process_output(self, line: str) -> None: # pylint: disable = no-self-use
		self.run_logging_handler.stream.write(line + "\n")
		self.run_logging_handler.flush()
