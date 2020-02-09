import logging

import flask

import bhamon_orchestra_service.user_controller as user_controller


logger = logging.getLogger("MeController")


def get_user():
	return flask.jsonify(flask.current_app.user_provider.get(flask.request.authorization.username))


def login():
	parameters = flask.request.get_json()
	if not flask.current_app.authentication_provider.authenticate_with_password(parameters["user"], parameters["password"]):
		flask.abort(401)

	user = flask.current_app.user_provider.get(parameters["user"])
	if not user["is_enabled"]:
		flask.abort(403)

	token_parameters = {
		"user": parameters["user"],
		"description": "Session from %s" % flask.request.environ["REMOTE_ADDR"],
		"expiration": flask.current_app.permanent_session_lifetime,
	}

	session_token = flask.current_app.authentication_provider.create_token(**token_parameters)
	return flask.jsonify({ "user_identifier": session_token["user"], "token_identifier": session_token["identifier"], "secret": session_token["secret"] })


def logout():
	if flask.request.authorization is not None:
		parameters = flask.request.get_json()
		flask.current_app.authentication_provider.delete_token(flask.request.authorization.username, parameters["token_identifier"])
	return flask.jsonify({})


def refresh_session():
	parameters = flask.request.get_json()

	operation_parameters = {
		"user_identifier": flask.request.authorization.username,
		"token_identifier": parameters["token_identifier"],
		"expiration": flask.current_app.permanent_session_lifetime,
	}

	flask.current_app.authentication_provider.set_token_expiration(**operation_parameters)
	return flask.jsonify({})


def change_password():
	parameters = flask.request.get_json()
	if not flask.current_app.authentication_provider.authenticate_with_password(flask.request.authorization.username, parameters["old_password"]):
		flask.abort(401)

	flask.current_app.authentication_provider.set_password(flask.request.authorization.username, parameters["new_password"])
	return flask.jsonify({})


def get_token_list():
	return user_controller.get_token_list(flask.request.authorization.username)


def create_token():
	return user_controller.create_token(flask.request.authorization.username)


def delete_token(token_identifier):
	return user_controller.delete_token(flask.request.authorization.username, token_identifier)
