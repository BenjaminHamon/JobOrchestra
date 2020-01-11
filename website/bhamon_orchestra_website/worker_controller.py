# pylint: disable=unused-argument

import logging

import flask

import bhamon_orchestra_website.helpers as helpers
import bhamon_orchestra_website.service_client as service_client


logger = logging.getLogger("WorkerController")


def worker_collection_index():
	item_total = service_client.get("/worker_count")
	pagination = helpers.get_pagination(item_total)

	query_parameters = {
		"skip": (pagination["page_number"] - 1) * pagination["item_count"],
		"limit": pagination["item_count"],
		"order_by": [ "identifier ascending" ],
	}

	view_data = {
		"worker_collection": service_client.get("/worker_collection", query_parameters),
		"pagination": pagination,
	}

	return flask.render_template("worker/collection.html", title = "Workers", **view_data)


def worker_index(worker_identifier):
	view_data = {
		"worker": service_client.get("/worker/{worker_identifier}".format(**locals())),
		"worker_runs": service_client.get("/worker/{worker_identifier}/runs".format(**locals()), { "limit": 10, "order_by": [ "update_date descending" ] }),
		"worker_tasks": service_client.get("/worker/{worker_identifier}/tasks".format(**locals()), { "limit": 10, "order_by": [ "update_date descending" ] }),
	}

	return flask.render_template("worker/index.html", title = "Worker " + worker_identifier, **view_data)


def stop_worker(worker_identifier):
	parameters = flask.request.form
	service_client.post("/worker/{worker_identifier}/stop".format(**locals()), parameters)
	return flask.redirect(flask.request.referrer or flask.url_for("worker_collection_index"))


def enable_worker(worker_identifier):
	service_client.post("/worker/{worker_identifier}/enable".format(**locals()))
	return flask.redirect(flask.request.referrer or flask.url_for("worker_collection_index"))


def disable_worker(worker_identifier):
	service_client.post("/worker/{worker_identifier}/disable".format(**locals()))
	return flask.redirect(flask.request.referrer or flask.url_for("worker_collection_index"))
