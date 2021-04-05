import logging
from typing import Any

import flask

import bhamon_orchestra_website.helpers as helpers
from bhamon_orchestra_website.service_client import ServiceClient


logger = logging.getLogger("JobController")


class JobController:


	def __init__(self, service_client: ServiceClient) -> None:
		self._service_client = service_client


	def show_collection(self, project_identifier: str) -> Any:
		item_total = self._service_client.get("/project/{project_identifier}/job_count".format(**locals()))
		pagination = helpers.get_pagination(item_total, { "project_identifier": project_identifier })

		query_parameters = {
			"skip": (pagination["page_number"] - 1) * pagination["item_count"],
			"limit": pagination["item_count"],
			"order_by": [ "identifier ascending" ],
		}

		view_data = {
			"project": self._service_client.get("/project/{project_identifier}".format(**locals())),
			"job_collection": self._service_client.get("/project/{project_identifier}/job_collection".format(**locals()), parameters = query_parameters),
			"pagination": pagination,
		}

		helpers.add_display_names([ view_data["project"] ], view_data["job_collection"], [], [], [])

		return flask.render_template("job/collection.html", title = "Jobs", **view_data)


	def show(self, project_identifier: str, job_identifier: str) -> Any: # pylint: disable = unused-argument
		run_query_parameters = { "limit": 10, "order_by": [ "update_date descending" ] }
		worker_query_parameters = { "limit": 1000, "order_by": [ "identifier ascending" ] }

		view_data = {
			"project": self._service_client.get("/project/{project_identifier}".format(**locals())),
			"job": self._service_client.get("/project/{project_identifier}/job/{job_identifier}".format(**locals())),
			"run_collection": self._service_client.get("/project/{project_identifier}/job/{job_identifier}/runs".format(**locals()), parameters = run_query_parameters),
			"worker_collection": self._service_client.get("/worker_collection", parameters = worker_query_parameters),
		}

		view_data["job"]["project_display_name"] = view_data["project"]["display_name"]
		helpers.add_display_names([ view_data["project"] ], [ view_data["job"] ], view_data["run_collection"], [], view_data["worker_collection"])

		return flask.render_template("job/index.html", title = "Job " + view_data["job"]["display_name"], **view_data)


	def trigger(self, project_identifier: str, job_identifier: str) -> Any: # pylint: disable = unused-argument
		request_data = { "parameters": {}, "source": { "type": "user", "identifier": flask.session["user"]["identifier"] } }
		for key, value in flask.request.form.items():
			if key.startswith("parameter-"):
				request_data["parameters"][key[len("parameter-"):]] = value
		self._service_client.post("/project/{project_identifier}/job/{job_identifier}/trigger".format(**locals()), data = request_data)
		return flask.redirect(flask.request.referrer or flask.url_for("job_controller.show_collection", project_identifier = project_identifier))


	def enable(self, project_identifier: str, job_identifier: str) -> Any: # pylint: disable = unused-argument
		self._service_client.post("/project/{project_identifier}/job/{job_identifier}/enable".format(**locals()))
		return flask.redirect(flask.request.referrer or flask.url_for("job_controller.show_collection", project_identifier = project_identifier))


	def disable(self, project_identifier: str, job_identifier: str) -> Any: # pylint: disable = unused-argument
		self._service_client.post("/project/{project_identifier}/job/{job_identifier}/disable".format(**locals()))
		return flask.redirect(flask.request.referrer or flask.url_for("job_controller.show_collection", project_identifier = project_identifier))
