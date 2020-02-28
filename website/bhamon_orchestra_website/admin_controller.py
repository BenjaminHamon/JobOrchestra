import logging
import platform

import flask
import requests

import bhamon_orchestra_website
import bhamon_orchestra_website.helpers as helpers
import bhamon_orchestra_website.service_client as service_client


logger = logging.getLogger("AdminController")


def index():
	view_data = {
		"website_information": _get_website_information(),
		"service_information": None,
		"external_service_collection": None,
	}

	try:
		service_client.get("/")
		view_data["service_status"] = { "status": "available" }
	except requests.HTTPError as exception:
		view_data["service_status"] = {
			"status": "unavailable",
			"status_code": exception.response.status_code,
			"status_message": helpers.get_error_message(exception.response.status_code),
		}

	if view_data["service_status"]["status"] == "available":
		try:
			view_data["service_information"] = service_client.get("/admin/information")
			view_data["external_service_collection"] = _get_status_for_external_services()
		except requests.HTTPError:
			logger.error("Failed to retrieve additional service information", exc_info = True)

	return flask.render_template("admin/index.html", title = "Administration", **view_data)


def _get_website_information():
	return {
		"python_version": platform.python_version() + "+" + platform.python_revision(),
		"website_version": bhamon_orchestra_website.__version__,
		"website_version_date": bhamon_orchestra_website.__date__,
	}


def _get_status_for_external_services():
	external_services = service_client.get("/admin/service_collection")

	status_collection = []
	for service in external_services:
		status_collection.append(service_client.get("/admin/service/{service}".format(service = service)))
	return status_collection
