import json
import logging
import os
from typing import List

from bhamon_orchestra_model.date_time_provider import DateTimeProvider
from bhamon_orchestra_worker.executor import Executor
from bhamon_orchestra_worker.process_exception import ProcessException
from bhamon_orchestra_worker.process_watcher import ProcessWatcher
from bhamon_orchestra_worker.worker_storage import WorkerStorage


logger = logging.getLogger("Executor")


class JobExecutor(Executor):


	def __init__(self, storage: WorkerStorage, date_time_provider: DateTimeProvider) -> None:
		super().__init__(storage, date_time_provider)

		self.result_file_path = None

		self.termination_timeout_seconds = 30


	async def initialize(self, environment: dict) -> None:
		await super().initialize(environment)

		self.result_file_path = os.path.join(self.workspace, ".orchestra", "runs", self.run_identifier, "results.json")


	async def execute_implementation(self) -> None:
		overall_success = True

		for command in self.job_definition["commands"]:
			success = await self.execute_command(command)

			if not success:
				overall_success = False
				break

		self.run_status = "succeeded" if overall_success else "failed"


	async def execute_command(self, command: List[str]) -> bool:
		process_watcher_instance = ProcessWatcher()
		process_watcher_instance.output_handler = lambda line: self.run_logging_handler.stream.write(line + "\n")

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
			with open(self.result_file_path, mode = "r", encoding = "utf-8") as result_file:
				results = json.load(result_file)
			self._storage.save_results(self.run_identifier, results)

		return process_watcher_instance.process.returncode == 0


	def format_command(self, command: List[str]) -> List[str]:
		results = {}
		if os.path.isfile(self.result_file_path):
			with open(self.result_file_path, mode = "r", encoding = "utf-8") as results_file:
				results = json.load(results_file)

		format_parameters = {
			"project_identifier": self.project_identifier,
			"job_identifier": self.job_identifier,
			"run_identifier": self.run_identifier,
			"environment": self.environment,
			"parameters": self.parameters,
			"results": results,
			"result_file_path": os.path.relpath(self.result_file_path, self.workspace),
		}

		return [ argument.format(**format_parameters) for argument in command ]
