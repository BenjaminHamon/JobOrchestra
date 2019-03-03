import logging

import flask

import bhamon_build_website.service_client as service_client


logger = logging.getLogger("AdminController")


def administration_index():
	return flask.render_template("admin/index.html", title = "Administration")


def reload_service():
	service_client.post("/admin/reload")
	return flask.redirect(flask.request.referrer or flask.url_for("administration_index"))
