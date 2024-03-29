import datetime
import logging
from typing import Any, Optional

import dateutil.parser
import flask
import requests
import werkzeug

from bhamon_orchestra_model.date_time_provider import DateTimeProvider
from bhamon_orchestra_model.users.authorization_provider import AuthorizationProvider
from bhamon_orchestra_website import helpers as website_helpers
from bhamon_orchestra_website.service_client import ServiceClient


main_logger = logging.getLogger("Website")
request_logger = logging.getLogger("Request")


class Website:


	def __init__(self, application: flask.Flask, date_time_provider: DateTimeProvider,
			authorization_provider: AuthorizationProvider, service_client: ServiceClient) -> None:

		self._application = application
		self._date_time_provider = date_time_provider
		self._authorization_provider = authorization_provider
		self._service_client = service_client

		self.session_refresh_interval = datetime.timedelta(days = 1)


	def run(self, address: Optional[str] = None, port: Optional[int] = None, debug: Optional[bool] = None) -> None:
		self._application.run(host = address, port = port, debug = debug)


	def log_request(self) -> None:
		request_logger.info("(%s) %s %s", flask.request.environ["REMOTE_ADDR"], flask.request.method, flask.request.base_url)


	def refresh_session(self) -> None:
		flask.request.user = None

		if "token" in flask.session:
			now = self._date_time_provider.now()
			last_refresh = flask.session.get("last_refresh", None)
			if last_refresh is not None:
				if isinstance(last_refresh, str):
					last_refresh = dateutil.parser.parse(last_refresh)
				last_refresh = last_refresh.replace(tzinfo = datetime.timezone.utc)

			if last_refresh is None or now > last_refresh + self.session_refresh_interval:
				request_data = { "token_identifier": flask.session["token"]["token_identifier"] }

				try:
					self._service_client.post("/me/refresh_session", data = request_data)
					flask.session["user"] = self._service_client.get("/me")
					flask.session["last_refresh"] = now
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


	def handle_error(self, exception: Exception) -> Any:
		remote_address = flask.request.environ["REMOTE_ADDR"]
		status_code = exception.code if isinstance(exception, werkzeug.exceptions.HTTPException) else 500
		status_message = website_helpers.get_error_message(status_code)
		request_logger.error("(%s) %s %s (StatusCode: %s)", remote_address, flask.request.method, flask.request.base_url, status_code, exc_info = True)
		if flask.request.headers.get("Accept") == "application/json":
			return flask.jsonify({ "status_code": status_code, "status_message": status_message }), status_code
		return flask.render_template("error.html", title = "Error", status_message = status_message, status_code = status_code), status_code


	def home(self) -> Any:
		return flask.render_template("home.html", title = "Home")


	def list_routes(self) -> Any:
		route_collection = []
		for rule in self._application.url_map.iter_rules():
			if not rule.rule.startswith("/static/"):
				for method in rule.methods:
					if method in [ "GET", "POST", "PUT", "DELETE" ]:
						is_authorized = self._authorization_provider.authorize_request(flask.request.user, method, rule.rule)
						route_collection.append({ "method": method, "path": rule.rule, "is_authorized": is_authorized })

		route_collection.sort(key = lambda x: (x["path"], x["method"]))

		return flask.jsonify(route_collection)


	def proxy_to_service(self, route: str) -> flask.Response:
		service_response = self._service_client.proxy("/" + route)

		response = flask.Response(service_response.content, service_response.status_code)
		for header_key in service_response.headers:
			if header_key in [ "Content-Type" ] or header_key.startswith("X-Orchestra-"):
				response.headers[header_key] = service_response.headers[header_key]

		return response
