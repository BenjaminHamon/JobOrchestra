# pylint: disable = redefined-builtin

import datetime
import io
import json
import logging
import os
import time
import uuid
import zipfile


logger = logging.getLogger("BuildProvider")


class BuildProvider:


	def __init__(self, database_client, file_storage):
		self.database_client = database_client
		self.file_storage = file_storage
		self.build_table = "build"


	def count(self, job = None, worker = None, status = None):
		filter = { "job": job, "worker": worker, "status": status }
		filter = { key: value for key, value in filter.items() if value is not None }
		return self.database_client.count(self.build_table, filter)


	def get_list(self, job = None, worker = None, status = None, skip = 0, limit = None, order_by = None):
		filter = { "job": job, "worker": worker, "status": status }
		filter = { key: value for key, value in filter.items() if value is not None }
		build_collection = self.database_client.find_many(self.build_table, filter, skip = skip, limit = limit, order_by = order_by)
		return [ self.convert_to_public(build) for build in build_collection ]


	def get_list_as_documents(self, job = None, worker = None, status = None, skip = 0, limit = None, order_by = None):
		filter = { "job": job, "worker": worker, "status": status }
		filter = { key: value for key, value in filter.items() if value is not None }
		return self.database_client.find_many(self.build_table, filter, skip = skip, limit = limit, order_by = order_by)


	def get(self, build_identifier):
		build = self.database_client.find_one(self.build_table, { "identifier": build_identifier })
		return self.convert_to_public(build)


	def create(self, job_identifier, parameters):
		build = {
			"identifier": str(uuid.uuid4()),
			"job": job_identifier,
			"parameters": parameters,
			"status": "pending",
			"creation_date": datetime.datetime.utcnow().replace(microsecond = 0).isoformat() + "Z",
			"update_date": datetime.datetime.utcnow().replace(microsecond = 0).isoformat() + "Z",
		}

		self.database_client.insert_one(self.build_table, build)
		return build


	def update_status(self, build, worker = None, status = None, start_date = None, completion_date = None):
		update_data = {}
		if worker is not None:
			update_data["worker"] = worker
		if status is not None:
			update_data["status"] = status
		if start_date is not None:
			update_data["start_date"] = start_date
		if completion_date is not None:
			update_data["completion_date"] = completion_date
		update_data["update_date"] = datetime.datetime.utcnow().replace(microsecond = 0).isoformat() + "Z"
		build.update(update_data)
		self.database_client.update_one(self.build_table, { "identifier": build["identifier"] }, update_data)


	def get_all_steps(self, build_identifier):
		return self.database_client.find_one(self.build_table, { "identifier": build_identifier }).get("steps", [])


	def get_step(self, build_identifier, step_index):
		return self.database_client.find_one(self.build_table, { "identifier": build_identifier })["steps"][step_index]


	def update_steps(self, build, step_collection):
		update_data = {
			"steps": step_collection,
			"update_date": datetime.datetime.utcnow().replace(microsecond = 0).isoformat() + "Z",
		}

		build.update(update_data)
		self.database_client.update_one(self.build_table, { "identifier": build["identifier"] }, update_data)


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
		return self.database_client.find_one(self.build_table, { "identifier": build_identifier }).get("results", {})


	def set_results(self, build, results):
		update_data = {
			"results": results,
			"update_date": datetime.datetime.utcnow().replace(microsecond = 0).isoformat() + "Z",
		}

		build.update(update_data)
		self.database_client.update_one(self.build_table, { "identifier": build["identifier"] }, update_data)


	def get_archive(self, build_identifier):
		build = self.database_client.find_one(self.build_table, { "identifier": build_identifier })
		if build is None:
			return None

		file_name = "{job}_{identifier}".format(**build) + ".zip"
		now = time.gmtime()

		with io.BytesIO() as file_object:
			with zipfile.ZipFile(file_object, mode = "w", compression = zipfile.ZIP_DEFLATED) as archive:
				entry_info = zipfile.ZipInfo("build.json", now[0:6])
				entry_info.external_attr = 0o644 << 16
				archive.writestr(entry_info, json.dumps(build, indent = 4))
				for step in build.get("steps", []):
					log_path = self._get_step_log_path(build_identifier, step["index"])
					entry_info = zipfile.ZipInfo(os.path.basename(log_path), now[0:6])
					entry_info.external_attr = 0o644 << 16
					archive.writestr(entry_info, self.file_storage.load(log_path))

			return { "file_name": file_name, "data": file_object.getvalue(), "type": "zip" }


	def convert_to_public(self, build): # pylint: disable = no-self-use
		keys_to_return = [ "identifier", "job", "worker", "parameters", "status", "start_date", "completion_date", "creation_date", "update_date" ]
		return { key: value for key, value in build.items() if key in keys_to_return }
