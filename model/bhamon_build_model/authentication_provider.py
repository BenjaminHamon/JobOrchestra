# pylint: disable = redefined-builtin

import copy
import datetime
import hashlib
import logging
import secrets
import uuid


logger = logging.getLogger("AuthenticationProvider")


class AuthenticationProvider:


	def __init__(self, database_client):
		self.database_client = database_client
		self.table = "user_authentication"
		self.token_size = 32
		self.salt_size = 32
		self.hash_function = "pbkdf2"
		self.hash_function_parameters = { "hash_name": "sha256", "iterations": 1000 * 1000 }


	def count_tokens(self, user = None):
		filter = { "user": user, "type": "token" }
		filter = { key: value for key, value in filter.items() if value is not None }
		return self.database_client.count(self.table, filter)


	def get_token_list(self, user = None, skip = 0, limit = None, order_by = None):
		filter = { "user": user, "type": "token" }
		filter = { key: value for key, value in filter.items() if value is not None }
		token_results = self.database_client.find_many(self.table, filter, skip = skip, limit = limit, order_by = order_by)
		return [ self.convert_token_for_public_eyes(token) for token in token_results ]


	def get_token(self, user_identifier, token_identifier):
		token = self.database_client.find_one(self.table, { "identifier": token_identifier, "user": user_identifier, "type": "token" })
		return self.convert_token_for_public_eyes(token)


	def create_token(self, user, description, expiration):
		hash_function_parameters = copy.deepcopy(self.hash_function_parameters)
		hash_function_parameters.update({ "salt": secrets.token_hex(self.salt_size) })

		raw_secret = secrets.token_hex(self.token_size)
		protected_secret = self.hash_secret(raw_secret, hash_function_parameters["salt"])

		now = datetime.datetime.utcnow().replace(microsecond = 0)

		token = {
			"identifier": str(uuid.uuid4()),
			"user": user,
			"type": "token",
			"description": description,
			"hash_function": self.hash_function,
			"hash_function_parameters": hash_function_parameters,
			"secret": protected_secret,
			"creation_date": now.isoformat() + "Z",
			"update_date": now.isoformat() + "Z",
		}

		if expiration is not None:
			token["expiration_date"] = (now + expiration).isoformat() + "Z"

		self.database_client.insert_one(self.table, token)
		result = self.convert_token_for_public_eyes(token)
		result["secret"] = raw_secret
		return result


	def refresh_token(self, user_identifier, token_identifier, expiration):
		token = self.database_client.find_one(self.table, { "identifier": token_identifier, "user": user_identifier, "type": "token" })
		if "expiration_date" not in token:
			raise ValueError("Token '%s' does not expire" % token_identifier)

		now = datetime.datetime.utcnow().replace(microsecond = 0)

		update_data = {
			"expiration_date": (now + expiration).isoformat() + "Z",
			"update_date": now.isoformat() + "Z",
		}

		self.database_client.update_one(self.table, { "identifier": token_identifier, "user": user_identifier, "type": "token" }, update_data)


	def delete_token(self, user_identifier, token_identifier):
		return self.database_client.delete_one(self.table, { "identifier": token_identifier, "user": user_identifier, "type": "token" })


	def hash_secret(self, secret, salt):
		if self.hash_function == "pbkdf2":
			return hashlib.pbkdf2_hmac(password = bytes.fromhex(secret), salt = bytes.fromhex(salt), **self.hash_function_parameters).hex()
		raise ValueError("Unsupported hash function '%s'" % self.hash_function)


	def convert_token_for_public_eyes(self, token): # pylint: disable = no-self-use
		keys_to_return = [ "identifier", "user", "description", "expiration_date", "creation_date", "update_date" ]
		return { key: value for key, value in token.items() if key in keys_to_return }
