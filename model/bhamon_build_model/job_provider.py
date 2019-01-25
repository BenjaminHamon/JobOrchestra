import datetime
import logging


logger = logging.getLogger("JobProvider")


class JobProvider:


	def __init__(self, database_client):
		self.database_client = database_client
		self.table = "job"


	def get_list(self):
		return self.database_client.find_many(self.table, {})


	def get(self, job_identifier):
		return self.database_client.find_one(self.table, { "identifier": job_identifier })


	def create_or_update(self, job_identifier, workspace, steps, parameters, properties, description):
		job = self.get(job_identifier)

		if job is None:
			job = {
				"identifier": job_identifier,
				"workspace": workspace,
				"steps": steps,
				"parameters": parameters,
				"properties": properties,
				"description": description,
				"is_enabled": True,
				"creation_date": datetime.datetime.utcnow().replace(microsecond = 0).isoformat(),
				"update_date": datetime.datetime.utcnow().replace(microsecond = 0).isoformat(),
			}
			self.database_client.insert_one(self.table, job)

		else:
			update_data = {
				"workspace": workspace,
				"steps": steps,
				"parameters": parameters,
				"properties": properties,
				"description": description,
				"update_date": datetime.datetime.utcnow().replace(microsecond = 0).isoformat(),
			}
			self.database_client.update_one(self.table, { "identifier": job_identifier }, update_data)


	def update_status(self, job, is_enabled = None):
		update_data = {}
		if is_enabled is not None:
			update_data["is_enabled"] = is_enabled
		update_data["update_date"] = datetime.datetime.utcnow().replace(microsecond = 0).isoformat()
		job.update(update_data)
		self.database_client.update_one(self.table, { "identifier": job["identifier"] }, job)


	def delete(self, job_identifier):
		return self.database_client.delete_one(self.table, { "identifier": job_identifier })
