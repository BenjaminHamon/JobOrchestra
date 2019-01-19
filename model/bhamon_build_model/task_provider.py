import datetime
import uuid


class TaskProvider:


	def __init__(self, database_client):
		self.database_client = database_client
		self.table = "task"


	def get_all(self):
		return self.database_client.get_all(self.table)


	def get_all_for_build(self, build_identifier):
		all_tasks = self.get_all()
		condition = lambda task: task["parameters"].get("build_identifier", None) == build_identifier
		return { task_identifier: task for task_identifier, task in all_tasks.items() if condition(task) }


	def get_all_for_worker(self, worker_identifier):
		all_tasks = self.get_all()
		condition = lambda task: task["parameters"].get("worker_identifier", None) == worker_identifier
		return { task_identifier: task for task_identifier, task in all_tasks.items() if condition(task) }


	def get(self, task_identifier):
		return self.database_client.get(self.table, task_identifier)


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

		self.database_client.create(self.table, task["identifier"], task)
		return task


	def update(self, task, status = None, should_cancel = None):
		if status is not None:
			task["status"] = status
		if should_cancel is not None:
			task["should_cancel"] = should_cancel
		task["update_date"] = datetime.datetime.utcnow().replace(microsecond = 0).isoformat()
		self.database_client.update(self.table, task["identifier"], task)
		return task
