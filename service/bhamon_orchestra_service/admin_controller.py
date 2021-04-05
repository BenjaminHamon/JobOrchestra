import logging
import platform
from typing import Any

import flask


logger = logging.getLogger("AdminController")


class AdminController:


	def __init__(self, external_services: dict) -> None:
		self._external_services = external_services


	def information(self) -> Any: # pylint: disable = no-self-use
		return flask.jsonify({
			"python_version": platform.python_version() + "+" + platform.python_revision(),
			"service_version": flask.current_app.config["SERVICE_VERSION"],
			"service_date": flask.current_app.config["SERVICE_DATE"],
		})


	def get_service_collection(self) -> Any:
		return flask.jsonify(list(sorted(self._external_services.keys())))


	def get_service_status(self, service_identifier: str) -> Any:
		service = self._external_services.get(service_identifier, None)
		if service is None:
			flask.abort(404)
		return flask.jsonify(service.get_service_status())
