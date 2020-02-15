import logging
import re


logger = logging.getLogger("UserProvider")


class UserProvider:


	def __init__(self, database_client, date_time_provider):
		self.database_client = database_client
		self.date_time_provider = date_time_provider
		self.table = "user"
		self.user_identifier_regex = re.compile(r"^[a-zA-Z0-9_\-\.]{3,32}$")


	def count(self):
		return self.database_client.count(self.table, {})


	def get_list(self, skip = 0, limit = None, order_by = None):
		return self.database_client.find_many(self.table, {}, skip = skip, limit = limit, order_by = order_by)


	def get(self, user_identifier):
		return self.database_client.find_one(self.table, { "identifier": user_identifier })


	def create(self, user_identifier, display_name):
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


	def update_identity(self, user, display_name = None):
		now = self.date_time_provider.now()

		update_data = {}
		if display_name is not None:
			update_data["display_name"] = display_name
		update_data["update_date"] = self.date_time_provider.serialize(now)

		user.update(update_data)
		self.database_client.update_one(self.table, { "identifier": user["identifier"] }, user)


	def update_roles(self, user, roles):
		now = self.date_time_provider.now()

		update_data = {
			"roles": roles,
			"update_date": self.date_time_provider.serialize(now),
		}

		user.update(update_data)
		self.database_client.update_one(self.table, { "identifier": user["identifier"] }, user)


	def update_status(self, user, is_enabled = None):
		now = self.date_time_provider.now()

		update_data = {}
		if is_enabled is not None:
			update_data["is_enabled"] = is_enabled
		update_data["update_date"] = self.date_time_provider.serialize(now)

		user.update(update_data)
		self.database_client.update_one(self.table, { "identifier": user["identifier"] }, user)
