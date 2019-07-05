import logging

import flask


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
	user = flask.current_app.user_provider.create(user_identifier, **parameters)
	return flask.jsonify(user)


def update_user(user_identifier):
	parameters = flask.request.get_json()
	user = flask.current_app.user_provider.get(user_identifier)
	flask.current_app.user_provider.update(user, **parameters)
	return flask.jsonify(user)


def enable_user(user_identifier):
	user = flask.current_app.user_provider.get(user_identifier)
	flask.current_app.user_provider.update_status(user, is_enabled = True)
	return flask.jsonify(user)


def disable_user(user_identifier):
	user = flask.current_app.user_provider.get(user_identifier)
	flask.current_app.user_provider.update_status(user, is_enabled = False)
	return flask.jsonify(user)
