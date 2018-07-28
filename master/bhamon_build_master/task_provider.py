import datetime
import uuid


class TaskProvider:


	def __init__(self, database_client):
		self.database_client = database_client


	def get_all(self):
		return self.database_client.get_all()


	def get(self, task_identifier):
		return self.database_client.get(task_identifier)


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

		self.database_client.create(task["identifier"], task)
		return task


	def update(self, task, status = None, should_cancel = None):
		if status is not None:
			task["status"] = status
		if should_cancel is not None:
			task["should_cancel"] = should_cancel
		task["update_date"] = datetime.datetime.utcnow().replace(microsecond = 0).isoformat()
		self.database_client.update(task["identifier"], task)
		return task
