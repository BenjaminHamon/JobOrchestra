import datetime


class WorkerProvider:


	def __init__(self, database_client):
		self.database_client = database_client


	def get_all(self):
		return self.database_client.get_all()


	def get(self, worker_identifier):
		return self.database_client.get(worker_identifier)


	def exists(self, worker_identifier):
		return self.database_client.exists(worker_identifier)


	def create_or_update(self, worker_identifier, description):
		try:
			worker = self.get(worker_identifier)
			worker["description"] = description
			worker["update_date"] = datetime.datetime.utcnow().replace(microsecond = 0).isoformat()
			self.database_client.update(worker_identifier, worker)
		
		except KeyError:
			worker = {
				"identifier": worker_identifier,
				"description": description,
				"is_enabled": True,
				"is_active": False,
				"creation_date": datetime.datetime.utcnow().replace(microsecond = 0).isoformat(),
				"update_date": datetime.datetime.utcnow().replace(microsecond = 0).isoformat(),
			}
			self.database_client.create(worker_identifier, worker)
