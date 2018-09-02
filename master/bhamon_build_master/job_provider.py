import datetime


class JobProvider:


	def __init__(self, database_client):
		self.database_client = database_client
		self.table = "job"


	def get_all(self):
		return self.database_client.get_all(self.table)


	def get(self, job_identifier):
		return self.database_client.get(self.table, job_identifier)


	def create_or_update(self, job_identifier, workspace, steps, parameters, properties, workers, description):
		try:
			job = self.get(job_identifier)
			job["workspace"] = workspace
			job["steps"] = steps
			job["parameters"] = parameters
			job["properties"] = properties
			job["workers"] = workers
			job["description"] = description
			job["update_date"] = datetime.datetime.utcnow().replace(microsecond = 0).isoformat()
			self.database_client.update(self.table, job_identifier, job)

		except KeyError:
			job = {
				"identifier": job_identifier,
				"workspace": workspace,
				"steps": steps,
				"parameters": parameters,
				"properties": properties,
				"workers": workers,
				"description": description,
				"is_enabled": True,
				"creation_date": datetime.datetime.utcnow().replace(microsecond = 0).isoformat(),
				"update_date": datetime.datetime.utcnow().replace(microsecond = 0).isoformat(),
			}
			self.database_client.create(self.table, job_identifier, job)


	def delete(self, job_identifier):
		return self.database_client.delete(self.table, job_identifier)
