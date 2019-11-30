# pylint: disable=unused-argument

import logging

import flask

import bhamon_build_website.helpers as helpers
import bhamon_build_website.service_client as service_client


logger = logging.getLogger("TaskController")


def task_collection_index():
	query_parameters = {
		"type": helpers.none_if_empty(flask.request.args.get("type", default = None)),
		"status": helpers.none_if_empty(flask.request.args.get("status", default = None)),
		"run": helpers.none_if_empty(flask.request.args.get("run", default = None)),
		"worker": helpers.none_if_empty(flask.request.args.get("worker", default = None)),
	}

	item_total = service_client.get("/task_count", query_parameters)
	pagination = helpers.get_pagination(item_total)

	query_parameters.update({
		"skip": (pagination["page_number"] - 1) * pagination["item_count"],
		"limit": pagination["item_count"],
		"order_by": [ "update_date descending" ],
	})

	view_data = {
		"task_collection": service_client.get("/task_collection", query_parameters),
		"worker_collection": service_client.get("/worker_collection", { "limit": 1000, "order_by": [ "identifier ascending" ] }),
		"status_collection": _get_status_collection(),
		"pagination": pagination,
	}

	return flask.render_template("task/collection.html", title = "Tasks", **view_data)


def cancel_task(task_identifier):
	service_client.post("/task/{task_identifier}/cancel".format(**locals()))
	return flask.redirect(flask.request.referrer or flask.url_for("task_collection_index"))


def _get_status_collection():
	return [ "pending", "running", "succeeded", "failed", "exception", "cancelled" ]
