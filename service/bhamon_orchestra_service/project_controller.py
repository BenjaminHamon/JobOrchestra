import logging

import flask


logger = logging.getLogger("ProjectController")


def get_project_count():
	return flask.jsonify(flask.current_app.project_provider.count())


def get_project_collection():
	query_parameters = {
		"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
		"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
		"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
	}

	return flask.jsonify(flask.current_app.project_provider.get_list(**query_parameters))


def get_project(project_identifier):
	return flask.jsonify(flask.current_app.project_provider.get(project_identifier))
