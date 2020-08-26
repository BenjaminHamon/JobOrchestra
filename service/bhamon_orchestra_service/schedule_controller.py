import logging

import flask


logger = logging.getLogger("ScheduleController")


def get_count(project_identifier):
	query_parameters = {
		"project": project_identifier,
		"job": flask.request.args.get("job", default = None),
	}

	database_client = flask.request.database_client()
	return flask.jsonify(flask.current_app.schedule_provider.count(database_client, **query_parameters))


def get_collection(project_identifier):
	query_parameters = {
		"project": project_identifier,
		"job": flask.request.args.get("job", default = None),
		"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
		"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
		"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
	}

	database_client = flask.request.database_client()
	return flask.jsonify(flask.current_app.schedule_provider.get_list(database_client, **query_parameters))


def get(project_identifier, schedule_identifier):
	database_client = flask.request.database_client()
	return flask.jsonify(flask.current_app.schedule_provider.get(database_client, project_identifier, schedule_identifier))


def enable(project_identifier, schedule_identifier):
	database_client = flask.request.database_client()
	flask.current_app.schedule_provider.update_status(database_client, { "project": project_identifier, "identifier": schedule_identifier }, is_enabled = True)
	return flask.jsonify({})


def disable(project_identifier, schedule_identifier):
	database_client = flask.request.database_client()
	flask.current_app.schedule_provider.update_status(database_client, { "project": project_identifier, "identifier": schedule_identifier }, is_enabled = False)
	return flask.jsonify({})
