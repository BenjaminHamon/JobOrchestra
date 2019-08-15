# pylint: disable = no-self-use, unused-argument

class BuildProviderFake:
	""" Fake build provider for unit tests """

	def count(self, job = None, worker = None, status = None):
		return 0

	def get_list(self, job = None, worker = None, status = None, skip = 0, limit = None, order_by = None):
		return []

	def get_list_as_documents(self, job = None, worker = None, status = None, skip = 0, limit = None, order_by = None):
		return []

	def get(self, build_identifier):
		return None

	def create(self, job_identifier, parameters):
		return None

	def update_status(self, build, worker = None, status = None, start_date = None, completion_date = None):
		pass

	def get_all_steps(self, build_identifier):
		return []

	def get_step(self, build_identifier, step_index):
		return None

	def update_steps(self, build, step_collection):
		pass

	def has_step_log(self, build_identifier, step_index):
		return False

	def get_step_log(self, build_identifier, step_index):
		return None

	def set_step_log(self, build_identifier, step_index, log_text):
		pass

	def get_results(self, build_identifier):
		return {}

	def set_results(self, build, results):
		pass
