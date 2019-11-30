# pylint: disable=unused-argument

import logging

import flask

import bhamon_build_website.helpers as helpers
import bhamon_build_website.service_client as service_client


logger = logging.getLogger("RunController")


def run_collection_index():
	query_parameters = {
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
		"run_collection": service_client.get("/run_collection", query_parameters),
		"job_collection": service_client.get("/job_collection", { "limit": 1000, "order_by": [ "identifier ascending" ] }),
		"worker_collection": service_client.get("/worker_collection", { "limit": 1000, "order_by": [ "identifier ascending" ] }),
		"status_collection": _get_status_collection(),
		"pagination": pagination,
	}

	return flask.render_template("run/collection.html", title = "Runs", **view_data)


def run_index(run_identifier):
	view_data = {
		"run": service_client.get("/run/{run_identifier}".format(**locals())),
		"run_steps": service_client.get("/run/{run_identifier}/step_collection".format(**locals())),
		"run_results": service_client.get("/run/{run_identifier}/results".format(**locals())),
		"run_tasks": service_client.get("/run/{run_identifier}/tasks".format(**locals()), { "limit": 10, "order_by": [ "update_date descending" ] }),
	}

	return flask.render_template("run/index.html", title = "Run " + view_data["run"]["identifier"][:18], **view_data)


def run_step_log(run_identifier, step_index):
	log_response = service_client.raw_get("/run/{run_identifier}/step/{step_index}/log".format(**locals()))
	return flask.Response(log_response.text, mimetype = "text/plain")


def abort_run(run_identifier):
	parameters = flask.request.form
	service_client.post("/run/{run_identifier}/abort".format(**locals()), parameters)
	return flask.redirect(flask.request.referrer or flask.url_for("run_collection_index"))


def download_run_archive(run_identifier):
	archive_response = service_client.raw_get("/run/{run_identifier}/download".format(**locals()))
	return flask.Response(archive_response.content,
		headers = { "Content-Disposition": archive_response.headers["Content-Disposition"] },
		mimetype = archive_response.headers["Content-Type"])


def _get_status_collection():
	return [ "pending", "running", "succeeded", "failed", "exception", "aborted", "cancelled" ]
