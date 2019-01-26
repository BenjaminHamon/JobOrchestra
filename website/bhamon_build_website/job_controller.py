import logging

import flask

import bhamon_build_website.helpers as helpers
import bhamon_build_website.service_client as service_client


logger = logging.getLogger("JobController")


def job_collection_index():
	item_total = service_client.get("/job_count")
	pagination = helpers.get_pagination(item_total)
	
	query_parameters = {
		"skip": (pagination["page_number"] - 1) * pagination["item_count"],
		"limit": pagination["item_count"],
		"order_by": [ "identifier ascending" ],
	}

	job_collection = service_client.get("/job_collection", query_parameters)
	return flask.render_template("job/collection.html", title = "Jobs", job_collection = job_collection, pagination = pagination)


def job_index(job_identifier):
	job = service_client.get("/job/{job_identifier}".format(**locals()))
	job_builds = service_client.get("/job/{job_identifier}/builds".format(**locals()), { "limit": 10, "order_by": [ "update_date descending" ] })
	return flask.render_template("job/index.html", title = job["identifier"], job = job, job_builds = job_builds)


def trigger_job(job_identifier):
	parameters = {}
	for key, value in flask.request.form.items():
		if key.startswith("parameter-"):
			parameters[key[len("parameter-"):]] = value
	service_client.post("/job/{job_identifier}/trigger".format(**locals()), parameters)
	return flask.redirect(flask.request.referrer or flask.url_for("job_collection_index"))


def enable_job(job_identifier):
	service_client.post("/job/{job_identifier}/enable".format(**locals()))
	return flask.redirect(flask.request.referrer or flask.url_for("job_collection_index"))


def disable_job(job_identifier):
	service_client.post("/job/{job_identifier}/disable".format(**locals()))
	return flask.redirect(flask.request.referrer or flask.url_for("job_collection_index"))
