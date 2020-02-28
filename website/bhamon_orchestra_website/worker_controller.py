import logging

import flask

import bhamon_orchestra_website.helpers as helpers
import bhamon_orchestra_website.service_client as service_client


logger = logging.getLogger("WorkerController")


def show_collection():
	item_total = service_client.get("/worker_count")
	pagination = helpers.get_pagination(item_total, {})

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


def show(worker_identifier):
	view_data = {
		"worker": service_client.get("/worker/{worker_identifier}".format(**locals())),
		"project_collection": service_client.get("/project_collection".format(**locals()), { "limit": 1000, "order_by": [ "identifier ascending" ] }),
		"job_collection": service_client.get("/worker/{worker_identifier}/job_collection".format(**locals()), { "limit": 1000, "order_by": [ "identifier ascending" ] }),
		"run_collection": service_client.get("/worker/{worker_identifier}/run_collection".format(**locals()), { "limit": 10, "order_by": [ "update_date descending" ] }),
	}

	helpers.add_display_names(view_data["project_collection"], view_data["job_collection"], view_data["run_collection"], [], [ view_data["worker"] ])

	return flask.render_template("worker/index.html", title = "Worker " + worker_identifier, **view_data)


def show_runs(worker_identifier):
	query_parameters = {
		"worker": worker_identifier,
		"project": helpers.none_if_empty(flask.request.args.get("project", default = None)),
		"status": helpers.none_if_empty(flask.request.args.get("status", default = None)),
	}

	item_total = service_client.get("/worker/{worker_identifier}/run_count".format(**locals()), query_parameters)
	pagination = helpers.get_pagination(item_total, { "worker_identifier": worker_identifier, **query_parameters })

	query_parameters.update({
		"skip": (pagination["page_number"] - 1) * pagination["item_count"],
		"limit": pagination["item_count"],
		"order_by": [ "update_date descending" ],
	})

	view_data = {
		"worker": service_client.get("/worker/{worker_identifier}".format(**locals())),
		"project_collection": service_client.get("/project_collection".format(**locals()), { "limit": 1000, "order_by": [ "identifier ascending" ] }),
		"job_collection": service_client.get("/worker/{worker_identifier}/job_collection".format(**locals()), { "limit": 1000, "order_by": [ "identifier ascending" ] }),
		"status_collection": helpers.get_run_status_collection(),
		"run_collection": service_client.get("/worker/{worker_identifier}/run_collection".format(**locals()), query_parameters),
		"pagination": pagination,
	}

	helpers.add_display_names(view_data["project_collection"], view_data["job_collection"], view_data["run_collection"], [], [ view_data["worker"] ])

	return flask.render_template("worker/runs.html", title = "Runs", **view_data)



def disconnect(worker_identifier): # pylint: disable = unused-argument
	parameters = flask.request.form
	service_client.post("/worker/{worker_identifier}/disconnect".format(**locals()), parameters)
	return flask.redirect(flask.request.referrer or flask.url_for("worker_controller.show_collection"))


def enable(worker_identifier): # pylint: disable = unused-argument
	service_client.post("/worker/{worker_identifier}/enable".format(**locals()))
	return flask.redirect(flask.request.referrer or flask.url_for("worker_controller.show_collection"))


def disable(worker_identifier): # pylint: disable = unused-argument
	service_client.post("/worker/{worker_identifier}/disable".format(**locals()))
	return flask.redirect(flask.request.referrer or flask.url_for("worker_controller.show_collection"))
