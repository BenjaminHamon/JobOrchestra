import logging
from typing import Any

import flask

import bhamon_orchestra_model.datetime_extensions as datetime_extensions


logger = logging.getLogger("UserController")


def get_count() -> Any:
	database_client = flask.request.database_client()
	return flask.jsonify(flask.current_app.user_provider.count(database_client))


def get_collection() -> Any:
	query_parameters = {
		"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
		"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
		"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
	}

	database_client = flask.request.database_client()
	return flask.jsonify(flask.current_app.user_provider.get_list(database_client, **query_parameters))


def get(user_identifier: str) -> Any:
	database_client = flask.request.database_client()
	return flask.jsonify(flask.current_app.user_provider.get(database_client, user_identifier))


def create(user_identifier: str) -> Any:
	parameters = flask.request.get_json()
	database_client = flask.request.database_client()
	user = flask.current_app.user_provider.create(database_client, user_identifier, parameters["display_name"])
	return flask.jsonify(user)


def update_identity(user_identifier: str) -> Any:
	parameters = flask.request.get_json()
	database_client = flask.request.database_client()
	user = flask.current_app.user_provider.get(database_client, user_identifier)
	flask.current_app.user_provider.update_identity(database_client, user, parameters["display_name"])
	return flask.jsonify(user)


def update_roles(user_identifier: str) -> Any:
	parameters = flask.request.get_json()
	database_client = flask.request.database_client()
	user = flask.current_app.user_provider.get(database_client, user_identifier)
	flask.current_app.user_provider.update_roles(database_client, user, roles = parameters["roles"])
	return flask.jsonify(user)


def reset_password(user_identifier: str) -> Any:
	parameters = flask.request.get_json()
	database_client = flask.request.database_client()
	flask.current_app.authentication_provider.set_password(database_client, user_identifier, parameters["password"])
	return flask.jsonify({})


def enable(user_identifier: str) -> Any:
	database_client = flask.request.database_client()
	user = flask.current_app.user_provider.get(database_client, user_identifier)
	flask.current_app.user_provider.update_status(database_client, user, is_enabled = True)
	return flask.jsonify(user)


def disable(user_identifier: str) -> Any:
	database_client = flask.request.database_client()
	user = flask.current_app.user_provider.get(database_client, user_identifier)
	flask.current_app.user_provider.update_status(database_client, user, is_enabled = False)
	return flask.jsonify(user)


def get_token_count(user_identifier: str) -> Any:
	database_client = flask.request.database_client()
	return flask.jsonify(flask.current_app.authentication_provider.count_tokens(database_client, user = user_identifier))


def get_token_list(user_identifier: str) -> Any:
	query_parameters = {
		"user": user_identifier,
		"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
		"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
		"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
	}

	database_client = flask.request.database_client()
	return flask.jsonify(flask.current_app.authentication_provider.get_token_list(database_client, **query_parameters))


def create_token(user_identifier: str) -> Any:
	parameters = flask.request.get_json()
	description = parameters.get("description", None)
	expiration = parameters.get("expiration", None)

	if expiration is not None:
		expiration = datetime_extensions.parse_timedelta(expiration)

	database_client = flask.request.database_client()
	token = flask.current_app.authentication_provider.create_token(database_client, user_identifier, description, expiration)
	return flask.jsonify({ "token_identifier": token["identifier"], "secret": token["secret"] })


def set_token_expiration(user_identifier: str, token_identifier: str) -> Any:
	parameters = flask.request.get_json()
	expiration = datetime_extensions.parse_timedelta(parameters["expiration"])
	database_client = flask.request.database_client()
	flask.current_app.authentication_provider.set_token_expiration(database_client, user_identifier, token_identifier, expiration)
	return flask.jsonify({})


def delete_token(user_identifier: str, token_identifier: str) -> Any:
	database_client = flask.request.database_client()
	flask.current_app.authentication_provider.delete_token(database_client, user_identifier, token_identifier)
	return flask.jsonify({})
