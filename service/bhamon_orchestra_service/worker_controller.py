import logging
from typing import Any

import flask

from bhamon_orchestra_model.job_provider import JobProvider
from bhamon_orchestra_model.run_provider import RunProvider
from bhamon_orchestra_model.worker_provider import WorkerProvider


logger = logging.getLogger("WorkerController")


class WorkerController:


	def __init__(self, job_provider: JobProvider, run_provider: RunProvider, worker_provider: WorkerProvider) -> None:
		self._job_provider = job_provider
		self._run_provider = run_provider
		self._worker_provider = worker_provider


	def get_count(self) -> Any:
		database_client = flask.request.database_client()
		return flask.jsonify(self._worker_provider.count(database_client))


	def get_collection(self) -> Any:
		query_parameters = {
			"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
			"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
			"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
		}

		database_client = flask.request.database_client()
		return flask.jsonify(self._worker_provider.get_list(database_client, **query_parameters))


	def get(self, worker_identifier: str) -> Any:
		database_client = flask.request.database_client()
		return flask.jsonify(self._worker_provider.get(database_client, worker_identifier))


	def get_job_collection(self, worker_identifier: str) -> Any: # pylint: disable = unused-argument
		query_parameters = {
			"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
			"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
			"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
		}

		database_client = flask.request.database_client()
		return flask.jsonify(self._job_provider.get_list(database_client, **query_parameters))


	def get_run_count(self, worker_identifier: str) -> Any:
		query_parameters = {
			"worker": worker_identifier,
			"project": flask.request.args.get("project", default = None),
			"status": flask.request.args.get("status", default = None),
		}

		database_client = flask.request.database_client()
		return flask.jsonify(self._run_provider.count(database_client, **query_parameters))


	def get_run_collection(self, worker_identifier: str) -> Any:
		query_parameters = {
			"worker": worker_identifier,
			"project": flask.request.args.get("project", default = None),
			"status": flask.request.args.get("status", default = None),
			"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
			"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
			"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
		}

		database_client = flask.request.database_client()
		return flask.jsonify(self._run_provider.get_list(database_client, **query_parameters))


	def disconnect(self, worker_identifier: str) -> Any:
		database_client = flask.request.database_client()
		self._worker_provider.update_status(database_client, { "identifier": worker_identifier }, should_disconnect = True)
		return flask.jsonify({})


	def enable(self, worker_identifier: str) -> Any:
		database_client = flask.request.database_client()
		self._worker_provider.update_status(database_client, { "identifier": worker_identifier }, is_enabled = True)
		return flask.jsonify({})


	def disable(self, worker_identifier: str) -> Any:
		database_client = flask.request.database_client()
		self._worker_provider.update_status(database_client, { "identifier": worker_identifier }, is_enabled = False)
		return flask.jsonify({})
