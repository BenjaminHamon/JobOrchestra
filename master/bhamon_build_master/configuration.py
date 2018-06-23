class Configuration:


	def __init__(self, loader, job_provider, worker_provider):
		self._loader = loader
		self._job_provider = job_provider
		self._worker_provider = worker_provider
		self._data = ConfigurationData([], [], [])


	def reload(self):
		self._data = self._loader()
		self._update_database()


	@property
	def job_collection(self):
		return self._data.job_collection

	@property
	def worker_collection(self):
		return self._data.worker_collection

	@property
	def workers_by_job(self):
		return self._data.workers_by_job


	def _update_database(self):
		for job in self.job_collection.values():
			self._job_provider.create_or_update(job["identifier"], job["description"], job["parameters"])
		for worker in self.worker_collection.values():
			self._worker_provider.create_or_update(worker["identifier"], worker["description"])


class ConfigurationData:

	def __init__(self, job_collection, worker_collection, workers_by_job):
		self.job_collection = { job["identifier"]: job for job in job_collection }
		self.worker_collection = { worker["identifier"]: worker for worker in worker_collection }
		self.workers_by_job = workers_by_job
