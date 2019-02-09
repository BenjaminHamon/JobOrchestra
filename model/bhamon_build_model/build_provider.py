# pylint: disable=redefined-builtin

import datetime
import logging
import os
import uuid


logger = logging.getLogger("BuildProvider")


class BuildProvider:


	def __init__(self, database_client, file_storage):
		self.database_client = database_client
		self.file_storage = file_storage
		self.build_table = "build"
		self.step_table = "build_step"
		self.result_table = "build_result"


	def count(self, job = None, worker = None, status = None):
		filter = { "job": job, "worker": worker, "status": status }
		filter = { key: value for key, value in filter.items() if value is not None }
		return self.database_client.count(self.build_table, filter)


	def get_list(self, job = None, worker = None, status = None, skip = 0, limit = None, order_by = None):
		filter = { "job": job, "worker": worker, "status": status }
		filter = { key: value for key, value in filter.items() if value is not None }
		return self.database_client.find_many(self.build_table, filter, skip = skip, limit = limit, order_by = order_by)


	def get(self, build_identifier):
		return self.database_client.find_one(self.build_table, { "identifier": build_identifier })


	def create(self, job_identifier, parameters):
		build = {
			"identifier": str(uuid.uuid4()),
			"job": job_identifier,
			"parameters": parameters,
			"status": "pending",
			"creation_date": datetime.datetime.utcnow().replace(microsecond = 0).isoformat(),
			"update_date": datetime.datetime.utcnow().replace(microsecond = 0).isoformat(),
		}

		build_results = {
			"build": build["identifier"],
			"results": {},
		}

		self.database_client.insert_one(self.build_table, build)
		self.database_client.insert_one(self.result_table, build_results)
		return build


	def update_status(self, build, worker = None, status = None):
		update_data = {}
		if worker is not None:
			update_data["worker"] = worker
		if status is not None:
			update_data["status"] = status
		update_data["update_date"] = datetime.datetime.utcnow().replace(microsecond = 0).isoformat()
		build.update(update_data)
		self.database_client.update_one(self.build_table, { "identifier": build["identifier"] }, update_data)


	def get_all_steps(self, build_identifier):
		return self.database_client.find_many(self.step_table, { "build": build_identifier })


	def get_step(self, build_identifier, step_index):
		return self.database_client.find_one(self.step_table, { "build": build_identifier, "index": step_index })


	def update_steps(self, build_identifier, build_step_collection):
		for build_step in build_step_collection:
			build_step["build"] = build_identifier
		for build_step in build_step_collection:
			existing_step = self.get_step(build_identifier, build_step["index"])
			if existing_step is None:
				self.database_client.insert_one(self.step_table, build_step)
			else:
				self.database_client.update_one(self.step_table, { "build": build_identifier, "index": build_step["index"] }, build_step)


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


	def get_results(self, build_identifier):
		return self.database_client.find_one(self.result_table, { "build": build_identifier })["results"]


	def set_results(self, build_identifier, results):
		self.database_client.update_one(self.result_table, { "build": build_identifier }, { "results": results })
