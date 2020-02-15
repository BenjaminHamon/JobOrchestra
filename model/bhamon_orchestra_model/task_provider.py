import logging
import uuid


logger = logging.getLogger("TaskProvider")


class TaskProvider:


	def __init__(self, database_client, date_time_provider):
		self.database_client = database_client
		self.date_time_provider = date_time_provider
		self.table = "task"


	def count(self, type = None, status = None, run = None, worker = None): # pylint: disable = redefined-builtin
		filter = { "type": type, "status": status, "parameters.run_identifier": run, "parameters.worker_identifier": worker } # pylint: disable = redefined-builtin
		filter = { key: value for key, value in filter.items() if value is not None }
		return self.database_client.count(self.table, filter)


	def get_list( # pylint: disable = too-many-arguments
			self, type = None, status = None, run = None, worker = None, skip = 0, limit = None, order_by = None): # pylint: disable = redefined-builtin
		filter = { "type": type, "status": status, "parameters.run_identifier": run, "parameters.worker_identifier": worker } # pylint: disable = redefined-builtin
		filter = { key: value for key, value in filter.items() if value is not None }
		return self.database_client.find_many(self.table, filter, skip = skip, limit = limit, order_by = order_by)


	def get(self, task_identifier):
		return self.database_client.find_one(self.table, { "identifier": task_identifier })


	def create(self, type, parameters): # pylint: disable = redefined-builtin
		now = self.date_time_provider.now()

		task = {
			"identifier": str(uuid.uuid4()),
			"type": type,
			"parameters": parameters,
			"status": "pending",
			"should_cancel": False,
			"creation_date": self.date_time_provider.serialize(now),
			"update_date": self.date_time_provider.serialize(now),
		}

		self.database_client.insert_one(self.table, task)
		return task


	def update_status(self, task, status = None, should_cancel = None):
		now = self.date_time_provider.now()

		update_data = {
			"status": status,
			"should_cancel": should_cancel,
			"update_date": self.date_time_provider.serialize(now),
		}

		update_data = { key: value for key, value in update_data.items() if value is not None }

		task.update(update_data)
		self.database_client.update_one(self.table, { "identifier": task["identifier"] }, task)
