import logging
from typing import Any

import flask

from bhamon_orchestra_model.authentication_provider import AuthenticationProvider
from bhamon_orchestra_model.user_provider import UserProvider
from bhamon_orchestra_service.user_controller import UserController


logger = logging.getLogger("MeController")


class MeController:


	def __init__(self, authentication_provider: AuthenticationProvider, user_provider: UserProvider, user_controller: UserController) -> None:
		self._authentication_provider = authentication_provider
		self._user_provider = user_provider
		self._user_controller = user_controller


	def get_user(self) -> Any:
		database_client = flask.request.database_client()
		return flask.jsonify(self._user_provider.get(database_client, flask.request.authorization.username))


	def login(self) -> Any:
		parameters = flask.request.get_json()
		database_client = flask.request.database_client()

		if not self._authentication_provider.authenticate_with_password(database_client, parameters["user"], parameters["password"]):
			flask.abort(401)

		token_parameters = {
			"user": parameters["user"],
			"description": "Session from %s" % flask.request.environ["REMOTE_ADDR"],
			"expiration": flask.current_app.permanent_session_lifetime,
		}

		session_token = self._authentication_provider.create_token(database_client, **token_parameters)
		return flask.jsonify({ "user_identifier": session_token["user"], "token_identifier": session_token["identifier"], "secret": session_token["secret"] })


	def logout(self) -> Any:
		if flask.request.authorization is not None:
			parameters = flask.request.get_json()
			database_client = flask.request.database_client()
			self._authentication_provider.delete_token(database_client, flask.request.authorization.username, parameters["token_identifier"])

		return flask.jsonify({})


	def refresh_session(self) -> Any:
		parameters = flask.request.get_json()
		database_client = flask.request.database_client()

		operation_parameters = {
			"user_identifier": flask.request.authorization.username,
			"token_identifier": parameters["token_identifier"],
			"expiration": flask.current_app.permanent_session_lifetime,
		}

		self._authentication_provider.set_token_expiration(database_client, **operation_parameters)
		return flask.jsonify({})


	def change_password(self) -> Any:
		parameters = flask.request.get_json()
		database_client = flask.request.database_client()

		if not self._authentication_provider.authenticate_with_password(database_client, flask.request.authorization.username, parameters["old_password"]):
			flask.abort(401)

		self._authentication_provider.set_password(database_client, flask.request.authorization.username, parameters["new_password"])
		return flask.jsonify({})


	def get_token_list(self) -> Any:
		return self._user_controller.get_token_list(flask.request.authorization.username)


	def create_token(self) -> Any:
		return self._user_controller.create_token(flask.request.authorization.username)


	def delete_token(self, token_identifier: str) -> Any:
		return self._user_controller.delete_token(flask.request.authorization.username, token_identifier)
