import abc


class Database(abc.ABC):

	@abc.abstractmethod
	def get_job_collection(self):
		pass

	@abc.abstractmethod
	def get_job(self, identifier):
		pass

	@abc.abstractmethod
	def get_build_collection(self, sort_by_date, limit):
		pass

	@abc.abstractmethod
	def get_pending_builds(self):
		pass

	@abc.abstractmethod
	def get_build(self, identifier):
		pass

	@abc.abstractmethod
	def create_build(self, job, parameters):
		pass

	@abc.abstractmethod
	def update_build(self, build_to_update):
		pass

	@abc.abstractmethod
	def get_build_step_collection(self, build_identifier):
		pass

	@abc.abstractmethod
	def get_build_step(self, build_identifier, step_index):
		pass

	@abc.abstractmethod
	def update_build_steps(self, build_identifier, build_step_collection):
		pass

	@abc.abstractmethod
	def get_worker_collection(self):
		pass

	@abc.abstractmethod
	def get_worker(self, identifier):
		pass

	@abc.abstractmethod
	def update_configuration(self, job_collection, worker_collection):
		pass
