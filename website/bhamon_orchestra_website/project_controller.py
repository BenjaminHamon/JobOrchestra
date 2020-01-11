# pylint: disable=unused-argument

import logging

import flask

import bhamon_orchestra_website.helpers as helpers
import bhamon_orchestra_website.service_client as service_client


logger = logging.getLogger("ProjectController")


def project_collection_index():
	item_total = service_client.get("/project_count")
	pagination = helpers.get_pagination(item_total)

	query_parameters = {
		"skip": (pagination["page_number"] - 1) * pagination["item_count"],
		"limit": pagination["item_count"],
		"order_by": [ "identifier ascending" ],
	}

	project_collection = service_client.get("/project_collection", query_parameters)
	return flask.render_template("project/collection.html", title = "Projects", project_collection = project_collection, pagination = pagination)


def project_index(project_identifier):
	project = service_client.get("/project/{project_identifier}".format(**locals()))
	return flask.render_template("project/index.html", title = "Project " + project["identifier"], project = project)
