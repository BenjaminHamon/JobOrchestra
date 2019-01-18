import logging

import flask

import bhamon_build_website.service_client as service_client


logger = logging.getLogger("TaskController")


def task_collection_index():
	task_collection = service_client.get("/task_collection")
	task_collection = list(task_collection.values())
	task_collection.sort(key = lambda task: task["update_date"], reverse = True)
	return flask.render_template("task/collection.html", title = "Tasks", task_collection = task_collection)


def cancel_task(task_identifier):
	service_client.post("/task/{task_identifier}/cancel".format(**locals()))
	return flask.redirect(flask.url_for("task_collection_index"))
