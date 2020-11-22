import json
import logging
import os
import platform
import signal
import subprocess
import time
from typing import List

from bhamon_orchestra_model.date_time_provider import DateTimeProvider
from bhamon_orchestra_worker.executor import Executor
from bhamon_orchestra_worker.worker_storage import WorkerStorage


logger = logging.getLogger("Executor")

shutdown_signal = signal.CTRL_BREAK_EVENT if platform.system() == "Windows" else signal.SIGINT # pylint: disable = no-member
subprocess_flags = subprocess.CREATE_NEW_PROCESS_GROUP if platform.system() == "Windows" else 0


class JobExecutor(Executor):


	def __init__(self, storage: WorkerStorage, date_time_provider: DateTimeProvider) -> None:
		super().__init__(storage, date_time_provider)

		self.result_file_path = None

		self.termination_timeout_seconds = 30


	def initialize(self, environment: dict) -> None:
		super().initialize(environment)

		self.result_file_path = os.path.join(self.workspace, ".orchestra", "runs", self.run_identifier, "results.json")


	def execute_implementation(self) -> None:
		overall_success = True

		for command in self.job_definition["commands"]:
			success = self.execute_command(command)

			if not success:
				overall_success = False
				break

		self.run_status = "succeeded" if overall_success else "failed"


	def execute_command(self, command: List[str]):
		command = self.format_command(command)
		logger.info("(%s) + %s", self.run_identifier, " ".join(("'" + x + "'") if " " in x else x for x in command))

		with open(self.log_file_path, mode = "a", encoding = "utf-8") as log_file:
			log_file.write("(orchestra) + %s\n" % " ".join(("'" + x + "'") if " " in x else x for x in command))
			log_file.write("\n")
			log_file.flush()

			executor_directory = os.getcwd()
			os.chdir(self.workspace)

			try:
				child_process = subprocess.Popen(command, stdout = log_file, stderr = subprocess.STDOUT, creationflags = subprocess_flags)
			finally:
				os.chdir(executor_directory)

			try:
				success = self._wait_process(child_process)
			finally:
				log_file.write("\n")

		if os.path.isfile(self.result_file_path):
			with open(self.result_file_path, mode = "r", encoding = "utf-8") as result_file:
				results = json.load(result_file)
			self._storage.save_results(self.run_identifier, results)

		return success


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


	def _wait_process(self, child_process: subprocess.Popen) -> bool:
		result = None
		while result is None:
			if self._should_shutdown:
				logger.info("(%s) Terminating child process", self.run_identifier)
				os.kill(child_process.pid, shutdown_signal)
				try:
					result = child_process.wait(timeout = self.termination_timeout_seconds)
				except subprocess.TimeoutExpired:
					logger.warning("(%s) Terminating child process (force)", self.run_identifier)
					child_process.kill()
				raise KeyboardInterrupt
			time.sleep(1)
			result = child_process.poll()
		return result == 0
