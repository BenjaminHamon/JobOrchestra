import datetime
import logging
import uuid


logger = logging.getLogger("TaskProvider")


class TaskProvider:


	def __init__(self, database_client):
		self.database_client = database_client
		self.table = "task"


	def get_list(self):
		return self.database_client.find_many(self.table, {})


	def get_list_for_build(self, build_identifier):
		return self.database_client.find_many(self.table, { "parameters.build_identifier": build_identifier })


	def get_list_for_worker(self, worker_identifier):
		return self.database_client.find_many(self.table, { "parameters.worker_identifier": worker_identifier })


	def get(self, task_identifier):
		return self.database_client.find_one(self.table, { "identifier": task_identifier })


	def create(self, type, parameters):
		task = {
			"identifier": str(uuid.uuid4()),
			"type": type,
			"parameters": parameters,
			"status": "pending",
			"should_cancel": False,
			"creation_date": datetime.datetime.utcnow().replace(microsecond = 0).isoformat(),
			"update_date": datetime.datetime.utcnow().replace(microsecond = 0).isoformat(),
		}

		self.database_client.insert_one(self.table, task)
		return task


	def update_status(self, task, status = None, should_cancel = None):
		update_data = {}
		if status is not None:
			update_data["status"] = status
		if should_cancel is not None:
			update_data["should_cancel"] = should_cancel
		update_data["update_date"] = datetime.datetime.utcnow().replace(microsecond = 0).isoformat()
		task.update(update_data)
		self.database_client.update_one(self.table, { "identifier": task["identifier"] }, task)
