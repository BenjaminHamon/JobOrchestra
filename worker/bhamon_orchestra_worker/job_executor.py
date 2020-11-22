import json
import logging
import os
import platform
import signal
import subprocess
import sys
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

		self.is_skipping = False
		self.step_collection = []
		self.result_file_path = None

		self.termination_timeout_seconds = 30


	def initialize(self, environment: dict) -> None:
		super().initialize(environment)

		self.result_file_path = os.path.join(self.workspace, ".orchestra", "runs", self.run_identifier, "results.json")

		self.step_collection = []

		for step_index, step in enumerate(self.job_definition["steps"]):
			self.step_collection.append({
				"index": step_index,
				"name": step["name"],
				"status": "pending",
				"command": step["command"],
			})

		self._save_status()


	def execute_implementation(self) -> None:
		run_final_status = "succeeded"
		self.is_skipping = False

		for step in self.step_collection:
			if not self.is_skipping and self._should_shutdown:
				run_final_status = "aborted"
				self.is_skipping = True

			self.execute_step(step)

			if not self.is_skipping and step["status"] != "succeeded":
				run_final_status = step["status"]
				self.is_skipping = True

		self.run_status = run_final_status


	def execute_step(self, step: dict) -> None:
		logger.info("(%s) Step %s is starting", self.run_identifier, step["name"])

		try:
			step["status"] = "running"
			self._save_status()

			if self.is_skipping:
				step["status"] = "skipped"

			else:
				step_command = self.format_command(step["command"])
				logger.info("(%s) + %s", self.run_identifier, " ".join(step_command))
				step["status"] = self.execute_command(step_command)

				if os.path.isfile(self.result_file_path):
					with open(self.result_file_path, mode = "r", encoding = "utf-8") as result_file:
						results = json.load(result_file)
					self._storage.save_results(self.run_identifier, results)

			self._save_status()

		except KeyboardInterrupt: # pylint: disable = bare-except
			logger.error("(%s) Step was aborted", self.run_identifier, exc_info = True)
			self.run_status = "aborted"
			self._save_status()
			self._log_exception(sys.exc_info())

		except: # pylint: disable = bare-except
			logger.error("(%s) Step %s raised an exception", self.run_identifier, step["name"], exc_info = True)
			step["status"] = "exception"
			self._save_status()
			self._log_exception(sys.exc_info())

		logger.info("(%s) Step %s completed with status %s", self.run_identifier, step["name"], step["status"])


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


	def execute_command(self, command):
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
				return self._wait_process(child_process)
			finally:
				log_file.write("\n")


	def _wait_process(self, child_process: subprocess.Popen) -> str:
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
				return "aborted"
			time.sleep(1)
			result = child_process.poll()
		return "succeeded" if result == 0 else "failed"


	def _save_status(self) -> None:
		status = {
			"project_identifier": self.project_identifier,
			"job_identifier": self.job_identifier,
			"run_identifier": self.run_identifier,
			"workspace": self.workspace,
			"environment": self.environment,
			"status": self.run_status,
			"start_date": self.start_date,
			"completion_date": self.completion_date,
		}

		status["steps"] = []
		for step in self.step_collection:
			status["steps"].append({
				"index": step["index"],
				"name": step["name"],
				"status": step["status"],
			})

		self._storage.save_status(self.run_identifier, status)
