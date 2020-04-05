import logging


logger = logging.getLogger("WorkerSelector")


class WorkerSelector:


	def __init__(self, worker_provider, supervisor):
		self._worker_provider = worker_provider
		self._supervisor = supervisor


	def __call__(self, job):
		return self.select_worker(job)


	def select_worker(self, job):
		all_workers = self._worker_provider.get_list()
		all_available_workers = (worker for worker in all_workers if self._supervisor.is_worker_available(worker["identifier"]))
		return next((worker["identifier"] for worker in all_available_workers if self.are_compatible(worker, job)), None)


	def are_compatible(self, worker, job):
		executors = self._supervisor.get_worker(worker["identifier"]).executors

		try:
			return job["properties"]["is_controller"] == worker["properties"]["is_controller"] \
				and len(executors) < worker["properties"]["executor_limit"]

		except KeyError:
			logger.warning("Missing property for matching job and worker", exc_info = True)
			return False
