import logging

import flask


logger = logging.getLogger("ScheduleController")


def get_schedule_count():
	query_parameters = {
		"project": flask.request.args.get("project", default = None),
		"job": flask.request.args.get("job", default = None),
	}

	return flask.jsonify(flask.current_app.schedule_provider.count(**query_parameters))


def get_schedule_collection():
	query_parameters = {
		"project": flask.request.args.get("project", default = None),
		"job": flask.request.args.get("job", default = None),
		"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
		"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
		"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
	}

	return flask.jsonify(flask.current_app.schedule_provider.get_list(**query_parameters))


def get_schedule(schedule_identifier):
	return flask.jsonify(flask.current_app.schedule_provider.get(schedule_identifier))


def enable_schedule(schedule_identifier):
	flask.current_app.schedule_provider.update_status({ "identifier": schedule_identifier }, is_enabled = True)
	return flask.jsonify({})


def disable_schedule(schedule_identifier):
	flask.current_app.schedule_provider.update_status({ "identifier": schedule_identifier }, is_enabled = False)
	return flask.jsonify({})
