import logging

import flask

import bhamon_build_website.service_client as service_client


logger = logging.getLogger("WorkerController")


def worker_collection_index():
	worker_collection = service_client.get("/worker_collection")
	worker_collection = list(worker_collection.values())
	worker_collection.sort(key = lambda worker: worker["identifier"])
	return flask.render_template("worker/collection.html", title = "Workers", worker_collection = worker_collection)


def worker_index(worker_identifier):
	worker = service_client.get("/worker/{worker_identifier}".format(**locals()))
	worker_builds = service_client.get("/worker/{worker_identifier}/builds".format(**locals()))
	worker_builds = list(worker_builds.values())
	worker_builds.sort(key = lambda build: build["update_date"], reverse = True)
	worker_tasks = service_client.get("/worker/{worker_identifier}/tasks".format(**locals()))
	worker_tasks = list(worker_tasks.values())
	worker_tasks.sort(key = lambda task: task["update_date"], reverse = True)
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
