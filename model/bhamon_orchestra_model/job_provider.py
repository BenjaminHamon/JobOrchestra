import logging


logger = logging.getLogger("JobProvider")


class JobProvider:


	def __init__(self, database_client, date_time_provider):
		self.database_client = database_client
		self.date_time_provider = date_time_provider
		self.table = "job"


	def count(self, project = None):
		filter = { "project": project } # pylint: disable = redefined-builtin
		filter = { key: value for key, value in filter.items() if value is not None }
		return self.database_client.count(self.table, filter)


	def get_list(self, project = None, skip = 0, limit = None, order_by = None):
		filter = { "project": project } # pylint: disable = redefined-builtin
		filter = { key: value for key, value in filter.items() if value is not None }
		return self.database_client.find_many(self.table, filter, skip = skip, limit = limit, order_by = order_by)


	def get(self, job_identifier):
		return self.database_client.find_one(self.table, { "identifier": job_identifier })


	def create_or_update( # pylint: disable = too-many-arguments
			self, job_identifier, project, workspace, steps, parameters, properties, description):
		now = self.date_time_provider.now()
		job = self.get(job_identifier)

		if job is None:
			job = {
				"identifier": job_identifier,
				"project": project,
				"workspace": workspace,
				"steps": steps,
				"parameters": parameters,
				"properties": properties,
				"description": description,
				"is_enabled": True,
				"creation_date": self.date_time_provider.serialize(now),
				"update_date": self.date_time_provider.serialize(now),
			}

			self.database_client.insert_one(self.table, job)

		else:
			update_data = {
				"project": project,
				"workspace": workspace,
				"steps": steps,
				"parameters": parameters,
				"properties": properties,
				"description": description,
				"update_date": self.date_time_provider.serialize(now),
			}

			job.update(update_data)
			self.database_client.update_one(self.table, { "identifier": job_identifier }, update_data)

		return job


	def update_status(self, job, is_enabled = None):
		now = self.date_time_provider.now()

		update_data = {
			"is_enabled": is_enabled,
			"update_date": self.date_time_provider.serialize(now),
		}

		update_data = { key: value for key, value in update_data.items() if value is not None }

		job.update(update_data)
		self.database_client.update_one(self.table, { "identifier": job["identifier"] }, update_data)


	def delete(self, job_identifier):
		self.database_client.delete_one(self.table, { "identifier": job_identifier })
