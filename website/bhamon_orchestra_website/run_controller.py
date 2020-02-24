import logging

import flask

import bhamon_orchestra_website.helpers as helpers
import bhamon_orchestra_website.service_client as service_client


logger = logging.getLogger("RunController")


def show_collection(project_identifier):
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
		"status_collection": helpers.get_status_collection(),
		"run_collection": service_client.get("/project/{project_identifier}/run_collection".format(**locals()), query_parameters),
		"pagination": pagination,
	}

	helpers.add_display_names([ view_data["project"] ], view_data["job_collection"], view_data["run_collection"], [], view_data["worker_collection"])

	return flask.render_template("run/collection.html", title = "Runs", **view_data)


def show(project_identifier, run_identifier): # pylint: disable = unused-argument
	view_data = {
		"project": service_client.get("/project/{project_identifier}".format(**locals())),
		"run": service_client.get("/project/{project_identifier}/run/{run_identifier}".format(**locals())),
		"run_steps": service_client.get("/project/{project_identifier}/run/{run_identifier}/step_collection".format(**locals())),
		"run_results": service_client.get("/project/{project_identifier}/run/{run_identifier}/results".format(**locals())),
		"run_tasks": service_client.get("/project/{project_identifier}/run/{run_identifier}/tasks".format(**locals()), { "limit": 10, "order_by": [ "update_date descending" ] }),
	}

	return flask.render_template("run/index.html", title = "Run " + run_identifier[:18], **view_data)


def show_step(project_identifier, run_identifier, step_index): # pylint: disable = unused-argument
	project = service_client.get("/project/{project_identifier}".format(**locals()))
	run = service_client.get("/project/{project_identifier}/run/{run_identifier}".format(**locals()))
	step_collection = service_client.get("/project/{project_identifier}/run/{run_identifier}/step_collection".format(**locals()))
	log_response = service_client.raw_get("/project/{project_identifier}/run/{run_identifier}/step/{step_index}/log".format(**locals()))

	view_data = {
		"project": project,
		"run": run,
		"current": step_collection[step_index],
		"previous": step_collection[step_index - 1] if step_index > 0 else None,
		"next": step_collection[step_index + 1] if step_index < (len(step_collection) - 1) else None,
		"log_text": log_response.text,
		"log_cursor": log_response.headers["X-Orchestra-FileCursor"],
	}

	return flask.render_template("run/step.html", title = "Run " + run_identifier[:18], **view_data)


def show_step_log(project_identifier, run_identifier, step_index): # pylint: disable = unused-argument
	log_text = service_client.raw_get("/project/{project_identifier}/run/{run_identifier}/step/{step_index}/log".format(**locals())).text
	return flask.Response(log_text, mimetype = "text/plain")


def cancel(project_identifier, run_identifier): # pylint: disable = unused-argument
	parameters = flask.request.form
	service_client.post("/project/{project_identifier}/run/{run_identifier}/cancel".format(**locals()), parameters)
	return flask.redirect(flask.request.referrer or flask.url_for("run_controller.show_collection", project_identifier = project_identifier))


def abort(project_identifier, run_identifier): # pylint: disable = unused-argument
	parameters = flask.request.form
	service_client.post("/project/{project_identifier}/run/{run_identifier}/abort".format(**locals()), parameters)
	return flask.redirect(flask.request.referrer or flask.url_for("run_controller.show_collection", project_identifier = project_identifier))


def download_archive(project_identifier, run_identifier): # pylint: disable = unused-argument
	archive_response = service_client.raw_get("/project/{project_identifier}/run/{run_identifier}/download".format(**locals()))
	return flask.Response(archive_response.content,
		headers = { "Content-Disposition": archive_response.headers["Content-Disposition"] },
		mimetype = archive_response.headers["Content-Type"])
