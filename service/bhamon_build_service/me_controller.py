import datetime
import logging

import flask

import bhamon_build_service.user_controller as user_controller


logger = logging.getLogger("MeController")


def get_my_user():
	return flask.jsonify(flask.current_app.user_provider.get(flask.request.authorization.username))


def login():
	parameters = flask.request.get_json()
	if not flask.current_app.authentication_provider.authenticate_with_password(parameters["user"], parameters["password"]):
		flask.abort(401)

	token_parameters = {
		"user": parameters["user"],
		"description": "Session from %s" % flask.request.environ["REMOTE_ADDR"],
		"expiration": datetime.timedelta(days = 7),
	}

	session_token = flask.current_app.authentication_provider.create_token(**token_parameters)
	return flask.jsonify({ "user_identifier": session_token["user"], "token_identifier": session_token["identifier"], "secret": session_token["secret"] })


def logout():
	parameters = flask.request.get_json()
	flask.current_app.authentication_provider.delete_token(flask.request.authorization.username, parameters["token_identifier"])
	return flask.jsonify({})


def get_my_token_list():
	return user_controller.get_token_list(flask.request.authorization.username)
