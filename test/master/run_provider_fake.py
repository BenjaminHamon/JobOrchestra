# pylint: disable = no-self-use, unused-argument

class RunProviderFake:
	""" Fake run provider for unit tests """

	def count(self, job = None, worker = None, status = None):
		return 0

	def get_list(self, job = None, worker = None, status = None, skip = 0, limit = None, order_by = None):
		return []

	def get_list_as_documents(self, job = None, worker = None, status = None, skip = 0, limit = None, order_by = None):
		return []

	def get(self, run_identifier):
		return None

	def create(self, job_identifier, parameters):
		return None

	def update_status(self, run, worker = None, status = None, start_date = None, completion_date = None):
		pass

	def get_all_steps(self, run_identifier):
		return []

	def get_step(self, run_identifier, step_index):
		return None

	def update_steps(self, run, step_collection):
		pass

	def has_step_log(self, run_identifier, step_index):
		return False

	def get_step_log(self, run_identifier, step_index):
		return None

	def set_step_log(self, run_identifier, step_index, log_text):
		pass

	def get_results(self, run_identifier):
		return {}

	def set_results(self, run, results):
		pass
