import datetime
import os
import uuid


class BuildProvider:


	def __init__(self, database_client, file_storage):
		self.database_client = database_client
		self.file_storage = file_storage
		self.build_table = "build"
		self.step_table = "build_step"


	def get_all(self):
		return self.database_client.get_all(self.build_table)


	def get(self, build_identifier):
		return self.database_client.get(self.build_table, build_identifier)


	def create(self, job_identifier, parameters):
		build = {
			"identifier": str(uuid.uuid4()),
			"job": job_identifier,
			"parameters": parameters,
			"status": "pending",
			"creation_date": datetime.datetime.utcnow().replace(microsecond = 0).isoformat(),
			"update_date": datetime.datetime.utcnow().replace(microsecond = 0).isoformat(),
		}

		self.database_client.create(self.build_table, build["identifier"], build)
		return build


	def update(self, build, worker = None, status = None):
		if worker is not None:
			build["worker"] = worker
		if status is not None:
			build["status"] = status
		build["update_date"] = datetime.datetime.utcnow().replace(microsecond = 0).isoformat()
		self.database_client.update(self.build_table, build["identifier"], build)
		return build


	def get_all_steps(self, build_identifier):
		all_build_steps = self.database_client.get_all(self.step_table)
		all_build_steps = { tuple(key.split(", ")) : value for key, value in all_build_steps.items() }
		return [ all_build_steps[key] for key in all_build_steps.keys() if key[0] == build_identifier ]


	def get_step(self, build_identifier, step_index):
		all_build_steps = self.database_client.get_all(self.step_table)
		all_build_steps = { tuple(key.split(", ")) : value for key, value in all_build_steps.items() }
		return all_build_steps[(build_identifier, str(step_index))]


	def update_steps(self, build_identifier, build_step_collection):
		for build_step in build_step_collection:
			build_step["build"] = build_identifier
			key = ", ".join((build_identifier, str(build_step["index"])))
			try:
				self.database_client.update(self.step_table, key, build_step)
			except KeyError:
				self.database_client.create(self.step_table, key, build_step)


	def _get_step_log_path(self, build_identifier, step_index):
		build = self.get(build_identifier)
		build_step = self.get_step(build_identifier, step_index)
		return os.path.join("logs", "{job}_{identifier}".format(**build), "step_{index}_{name}.log".format(**build_step))


	def has_step_log(self, build_identifier, step_index):
		return self.file_storage.exists(self._get_step_log_path(build_identifier, step_index))


	def get_step_log(self, build_identifier, step_index):
		return self.file_storage.load(self._get_step_log_path(build_identifier, step_index))


	def set_step_log(self, build_identifier, step_index, log_text):
		self.file_storage.save(self._get_step_log_path(build_identifier, step_index), log_text)
