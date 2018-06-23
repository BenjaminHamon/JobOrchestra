import datetime
import json
import logging
import os
import uuid

import bhamon_build_master.database as database


logger = logging.getLogger("JsonDatabase")


class JsonDatabase(database.Database):


	def __init__(self, data_directory):
		self._data_directory = data_directory


	def get_build_collection(self, sort_by_date, limit):
		all_builds = self._load_data("builds", [])
		if sort_by_date:
			all_builds.sort(key = lambda build: build["update_date"], reverse = True)
		return all_builds[ : limit ]


	def get_pending_builds(self):
		all_builds = self._load_data("builds", [])
		return [ build for build in all_builds if build["status"] == "pending" ]


	def get_build(self, identifier):
		all_builds = self._load_data("builds", [])
		return next(build for build in all_builds if build["identifier"] == identifier)


	def create_build(self, job_identifier, parameters):
		now = JsonDatabase._utc_now_as_string()
		new_build = {
			"identifier": str(uuid.uuid4()),
			"job": job_identifier,
			"parameters": parameters,
			"status": "pending",
			"creation_date": now,
			"update_date": now,
		}

		all_builds = self._load_data("builds", [])
		all_builds.append(new_build)
		self._save_data("builds", all_builds)
		return new_build["identifier"]


	def update_build(self, build_to_update):
		build_to_update["update_date"] = JsonDatabase._utc_now_as_string()
		all_builds = self._load_data("builds", [])
		all_builds = [ build_to_update if build["identifier"] == build_to_update["identifier"] else build for build in all_builds ]
		self._save_data("builds", all_builds)


	def get_build_step_collection(self, build_identifier):
		all_build_steps = self._load_data("build_steps", [])
		return [ build_step for build_step in all_build_steps if build_step["build"] == build_identifier ]


	def get_build_step(self, build_identifier, step_index):
		all_build_steps = self._load_data("build_steps", [])
		return next((build_step for build_step in all_build_steps if (build_step["build"] == build_identifier and build_step["index"] == step_index)))


	def update_build_steps(self, build_identifier, build_step_collection):
		for build_step in build_step_collection:
			build_step["build"] = build_identifier
		all_build_steps = self._load_data("build_steps", [])
		all_build_steps = [ build_step for build_step in all_build_steps if build_step["build"] != build_identifier ]
		all_build_steps += build_step_collection
		self._save_data("build_steps", all_build_steps)


	def _get_build_step_log_path(self, build_identifier, step_index):
		build = self.get_build(build_identifier)
		build_step = self.get_build_step(build_identifier, step_index)
		return os.path.join("{job}_{identifier}".format(**build), "step_{index}_{name}".format(**build_step))


	def has_build_step_log(self, build_identifier, step_index):
		return self._has_log(self._get_build_step_log_path(build_identifier, step_index))


	def get_build_step_log(self, build_identifier, step_index):
		return self._load_log(self._get_build_step_log_path(build_identifier, step_index))


	def set_build_step_log(self, build_identifier, step_index, log_text):
		self._save_log(self._get_build_step_log_path(build_identifier, step_index), log_text)


	def _load_data(self, file_name, default_value):
		file_path = os.path.join(self._data_directory, file_name + ".json")
		if not os.path.exists(file_path):
			return default_value
		with open(file_path) as data_file:
			return json.load(data_file)


	def _save_data(self, file_name, data):
		file_path = os.path.join(self._data_directory, file_name + ".json")
		if not os.path.exists(os.path.dirname(file_path)):
			os.makedirs(os.path.dirname(file_path))
		with open(file_path + ".tmp", "w") as data_file:
			json.dump(data, data_file, indent = 4)
		if os.path.exists(file_path):
			os.remove(file_path)
		os.rename(file_path + ".tmp", file_path)


	def _has_log(self, file_path):
		file_path = os.path.join(self._data_directory, "logs", file_path + ".log")
		return os.path.isfile(file_path)


	def _load_log(self, file_path):
		file_path = os.path.join(self._data_directory, "logs", file_path + ".log")
		if not os.path.exists(file_path):
			return ""
		with open(file_path) as log_file:
			return log_file.read()


	def _save_log(self, file_path, data):
		file_path = os.path.join(self._data_directory, "logs", file_path + ".log")
		if not os.path.exists(os.path.dirname(file_path)):
			os.makedirs(os.path.dirname(file_path))
		with open(file_path + ".tmp", "w") as log_file:
			log_file.write(data)
		if os.path.exists(file_path):
			os.remove(file_path)
		os.rename(file_path + ".tmp", file_path)


	@staticmethod
	def _utc_now_as_string():
		return datetime.datetime.utcnow().replace(microsecond = 0).isoformat()
