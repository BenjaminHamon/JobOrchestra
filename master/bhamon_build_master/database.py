import abc


class Database(abc.ABC):

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
	def create_build(self, job_identifier, parameters):
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
	def has_build_step_log(self, build_identifier, step_index):
		pass

	@abc.abstractmethod
	def get_build_step_log(self, build_identifier, step_index):
		pass

	@abc.abstractmethod
	def set_build_step_log(self, build_identifier, step_index, log_text):
		pass
