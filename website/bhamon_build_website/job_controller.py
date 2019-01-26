import logging

import flask

import bhamon_build_website.service_client as service_client


logger = logging.getLogger("JobController")


def job_collection_index():
	job_collection = service_client.get("/job_collection", { "limit": 100, "order_by": [ "identifier ascending" ] })
	return flask.render_template("job/collection.html", title = "Jobs", job_collection = job_collection)


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
