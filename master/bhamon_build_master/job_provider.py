import datetime


class JobProvider:


	def __init__(self, database_client):
		self.database_client = database_client


	def get_all(self):
		return self.database_client.get_all()


	def get(self, job_identifier):
		return self.database_client.get(job_identifier)


	def create_or_update(self, job_identifier, description, parameters):
		try:
			job = self.get(job_identifier)
			job["description"] = description
			job["parameters"] = parameters
			job["update_date"] = datetime.datetime.utcnow().replace(microsecond = 0).isoformat()
			self.database_client.update(job_identifier, job)
		
		except KeyError:
			job = {
				"identifier": job_identifier,
				"description": description,
				"is_enabled": True,
				"creation_date": datetime.datetime.utcnow().replace(microsecond = 0).isoformat(),
				"update_date": datetime.datetime.utcnow().replace(microsecond = 0).isoformat(),
			}
			self.database_client.create(job_identifier, job)
