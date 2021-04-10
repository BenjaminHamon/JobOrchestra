import datetime
import logging
from typing import Any

import flask
import requests
import werkzeug

from bhamon_orchestra_model.authorization_provider import AuthorizationProvider
from bhamon_orchestra_model.date_time_provider import DateTimeProvider
import bhamon_orchestra_website.helpers as helpers
from bhamon_orchestra_website.service_client import ServiceClient


main_logger = logging.getLogger("Website")
request_logger = logging.getLogger("Request")


class Website:


	def __init__(self, date_time_provider: DateTimeProvider,
			authorization_provider: AuthorizationProvider, service_client: ServiceClient) -> None:

		self._date_time_provider = date_time_provider
		self._authorization_provider = authorization_provider
		self._service_client = service_client

		self.session_refresh_interval = datetime.timedelta(days = 1)


	def log_request(self) -> None: # pylint: disable = no-self-use
		request_logger.info("(%s) %s %s", flask.request.environ["REMOTE_ADDR"], flask.request.method, flask.request.base_url)


	def refresh_session(self) -> None:
		flask.request.user = None

		if "token" in flask.session:
			now = self._date_time_provider.now()
			last_refresh = flask.session.get("last_refresh", None)
			if last_refresh is not None:
				last_refresh = self._date_time_provider.deserialize(last_refresh)

			if last_refresh is None or now > last_refresh + self.session_refresh_interval:
				request_data = { "token_identifier": flask.session["token"]["token_identifier"] }

				try:
					self._service_client.post("/me/refresh_session", data = request_data)
					flask.session["user"] = self._service_client.get("/me")
					flask.session["last_refresh"] = self._date_time_provider.serialize(now)
				except requests.HTTPError as exception:
					if exception.response.status_code == 403:
						flask.session.clear()
					raise

		flask.request.user = flask.session.get("user", None)


	def authorize_request(self) -> None:
		if flask.request.url_rule is None:
			return
		if not self._authorization_provider.authorize_request(flask.request.user, flask.request.method, flask.request.url_rule.rule):
			flask.abort(403)


	def authorize_view(self, view: str) -> bool:
		return self._authorization_provider.authorize_view(flask.request.user, view)


	def handle_error(self, exception: Exception) -> Any: # pylint: disable = no-self-use
		status_code = exception.code if isinstance(exception, werkzeug.exceptions.HTTPException) else 500
		status_message = helpers.get_error_message(status_code)
		request_logger.error("(%s) %s %s (StatusCode: %s)", flask.request.environ["REMOTE_ADDR"], flask.request.method, flask.request.base_url, status_code, exc_info = True)
		if flask.request.headers.get("Accept") == "application/json":
			return flask.jsonify({ "status_code": status_code, "status_message": status_message }), status_code
		return flask.render_template("error.html", title = "Error", status_message = status_message, status_code = status_code), status_code


	def home(self) -> Any: # pylint: disable = no-self-use
		return flask.render_template("home.html", title = "Home")


	def proxy_to_service(self, route: str) -> flask.Response:
		service_response = self._service_client.proxy("/" + route)

		response = flask.Response(service_response.content, service_response.status_code)
		for header_key in service_response.headers:
			if header_key in [ "Content-Type" ] or header_key.startswith("X-Orchestra-"):
				response.headers[header_key] = service_response.headers[header_key]

		return response
