import logging
from typing import Any, Callable

import flask
import werkzeug

from bhamon_orchestra_model.authentication_provider import AuthenticationProvider
from bhamon_orchestra_model.authorization_provider import AuthorizationProvider
from bhamon_orchestra_model.database.database_client import DatabaseClient
from bhamon_orchestra_model.user_provider import UserProvider
import bhamon_orchestra_service.helpers as helpers


main_logger = logging.getLogger("Service")
request_logger = logging.getLogger("Request")


class Service:


	def __init__(self, # pylint: disable = too-many-arguments
			application: flask.Flask, database_client_factory: Callable[[], DatabaseClient],
			authentication_provider: AuthenticationProvider, authorization_provider: AuthorizationProvider,
			user_provider: UserProvider) -> None:

		self._application = application
		self._database_client_factory = database_client_factory
		self._authentication_provider = authentication_provider
		self._authorization_provider = authorization_provider
		self._user_provider = user_provider


	def log_request(self) -> None: # pylint: disable = no-self-use
		request_logger.info("(%s) %s %s", flask.request.environ["REMOTE_ADDR"], flask.request.method, flask.request.base_url)


	def setup_request_dependencies(self) -> None:

		def get_or_create_database_client() -> DatabaseClient:
			if getattr(flask.request, "database_client_instance", None) is None:
				flask.request.database_client_instance = self._database_client_factory()
			return flask.request.database_client_instance

		flask.request.database_client = get_or_create_database_client


	def teardown_request_dependencies(self, exception: Exception) -> None: # pylint: disable = no-self-use, unused-argument
		if getattr(flask.request, "database_client_instance", None) is not None:
			flask.request.database_client_instance.close()
			flask.request.database_client_instance = None


	def authorize_request(self) -> None:
		flask.request.user = None

		if flask.request.url_rule is None:
			return

		if flask.request.authorization is not None:
			user_identifier = flask.request.authorization.username
			token = flask.request.authorization.password
			database_client = flask.request.database_client()
			is_authenticated = self._authentication_provider.authenticate_with_token(database_client, user_identifier, token)
			flask.request.user = self._user_provider.get(database_client, user_identifier) if is_authenticated else None

		is_authorized = self._authorization_provider.authorize_request(flask.request.user, flask.request.method, flask.request.url_rule.rule)
		if not is_authorized:
			flask.abort(403)


	def handle_error(self, exception: Exception) -> None: # pylint: disable = no-self-use
		status_code = exception.code if isinstance(exception, werkzeug.exceptions.HTTPException) else 500
		status_message = helpers.get_error_message(status_code)
		request_logger.error("(%s) %s %s (StatusCode: %s)", flask.request.environ["REMOTE_ADDR"], flask.request.method, flask.request.base_url, status_code, exc_info = True)
		return flask.jsonify({ "status_code": status_code, "status_message": status_message }), status_code


	def home(self) -> Any:
		return flask.jsonify({
			"title": self._application.config["SERVICE_TITLE"],
			"copyright": self._application.config["SERVICE_COPYRIGHT"],
			"version": self._application.config["SERVICE_VERSION"],
			"date": self._application.config["SERVICE_DATE"],
		})


	def help(self) -> Any: # pylint: disable = redefined-builtin
		route_collection = []
		for rule in self._application.url_map.iter_rules():
			if not rule.rule.startswith("/static/"):
				route_collection.append(rule.rule)
		route_collection.sort()
		return flask.jsonify(route_collection)
