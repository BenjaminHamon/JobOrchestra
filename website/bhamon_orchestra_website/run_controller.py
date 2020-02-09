import logging

import flask

import bhamon_orchestra_website.helpers as helpers
import bhamon_orchestra_website.service_client as service_client


logger = logging.getLogger("RunController")


def show_collection():
	query_parameters = {
		"project": helpers.none_if_empty(flask.request.args.get("project", default = None)),
		"job": helpers.none_if_empty(flask.request.args.get("job", default = None)),
		"worker": helpers.none_if_empty(flask.request.args.get("worker", default = None)),
		"status": helpers.none_if_empty(flask.request.args.get("status", default = None)),
	}

	item_total = service_client.get("/run_count", query_parameters)
	pagination = helpers.get_pagination(item_total)

	query_parameters.update({
		"skip": (pagination["page_number"] - 1) * pagination["item_count"],
		"limit": pagination["item_count"],
		"order_by": [ "update_date descending" ],
	})

	view_data = {
		"project_collection": service_client.get("/project_collection", { "limit": 1000, "order_by": [ "identifier ascending" ] }),
		"job_collection": service_client.get("/job_collection", { "limit": 1000, "order_by": [ "identifier ascending" ] }),
		"worker_collection": service_client.get("/worker_collection", { "limit": 1000, "order_by": [ "identifier ascending" ] }),
		"status_collection": _get_status_collection(),
		"run_collection": service_client.get("/run_collection", query_parameters),
		"pagination": pagination,
	}

	return flask.render_template("run/collection.html", title = "Runs", **view_data)


def show(run_identifier):
	view_data = {
		"run": service_client.get("/run/{run_identifier}".format(**locals())),
		"run_steps": service_client.get("/run/{run_identifier}/step_collection".format(**locals())),
		"run_results": service_client.get("/run/{run_identifier}/results".format(**locals())),
		"run_tasks": service_client.get("/run/{run_identifier}/tasks".format(**locals()), { "limit": 10, "order_by": [ "update_date descending" ] }),
	}

	return flask.render_template("run/index.html", title = "Run " + run_identifier[:18], **view_data)


def show_step(run_identifier, step_index):
	step_collection = service_client.get("/run/{run_identifier}/step_collection".format(**locals()))
	log_response = service_client.raw_get("/run/{run_identifier}/step/{step_index}/log".format(**locals()))

	view_data = {
		"run_identifier": run_identifier,
		"current": step_collection[step_index],
		"previous": step_collection[step_index - 1] if step_index > 0 else None,
		"next": step_collection[step_index + 1] if step_index < (len(step_collection) - 1) else None,
		"log_text": log_response.text,
		"log_cursor": log_response.headers["X-Orchestra-FileCursor"],
	}

	return flask.render_template("run/step.html", title = "Run " + run_identifier[:18], **view_data)


def show_step_log(run_identifier, step_index): # pylint: disable = unused-argument
	log_text = service_client.raw_get("/run/{run_identifier}/step/{step_index}/log".format(**locals())).text
	return flask.Response(log_text, mimetype = "text/plain")


def cancel(run_identifier): # pylint: disable = unused-argument
	parameters = flask.request.form
	service_client.post("/run/{run_identifier}/cancel".format(**locals()), parameters)
	return flask.redirect(flask.request.referrer or flask.url_for("run_controller.show_collection"))


def abort(run_identifier): # pylint: disable = unused-argument
	parameters = flask.request.form
	service_client.post("/run/{run_identifier}/abort".format(**locals()), parameters)
	return flask.redirect(flask.request.referrer or flask.url_for("run_controller.show_collection"))


def download_archive(run_identifier): # pylint: disable = unused-argument
	archive_response = service_client.raw_get("/run/{run_identifier}/download".format(**locals()))
	return flask.Response(archive_response.content,
		headers = { "Content-Disposition": archive_response.headers["Content-Disposition"] },
		mimetype = archive_response.headers["Content-Type"])


def _get_status_collection():
	return [ "pending", "running", "succeeded", "failed", "exception", "aborted", "cancelled" ]
