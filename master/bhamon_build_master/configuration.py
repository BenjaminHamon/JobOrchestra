class Configuration:


	def __init__(self, database, loader):
		self._database = database
		self._loader = loader
		self._data = ConfigurationData([], [], [])


	def reload(self):
		self._data = self._loader()
		self._database.update_configuration(self.job_collection, self.worker_collection)


	@property
	def job_collection(self):
		return self._data.job_collection

	@property
	def worker_collection(self):
		return self._data.worker_collection

	@property
	def workers_by_job(self):
		return self._data.workers_by_job



class ConfigurationData:

	def __init__(self, job_collection, worker_collection, workers_by_job):
		self.job_collection = { job["identifier"]: job for job in job_collection }
		self.worker_collection = { worker["identifier"]: worker for worker in worker_collection }
		self.workers_by_job = workers_by_job
