import logging
from typing import Any

import flask

from bhamon_orchestra_model.schedule_provider import ScheduleProvider


logger = logging.getLogger("ScheduleController")


class ScheduleController:


	def __init__(self, schedule_provider: ScheduleProvider) -> None:
		self._schedule_provider = schedule_provider


	def get_count(self, project_identifier: str) -> Any:
		query_parameters = {
			"project": project_identifier,
			"job": flask.request.args.get("job", default = None),
		}

		database_client = flask.request.database_client()
		return flask.jsonify(self._schedule_provider.count(database_client, **query_parameters))


	def get_collection(self, project_identifier: str) -> Any:
		query_parameters = {
			"project": project_identifier,
			"job": flask.request.args.get("job", default = None),
			"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
			"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
			"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
		}

		database_client = flask.request.database_client()
		return flask.jsonify(self._schedule_provider.get_list(database_client, **query_parameters))


	def get(self, project_identifier: str, schedule_identifier: str) -> Any:
		database_client = flask.request.database_client()
		return flask.jsonify(self._schedule_provider.get(database_client, project_identifier, schedule_identifier))


	def enable(self, project_identifier: str, schedule_identifier: str) -> Any:
		database_client = flask.request.database_client()
		self._schedule_provider.update_status(database_client, { "project": project_identifier, "identifier": schedule_identifier }, is_enabled = True)
		return flask.jsonify({})


	def disable(self, project_identifier: str, schedule_identifier: str) -> Any:
		database_client = flask.request.database_client()
		self._schedule_provider.update_status(database_client, { "project": project_identifier, "identifier": schedule_identifier }, is_enabled = False)
		return flask.jsonify({})
