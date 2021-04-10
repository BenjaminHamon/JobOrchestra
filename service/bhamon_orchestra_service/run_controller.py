import logging
from typing import Any

import flask

from bhamon_orchestra_model.run_provider import RunProvider
from bhamon_orchestra_model.serialization.serializer import Serializer
from bhamon_orchestra_service.response_builder import ResponseBuilder


logger = logging.getLogger("RunController")


class RunController:


	def __init__(self, response_builder: ResponseBuilder, serializer: Serializer, run_provider: RunProvider) -> None:
		self._response_builder = response_builder
		self._serializer = serializer
		self._run_provider = run_provider


	def get_count(self, project_identifier: str) -> Any:
		query_parameters = {
			"project": project_identifier,
			"job": flask.request.args.get("job", default = None),
			"worker": flask.request.args.get("worker", default = None),
			"status": flask.request.args.get("status", default = None),
		}

		database_client = flask.request.database_client()
		run_count = self._run_provider.count(database_client, **query_parameters)
		return self._response_builder.create_data_response(run_count)


	def get_collection(self, project_identifier: str) -> Any:
		query_parameters = {
			"project": project_identifier,
			"job": flask.request.args.get("job", default = None),
			"worker": flask.request.args.get("worker", default = None),
			"status": flask.request.args.get("status", default = None),
			"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
			"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
			"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
		}

		database_client = flask.request.database_client()
		run_collection = self._run_provider.get_list(database_client, **query_parameters)
		return self._response_builder.create_data_response(run_collection)


	def get(self, project_identifier: str, run_identifier: str) -> Any:
		database_client = flask.request.database_client()
		run = self._run_provider.get(database_client, project_identifier, run_identifier)
		return self._response_builder.create_data_response(run)


	def get_log(self, project_identifier: str, run_identifier: str) -> Any:
		log_text, log_cursor = self._run_provider.get_log(project_identifier, run_identifier)
		return flask.Response(log_text, mimetype = "text/plain", headers = { "X-Orchestra-FileCursor": log_cursor })


	def get_log_chunk(self, project_identifier: str, run_identifier: str) -> Any:
		query_parameters = {
			"project": project_identifier,
			"run_identifier": run_identifier,
			"skip": max(flask.request.headers.get("X-Orchestra-FileCursor", default = 0, type = int), 0),
			"limit": max(flask.request.args.get("limit", default = 1024 * 1024, type = int), 0),
		}

		log_text, log_cursor = self._run_provider.get_log_chunk(**query_parameters)
		return flask.Response(log_text, mimetype = "text/plain", headers = { "X-Orchestra-FileCursor": log_cursor })


	def get_results(self, project_identifier: str, run_identifier: str) -> Any:
		database_client = flask.request.database_client()
		run_results = self._run_provider.get_results(database_client, project_identifier, run_identifier)
		return self._response_builder.create_data_response(run_results)


	def cancel(self, project_identifier: str, run_identifier: str) -> Any:
		database_client = flask.request.database_client()
		self._run_provider.update_status(database_client, { "project": project_identifier, "identifier": run_identifier }, should_cancel = True)
		return self._response_builder.create_empty_response()


	def abort(self, project_identifier: str, run_identifier: str) -> Any:
		database_client = flask.request.database_client()
		self._run_provider.update_status(database_client, { "project": project_identifier, "identifier": run_identifier }, should_abort = True)
		return self._response_builder.create_empty_response()


	def download_archive(self, project_identifier: str, run_identifier: str) -> Any:
		database_client = flask.request.database_client()
		archive = self._run_provider.get_archive(database_client, self._serializer, project_identifier, run_identifier)
		headers = { "Content-Disposition": "attachment;filename=" + '"' + archive["file_name"] + '"' }
		return flask.Response(archive["data"], headers = headers, mimetype = "application/" + archive["type"])
