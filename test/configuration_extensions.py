class WorkerSelector:

	def __init__(self, worker_provider):
		self._worker_provider = worker_provider


	def __call__(self, supervisor, job):
		return self.select_worker(supervisor, job)


	def select_worker(self, supervisor, job):
		all_workers = self._worker_provider.get_list()
		all_available_workers = (worker for worker in all_workers if supervisor.is_worker_available(worker["identifier"]))
		return next((worker["identifier"] for worker in all_available_workers if self.are_compatible(supervisor, worker, job)), None)


	def are_compatible(self, supervisor, worker, job): # pylint: disable = no-self-use
		executors = supervisor.get_worker(worker["identifier"]).executors
		return (job["properties"]["project"] in worker["properties"]["project"]
			and job["properties"]["is_controller"] == worker["properties"]["is_controller"]
			and len(executors) < worker["properties"]["executor_limit"])
