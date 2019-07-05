import datetime
import logging
import re


logger = logging.getLogger("UserProvider")


class UserProvider:


	def __init__(self, database_client):
		self.database_client = database_client
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

		user = {
			"identifier": user_identifier,
			"display_name": display_name,
			"is_enabled": True,
			"creation_date": datetime.datetime.utcnow().replace(microsecond = 0).isoformat() + "Z",
			"update_date": datetime.datetime.utcnow().replace(microsecond = 0).isoformat() + "Z",
		}

		self.database_client.insert_one(self.table, user)
		return user


	def update(self, user, display_name = None):
		update_data = {}
		if display_name is not None:
			update_data["display_name"] = display_name
		update_data["update_date"] = datetime.datetime.utcnow().replace(microsecond = 0).isoformat() + "Z"
		user.update(update_data)
		self.database_client.update_one(self.table, { "identifier": user["identifier"] }, user)


	def update_status(self, user, is_enabled = None):
		update_data = {}
		if is_enabled is not None:
			update_data["is_enabled"] = is_enabled
		update_data["update_date"] = datetime.datetime.utcnow().replace(microsecond = 0).isoformat() + "Z"
		user.update(update_data)
		self.database_client.update_one(self.table, { "identifier": user["identifier"] }, user)
