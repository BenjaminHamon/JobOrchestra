import logging
from typing import Any

import flask


from bhamon_orchestra_model.authentication_provider import AuthenticationProvider
import bhamon_orchestra_model.datetime_extensions as datetime_extensions
from bhamon_orchestra_model.user_provider import UserProvider
from bhamon_orchestra_service.response_builder import ResponseBuilder


logger = logging.getLogger("UserController")


class UserController:


	def __init__(self, response_builder: ResponseBuilder,
			authentication_provider: AuthenticationProvider, user_provider: UserProvider) -> None:

		self._response_builder = response_builder
		self._authentication_provider = authentication_provider
		self._user_provider = user_provider


	def get_count(self) -> Any:
		database_client = flask.request.database_client()
		user_count = self._user_provider.count(database_client)
		return self._response_builder.create_data_response(user_count)


	def get_collection(self) -> Any:
		query_parameters = {
			"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
			"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
			"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
		}

		database_client = flask.request.database_client()
		user_collection = self._user_provider.get_list(database_client, **query_parameters)
		return self._response_builder.create_data_response(user_collection)


	def get(self, user_identifier: str) -> Any:
		database_client = flask.request.database_client()
		user = self._user_provider.get(database_client, user_identifier)
		return self._response_builder.create_data_response(user)


	def create(self, user_identifier: str) -> Any:
		parameters = flask.request.get_json()
		database_client = flask.request.database_client()
		user = self._user_provider.create(database_client, user_identifier, parameters["display_name"])
		return self._response_builder.create_data_response(user)


	def update_identity(self, user_identifier: str) -> Any:
		parameters = flask.request.get_json()
		database_client = flask.request.database_client()
		user = self._user_provider.get(database_client, user_identifier)
		self._user_provider.update_identity(database_client, user, parameters["display_name"])
		return self._response_builder.create_data_response(user)


	def update_roles(self, user_identifier: str) -> Any:
		parameters = flask.request.get_json()
		database_client = flask.request.database_client()
		user = self._user_provider.get(database_client, user_identifier)
		self._user_provider.update_roles(database_client, user, roles = parameters["roles"])
		return self._response_builder.create_data_response(user)


	def reset_password(self, user_identifier: str) -> Any:
		parameters = flask.request.get_json()
		database_client = flask.request.database_client()
		self._authentication_provider.set_password(database_client, user_identifier, parameters["password"])
		return self._response_builder.create_empty_response()


	def enable(self, user_identifier: str) -> Any:
		database_client = flask.request.database_client()
		user = self._user_provider.get(database_client, user_identifier)
		self._user_provider.update_status(database_client, user, is_enabled = True)
		return self._response_builder.create_empty_response()


	def disable(self, user_identifier: str) -> Any:
		database_client = flask.request.database_client()
		user = self._user_provider.get(database_client, user_identifier)
		self._user_provider.update_status(database_client, user, is_enabled = False)
		return self._response_builder.create_empty_response()


	def get_token_count(self, user_identifier: str) -> Any:
		database_client = flask.request.database_client()
		token_count = self._authentication_provider.count_tokens(database_client, user = user_identifier)
		return self._response_builder.create_data_response(token_count)


	def get_token_list(self, user_identifier: str) -> Any:
		query_parameters = {
			"user": user_identifier,
			"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
			"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
			"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
		}

		database_client = flask.request.database_client()
		token_collection = self._authentication_provider.get_token_list(database_client, **query_parameters)
		return self._response_builder.create_data_response(token_collection)


	def create_token(self, user_identifier: str) -> Any:
		parameters = flask.request.get_json()
		description = parameters.get("description", None)
		expiration = parameters.get("expiration", None)

		if expiration is not None:
			expiration = datetime_extensions.parse_timedelta(expiration)

		database_client = flask.request.database_client()
		token = self._authentication_provider.create_token(database_client, user_identifier, description, expiration)
		response_data = { "token_identifier": token["identifier"], "secret": token["secret"] }
		return self._response_builder.create_data_response(response_data)


	def set_token_expiration(self, user_identifier: str, token_identifier: str) -> Any:
		parameters = flask.request.get_json()
		expiration = datetime_extensions.parse_timedelta(parameters["expiration"])
		database_client = flask.request.database_client()
		self._authentication_provider.set_token_expiration(database_client, user_identifier, token_identifier, expiration)
		return self._response_builder.create_empty_response()


	def delete_token(self, user_identifier: str, token_identifier: str) -> Any:
		database_client = flask.request.database_client()
		self._authentication_provider.delete_token(database_client, user_identifier, token_identifier)
		return self._response_builder.create_empty_response()
