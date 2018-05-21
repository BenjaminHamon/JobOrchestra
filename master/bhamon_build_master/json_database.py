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


	def get_job_collection(self):
		return self._load_data("jobs", [])


	def get_job(self, identifier):
		all_jobs = self._load_data("jobs", [])
		return next(job for job in all_jobs if job["identifier"] == identifier)


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


	def create_build(self, job, parameters):
		now = JsonDatabase._utc_now_as_string()
		new_build = {
			"identifier": str(uuid.uuid4()),
			"job": job,
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


	def get_worker_collection(self):
		return self._load_data("workers", [])


	def get_worker(self, identifier):
		all_workers = self._load_data("workers", [])
		return next(worker for worker in all_workers if worker["identifier"] == identifier)


	def update_configuration(self, job_collection, worker_collection):
		saved_job_collection = self._load_data("jobs", [])
		saved_worker_collection = self._load_data("workers", [])

		updated_job_collection = []
		for job in job_collection.values():
			job_data = {
				"identifier": job["identifier"],
				"description": job["description"],
				"is_enabled": True,
			}

			saved_job_data = next((data for data in saved_job_collection if data["identifier"] == job["identifier"]), None)
			if saved_job_data is not None:
				job_data["is_enabled"] = saved_job_data["is_enabled"]
			job_data["update_date"] = JsonDatabase._utc_now_as_string()

			updated_job_collection.append(job_data)

		updated_worker_collection = []
		for worker in worker_collection.values():
			worker_data = {
				"identifier": worker["identifier"],
				"description": worker["description"],
				"is_enabled": True,
				"is_active": False,
			}

			saved_worker_data = next((data for data in saved_worker_collection if data["identifier"] == worker["identifier"]), None)
			if saved_worker_data is not None:
				worker_data["is_enabled"] = saved_worker_data["is_enabled"]
				worker_data["is_active"] = saved_worker_data["is_active"]
			worker_data["update_date"] = JsonDatabase._utc_now_as_string()

			updated_worker_collection.append(worker_data)

		updated_job_collection.sort(key = lambda job: job["identifier"])
		updated_worker_collection.sort(key = lambda worker: worker["identifier"])

		self._save_data("jobs", updated_job_collection)
		self._save_data("workers", updated_worker_collection)



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


	@staticmethod
	def _utc_now_as_string():
		return datetime.datetime.utcnow().replace(microsecond = 0).isoformat()
