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
			flask.flash("User '%s' was created successfully." % user_identifier, "success")
			return flask.redirect(flask.url_for("user_collection_index"))
		except requests.HTTPError as exception:
			flask.flash("User '%s' could not be created: %s." % (user_identifier, helpers.get_error_message(exception.response.status_code)), "error")
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
		flask.flash("Identity for user '%s' was updated successfully." % user_identifier, "success")
	except requests.HTTPError as exception:
		flask.flash("Identity for user '%s' could not be updated: %s." % (user_identifier, helpers.get_error_message(exception.response.status_code)), "error")
	return edit_user_resume(user_identifier, parameters)


def update_user_roles(user_identifier):
	parameters = { "roles": [ role.strip() for role in flask.request.form["roles"].splitlines() ] }

	try:
		service_client.post("/user/{user_identifier}/update_roles".format(**locals()), data = parameters)
		flask.flash("Roles for user '%s' were updated successfully." % user_identifier, "success")
	except requests.HTTPError as exception:
		flask.flash( "Roles for user '%s' could not be updated: %s." % (user_identifier, helpers.get_error_message(exception.response.status_code)), "error")
	return edit_user_resume(user_identifier, parameters)


def enable_user(user_identifier):
	service_client.post("/user/{user_identifier}/enable".format(**locals()))
	return flask.redirect(flask.request.referrer or flask.url_for("user_collection_index"))


def disable_user(user_identifier):
	service_client.post("/user/{user_identifier}/disable".format(**locals()))
	return flask.redirect(flask.request.referrer or flask.url_for("user_collection_index"))


def reset_user_password(user_identifier):
	if flask.request.method == "GET":
		return flask.render_template("user/reset_password.html", title = "Reset User Password", user_identifier = user_identifier)

	if flask.request.method == "POST":
		parameters = { "password": flask.request.form["password"] }

		try:
			service_client.post("/user/{user_identifier}/reset_password".format(**locals()), data = parameters)
			flask.flash("Password for user '%s' was set successfully." % user_identifier, "success")
			return flask.redirect(flask.url_for("user_index", user_identifier = user_identifier))
		except requests.HTTPError as exception:
			flask.flash("Password for user '%s' could not be set: %s." % (user_identifier, helpers.get_error_message(exception.response.status_code)), "error")
			return flask.render_template("user/reset_password.html", title = "Reset User Password", user_identifier = user_identifier)

	return flask.abort(405)


def create_user_token(user_identifier):
	if flask.request.method == "GET":
		return flask.render_template("user/create_token.html", title = "Create User Authentication Token", user_identifier = user_identifier)

	if flask.request.method == "POST":
		parameters = { "description": flask.request.form["description"] }
		if flask.request.form["expiration"]:
			parameters["expiration"]  = flask.request.form["expiration"]

		try:
			token = service_client.post("/user/{user_identifier}/token_create".format(**locals()), data = parameters)
			flask.flash("Token '%s' was created successfully." % token["token_identifier"], "success")
			flask.flash("Token secret: '%s'." % token["secret"], "info")
			return flask.redirect(flask.url_for("user_index", user_identifier = user_identifier))
		except requests.HTTPError as exception:
			flask.flash("Token could not be created: %s." % helpers.get_error_message(exception.response.status_code), "error")
			return flask.render_template("user/create_token.html", title = "Create User Authentication Token", user_identifier = user_identifier)

	return flask.abort(405)


def delete_user_token(user_identifier, token_identifier):
	try:
		service_client.post("/user/{user_identifier}/token/{token_identifier}/delete".format(**locals()))
		flask.flash("Token '%s' was deleted successfully." % token_identifier, "success")
	except requests.HTTPError as exception:
		flask.flash("Token '%s' could not be deleted: %s." % (token_identifier, helpers.get_error_message(exception.response.status_code)), "error")
	return flask.redirect(flask.url_for("user_index", user_identifier = user_identifier))
