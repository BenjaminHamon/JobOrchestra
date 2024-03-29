import logging
import platform
from typing import Any, List

import dateutil.parser
import flask
import requests

from bhamon_orchestra_website import helpers as website_helpers
from bhamon_orchestra_website.service_client import ServiceClient


logger = logging.getLogger("AdminController")


class AdminController: # pylint: disable = too-few-public-methods


	def __init__(self, application: flask.Flask, service_client: ServiceClient) -> None:
		self._application = application
		self._service_client = service_client


	def index(self) -> Any:
		view_data = {
			"website_information": self._get_website_information(),
			"service_information": None,
			"external_service_collection": None,
		}

		view_data["service_status"] = self._get_service_status()

		if view_data["service_status"]["status"] == "available":
			try:
				view_data["service_information"] = self._service_client.get("/admin/information")
				view_data["external_service_collection"] = self._get_status_for_external_services()
			except requests.HTTPError:
				logger.error("Failed to retrieve additional service information", exc_info = True)

		return flask.render_template("admin/index.html", title = "Administration", **view_data)


	def _get_website_information(self) -> dict:
		return {
			"python_version": platform.python_version() + "+" + platform.python_revision(),
			"website_version": self._application.config["WEBSITE_VERSION"],
			"website_date": dateutil.parser.parse(self._application.config["WEBSITE_DATE"]),
		}


	def _get_service_status(self) -> dict:
		try:
			self._service_client.get("/")

			return {
				"status": "available",
			}

		except requests.HTTPError as exception:
			return {
				"status": "unavailable",
				"status_code": exception.response.status_code,
				"status_message": website_helpers.get_error_message(exception.response.status_code),
			}


	def _get_status_for_external_services(self) -> List[dict]:
		external_services = self._service_client.get("/admin/service_collection")
		for service in external_services:
			service.update(self._service_client.get("/admin/service/" + service["identifier"] + "/status"))
		return external_services
