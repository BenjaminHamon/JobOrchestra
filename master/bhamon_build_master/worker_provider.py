import datetime


class WorkerProvider:


	def __init__(self, database_client):
		self.database_client = database_client
		self.table = "worker"


	def get_all(self):
		return self.database_client.get_all(self.table)


	def get(self, worker_identifier):
		return self.database_client.get(self.table, worker_identifier)


	def exists(self, worker_identifier):
		return self.database_client.exists(self.table, worker_identifier)


	def create_or_update(self, worker_identifier, description):
		try:
			worker = self.get(worker_identifier)
			worker["description"] = description
			worker["update_date"] = datetime.datetime.utcnow().replace(microsecond = 0).isoformat()
			self.database_client.update(self.table, worker_identifier, worker)
		
		except KeyError:
			worker = {
				"identifier": worker_identifier,
				"description": description,
				"is_enabled": True,
				"is_active": False,
				"creation_date": datetime.datetime.utcnow().replace(microsecond = 0).isoformat(),
				"update_date": datetime.datetime.utcnow().replace(microsecond = 0).isoformat(),
			}
			self.database_client.create(self.table, worker_identifier, worker)


	def update(self, worker_identifier, is_active = None, is_enabled = None):
		worker = self.get(worker_identifier)
		if is_active is not None:
			worker["is_active"] = is_active
		if is_enabled is not None:
			worker["is_enabled"] = is_enabled
		worker["update_date"] = datetime.datetime.utcnow().replace(microsecond = 0).isoformat()
		self.database_client.update(self.table, worker_identifier, worker)
