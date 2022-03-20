import logging
from typing import Any

import flask

from bhamon_orchestra_website import helpers as website_helpers
from bhamon_orchestra_website.service_client import ServiceClient


logger = logging.getLogger("ScheduleController")


class ScheduleController:


	def __init__(self, service_client: ServiceClient) -> None:
		self._service_client = service_client


	def show_collection(self, project_identifier: str) -> Any:
		query_parameters = {
			"job": website_helpers.none_if_empty(flask.request.args.get("job", default = None)),
		}

		item_total = self._service_client.get("/project/" + project_identifier + "/schedule_count", parameters = query_parameters)
		pagination = website_helpers.get_pagination(item_total, { "project_identifier": project_identifier, **query_parameters })

		query_parameters.update({
			"skip": (pagination["page_number"] - 1) * pagination["item_count"],
			"limit": pagination["item_count"],
			"order_by": [ "identifier ascending" ],
		})

		job_query_parameters = { "limit": 1000, "order_by": [ "identifier ascending" ] }

		view_data = {
			"project": self._service_client.get("/project/" + project_identifier),
			"job_collection": self._service_client.get("/project/" + project_identifier + "/job_collection", parameters = job_query_parameters),
			"schedule_collection": self._service_client.get("/project/" + project_identifier + "/schedule_collection", parameters = query_parameters),
			"pagination": pagination,
		}

		website_helpers.add_display_names([ view_data["project"] ], view_data["job_collection"], [], view_data["schedule_collection"], [])

		return flask.render_template("schedule/collection.html", title = "Schedules", **view_data)


	def show(self, project_identifier: str, schedule_identifier: str) -> Any:
		view_data = {
			"project": self._service_client.get("/project/" + project_identifier),
			"schedule": self._service_client.get("/project/" + project_identifier + "/schedule/" + schedule_identifier),
		}

		view_data["schedule"]["project_display_name"] = view_data["project"]["display_name"]

		job_route = "/project/" + project_identifier + "/job/" + view_data["schedule"]["job"]
		job = self._service_client.get_or_default(job_route, default_value = {})
		view_data["schedule"]["job_display_name"] = job.get("display_name", view_data["schedule"]["job"])

		return flask.render_template("schedule/index.html", title = "Schedule " + schedule_identifier, **view_data)


	def enable(self, project_identifier: str, schedule_identifier: str) -> Any:
		self._service_client.post("/project/" + project_identifier + "/schedule/" + schedule_identifier + "/enable")
		return flask.redirect(flask.request.referrer or flask.url_for("schedule_controller.show_collection", project_identifier = project_identifier))


	def disable(self, project_identifier: str, schedule_identifier: str) -> Any:
		self._service_client.post("/project/" + project_identifier + "/schedule/" + schedule_identifier + "/disable")
		return flask.redirect(flask.request.referrer or flask.url_for("schedule_controller.show_collection", project_identifier = project_identifier))
