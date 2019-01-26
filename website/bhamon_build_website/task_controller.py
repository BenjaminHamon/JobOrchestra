import logging

import flask

import bhamon_build_website.helpers as helpers
import bhamon_build_website.service_client as service_client


logger = logging.getLogger("TaskController")


def task_collection_index():
	item_total = service_client.get("/task_count")
	pagination = helpers.get_pagination(item_total)

	query_parameters = {
		"skip": (pagination["page_number"] - 1) * pagination["item_count"],
		"limit": pagination["item_count"],
		"order_by": [ "update_date descending" ],
	}

	task_collection = service_client.get("/task_collection", query_parameters)
	return flask.render_template("task/collection.html", title = "Tasks", task_collection = task_collection, pagination = pagination)


def cancel_task(task_identifier):
	service_client.post("/task/{task_identifier}/cancel".format(**locals()))
	return flask.redirect(flask.request.referrer or flask.url_for("task_collection_index"))
