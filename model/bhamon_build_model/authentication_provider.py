# pylint: disable = redefined-builtin

import datetime
import hashlib
import hmac
import logging
import secrets
import uuid


logger = logging.getLogger("AuthenticationProvider")


class AuthenticationProvider:


	def __init__(self, database_client):
		self.database_client = database_client
		self.table = "user_authentication"

		self.password_salt_size = 32
		self.password_hash_function = "pbkdf2"
		self.password_hash_function_parameters = { "hash_name": "sha256", "iterations": 1000 * 1000 }

		self.token_size = 32
		self.token_hash_function = "sha256"
		self.token_hash_function_parameters = {}


	def set_password(self, user, password):
		now = datetime.datetime.utcnow().replace(microsecond = 0)
		authentication = self.database_client.find_one(self.table, { "user": user, "type": "password" })

		if authentication is None:
			authentication = {
				"identifier": str(uuid.uuid4()),
				"user": user,
				"type": "password",
				"creation_date": now.isoformat() + "Z",
				"update_date": now.isoformat() + "Z",
			}

			self.database_client.insert_one(self.table, authentication)

		authentication.update({
			"hash_function": self.password_hash_function,
			"hash_function_parameters": self.password_hash_function_parameters,
			"hash_function_salt": secrets.token_hex(self.password_salt_size),
			"update_date": now.isoformat() + "Z",
		})

		authentication["secret"] = self.hash_password(password, authentication["hash_function_salt"], authentication["hash_function"], authentication["hash_function_parameters"])

		self.database_client.update_one(self.table, { "identifier": authentication["identifier"] }, authentication)
		return self.convert_for_public_eyes(authentication)


	def remove_password(self, user):
		self.database_client.delete_one(self.table, { "user": user, "type": "password" })


	def authenticate_with_password(self, user_identifier, password):
		authentication = self.database_client.find_one(self.table, { "user": user_identifier, "type": "password" })
		if authentication is None:
			return False
		hashed_password = self.hash_password(password, authentication["hash_function_salt"], authentication["hash_function"], authentication["hash_function_parameters"])
		return hmac.compare_digest(hashed_password, authentication["secret"])


	def authenticate_with_token(self, user_identifier, token_identifier, secret):
		token = self.database_client.find_one(self.table, { "identifier": token_identifier, "user": user_identifier, "type": "token" })
		if token is None:
			return False
		hashed_secret = self.hash_token(secret, token["hash_function"], token["hash_function_parameters"])
		return hashed_secret == token["secret"]


	def count_tokens(self, user = None):
		filter = { "user": user, "type": "token" }
		filter = { key: value for key, value in filter.items() if value is not None }
		return self.database_client.count(self.table, filter)


	def get_token_list(self, user = None, skip = 0, limit = None, order_by = None):
		filter = { "user": user, "type": "token" }
		filter = { key: value for key, value in filter.items() if value is not None }
		token_list = self.database_client.find_many(self.table, filter, skip = skip, limit = limit, order_by = order_by)
		return [ self.convert_for_public_eyes(token) for token in token_list ]


	def get_token(self, user_identifier, token_identifier):
		token = self.database_client.find_one(self.table, { "identifier": token_identifier, "user": user_identifier, "type": "token" })
		return self.convert_for_public_eyes(token)


	def create_token(self, user, description, expiration):
		now = datetime.datetime.utcnow().replace(microsecond = 0)

		token = {
			"identifier": str(uuid.uuid4()),
			"user": user,
			"type": "token",
			"description": description,
			"hash_function": self.token_hash_function,
			"hash_function_parameters": self.token_hash_function_parameters,
			"creation_date": now.isoformat() + "Z",
			"update_date": now.isoformat() + "Z",
		}

		if expiration is not None:
			token["expiration_date"] = (now + expiration).isoformat() + "Z"

		secret = secrets.token_hex(self.token_size)
		token["secret"] = self.hash_token(secret, token["hash_function"], token["hash_function_parameters"])

		self.database_client.insert_one(self.table, token)
		result = self.convert_for_public_eyes(token)
		result["secret"] = secret
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
		self.database_client.delete_one(self.table, { "identifier": token_identifier, "user": user_identifier, "type": "token" })


	def hash_password(self, password, salt, function, parameters): # pylint: disable = no-self-use
		if function == "pbkdf2":
			return hashlib.pbkdf2_hmac(password = password.encode("utf-8"), salt = bytes.fromhex(salt), **parameters).hex()
		raise ValueError("Unsupported hash function '%s'" % function)


	def hash_token(self, token, function, parameters): # pylint: disable = no-self-use
		if function == "sha256":
			return hashlib.sha256(bytes.fromhex(token)).hexdigest()
		raise ValueError("Unsupported hash function '%s'" % function)


	def convert_for_public_eyes(self, authentication): # pylint: disable = no-self-use
		keys_to_return = [ "identifier", "user", "type", "description", "expiration_date", "creation_date", "update_date" ]
		return { key: value for key, value in authentication.items() if key in keys_to_return }
