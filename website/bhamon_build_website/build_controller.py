import logging
import re

import flask

import bhamon_build_website.helpers as helpers
import bhamon_build_website.service_client as service_client


logger = logging.getLogger("BuildController")


def build_collection_index():
	query_parameters = {
		"job": helpers.none_if_empty(flask.request.args.get("job", default = None)),
		"worker": helpers.none_if_empty(flask.request.args.get("worker", default = None)),
		"status": helpers.none_if_empty(flask.request.args.get("status", default = None)),
	}

	item_total = service_client.get("/build_count", query_parameters)
	pagination = helpers.get_pagination(item_total)
	
	query_parameters.update({
		"skip": (pagination["page_number"] - 1) * pagination["item_count"],
		"limit": pagination["item_count"],
		"order_by": [ "update_date descending" ],
	})

	view_data = {
		"build_collection": service_client.get("/build_collection", query_parameters),
		"job_collection": service_client.get("/job_collection", { "limit": 1000, "order_by": [ "identifier ascending" ] }),
		"worker_collection": service_client.get("/worker_collection", { "limit": 1000, "order_by": [ "identifier ascending" ] }),
		"status_collection": _get_status_collection(),
		"pagination": pagination,
	}

	return flask.render_template("build/collection.html", title = "Builds", **view_data)


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


def _get_status_collection():
	return [ "pending", "running", "succeeded", "failed", "exception", "aborted", "cancelled" ]
