import logging
from typing import Any

import flask

import bhamon_orchestra_website.helpers as helpers
import bhamon_orchestra_website.service_client as service_client


logger = logging.getLogger("RunController")


def show_collection(project_identifier: str) -> Any:
	query_parameters = {
		"job": helpers.none_if_empty(flask.request.args.get("job", default = None)),
		"worker": helpers.none_if_empty(flask.request.args.get("worker", default = None)),
		"status": helpers.none_if_empty(flask.request.args.get("status", default = None)),
	}

	item_total = service_client.get("/project/{project_identifier}/run_count".format(**locals()), query_parameters)
	pagination = helpers.get_pagination(item_total, { "project_identifier": project_identifier, **query_parameters })

	query_parameters.update({
		"skip": (pagination["page_number"] - 1) * pagination["item_count"],
		"limit": pagination["item_count"],
		"order_by": [ "update_date descending" ],
	})

	view_data = {
		"project": service_client.get("/project/{project_identifier}".format(**locals())),
		"job_collection": service_client.get("/project/{project_identifier}/job_collection".format(**locals()), { "limit": 1000, "order_by": [ "identifier ascending" ] }),
		"worker_collection": service_client.get("/worker_collection", { "limit": 1000, "order_by": [ "identifier ascending" ] }),
		"status_collection": helpers.get_run_status_collection(),
		"run_collection": service_client.get("/project/{project_identifier}/run_collection".format(**locals()), query_parameters),
		"pagination": pagination,
	}

	helpers.add_display_names([ view_data["project"] ], view_data["job_collection"], view_data["run_collection"], [], view_data["worker_collection"])

	return flask.render_template("run/collection.html", title = "Runs", **view_data)


def show(project_identifier: str, run_identifier: str) -> Any: # pylint: disable = unused-argument
	project = service_client.get("/project/{project_identifier}".format(**locals()))
	run = service_client.get("/project/{project_identifier}/run/{run_identifier}".format(**locals()))
	run_results = service_client.get("/project/{project_identifier}/run/{run_identifier}/results".format(**locals()))

	run["project_display_name"] = project["display_name"]

	job_route = "/project/{project}/job/{job}".format(project = project_identifier, job = run["job"])
	job = service_client.get_or_default(job_route, default_value = {})
	run["job_display_name"] = job.get("display_name", run["job"])

	if run["source"] is not None:
		if run["source"]["type"] == "schedule":
			schedule_route = "/project/{project}/schedule/{schedule}".format(project = project_identifier, schedule = run["source"]["identifier"])
			schedule = service_client.get_or_default(schedule_route, default_value = {})
			run["source"]["display_name"] = schedule.get("display_name", run["source"]["identifier"])
		if run["source"]["type"] == "user":
			user_route = "/user/{user}".format(user = run["source"]["identifier"])
			user = service_client.get_or_default(user_route, default_value = {})
			run["source"]["display_name"] = user.get("display_name", run["source"]["identifier"])

	if run["worker"] is not None:
		worker_route = "/worker/{worker}".format(worker = run["worker"])
		worker = service_client.get_or_default(worker_route, default_value = {})
		run["worker_display_name"] = worker.get("display_name", run["worker"])

	view_data = { "project": project, "run": run, "run_results": run_results }

	return flask.render_template("run/index.html", title = "Run " + run_identifier[:18], **view_data)


def show_log(project_identifier: str, run_identifier: str) -> Any: # pylint: disable = unused-argument
	view_data = {
		"project": service_client.get("/project/{project_identifier}".format(**locals())),
		"run": service_client.get("/project/{project_identifier}/run/{run_identifier}".format(**locals())),
	}

	return flask.render_template("run/log.html", title = "Run " + run_identifier[:18], **view_data)


def show_log_raw(project_identifier: str, run_identifier: str) -> Any: # pylint: disable = unused-argument
	log_text = service_client.send_request("GET", "/project/{project_identifier}/run/{run_identifier}/log".format(**locals())).text
	content_disposition = "inline; filename=\"%s.log\"" % run_identifier
	return flask.Response(log_text, headers = { "Content-Disposition": content_disposition }, mimetype = "text/plain")


def cancel(project_identifier: str, run_identifier: str) -> Any: # pylint: disable = unused-argument
	parameters = flask.request.form
	service_client.post("/project/{project_identifier}/run/{run_identifier}/cancel".format(**locals()), parameters)
	return flask.redirect(flask.request.referrer or flask.url_for("run_controller.show_collection", project_identifier = project_identifier))


def abort(project_identifier: str, run_identifier: str) -> Any: # pylint: disable = unused-argument
	parameters = flask.request.form
	service_client.post("/project/{project_identifier}/run/{run_identifier}/abort".format(**locals()), parameters)
	return flask.redirect(flask.request.referrer or flask.url_for("run_controller.show_collection", project_identifier = project_identifier))


def download_archive(project_identifier: str, run_identifier: str) -> Any: # pylint: disable = unused-argument
	archive_response = service_client.send_request("GET", "/project/{project_identifier}/run/{run_identifier}/download".format(**locals()))
	return flask.Response(archive_response.content,
		headers = { "Content-Disposition": archive_response.headers["Content-Disposition"] },
		mimetype = archive_response.headers["Content-Type"])
