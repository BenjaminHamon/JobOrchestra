import logging
from typing import Any

import flask

import bhamon_orchestra_website.helpers as helpers
from bhamon_orchestra_website.service_client import ServiceClient


logger = logging.getLogger("ProjectController")


class ProjectController:


	def __init__(self, service_client: ServiceClient) -> None:
		self._service_client = service_client


	def show_collection(self) -> Any:
		item_total = self._service_client.get("/project_count")
		pagination = helpers.get_pagination(item_total, {})

		query_parameters = {
			"skip": (pagination["page_number"] - 1) * pagination["item_count"],
			"limit": pagination["item_count"],
			"order_by": [ "identifier ascending" ],
		}

		project_collection = self._service_client.get("/project_collection", parameters = query_parameters)
		return flask.render_template("project/collection.html", title = "Projects", project_collection = project_collection, pagination = pagination)


	def show(self, project_identifier: str) -> Any:
		run_query_parameters = { "limit": 10, "order_by": [ "update_date descending" ] }

		view_data = {
			"project": self._service_client.get("/project/" + project_identifier),
			"run_collection": self._service_client.get("/project/" + project_identifier + "/run_collection", parameters = run_query_parameters),
		}

		if "revision_control" in view_data["project"]["services"]:
			view_data["revision_collection"] = []
			for reference in view_data["project"]["services"]["revision_control"]["references_for_status"]:
				reference_status = self._service_client.get("/project/" + project_identifier + "/repository/revision/" + reference + "/status")
				view_data["revision_collection"].append(reference_status)

		job_query_parameters = { "order_by": [ "identifier ascending" ] }
		worker_query_parameters = { "order_by": [ "identifier ascending" ] }

		job_collection = self._service_client.get("/project/" + project_identifier + "/job_collection", parameters = job_query_parameters)
		worker_collection = self._service_client.get("/worker_collection", parameters = worker_query_parameters)
		helpers.add_display_names([ view_data["project"] ], job_collection, view_data["run_collection"], [], worker_collection)

		return flask.render_template("project/index.html", title = "Project " + view_data["project"]["display_name"], **view_data)


	def show_status(self, project_identifier: str) -> Any: # pylint: disable = too-many-locals
		reference = flask.request.args.get("reference", default = None)
		status_limit = max(min(flask.request.args.get("limit", default = 20, type = int), 100), 1)

		job_query_parameters = { "order_by": [ "identifier ascending" ] }

		project = self._service_client.get("/project/" + project_identifier)
		reference_collection = project["services"]["revision_control"]["references_for_status"]
		job_collection = self._service_client.get("/project/" + project_identifier + "/job_collection", parameters = job_query_parameters)

		context = { "filter_collection": [] }
		for job in job_collection:
			if job["properties"]["include_in_status"]:
				context["filter_collection"].append({
					"identifier": job["identifier"],
					"display_name": job["display_name"],
					"job": job["identifier"],
				})

		if reference is None:
			reference = reference_collection[0]

		status_parameters = {
			"reference": reference,
			"revision_limit": 20,
			"run_limit": 1000,
		}

		status = self._service_client.get("/project/" + project_identifier + "/status", parameters = status_parameters)
		status = [ revision for index, revision in enumerate(status) if index == 0 or len(revision["runs"]) > 0 ][ : status_limit ]

		for revision in status:
			revision["runs_by_filter"] = { f["identifier"]: [] for f in context["filter_collection"] }
			for run in revision["runs"]:
				for run_filter in context["filter_collection"]:
					if run["job"] == run_filter["job"]:
						revision["runs_by_filter"][run_filter["identifier"]].append(run)

		view_data = {
			"project": project,
			"project_reference": reference,
			"project_reference_collection": reference_collection,
			"project_context": context,
			"project_status": status,
		}

		return flask.render_template("project/status.html", title = "Project " + project["display_name"], **view_data)
