import logging
import platform

import flask
import requests

import bhamon_build_website
import bhamon_build_website.helpers as helpers
import bhamon_build_website.service_client as service_client


logger = logging.getLogger("AdminController")


def administration_index():
	try:
		service_client.get("/")
		service_status = { "status": "available" }
	except requests.HTTPError as exception:
		service_status = {
			"status": "unavailable",
			"status_code": exception.response.status_code,
			"status_message": helpers.get_error_message(exception.response.status_code),
		}

	service_information = None
	try:
		service_information = service_client.get("/admin/information")
	except requests.HTTPError:
		logger.error("Failed to retrieve service information", exc_info = True)

	view_data = {
		"service_status": service_status,
		"service_information": service_information,
		"website_information": {
			"python_version": platform.python_version() + "+" + platform.python_revision(),
			"website_version": bhamon_build_website.__version__,
			"website_version_date": bhamon_build_website.__date__,
		}
	}

	return flask.render_template("admin/index.html", title = "Administration", **view_data)


def reload_service():
	service_client.post("/admin/reload")
	return flask.redirect(flask.request.referrer or flask.url_for("administration_index"))
