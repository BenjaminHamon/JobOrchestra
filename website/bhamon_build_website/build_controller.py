import re
import logging

import flask

import bhamon_build_website.service_client as service_client


logger = logging.getLogger("BuildController")


def build_collection_index():
	build_collection = service_client.get("/build_collection", { "limit": 100, "order_by": [ "update_date descending" ] })
	return flask.render_template("build/collection.html", title = "Builds", build_collection = build_collection)


def build_index(build_identifier):
	build = service_client.get("/build/{build_identifier}".format(**locals()))
	build_steps = service_client.get("/build/{build_identifier}/step_collection".format(**locals()))
	build_results = service_client.get("/build/{build_identifier}/results".format(**locals()))
	build_tasks = service_client.get("/build/{build_identifier}/tasks".format(**locals()), { "limit": 10, "order_by": [ "update_date descending" ] })

	if "artifacts" in build_results:
		for artifact in build_results["artifacts"]:
			artifact["url"] = re.sub("^" + flask.current_app.artifact_storage_path, flask.current_app.artifact_storage_url, artifact["path"])

	return flask.render_template("build/index.html", title = build["identifier"],
			build = build, build_steps = build_steps, build_results = build_results, build_tasks = build_tasks)


def build_step_log(build_identifier, step_index):
	log_text = service_client.get_text("/build/{build_identifier}/step/{step_index}/log".format(**locals()))
	return flask.Response(log_text, mimetype = "text/plain")


def abort_build(build_identifier):
	parameters = flask.request.form
	service_client.post("/build/{build_identifier}/abort".format(**locals()), parameters)
	return flask.redirect(flask.request.referrer or flask.url_for("build_collection_index"))
