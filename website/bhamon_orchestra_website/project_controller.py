import logging

import flask

import bhamon_orchestra_website.helpers as helpers
import bhamon_orchestra_website.service_client as service_client


logger = logging.getLogger("ProjectController")


def show_collection():
	item_total = service_client.get("/project_count")
	pagination = helpers.get_pagination(item_total, {})

	query_parameters = {
		"skip": (pagination["page_number"] - 1) * pagination["item_count"],
		"limit": pagination["item_count"],
		"order_by": [ "identifier ascending" ],
	}

	project_collection = service_client.get("/project_collection", query_parameters)
	return flask.render_template("project/collection.html", title = "Projects", project_collection = project_collection, pagination = pagination)


def show(project_identifier):
	view_data = {
		"project": service_client.get("/project/{project_identifier}".format(**locals())),
		"job_collection": service_client.get("/project/{project_identifier}/job_collection".format(**locals()), { "limit": 10, "order_by": [ "update_date descending" ] }),
		"run_collection": service_client.get("/project/{project_identifier}/runs".format(**locals()), { "limit": 10, "order_by": [ "update_date descending" ] }),
		"schedule_collection": service_client.get("/project/{project_identifier}/schedule_collection".format(**locals()), { "limit": 10, "order_by": [ "update_date descending" ] }),
	}

	return flask.render_template("project/index.html", title = "Project " + project_identifier, **view_data)


def show_status(project_identifier):
	branch = flask.request.args.get("branch", default = None)
	status_limit = max(min(flask.request.args.get("limit", default = 20, type = int), 100), 1)

	project = service_client.get("/project/{project_identifier}".format(**locals()))
	repository = service_client.get("/project/{project_identifier}/repository".format(**locals()))
	branch_collection = service_client.get("/project/{project_identifier}/branches".format(**locals()))
	job_collection = service_client.get("/project/{project_identifier}/job_collection".format(**locals()), { "order_by": [ "identifier ascending" ] })
	context = { "filter_collection": [ { "identifier": job["identifier"], "job": job["identifier"] } for job in job_collection ] }

	if branch is None:
		branch = repository["default_branch"]

	status_parameters = {
		"branch": branch,
		"revision_limit": 20,
		"run_limit": 1000,
	}

	status = service_client.get("/project/{project_identifier}/status".format(**locals()), status_parameters)
	status = [ revision for revision in status if len(revision["runs"]) > 0 ][ : status_limit ]

	for revision in status:
		revision["runs_by_filter"] = { f["identifier"]: [] for f in context["filter_collection"] }
		for run in revision["runs"]:
			for run_filter in context["filter_collection"]:
				if run["job"] == run_filter["job"]:
					revision["runs_by_filter"][run_filter["identifier"]].append(run)

	view_data = {
		"project": project,
		"project_branch": branch,
		"project_branch_collection": branch_collection,
		"project_context": context,
		"project_status": status,
	}

	return flask.render_template("project/status.html", title = "Project " + project_identifier, **view_data)
