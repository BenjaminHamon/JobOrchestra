import logging

import flask

import bhamon_build_website.service_client as service_client


logger = logging.getLogger("WorkerController")


def worker_collection_index():
	worker_collection = service_client.get("/worker_collection", { "limit": 100, "order_by": [ "identifier ascending" ] })
	return flask.render_template("worker/collection.html", title = "Workers", worker_collection = worker_collection)


def worker_index(worker_identifier):
	worker = service_client.get("/worker/{worker_identifier}".format(**locals()))
	worker_builds = service_client.get("/worker/{worker_identifier}/builds".format(**locals()), { "limit": 10, "order_by": [ "update_date descending" ] })
	worker_tasks = service_client.get("/worker/{worker_identifier}/tasks".format(**locals()), { "limit": 10, "order_by": [ "update_date descending" ] })
	return flask.render_template("worker/index.html", title = worker["identifier"],
			worker = worker, worker_builds = worker_builds, worker_tasks = worker_tasks)


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
