import io
import json
import logging
import os
import time
import uuid
import zipfile


logger = logging.getLogger("RunProvider")


class RunProvider:


	def __init__(self, database_client, file_storage, date_time_provider):
		self.database_client = database_client
		self.file_storage = file_storage
		self.date_time_provider = date_time_provider
		self.table = "run"


	def count(self, project = None, job = None, worker = None, status = None):
		filter = { "project": project, "job": job, "worker": worker, "status": status } # pylint: disable = redefined-builtin
		filter = { key: value for key, value in filter.items() if value is not None }
		return self.database_client.count(self.table, filter)


	def get_list( # pylint: disable = too-many-arguments
			self, project = None, job = None, worker = None, status = None, skip = 0, limit = None, order_by = None):
		filter = { "project": project, "job": job, "worker": worker, "status": status } # pylint: disable = redefined-builtin
		filter = { key: value for key, value in filter.items() if value is not None }
		run_collection = self.database_client.find_many(self.table, filter, skip = skip, limit = limit, order_by = order_by)
		return [ self.convert_to_public(run) for run in run_collection ]


	def get_list_as_documents( # pylint: disable = too-many-arguments
			self, project = None, job = None, worker = None, status = None, skip = 0, limit = None, order_by = None):
		filter = { "project": project, "job": job, "worker": worker, "status": status } # pylint: disable = redefined-builtin
		filter = { key: value for key, value in filter.items() if value is not None }
		return self.database_client.find_many(self.table, filter, skip = skip, limit = limit, order_by = order_by)


	def get(self, run_identifier):
		run = self.database_client.find_one(self.table, { "identifier": run_identifier })
		return self.convert_to_public(run) if run is not None else None


	def create(self, project_identifier, job_identifier, parameters):
		now = self.date_time_provider.now()

		run = {
			"identifier": str(uuid.uuid4()),
			"project": project_identifier,
			"job": job_identifier,
			"parameters": parameters,
			"status": "pending",
			"worker": None,
			"creation_date": self.date_time_provider.serialize(now),
			"update_date": self.date_time_provider.serialize(now),
		}

		self.database_client.insert_one(self.table, run)
		return run


	def update_status( # pylint: disable = too-many-arguments
			self, run, worker = None, status = None, start_date = None, completion_date = None):
		now = self.date_time_provider.now()

		update_data = {
			"worker": worker,
			"status": status,
			"start_date": start_date,
			"completion_date": completion_date,
			"update_date": self.date_time_provider.serialize(now),
		}

		update_data = { key: value for key, value in update_data.items() if value is not None }

		run.update(update_data)
		self.database_client.update_one(self.table, { "identifier": run["identifier"] }, update_data)


	def get_all_steps(self, run_identifier):
		return self.database_client.find_one(self.table, { "identifier": run_identifier }).get("steps", [])


	def get_step(self, run_identifier, step_index):
		return self.database_client.find_one(self.table, { "identifier": run_identifier })["steps"][step_index]


	def update_steps(self, run, step_collection):
		now = self.date_time_provider.now()

		update_data = {
			"steps": step_collection,
			"update_date": self.date_time_provider.serialize(now),
		}

		run.update(update_data)
		self.database_client.update_one(self.table, { "identifier": run["identifier"] }, update_data)


	def _get_step_log_path(self, run_identifier, step_index):
		run = self.get(run_identifier)
		run_step = self.get_step(run_identifier, step_index)
		return os.path.join("logs", "{job}_{identifier}".format(**run), "step_{index}_{name}.log".format(**run_step))


	def has_step_log(self, run_identifier, step_index):
		return self.file_storage.exists(self._get_step_log_path(run_identifier, step_index))


	def get_step_log(self, run_identifier, step_index):
		return self.file_storage.load_chunk_or_default(self._get_step_log_path(run_identifier, step_index), "", skip = 0, limit = None)


	def get_step_log_chunk(self, run_identifier, step_index, skip = 0, limit = None):
		return self.file_storage.load_chunk_or_default(self._get_step_log_path(run_identifier, step_index), "", skip = skip, limit = limit)


	def get_step_log_size(self, run_identifier, step_index):
		return self.file_storage.get_universal_size(self._get_step_log_path(run_identifier, step_index))


	def append_step_log(self, run_identifier, step_index, log_text):
		self.file_storage.append_unsafe(self._get_step_log_path(run_identifier, step_index), log_text)


	def delete_step_log(self, run_identifier, step_index):
		self.file_storage.delete(self._get_step_log_path(run_identifier, step_index))


	def get_results(self, run_identifier):
		return self.database_client.find_one(self.table, { "identifier": run_identifier }).get("results", {})


	def set_results(self, run, results):
		now = self.date_time_provider.now()

		update_data = {
			"results": results,
			"update_date": self.date_time_provider.serialize(now),
		}

		run.update(update_data)
		self.database_client.update_one(self.table, { "identifier": run["identifier"] }, update_data)


	def get_archive(self, run_identifier):
		run = self.database_client.find_one(self.table, { "identifier": run_identifier })
		if run is None:
			return None

		file_name = "{job}_{identifier}".format(**run) + ".zip"
		now = time.gmtime()

		with io.BytesIO() as file_object:
			with zipfile.ZipFile(file_object, mode = "w", compression = zipfile.ZIP_DEFLATED) as archive:
				entry_info = zipfile.ZipInfo("run.json", now[0:6])
				entry_info.external_attr = 0o644 << 16
				archive.writestr(entry_info, json.dumps(run, indent = 4))
				for step in run.get("steps", []):
					log_path = self._get_step_log_path(run_identifier, step["index"])
					entry_info = zipfile.ZipInfo(os.path.basename(log_path), now[0:6])
					entry_info.external_attr = 0o644 << 16
					archive.writestr(entry_info, self.file_storage.load_or_default(log_path, ""))

			return { "file_name": file_name, "data": file_object.getvalue(), "type": "zip" }


	def convert_to_public(self, run): # pylint: disable = no-self-use
		keys_to_return = [ "identifier", "project", "job", "worker", "parameters", "status", "start_date", "completion_date", "creation_date", "update_date" ]
		return { key: value for key, value in run.items() if key in keys_to_return }
