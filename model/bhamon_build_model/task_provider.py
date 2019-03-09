# pylint: disable=redefined-builtin

import datetime
import logging
import uuid


logger = logging.getLogger("TaskProvider")


class TaskProvider:


	def __init__(self, database_client):
		self.database_client = database_client
		self.table = "task"


	def count(self, type = None, status = None, build = None, worker = None):
		filter = { "type": type, "status": status, "parameters.build_identifier": build, "parameters.worker_identifier": worker }
		filter = { key: value for key, value in filter.items() if value is not None }
		return self.database_client.count(self.table, filter)


	def get_list(self, type = None, status = None, build = None, worker = None, skip = 0, limit = None, order_by = None):
		filter = { "type": type, "status": status, "parameters.build_identifier": build, "parameters.worker_identifier": worker }
		filter = { key: value for key, value in filter.items() if value is not None }
		return self.database_client.find_many(self.table, filter, skip = skip, limit = limit, order_by = order_by)


	def get(self, task_identifier):
		return self.database_client.find_one(self.table, { "identifier": task_identifier })


	def create(self, type, parameters):
		task = {
			"identifier": str(uuid.uuid4()),
			"type": type,
			"parameters": parameters,
			"status": "pending",
			"should_cancel": False,
			"creation_date": datetime.datetime.utcnow().replace(microsecond = 0).isoformat() + "Z",
			"update_date": datetime.datetime.utcnow().replace(microsecond = 0).isoformat() + "Z",
		}

		self.database_client.insert_one(self.table, task)
		return task


	def update_status(self, task, status = None, should_cancel = None):
		update_data = {}
		if status is not None:
			update_data["status"] = status
		if should_cancel is not None:
			update_data["should_cancel"] = should_cancel
		update_data["update_date"] = datetime.datetime.utcnow().replace(microsecond = 0).isoformat() + "Z"
		task.update(update_data)
		self.database_client.update_one(self.table, { "identifier": task["identifier"] }, task)
