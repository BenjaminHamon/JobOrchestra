import logging
import random

from typing import Callable, Optional

from bhamon_orchestra_master.supervisor import Supervisor
from bhamon_orchestra_model.database.database_client import DatabaseClient
from bhamon_orchestra_model.worker_provider import WorkerProvider


logger = logging.getLogger("WorkerSelector")


class WorkerSelector:
	""" Callable class for matching a pending run with an available worker.

	Override are_compatible to implement more conditions (operating system, software, resources, projects...).

	"""


	def __init__(self, database_client_factory: Callable[[], DatabaseClient],
			worker_provider: WorkerProvider, supervisor: Supervisor) -> None:

		self._database_client_factory = database_client_factory
		self._worker_provider = worker_provider
		self._supervisor = supervisor


	def __call__(self, job: dict, run: dict) -> Optional[str]:
		return self.select_worker(job, run)


	def select_worker(self, job: dict, run: dict) -> Optional[str]:
		""" Find an available and suitable worker to execute the specified run """

		with self._database_client_factory() as database_client:
			all_workers = self._worker_provider.get_list(database_client)
			all_available_workers = [ worker for worker in all_workers if self._supervisor.is_worker_available(database_client, worker["identifier"]) ]

		random.shuffle(all_available_workers)

		return next((worker["identifier"] for worker in all_available_workers if self.are_compatible(worker, job, run)), None)


	def are_compatible(self, worker: dict, job: dict, run: dict) -> bool: # pylint: disable = unused-argument
		""" Check if a worker is able to execute the specified run """

		executors = self._supervisor.get_worker(worker["identifier"]).executors

		try:
			return job["properties"]["is_controller"] == worker["properties"]["is_controller"] \
				and len(executors) < worker["properties"]["executor_limit"]

		except KeyError:
			logger.warning("Missing property for matching job and worker", exc_info = True)
			return False
