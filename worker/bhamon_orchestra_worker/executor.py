import logging
import os
import platform
import signal
import socket
import sys
import traceback

from bhamon_orchestra_model.date_time_provider import DateTimeProvider
from bhamon_orchestra_worker.worker_storage import WorkerStorage

import bhamon_orchestra_worker


logger = logging.getLogger("Executor")


class Executor: # pylint: disable = too-many-instance-attributes


	def __init__(self, storage: WorkerStorage, date_time_provider: DateTimeProvider) -> None:
		self._storage = storage
		self._date_time_provider = date_time_provider

		self.project_identifier = None
		self.job_identifier = None
		self.run_identifier = None

		self.job_definition = None
		self.parameters = None
		self.run_status = None
		self.workspace = None
		self.environment = None
		self.log_file_path = None
		self.start_date = None
		self.completion_date = None

		self._should_shutdown = False


	def run(self, run_identifier: str, environment: dict) -> None:
		if platform.system() == "Windows":
			signal.signal(signal.SIGBREAK, lambda signal_number, frame: self._shutdown()) # pylint: disable = no-member
		signal.signal(signal.SIGINT, lambda signal_number, frame: self._shutdown())
		signal.signal(signal.SIGTERM, lambda signal_number, frame: self._shutdown())

		self.run_identifier = run_identifier

		# Prevent executor pyvenv from overriding a python executable specified in a command
		if "__PYVENV_LAUNCHER__" in os.environ:
			del os.environ["__PYVENV_LAUNCHER__"]

		self.initialize(environment)
		self.execute()


	def _shutdown(self) -> None:
		self._should_shutdown = True


	def initialize(self, environment: dict) -> None:
		run_request = self._storage.load_request(self.run_identifier)

		self.project_identifier = run_request["project_identifier"]
		self.job_identifier = run_request["job_identifier"]
		self.job_definition = run_request["job_definition"]
		self.parameters = run_request["parameters"]

		self.run_status = "pending"

		self.workspace = os.path.join("workspaces", run_request["project_identifier"])
		self.environment = environment
		self.log_file_path = self._storage.get_log_path(self.run_identifier)

		self._save_status()


	def execute(self) -> None:
		logger.info("(%s) Run is starting for project '%s' and job '%s'", self.run_identifier, self.project_identifier, self.job_identifier)


		try:
			self.run_status = "running"
			self.start_date = self._date_time_provider.serialize(self._date_time_provider.now())
			self._save_status()

			self._log_executor_information()

			if not os.path.exists(self.workspace):
				os.makedirs(self.workspace)

			self.execute_implementation()

			if self.run_status == "running":
				raise RuntimeError("Unexpected status 'running' after execution")

			self.completion_date = self._date_time_provider.serialize(self._date_time_provider.now())
			self._log_completion()
			self._save_status()

		except KeyboardInterrupt: # pylint: disable = bare-except
			logger.error("(%s) Run was aborted", self.run_identifier, exc_info = True)
			self.run_status = "aborted"
			self.completion_date = self._date_time_provider.serialize(self._date_time_provider.now())
			self._log_completion()
			self._log_exception(sys.exc_info())
			self._save_status()

		except Exception: # pylint: disable = broad-except
			logger.error("(%s) Run raised an exception", self.run_identifier, exc_info = True)
			self.run_status = "exception"
			self.completion_date = self._date_time_provider.serialize(self._date_time_provider.now())
			self._log_completion()
			self._log_exception(sys.exc_info())
			self._save_status()

		logger.info("(%s) Run completed with status %s", self.run_identifier, self.run_status)


	def execute_implementation(self) -> None:
		raise NotImplementedError


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

		self._storage.save_status(self.run_identifier, status)


	def _log_executor_information(self) -> None:
		orchestra_title = "Job Orchestra"
		worker_version = bhamon_orchestra_worker.__version__

		executor_information = {
			"Run": self.run_identifier,
			"Host": socket.gethostname(),
			"Workspace": os.path.abspath(self.workspace)
		}

		text = "%s %s" % (orchestra_title, worker_version) + "\n"
		text += "\n"
		for key, value in executor_information.items():
			text += "%s: '%s'" % (key, value) + "\n"
		text += "\n"

		with open(self.log_file_path, mode = "a", encoding = "utf-8") as log_file:
			log_file.write(text)


	def _log_exception(self, exc_info: tuple) -> None:
		text = "(orchestra) Exception" + "\n"
		text += "".join(traceback.format_exception(*exc_info)) + "\n"
		with open(self.log_file_path, mode = "a", encoding = "utf-8") as log_file:
			log_file.write(text)


	def _log_completion(self) -> None:
		text = "(orchestra) Run completed with status %s" % self.run_status + "\n"
		with open(self.log_file_path, mode = "a", encoding = "utf-8") as log_file:
			log_file.write(text)
