import logging
from typing import Any

import flask

import bhamon_orchestra_website.helpers as helpers
import bhamon_orchestra_website.service_client as service_client


logger = logging.getLogger("ProjectController")


def show_collection() -> Any:
	item_total = service_client.get("/project_count")
	pagination = helpers.get_pagination(item_total, {})

	query_parameters = {
		"skip": (pagination["page_number"] - 1) * pagination["item_count"],
		"limit": pagination["item_count"],
		"order_by": [ "identifier ascending" ],
	}

	project_collection = service_client.get("/project_collection", query_parameters)
	return flask.render_template("project/collection.html", title = "Projects", project_collection = project_collection, pagination = pagination)


def show(project_identifier: str) -> Any: # pylint: disable = unused-argument
	view_data = {
		"project": service_client.get("/project/{project_identifier}".format(**locals())),
		"run_collection": service_client.get("/project/{project_identifier}/run_collection".format(**locals()), { "limit": 10, "order_by": [ "update_date descending" ] }),
	}

	if "revision_control" in view_data["project"]["services"]:
		view_data["revision_collection"] = []
		for branch in view_data["project"]["services"]["revision_control"]["branches_for_status"]: # pylint: disable = possibly-unused-variable
			branch_status = service_client.get("/project/{project_identifier}/repository/revision/{branch}/status".format(**locals()))
			view_data["revision_collection"].append(branch_status)

	job_collection = service_client.get("/project/{project_identifier}/job_collection".format(**locals()), { "order_by": [ "identifier ascending" ] })
	worker_collection = service_client.get("/worker_collection", { "order_by": [ "identifier ascending" ] })
	helpers.add_display_names([ view_data["project"] ], job_collection, view_data["run_collection"], [], worker_collection)

	return flask.render_template("project/index.html", title = "Project " + view_data["project"]["display_name"], **view_data)


def show_status(project_identifier: str) -> Any: # pylint: disable = unused-argument
	branch = flask.request.args.get("branch", default = None)
	status_limit = max(min(flask.request.args.get("limit", default = 20, type = int), 100), 1)

	project = service_client.get("/project/{project_identifier}".format(**locals()))
	branch_collection = project["services"]["revision_control"]["branches_for_status"]
	job_collection = service_client.get("/project/{project_identifier}/job_collection".format(**locals()), { "order_by": [ "identifier ascending" ] })

	context = { "filter_collection": [] }
	for job in job_collection:
		if job["properties"]["include_in_status"]:
			context["filter_collection"].append({
				"identifier": job["identifier"],
			 	"display_name": job["display_name"],
				"job": job["identifier"],
			})

	if branch is None:
		branch = branch_collection[0]

	status_parameters = {
		"branch": branch,
		"revision_limit": 20,
		"run_limit": 1000,
	}

	status = service_client.get("/project/{project_identifier}/status".format(**locals()), status_parameters)
	status = [ revision for index, revision in enumerate(status) if index == 0 or len(revision["runs"]) > 0 ][ : status_limit ]

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

	return flask.render_template("project/status.html", title = "Project " + project["display_name"], **view_data)
