import logging
import re

from typing import List, Optional, Tuple

from bhamon_orchestra_model.database.database_client import DatabaseClient
from bhamon_orchestra_model.date_time_provider import DateTimeProvider


logger = logging.getLogger("UserProvider")


class UserProvider:


	def __init__(self, database_client: DatabaseClient, date_time_provider: DateTimeProvider) -> None:
		self.database_client = database_client
		self.date_time_provider = date_time_provider
		self.table = "user"
		self.user_identifier_regex = re.compile(r"^[a-zA-Z0-9_\-\.]{3,32}$")


	def count(self) -> int:
		return self.database_client.count(self.table, {})


	def get_list(self, skip: int = 0, limit: Optional[int] = None, order_by: Optional[Tuple[str,str]] = None) -> List[dict]:
		return self.database_client.find_many(self.table, {}, skip = skip, limit = limit, order_by = order_by)


	def get(self, user_identifier: str) -> Optional[dict]:
		return self.database_client.find_one(self.table, { "identifier": user_identifier })


	def create(self, user_identifier: str, display_name: str) -> dict:
		if self.user_identifier_regex.search(user_identifier) is None:
			raise ValueError("User identifier is invalid: '%s'" % user_identifier)

		now = self.date_time_provider.now()

		user = {
			"identifier": user_identifier,
			"display_name": display_name,
			"roles": [],
			"is_enabled": True,
			"creation_date": self.date_time_provider.serialize(now),
			"update_date": self.date_time_provider.serialize(now),
		}

		self.database_client.insert_one(self.table, user)
		return user


	def update_identity(self, user: dict, display_name: Optional[str] = None) -> None:
		now = self.date_time_provider.now()

		update_data = {
			"display_name": display_name,
			"update_date": self.date_time_provider.serialize(now),
		}

		update_data = { key: value for key, value in update_data.items() if value is not None }

		user.update(update_data)
		self.database_client.update_one(self.table, { "identifier": user["identifier"] }, update_data)


	def update_roles(self, user: dict, roles: List[str]) -> None:
		now = self.date_time_provider.now()

		update_data = {
			"roles": roles,
			"update_date": self.date_time_provider.serialize(now),
		}

		user.update(update_data)
		self.database_client.update_one(self.table, { "identifier": user["identifier"] }, update_data)


	def update_status(self, user: dict, is_enabled: Optional[bool] = None) -> None:
		now = self.date_time_provider.now()

		update_data = {
			"is_enabled": is_enabled,
			"update_date": self.date_time_provider.serialize(now),
		}

		update_data = { key: value for key, value in update_data.items() if value is not None }

		user.update(update_data)
		self.database_client.update_one(self.table, { "identifier": user["identifier"] }, update_data)
