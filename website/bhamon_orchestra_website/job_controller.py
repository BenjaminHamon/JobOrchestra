import logging

import flask

import bhamon_orchestra_website.helpers as helpers
import bhamon_orchestra_website.service_client as service_client


logger = logging.getLogger("JobController")


def show_collection(project_identifier):
	item_total = service_client.get("/project/{project_identifier}/job_count".format(**locals()))
	pagination = helpers.get_pagination(item_total, { "project_identifier": project_identifier })

	query_parameters = {
		"skip": (pagination["page_number"] - 1) * pagination["item_count"],
		"limit": pagination["item_count"],
		"order_by": [ "identifier ascending" ],
	}

	view_data = {
		"project": service_client.get("/project/{project_identifier}".format(**locals())),
		"job_collection": service_client.get("/project/{project_identifier}/job_collection".format(**locals()), query_parameters),
		"pagination": pagination,
	}

	return flask.render_template("job/collection.html", title = "Jobs", **view_data)


def show(project_identifier, job_identifier): # pylint: disable = unused-argument
	run_query_parameters = { "limit": 10, "order_by": [ "update_date descending" ] }

	view_data = {
		"project": service_client.get("/project/{project_identifier}".format(**locals())),
		"job": service_client.get("/project/{project_identifier}/job/{job_identifier}".format(**locals())),
		"job_runs": service_client.get("/project/{project_identifier}/job/{job_identifier}/runs".format(**locals()), run_query_parameters),
	}

	return flask.render_template("job/index.html", title = "Job " + job_identifier, **view_data)


def trigger(project_identifier, job_identifier): # pylint: disable = unused-argument
	parameters = {}
	for key, value in flask.request.form.items():
		if key.startswith("parameter-"):
			parameters[key[len("parameter-"):]] = value
	service_client.post("/project/{project_identifier}/job/{job_identifier}/trigger".format(**locals()), parameters)
	return flask.redirect(flask.request.referrer or flask.url_for("job_controller.show_collection", project_identifier = project_identifier))


def enable(project_identifier, job_identifier): # pylint: disable = unused-argument
	service_client.post("/project/{project_identifier}/job/{job_identifier}/enable".format(**locals()))
	return flask.redirect(flask.request.referrer or flask.url_for("job_controller.show_collection", project_identifier = project_identifier))


def disable(project_identifier, job_identifier): # pylint: disable = unused-argument
	service_client.post("/project/{project_identifier}/job/{job_identifier}/disable".format(**locals()))
	return flask.redirect(flask.request.referrer or flask.url_for("job_controller.show_collection", project_identifier = project_identifier))
