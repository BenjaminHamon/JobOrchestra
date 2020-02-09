import logging

import flask

import bhamon_orchestra_website.helpers as helpers
import bhamon_orchestra_website.service_client as service_client


logger = logging.getLogger("ScheduleController")


def show_collection():
	query_parameters = {
		"project": helpers.none_if_empty(flask.request.args.get("project", default = None)),
		"job": helpers.none_if_empty(flask.request.args.get("job", default = None)),
	}

	item_total = service_client.get("/schedule_count", query_parameters)
	pagination = helpers.get_pagination(item_total)

	query_parameters.update({
		"skip": (pagination["page_number"] - 1) * pagination["item_count"],
		"limit": pagination["item_count"],
		"order_by": [ "identifier ascending" ],
	})

	view_data = {
		"project_collection": service_client.get("/project_collection", { "limit": 1000, "order_by": [ "identifier ascending" ] }),
		"job_collection": service_client.get("/job_collection", { "limit": 1000, "order_by": [ "identifier ascending" ] }),
		"schedule_collection": service_client.get("/schedule_collection", query_parameters),
		"pagination": pagination,
	}

	return flask.render_template("schedule/collection.html", title = "Schedules", **view_data)


def show(schedule_identifier):
	view_data = {
		"schedule": service_client.get("/schedule/{schedule_identifier}".format(**locals())),
	}

	return flask.render_template("schedule/index.html", title = "Schedule " + schedule_identifier, **view_data)


def enable(schedule_identifier): # pylint: disable = unused-argument
	service_client.post("/schedule/{schedule_identifier}/enable".format(**locals()))
	return flask.redirect(flask.request.referrer or flask.url_for("schedule_controller.show_collection"))


def disable(schedule_identifier): # pylint: disable = unused-argument
	service_client.post("/schedule/{schedule_identifier}/disable".format(**locals()))
	return flask.redirect(flask.request.referrer or flask.url_for("schedule_controller.show_collection"))
