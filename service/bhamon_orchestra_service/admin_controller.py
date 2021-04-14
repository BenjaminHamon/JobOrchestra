import logging
import platform
from typing import Any

import flask

from bhamon_orchestra_service.response_builder import ResponseBuilder


logger = logging.getLogger("AdminController")


class AdminController:


	def __init__(self, response_builder: ResponseBuilder, external_services: dict) -> None:
		self._response_builder = response_builder
		self._external_services = external_services


	def information(self) -> Any:
		admin_information = {
			"python_version": platform.python_version() + "+" + platform.python_revision(),
			"service_version": flask.current_app.config["SERVICE_VERSION"],
			"service_date": flask.current_app.config["SERVICE_DATE"],
		}

		return self._response_builder.create_data_response(admin_information)


	def get_service_collection(self) -> Any:
		service_collection = list(sorted(self._external_services.keys()))
		return self._response_builder.create_data_response(service_collection)


	def get_service_status(self, service_identifier: str) -> Any:
		service = self._external_services.get(service_identifier, None)
		if service is None:
			flask.abort(404)

		service_status = service.get_service_status()
		return self._response_builder.create_data_response(service_status)
