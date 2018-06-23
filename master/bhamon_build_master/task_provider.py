import datetime
import uuid


class TaskProvider:


	def __init__(self, database_client):
		self.database_client = database_client


	def get_all(self):
		return self.database_client.get_all()


	def create(self, type, parameters):
		task = {
			"identifier": str(uuid.uuid4()),
			"type": type,
			"parameters": parameters,
			"status": "pending",
			"creation_date": datetime.datetime.utcnow().replace(microsecond = 0).isoformat(),
			"update_date": datetime.datetime.utcnow().replace(microsecond = 0).isoformat(),
		}

		return self.database_client.create(task["identifier"], task)


	def update(self, task):
		task["update_date"] = datetime.datetime.utcnow().replace(microsecond = 0).isoformat()
		self.database_client.update(task["identifier"], task)


	def cancel(self, task_identifier):
		pass
