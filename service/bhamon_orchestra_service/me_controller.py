import logging
from typing import Any

import flask

import bhamon_orchestra_service.user_controller as user_controller


logger = logging.getLogger("MeController")


def get_user() -> Any:
	database_client = flask.request.database_client()
	return flask.jsonify(flask.current_app.user_provider.get(database_client, flask.request.authorization.username))


def login() -> Any:
	parameters = flask.request.get_json()
	database_client = flask.request.database_client()

	if not flask.current_app.authentication_provider.authenticate_with_password(database_client, parameters["user"], parameters["password"]):
		flask.abort(401)

	token_parameters = {
		"user": parameters["user"],
		"description": "Session from %s" % flask.request.environ["REMOTE_ADDR"],
		"expiration": flask.current_app.permanent_session_lifetime,
	}

	session_token = flask.current_app.authentication_provider.create_token(database_client, **token_parameters)
	return flask.jsonify({ "user_identifier": session_token["user"], "token_identifier": session_token["identifier"], "secret": session_token["secret"] })


def logout() -> Any:
	if flask.request.authorization is not None:
		parameters = flask.request.get_json()
		database_client = flask.request.database_client()
		flask.current_app.authentication_provider.delete_token(database_client, flask.request.authorization.username, parameters["token_identifier"])

	return flask.jsonify({})


def refresh_session() -> Any:
	parameters = flask.request.get_json()
	database_client = flask.request.database_client()

	operation_parameters = {
		"user_identifier": flask.request.authorization.username,
		"token_identifier": parameters["token_identifier"],
		"expiration": flask.current_app.permanent_session_lifetime,
	}

	flask.current_app.authentication_provider.set_token_expiration(database_client, **operation_parameters)
	return flask.jsonify({})


def change_password() -> Any:
	parameters = flask.request.get_json()
	database_client = flask.request.database_client()

	if not flask.current_app.authentication_provider.authenticate_with_password(database_client, flask.request.authorization.username, parameters["old_password"]):
		flask.abort(401)

	flask.current_app.authentication_provider.set_password(database_client, flask.request.authorization.username, parameters["new_password"])
	return flask.jsonify({})


def get_token_list() -> Any:
	return user_controller.get_token_list(flask.request.authorization.username)


def create_token() -> Any:
	return user_controller.create_token(flask.request.authorization.username)


def delete_token(token_identifier: str) -> Any:
	return user_controller.delete_token(flask.request.authorization.username, token_identifier)
