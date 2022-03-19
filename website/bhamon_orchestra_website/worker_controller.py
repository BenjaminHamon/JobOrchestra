import logging
from typing import Any

import flask

from bhamon_orchestra_website import helpers as website_helpers
from bhamon_orchestra_website.service_client import ServiceClient


logger = logging.getLogger("WorkerController")


class WorkerController:


	def __init__(self, service_client: ServiceClient) -> None:
		self._service_client = service_client


	def show_collection(self) -> Any:
		item_total = self._service_client.get("/worker_count")
		pagination = website_helpers.get_pagination(item_total, {})

		query_parameters = {
			"skip": (pagination["page_number"] - 1) * pagination["item_count"],
			"limit": pagination["item_count"],
			"order_by": [ "identifier ascending" ],
		}

		view_data = {
			"worker_collection": self._service_client.get("/worker_collection", parameters =  query_parameters),
			"pagination": pagination,
		}

		return flask.render_template("worker/collection.html", title = "Workers", **view_data)


	def show(self, worker_identifier: str) -> Any:
		project_query_parameters = { "limit": 1000, "order_by": [ "identifier ascending" ] }
		job_query_parameters = { "limit": 1000, "order_by": [ "identifier ascending" ] }
		run_query_parameters = { "limit": 10, "order_by": [ "update_date descending" ] }

		view_data = {
			"worker": self._service_client.get("/worker/" + worker_identifier),
			"project_collection": self._service_client.get("/project_collection", parameters = project_query_parameters),
			"job_collection": self._service_client.get("/worker/" + worker_identifier + "/job_collection", parameters = job_query_parameters),
			"run_collection": self._service_client.get("/worker/" + worker_identifier + "/run_collection", parameters = run_query_parameters),
		}

		owner = self._service_client.get("/user/" + view_data["worker"]["owner"])
		view_data["worker"]["owner_display_name"] = owner["display_name"]

		website_helpers.add_display_names(view_data["project_collection"], view_data["job_collection"], view_data["run_collection"], [], [ view_data["worker"] ])

		return flask.render_template("worker/index.html", title = "Worker " + worker_identifier, **view_data)


	def show_runs(self, worker_identifier: str) -> Any:
		query_parameters = {
			"worker": worker_identifier,
			"project": website_helpers.none_if_empty(flask.request.args.get("project", default = None)),
			"status": website_helpers.none_if_empty(flask.request.args.get("status", default = None)),
		}

		item_total = self._service_client.get("/worker/" + worker_identifier + "/run_count", parameters = query_parameters)
		pagination = website_helpers.get_pagination(item_total, { "worker_identifier": worker_identifier, **query_parameters })

		query_parameters.update({
			"skip": (pagination["page_number"] - 1) * pagination["item_count"],
			"limit": pagination["item_count"],
			"order_by": [ "update_date descending" ],
		})

		project_query_parameters = { "limit": 1000, "order_by": [ "identifier ascending" ] }
		job_query_parameters = { "limit": 1000, "order_by": [ "identifier ascending" ] }

		view_data = {
			"worker": self._service_client.get("/worker/" + worker_identifier),
			"project_collection": self._service_client.get("/project_collection", parameters = project_query_parameters),
			"job_collection": self._service_client.get("/worker/" + worker_identifier + "/job_collection", parameters = job_query_parameters),
			"status_collection": website_helpers.get_run_status_collection(),
			"run_collection": self._service_client.get("/worker/" + worker_identifier + "/run_collection", parameters = query_parameters),
			"pagination": pagination,
		}

		website_helpers.add_display_names(view_data["project_collection"], view_data["job_collection"], view_data["run_collection"], [], [ view_data["worker"] ])

		return flask.render_template("worker/runs.html", title = "Runs", **view_data)



	def disconnect(self, worker_identifier: str) -> Any:
		request_data = flask.request.form
		self._service_client.post("/worker/" + worker_identifier + "/disconnect", data = request_data)
		return flask.redirect(flask.request.referrer or flask.url_for("worker_controller.show_collection"))


	def enable(self, worker_identifier: str) -> Any:
		self._service_client.post("/worker/" + worker_identifier + "/enable")
		return flask.redirect(flask.request.referrer or flask.url_for("worker_controller.show_collection"))


	def disable(self, worker_identifier: str) -> Any:
		self._service_client.post("/worker/" + worker_identifier + "/disable")
		return flask.redirect(flask.request.referrer or flask.url_for("worker_controller.show_collection"))
