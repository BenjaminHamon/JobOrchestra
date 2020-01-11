import logging

import flask

import bhamon_orchestra_website.helpers as helpers
import bhamon_orchestra_website.service_client as service_client


logger = logging.getLogger("JobController")


def job_collection_index():
	query_parameters = {
		"project": helpers.none_if_empty(flask.request.args.get("project", default = None)),
	}

	item_total = service_client.get("/job_count", query_parameters)
	pagination = helpers.get_pagination(item_total)

	query_parameters.update({
		"skip": (pagination["page_number"] - 1) * pagination["item_count"],
		"limit": pagination["item_count"],
		"order_by": [ "identifier ascending" ],
	})

	view_data = {
		"project_collection": service_client.get("/project_collection", { "limit": 1000, "order_by": [ "identifier ascending" ] }),
		"job_collection": service_client.get("/job_collection", query_parameters),
		"pagination": pagination,
	}

	return flask.render_template("job/collection.html", title = "Jobs", **view_data)


def job_index(job_identifier):
	view_data = {
		"job": service_client.get("/job/{job_identifier}".format(**locals())),
		"job_runs": service_client.get("/job/{job_identifier}/runs".format(**locals()), { "limit": 10, "order_by": [ "update_date descending" ] }),
	}

	return flask.render_template("job/index.html", title = "Job " + job_identifier, **view_data)


def trigger_job(job_identifier): # pylint: disable = unused-argument
	parameters = {}
	for key, value in flask.request.form.items():
		if key.startswith("parameter-"):
			parameters[key[len("parameter-"):]] = value
	service_client.post("/job/{job_identifier}/trigger".format(**locals()), parameters)
	return flask.redirect(flask.request.referrer or flask.url_for("job_collection_index"))


def enable_job(job_identifier): # pylint: disable = unused-argument
	service_client.post("/job/{job_identifier}/enable".format(**locals()))
	return flask.redirect(flask.request.referrer or flask.url_for("job_collection_index"))


def disable_job(job_identifier): # pylint: disable = unused-argument
	service_client.post("/job/{job_identifier}/disable".format(**locals()))
	return flask.redirect(flask.request.referrer or flask.url_for("job_collection_index"))
