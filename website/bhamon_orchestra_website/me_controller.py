import logging
from typing import Any

import flask
import requests

from bhamon_orchestra_model.date_time_provider import DateTimeProvider

import bhamon_orchestra_website.helpers as helpers
from bhamon_orchestra_website.service_client import ServiceClient


logger = logging.getLogger("MeController")


class MeController:


	def __init__(self, date_time_provider: DateTimeProvider, service_client: ServiceClient) -> None:
		self._date_time_provider = date_time_provider
		self._service_client = service_client


	def login(self) -> Any:
		if flask.request.method == "GET":
			if "token" in flask.session:
				return flask.redirect(flask.url_for("website.home"))
			return flask.render_template("me/login.html", title = "Log In")

		if flask.request.method == "POST":
			now = self._date_time_provider.now()
			parameters = { "user": flask.request.form["user"], "password": flask.request.form["password"] }

			try:
				flask.session["token"] = self._service_client.post("/me/login", data = parameters)
				flask.session["user"] = self._service_client.get("/me")
				flask.session["last_refresh"] = self._date_time_provider.serialize(now)
				flask.session.permanent = True
				flask.flash("Login succeeded.", "success")
				return flask.redirect(flask.url_for("website.home"))
			except requests.HTTPError as exception:
				if exception.response.status_code == 403:
					flask.session.clear()
				flask.flash("Login failed: %s." % helpers.get_error_message(exception.response.status_code), "error")
				return flask.render_template("me/login.html", title = "Log In")

		return flask.abort(405)


	def logout(self) -> Any:
		if flask.request.method == "GET":
			if "token" not in flask.session:
				return flask.redirect(flask.url_for("website.home"))
			return flask.render_template("me/logout.html", title = "Log Out")

		if flask.request.method == "POST":
			if "token" not in flask.session:
				return flask.redirect(flask.url_for("website.home"))

			try:
				self._service_client.post("/me/logout", { "token_identifier": flask.session["token"]["token_identifier"] })
				flask.flash("Logout succeeded.", "success")
				flask.session.clear()
				return flask.redirect(flask.url_for("website.home"))
			except requests.HTTPError as exception:
				flask.flash("Logout failed: %s." % helpers.get_error_message(exception.response.status_code), "error")
				return flask.render_template("me/logout.html", title = "Log Out")

		return flask.abort(405)


	def refresh_session(self) -> Any:
		now = self._date_time_provider.now()

		try:
			self._service_client.post("/me/refresh_session", { "token_identifier": flask.session["token"]["token_identifier"] })
			flask.session["user"] = self._service_client.get("/me")
			flask.session["last_refresh"] = self._date_time_provider.serialize(now)
		except requests.HTTPError as exception:
			if exception.response.status_code == 403:
				flask.session.clear()

		return flask.redirect(flask.url_for("me_controller.show_profile"))


	def show_profile(self) -> Any:
		user = self._service_client.get("/me")
		user_tokens = self._service_client.get("/me/token_collection", { "order_by": [ "update_date descending" ] })
		user_tokens.sort(key = lambda token: token["expiration_date"] is not None)

		now = self._date_time_provider.serialize(self._date_time_provider.now())
		for token in user_tokens:
			token["is_active"] = token["expiration_date"] > now if token["expiration_date"] is not None else True

		return flask.render_template("me/profile.html", title = "Profile", user = user, user_tokens = user_tokens)


	def change_password(self) -> Any:
		if flask.request.method == "GET":
			return flask.render_template("me/change_password.html", title = "Change Password")

		if flask.request.method == "POST":
			if flask.request.form["new-password"] != flask.request.form["new-password-confirmation"]:
				flask.flash("Password change failed: new passwords do not match.", "error")
				return flask.render_template("me/change_password.html", title = "Change Password")

			parameters = { "old_password": flask.request.form["old-password"], "new_password": flask.request.form["new-password"] }

			try:
				self._service_client.post("/me/change_password", data = parameters)
				flask.flash("Password change succeeded.", "success")
				return flask.redirect(flask.url_for("me_controller.show_profile"))
			except requests.HTTPError as exception:
				flask.flash("Password change failed: %s." % helpers.get_error_message(exception.response.status_code), "error")
				return flask.render_template("me/change_password.html", title = "Change Password")

		return flask.abort(405)


	def create_token(self) -> Any:
		if flask.request.method == "GET":
			return flask.render_template("me/create_token.html", title = "Create Authentication Token")

		if flask.request.method == "POST":
			parameters = { "description": flask.request.form["description"] }
			if flask.request.form["expiration"]:
				parameters["expiration"]  = flask.request.form["expiration"]

			try:
				token = self._service_client.post("/me/token_create", data = parameters)
				flask.flash("Token '%s' was created successfully." % token["token_identifier"], "success")
				flask.flash("Token secret: '%s'." % token["secret"], "info")
				return flask.redirect(flask.url_for("me_controller.show_profile"))
			except requests.HTTPError as exception:
				flask.flash("Token could not be created: %s." % helpers.get_error_message(exception.response.status_code), "error")
				return flask.render_template("me/create_token.html", title = "Create Authentication Token")

		return flask.abort(405)


	def delete_token(self, token_identifier: str) -> Any:
		try:
			self._service_client.post("/me/token/{token_identifier}/delete".format(**locals()))
			flask.flash("Token '%s' was deleted successfully." % token_identifier, "success")
		except requests.HTTPError as exception:
			flask.flash("Token '%s' could not be deleted: %s." % (token_identifier, helpers.get_error_message(exception.response.status_code)), "error")
		return flask.redirect(flask.url_for("me_controller.show_profile"))
