from typing import Any, Optional

import flask

from bhamon_orchestra_model.serialization.serializer import Serializer
import bhamon_orchestra_service.helpers as helpers


class ResponseBuilder:


	def __init__(self, application: flask.Flask, serializer: Serializer) -> None:
		self._application = application
		self._serializer = serializer


	def create_empty_response(self) -> Any:
		return self._application.response_class("", status = 204)


	def create_data_response(self, data: Optional[Any], status_code = 200) -> Any:
		serialized_data = self._serializer.serialize_to_string(data)
		return self._application.response_class(serialized_data, status = status_code, mimetype = self._serializer.get_content_type())


	def create_error_response(self, status_code: int) -> Any:
		status_message = helpers.get_error_message(status_code)
		error_data = { "status_code": status_code, "status_message": status_message }
		return self.create_data_response(error_data, status_code = status_code)
