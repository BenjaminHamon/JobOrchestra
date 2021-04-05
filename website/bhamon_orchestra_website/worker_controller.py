import logging
from typing import Any

import flask

import bhamon_orchestra_website.helpers as helpers
from bhamon_orchestra_website.service_client import ServiceClient


logger = logging.getLogger("WorkerController")


class WorkerController:


	def __init__(self, service_client: ServiceClient) -> None:
		self._service_client = service_client


	def show_collection(self) -> Any:
		item_total = self._service_client.get("/worker_count")
		pagination = helpers.get_pagination(item_total, {})

		query_parameters = {
			"skip": (pagination["page_number"] - 1) * pagination["item_count"],
			"limit": pagination["item_count"],
			"order_by": [ "identifier ascending" ],
		}

		view_data = {
			"worker_collection": self._service_client.get("/worker_collection", query_parameters),
			"pagination": pagination,
		}

		return flask.render_template("worker/collection.html", title = "Workers", **view_data)


	def show(self, worker_identifier: str) -> Any:
		view_data = {
			"worker": self._service_client.get("/worker/{worker_identifier}".format(**locals())),
			"project_collection": self._service_client.get("/project_collection".format(**locals()), { "limit": 1000, "order_by": [ "identifier ascending" ] }),
			"job_collection": self._service_client.get("/worker/{worker_identifier}/job_collection".format(**locals()), { "limit": 1000, "order_by": [ "identifier ascending" ] }),
			"run_collection": self._service_client.get("/worker/{worker_identifier}/run_collection".format(**locals()), { "limit": 10, "order_by": [ "update_date descending" ] }),
		}

		owner = self._service_client.get("/user/{user_identifier}".format(user_identifier = view_data["worker"]["owner"]))
		view_data["worker"]["owner_display_name"] = owner["display_name"]

		helpers.add_display_names(view_data["project_collection"], view_data["job_collection"], view_data["run_collection"], [], [ view_data["worker"] ])

		return flask.render_template("worker/index.html", title = "Worker " + worker_identifier, **view_data)


	def show_runs(self, worker_identifier: str) -> Any:
		query_parameters = {
			"worker": worker_identifier,
			"project": helpers.none_if_empty(flask.request.args.get("project", default = None)),
			"status": helpers.none_if_empty(flask.request.args.get("status", default = None)),
		}

		item_total = self._service_client.get("/worker/{worker_identifier}/run_count".format(**locals()), query_parameters)
		pagination = helpers.get_pagination(item_total, { "worker_identifier": worker_identifier, **query_parameters })

		query_parameters.update({
			"skip": (pagination["page_number"] - 1) * pagination["item_count"],
			"limit": pagination["item_count"],
			"order_by": [ "update_date descending" ],
		})

		view_data = {
			"worker": self._service_client.get("/worker/{worker_identifier}".format(**locals())),
			"project_collection": self._service_client.get("/project_collection".format(**locals()), { "limit": 1000, "order_by": [ "identifier ascending" ] }),
			"job_collection": self._service_client.get("/worker/{worker_identifier}/job_collection".format(**locals()), { "limit": 1000, "order_by": [ "identifier ascending" ] }),
			"status_collection": helpers.get_run_status_collection(),
			"run_collection": self._service_client.get("/worker/{worker_identifier}/run_collection".format(**locals()), query_parameters),
			"pagination": pagination,
		}

		helpers.add_display_names(view_data["project_collection"], view_data["job_collection"], view_data["run_collection"], [], [ view_data["worker"] ])

		return flask.render_template("worker/runs.html", title = "Runs", **view_data)



	def disconnect(self, worker_identifier: str) -> Any: # pylint: disable = unused-argument
		parameters = flask.request.form
		self._service_client.post("/worker/{worker_identifier}/disconnect".format(**locals()), parameters)
		return flask.redirect(flask.request.referrer or flask.url_for("worker_controller.show_collection"))


	def enable(self, worker_identifier: str) -> Any: # pylint: disable = unused-argument
		self._service_client.post("/worker/{worker_identifier}/enable".format(**locals()))
		return flask.redirect(flask.request.referrer or flask.url_for("worker_controller.show_collection"))


	def disable(self, worker_identifier: str) -> Any: # pylint: disable = unused-argument
		self._service_client.post("/worker/{worker_identifier}/disable".format(**locals()))
		return flask.redirect(flask.request.referrer or flask.url_for("worker_controller.show_collection"))
