import logging
from typing import Any, Optional

import flask
import requests

from bhamon_orchestra_model.authorization_provider import AuthorizationProvider
from bhamon_orchestra_model.date_time_provider import DateTimeProvider

import bhamon_orchestra_website.helpers as helpers
from bhamon_orchestra_website.service_client import ServiceClient


logger = logging.getLogger("UserController")


class UserController:


	def __init__(self, date_time_provider: DateTimeProvider,
			authorization_provider: AuthorizationProvider, service_client: ServiceClient) -> None:

		self._date_time_provider = date_time_provider
		self._authorization_provider = authorization_provider
		self._service_client = service_client


	def show_collection(self) -> Any:
		item_total = self._service_client.get("/user_count")
		pagination = helpers.get_pagination(item_total, {})

		query_parameters = {
			"skip": (pagination["page_number"] - 1) * pagination["item_count"],
			"limit": pagination["item_count"],
			"order_by": [ "identifier ascending" ],
		}

		view_data = {
			"user_collection": self._service_client.get("/user_collection", parameters = query_parameters),
			"pagination": pagination,
		}

		return flask.render_template("user/collection.html", title = "Users", **view_data)


	def show(self, user_identifier: str) -> Any:
		user = self._service_client.get("/user/" + user_identifier)

		view_data = {
			"user": user,
		}

		if self._authorization_provider.authorize_view(flask.request.user, "user-security"):
			token_query_parameters = { "order_by": [ "update_date descending" ] }
			user_tokens = self._service_client.get("/user/" + user_identifier + "/token_collection", parameters = token_query_parameters)
			user_tokens.sort(key = lambda token: token["expiration_date"] is not None)

			now = self._date_time_provider.serialize(self._date_time_provider.now())
			for token in user_tokens:
				token["is_active"] = token["expiration_date"] > now if token["expiration_date"] is not None else True

			view_data["user_tokens"] = user_tokens

		return flask.render_template("user/index.html", title = "User " + user["display_name"], **view_data)


	def create(self) -> Any:
		if flask.request.method == "GET":
			return flask.render_template("user/create.html", title = "Create User")

		if flask.request.method == "POST":
			user_identifier = flask.request.form["identifier"]
			request_data = { "display_name": flask.request.form["display_name"] }

			try:
				self._service_client.post("/user/" + user_identifier + "/create", data = request_data)
				flask.flash("User '%s' was created successfully." % user_identifier, "success")
				return flask.redirect(flask.url_for("user_controller.show_collection"))
			except requests.HTTPError as exception:
				flask.flash("User '%s' could not be created: %s." % (user_identifier, helpers.get_error_message(exception.response.status_code)), "error")
				return flask.render_template("user/create.html", title = "Create User")

		return flask.abort(405)


	def edit(self, user_identifier: str, form_data: Optional[dict] = None) -> Any:
		if form_data is None:
			form_data = {}

		user = self._service_client.get("/user/" + user_identifier)

		flask.request.form = user
		flask.request.form.update(form_data)
		flask.request.form["roles"] = "\n".join(flask.request.form["roles"])
		return flask.render_template("user/edit.html", title = "Edit User", user = user)


	def update_identity(self, user_identifier: str) -> Any:
		request_data = { "display_name": flask.request.form["display_name"] }

		try:
			self._service_client.post("/user/" + user_identifier + "/update_identity", data = request_data)
			flask.flash("Identity for user '%s' was updated successfully." % user_identifier, "success")
		except requests.HTTPError as exception:
			flask.flash("Identity for user '%s' could not be updated: %s." % (user_identifier, helpers.get_error_message(exception.response.status_code)), "error")
		return self.edit(user_identifier, request_data)


	def update_roles(self, user_identifier: str) -> Any:
		request_data = { "roles": [ role.strip() for role in flask.request.form["roles"].splitlines() ] }

		try:
			self._service_client.post("/user/" + user_identifier + "/update_roles", data = request_data)
			flask.flash("Roles for user '%s' were updated successfully." % user_identifier, "success")
		except requests.HTTPError as exception:
			flask.flash( "Roles for user '%s' could not be updated: %s." % (user_identifier, helpers.get_error_message(exception.response.status_code)), "error")
		return self.edit(user_identifier, request_data)


	def enable(self, user_identifier: str) -> Any:
		self._service_client.post("/user/" + user_identifier + "/enable")
		return flask.redirect(flask.request.referrer or flask.url_for("user_controller.show_collection"))


	def disable(self, user_identifier: str) -> Any:
		self._service_client.post("/user/" + user_identifier + "/disable")
		return flask.redirect(flask.request.referrer or flask.url_for("user_controller.show_collection"))


	def reset_password(self, user_identifier: str) -> Any:
		if flask.request.method == "GET":
			user = self._service_client.get("/user/" + user_identifier)
			return flask.render_template("user/reset_password.html", title = "Reset User Password", user = user)

		if flask.request.method == "POST":
			request_data = { "password": flask.request.form["password"] }

			try:
				self._service_client.post("/user/" + user_identifier + "/reset_password", data = request_data)
				flask.flash("Password for user '%s' was set successfully." % user_identifier, "success")
				return flask.redirect(flask.url_for("user_controller.show", user_identifier = user_identifier))
			except requests.HTTPError as exception:
				flask.flash("Password for user '%s' could not be set: %s." % (user_identifier, helpers.get_error_message(exception.response.status_code)), "error")
				user = self._service_client.get("/user/" + user_identifier)
				return flask.render_template("user/reset_password.html", title = "Reset User Password", user = user)

		return flask.abort(405)


	def create_token(self, user_identifier: str) -> Any:
		if flask.request.method == "GET":
			user = self._service_client.get("/user/" + user_identifier)
			return flask.render_template("user/create_token.html", title = "Create User Authentication Token", user = user)

		if flask.request.method == "POST":
			request_data = { "description": flask.request.form["description"] }
			if flask.request.form["expiration"]:
				request_data["expiration"]  = flask.request.form["expiration"]

			try:
				token = self._service_client.post("/user/" + user_identifier + "/token_create", data = request_data)
				flask.flash("Token '%s' was created successfully." % token["token_identifier"], "success")
				flask.flash("Token secret: '%s'." % token["secret"], "info")
				return flask.redirect(flask.url_for("user_controller.show", user_identifier = user_identifier))
			except requests.HTTPError as exception:
				flask.flash("Token could not be created: %s." % helpers.get_error_message(exception.response.status_code), "error")
				user = self._service_client.get("/user/" + user_identifier)
				return flask.render_template("user/create_token.html", title = "Create User Authentication Token", user = user)

		return flask.abort(405)


	def delete_token(self, user_identifier: str, token_identifier: str) -> Any:
		try:
			self._service_client.post("/user/" + user_identifier + "/token/" + token_identifier + "/delete")
			flask.flash("Token '%s' was deleted successfully." % token_identifier, "success")
		except requests.HTTPError as exception:
			flask.flash("Token '%s' could not be deleted: %s." % (token_identifier, helpers.get_error_message(exception.response.status_code)), "error")
		return flask.redirect(flask.url_for("user_controller.show", user_identifier = user_identifier))
