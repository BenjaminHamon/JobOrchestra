import logging

import flask
import requests

import bhamon_build_website.helpers as helpers
import bhamon_build_website.service_client as service_client


logger = logging.getLogger("MeController")


def login():
	if flask.request.method == "GET":
		return flask.render_template("me/login.html", title = "Log In")

	if flask.request.method == "POST":
		parameters = { "user": flask.request.form["user"], "password": flask.request.form["password"] }

		try:
			flask.session["token"] = service_client.post("/me/login", data = parameters)
			flask.flash("Login succeeded.", "info")
			return flask.redirect(flask.url_for("home"))
		except requests.HTTPError as exception:
			flask.flash( "Login failed: %s." % helpers.get_error_message(exception.response.status_code), "error")
			return flask.render_template("me/login.html", title = "Log In")

	return flask.abort(405)


def logout():
	if flask.request.method == "GET":
		return flask.render_template("me/logout.html", title = "Log Out")

	if flask.request.method == "POST":
		try:
			service_client.post("/me/logout", { "token_identifier": flask.session["token"]["token_identifier"] })
			flask.flash("Logout succeeded.", "info")
			del flask.session["token"]
			return flask.redirect(flask.url_for("home"))
		except requests.HTTPError as exception:
			flask.flash( "Logout failed: %s." % helpers.get_error_message(exception.response.status_code), "error")
			return flask.render_template("me/logout.html", title = "Log Out")

	return flask.abort(405)


def my_profile():
	user = service_client.get("/me")
	return flask.render_template("me/profile.html", title = "Profile", user = user)
