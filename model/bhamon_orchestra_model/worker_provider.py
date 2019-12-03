# pylint: disable = redefined-builtin

import datetime
import logging


logger = logging.getLogger("WorkerProvider")


class WorkerProvider:


	def __init__(self, database_client):
		self.database_client = database_client
		self.table = "worker"


	def count(self):
		return self.database_client.count(self.table, {})


	def get_list(self, skip = 0, limit = None, order_by = None):
		return self.database_client.find_many(self.table, {}, skip = skip, limit = limit, order_by = order_by)


	def get(self, worker_identifier):
		return self.database_client.find_one(self.table, { "identifier": worker_identifier })


	def create(self, worker_identifier, owner):
		worker = {
			"identifier": worker_identifier,
			"owner": owner,
			"properties": {},
			"is_enabled": True,
			"is_active": False,
			"creation_date": datetime.datetime.utcnow().replace(microsecond = 0).isoformat() + "Z",
			"update_date": datetime.datetime.utcnow().replace(microsecond = 0).isoformat() + "Z",
		}

		self.database_client.insert_one(self.table, worker)
		return worker


	def update_status(self, worker, is_active = None, is_enabled = None):
		update_data = {}
		if is_active is not None:
			update_data["is_active"] = is_active
		if is_enabled is not None:
			update_data["is_enabled"] = is_enabled
		update_data["update_date"] = datetime.datetime.utcnow().replace(microsecond = 0).isoformat() + "Z"
		worker.update(update_data)
		self.database_client.update_one(self.table, { "identifier": worker["identifier"] }, update_data)


	def update_properties(self, worker, properties):
		update_data = {
			"properties": properties,
			"update_date": datetime.datetime.utcnow().replace(microsecond = 0).isoformat() + "Z",
		}

		worker.update(update_data)
		self.database_client.update_one(self.table, { "identifier": worker["identifier"] }, update_data)


	def delete(self, worker_identifier, run_provider):
		worker_record = self.get(worker_identifier)
		if worker_record is None:
			raise ValueError("Worker '%s' does not exist" % worker_identifier)

		if worker_record["is_enabled"]:
			raise ValueError("Worker '%s' is enabled" % worker_identifier)
		if worker_record["is_active"]:
			raise ValueError("Worker '%s' is active" % worker_identifier)

		if run_provider.count(worker = worker_identifier, status = "pending") > 0:
			raise ValueError("Worker '%s' has pending runs" % worker_identifier)
		if run_provider.count(worker = worker_identifier, status = "running") > 0:
			raise ValueError("Worker '%s' has running runs" % worker_identifier)

		self.database_client.delete_one(self.table, { "identifier": worker_identifier })
