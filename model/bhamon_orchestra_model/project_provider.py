import logging

from typing import List, Optional, Tuple

from bhamon_orchestra_model.database.database_client import DatabaseClient
from bhamon_orchestra_model.date_time_provider import DateTimeProvider


logger = logging.getLogger("ProjectProvider")


class ProjectProvider:


	def __init__(self, database_client: DatabaseClient, date_time_provider: DateTimeProvider) -> None:
		self.database_client = database_client
		self.date_time_provider = date_time_provider
		self.table = "project"


	def count(self) -> int:
		return self.database_client.count(self.table, {})


	def get_list(self, skip: int = 0, limit: Optional[int] = None, order_by: Optional[Tuple[str,str]] = None) -> List[dict]:
		return self.database_client.find_many(self.table, {}, skip = skip, limit = limit, order_by = order_by)


	def get(self, project_identifier: str) -> Optional[dict]:
		return self.database_client.find_one(self.table, { "identifier": project_identifier })


	def create_or_update(self, project_identifier: str, services: dict) -> dict:
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
