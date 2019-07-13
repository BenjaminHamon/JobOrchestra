# pylint: disable=unused-argument

import datetime
import logging

import flask
import requests

import bhamon_build_website.helpers as helpers
import bhamon_build_website.service_client as service_client


logger = logging.getLogger("UserController")


def user_collection_index():
	item_total = service_client.get("/user_count")
	pagination = helpers.get_pagination(item_total)

	query_parameters = {
		"skip": (pagination["page_number"] - 1) * pagination["item_count"],
		"limit": pagination["item_count"],
		"order_by": [ "identifier ascending" ],
	}

	user_collection = service_client.get("/user_collection", query_parameters)
	return flask.render_template("user/collection.html", title = "Users", user_collection = user_collection, pagination = pagination)


def user_index(user_identifier):
	user = service_client.get("/user/{user_identifier}".format(**locals()))
	user_tokens = service_client.get("/user/{user_identifier}/token_collection".format(**locals()), { "order_by": [ "update_date descending" ] })
	user_tokens.sort(key = lambda token: "expiration_date" in token)

	now = datetime.datetime.utcnow().replace(microsecond = 0).isoformat() + "Z"
	for token in user_tokens:
		token["is_active"] = token["expiration_date"] > now if "expiration_date" in token else True

	return flask.render_template("user/index.html", title = "User " + user["display_name"], user = user, user_tokens = user_tokens)


def create_user():
	if flask.request.method == "GET":
		return flask.render_template("user/create.html", title = "Create User")

	if flask.request.method == "POST":
		user_identifier = flask.request.form["identifier"]
		parameters = { "display_name": flask.request.form["display_name"] }

		try:
			service_client.post("/user/{user_identifier}/create".format(**locals()), data = parameters)
			flask.flash("User '%s' was created successfully." % user_identifier, "info")
			return flask.redirect(flask.url_for("user_collection_index"))
		except requests.HTTPError:
			flask.flash( "User '%s' could not be created." % user_identifier, "error")
			return flask.render_template("user/create.html", title = "Create User")

	return flask.abort(405)


def edit_user(user_identifier):
	return edit_user_resume(user_identifier, {})


def edit_user_resume(user_identifier, local_parameters):
	flask.request.form = service_client.get("/user/{user_identifier}".format(**locals()))
	flask.request.form.update(local_parameters)
	flask.request.form["roles"] = "\n".join(flask.request.form["roles"])
	return flask.render_template("user/edit.html", title = "Edit User", user_identifier = user_identifier)


def update_user_identity(user_identifier):
	parameters = { "display_name": flask.request.form["display_name"] }

	try:
		service_client.post("/user/{user_identifier}/update_identity".format(**locals()), data = parameters)
		flask.flash("User identity was updated successfully.", "info")
	except requests.HTTPError:
		flask.flash( "User identity could not be updated.", "error")
	return edit_user_resume(user_identifier, parameters)


def update_user_roles(user_identifier):
	parameters = { "roles": [ role.strip() for role in flask.request.form["roles"].splitlines() ] }

	try:
		service_client.post("/user/{user_identifier}/update_roles".format(**locals()), data = parameters)
		flask.flash("User roles were updated successfully.", "info")
	except requests.HTTPError:
		flask.flash( "User roles could not be updated.", "error")
	return edit_user_resume(user_identifier, parameters)


def enable_user(user_identifier):
	service_client.post("/user/{user_identifier}/enable".format(**locals()))
	return flask.redirect(flask.request.referrer or flask.url_for("user_collection_index"))


def disable_user(user_identifier):
	service_client.post("/user/{user_identifier}/disable".format(**locals()))
	return flask.redirect(flask.request.referrer or flask.url_for("user_collection_index"))


def delete_token(user_identifier, token_identifier):
	service_client.post("/user/{user_identifier}/token/{token_identifier}/delete".format(**locals()))
	return flask.redirect(flask.request.referrer or flask.url_for("user_index", user_identifier = user_identifier))
