import logging

import flask

import bhamon_build_service.helpers as helpers


logger = logging.getLogger("UserController")


def get_user_count():
	return flask.jsonify(flask.current_app.user_provider.count())


def get_user_collection():
	query_parameters = {
		"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
		"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
		"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
	}

	return flask.jsonify(flask.current_app.user_provider.get_list(**query_parameters))


def get_user(user_identifier):
	return flask.jsonify(flask.current_app.user_provider.get(user_identifier))


def create_user(user_identifier):
	parameters = flask.request.get_json()
	user = flask.current_app.user_provider.create(user_identifier, parameters["display_name"])
	return flask.jsonify(user)


def update_user_identity(user_identifier):
	parameters = flask.request.get_json()
	user = flask.current_app.user_provider.get(user_identifier)
	flask.current_app.user_provider.update_identity(user, parameters["display_name"])
	return flask.jsonify(user)


def update_user_roles(user_identifier):
	parameters = flask.request.get_json()
	user = flask.current_app.user_provider.get(user_identifier)
	flask.current_app.user_provider.update_roles(user, roles = parameters["roles"])
	return flask.jsonify(user)


def reset_password(user_identifier):
	parameters = flask.request.get_json()
	flask.current_app.authentication_provider.set_password(user_identifier, parameters["password"])
	return flask.jsonify({})


def enable_user(user_identifier):
	user = flask.current_app.user_provider.get(user_identifier)
	flask.current_app.user_provider.update_status(user, is_enabled = True)
	return flask.jsonify(user)


def disable_user(user_identifier):
	user = flask.current_app.user_provider.get(user_identifier)
	flask.current_app.user_provider.update_status(user, is_enabled = False)
	return flask.jsonify(user)


def get_user_token_count(user_identifier):
	return flask.jsonify(flask.current_app.authentication_provider.count_tokens(user = user_identifier))


def get_user_token_list(user_identifier):
	query_parameters = {
		"user": user_identifier,
		"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
		"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
		"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
	}

	return flask.jsonify(flask.current_app.authentication_provider.get_token_list(**query_parameters))


def create_user_token(user_identifier):
	parameters = flask.request.get_json()
	description = parameters.get("description", None)
	expiration = parameters.get("expiration", None)

	if expiration is not None:
		expiration = helpers.parse_timedelta(expiration)

	token = flask.current_app.authentication_provider.create_token(user_identifier, description, expiration)
	return flask.jsonify({ "token_identifier": token["identifier"], "secret": token["secret"] })


def refresh_user_token(user_identifier, token_identifier):
	parameters = flask.request.get_json()
	expiration = parameters.get("expiration", None)

	if expiration is not None:
		expiration = helpers.parse_timedelta(expiration)

	flask.current_app.authentication_provider.refresh_token(user_identifier, token_identifier, expiration = expiration)
	return flask.jsonify({})


def delete_user_token(user_identifier, token_identifier):
	flask.current_app.authentication_provider.delete_token(user_identifier, token_identifier)
	return flask.jsonify({})
