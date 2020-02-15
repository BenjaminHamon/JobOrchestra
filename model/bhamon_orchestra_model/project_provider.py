import logging


logger = logging.getLogger("ProjectProvider")


class ProjectProvider:


	def __init__(self, database_client, date_time_provider):
		self.database_client = database_client
		self.date_time_provider = date_time_provider
		self.table = "project"


	def count(self):
		return self.database_client.count(self.table, {})


	def get_list(self, skip = 0, limit = None, order_by = None):
		return self.database_client.find_many(self.table, {}, skip = skip, limit = limit, order_by = order_by)


	def get(self, project_identifier):
		return self.database_client.find_one(self.table, { "identifier": project_identifier })


	def create_or_update(self, project_identifier, services):
		now = self.date_time_provider.now()
		project = self.get(project_identifier)

		if project is None:
			project = {
				"identifier": project_identifier,
				"services": services,
				"creation_date": self.date_time_provider.serialize(now),
				"update_date": self.date_time_provider.serialize(now),
			}

			self.database_client.insert_one(self.table, project)

		else:
			update_data = {
				"services": services,
				"update_date": self.date_time_provider.serialize(now),
			}

			project.update(update_data)
			self.database_client.update_one(self.table, { "identifier": project_identifier }, update_data)

		return project
