import asyncio
import logging
import os
import socket

from bhamon_orchestra_model.date_time_provider import DateTimeProvider
from bhamon_orchestra_worker.worker_storage import WorkerStorage

import bhamon_orchestra_worker


logger = logging.getLogger("Executor")


class Executor: # pylint: disable = too-many-instance-attributes


	def __init__(self, storage: WorkerStorage, date_time_provider: DateTimeProvider) -> None:
		self._storage = storage
		self._date_time_provider = date_time_provider

		self.run_logger = None
		self.run_logging_handler = None

		self.project_identifier = None
		self.job_identifier = None
		self.run_identifier = None

		self.job_definition = None
		self.parameters = None
		self.run_status = None
		self.workspace = None
		self.environment = None
		self.start_date = None
		self.completion_date = None


	async def run(self, run_identifier: str, environment: dict) -> None:

		# Prevent executor pyvenv from overriding a python executable specified in a command
		if "__PYVENV_LAUNCHER__" in os.environ:
			del os.environ["__PYVENV_LAUNCHER__"]

		self.run_identifier = run_identifier

		try:
			await self.initialize(environment)
			await self.execute()
		finally:
			await self.dispose()


	async def initialize(self, environment: dict) -> None:
		self.run_logger = logging.Logger("Executor", logging.INFO)
		self.run_logging_handler = logging.FileHandler(self._storage.get_log_path(self.run_identifier), mode = "a", encoding = "utf-8")
		self.run_logging_handler.formatter = logging.Formatter("{asctime} [{levelname}][{name}] {message}", "%Y-%m-%dT%H:%M:%S", "{")
		self.run_logger.handlers.append(self.run_logging_handler)

		run_request = self._storage.load_request(self.run_identifier)

		self.project_identifier = run_request["project_identifier"]
		self.job_identifier = run_request["job_identifier"]
		self.job_definition = run_request["job_definition"]
		self.parameters = run_request["parameters"]

		self.run_status = "pending"

		self.workspace = os.path.join("workspaces", run_request["project_identifier"])
		self.environment = environment

		self._save_status()


	async def execute(self) -> None:
		logger.info("(%s) Run is starting for project '%s' and job '%s'", self.run_identifier, self.project_identifier, self.job_identifier)

		try:
			self.run_status = "running"
			self.start_date = self._date_time_provider.serialize(self._date_time_provider.now())
			self._save_status()

			self._log_executor_information()

			if not os.path.exists(self.workspace):
				os.makedirs(self.workspace)

			await self.execute_implementation()

			if self.run_status == "running":
				raise RuntimeError("Unexpected status 'running' after execution")

			self.completion_date = self._date_time_provider.serialize(self._date_time_provider.now())
			self.run_logger.info("Run completed with status %s", self.run_status)
			self._save_status()

		except asyncio.CancelledError:
			logger.error("(%s) Run was aborted", self.run_identifier, exc_info = True)
			self.run_status = "aborted"
			self.completion_date = self._date_time_provider.serialize(self._date_time_provider.now())
			self.run_logger.info("Run completed with status %s", self.run_status)
			self.run_logger.error("Exception", exc_info = True)
			self._save_status()

			raise

		except Exception: # pylint: disable = broad-except
			logger.error("(%s) Run raised an exception", self.run_identifier, exc_info = True)
			self.run_status = "exception"
			self.completion_date = self._date_time_provider.serialize(self._date_time_provider.now())
			self.run_logger.info("Run completed with status %s", self.run_status)
			self.run_logger.error("Exception", exc_info = True)
			self._save_status()

		finally:
			logger.info("(%s) Run completed with status %s", self.run_identifier, self.run_status)


	async def execute_implementation(self) -> None:
		raise NotImplementedError


	async def dispose(self) -> None:
		self.run_logger.handlers.remove(self.run_logging_handler)
		self.run_logging_handler.close()


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
		self.run_logger.info("%s %s", bhamon_orchestra_worker.__product__, bhamon_orchestra_worker.__version__)
		self.run_logging_handler.stream.write("\n")

		executor_information = {
			"Run": self.run_identifier,
			"Host": socket.gethostname(),
			"Workspace": os.path.abspath(self.workspace)
		}

		for key, value in executor_information.items():
			self.run_logger.info("%s: '%s'", key, value)

		self.run_logging_handler.stream.write("\n")
		self.run_logging_handler.flush()
