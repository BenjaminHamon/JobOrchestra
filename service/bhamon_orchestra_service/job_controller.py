import logging
from typing import Any

import flask

from bhamon_orchestra_model.job_provider import JobProvider
from bhamon_orchestra_model.run_provider import RunProvider
from bhamon_orchestra_service.response_builder import ResponseBuilder


logger = logging.getLogger("JobController")


class JobController:


	def __init__(self, response_builder: ResponseBuilder, job_provider: JobProvider, run_provider: RunProvider) -> None:
		self._response_builder = response_builder
		self._job_provider = job_provider
		self._run_provider = run_provider


	def get_count(self, project_identifier: str) -> Any:
		query_parameters = {
			"project": project_identifier,
		}

		job_count = self._job_provider.count(flask.request.database_client(), **query_parameters)
		return self._response_builder.create_data_response(job_count)


	def get_collection(self, project_identifier: str) -> Any:
		query_parameters = {
			"project": project_identifier,
			"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
			"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
			"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
		}

		job_collection = self._job_provider.get_list(flask.request.database_client(), **query_parameters)
		return self._response_builder.create_data_response(job_collection)


	def get(self, project_identifier: str, job_identifier: str) -> Any:
		job = self._job_provider.get(flask.request.database_client(), project_identifier, job_identifier)
		return self._response_builder.create_data_response(job)


	def get_runs(self, project_identifier: str, job_identifier: str) -> Any:
		query_parameters = {
			"project": project_identifier,
			"job": job_identifier,
			"status": flask.request.args.get("status", default = None),
			"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
			"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
			"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
		}

		run_collection = self._run_provider.get_list(flask.request.database_client(), **query_parameters)
		return self._response_builder.create_data_response(run_collection)


	def trigger(self, project_identifier: str, job_identifier: str) -> Any:
		trigger_data = flask.request.get_json()
		job = self._job_provider.get(flask.request.database_client(), project_identifier, job_identifier)
		run = self._run_provider.create(flask.request.database_client(), job["project"], job_identifier, **trigger_data)
		response_data = { "project_identifier": project_identifier, "job_identifier": job_identifier, "run_identifier": run["identifier"] }
		return self._response_builder.create_data_response(response_data)


	def enable(self, project_identifier: str, job_identifier: str) -> Any:
		self._job_provider.update_status(flask.request.database_client(), { "project": project_identifier, "identifier": job_identifier }, is_enabled = True)
		return self._response_builder.create_empty_response()


	def disable(self, project_identifier: str, job_identifier: str) -> Any:
		self._job_provider.update_status(flask.request.database_client(), { "project": project_identifier, "identifier": job_identifier }, is_enabled = False)
		return self._response_builder.create_empty_response()
