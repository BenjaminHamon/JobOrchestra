import logging
from typing import Any

import flask

import bhamon_orchestra_website.helpers as helpers
from bhamon_orchestra_website.service_client import ServiceClient


logger = logging.getLogger("RunController")


class RunController:


	def __init__(self, service_client: ServiceClient) -> None:
		self._service_client = service_client


	def show_collection(self, project_identifier: str) -> Any:
		query_parameters = {
			"job": helpers.none_if_empty(flask.request.args.get("job", default = None)),
			"worker": helpers.none_if_empty(flask.request.args.get("worker", default = None)),
			"status": helpers.none_if_empty(flask.request.args.get("status", default = None)),
		}

		item_total = self._service_client.get("/project/{project_identifier}/run_count".format(**locals()), parameters = query_parameters)
		pagination = helpers.get_pagination(item_total, { "project_identifier": project_identifier, **query_parameters })

		query_parameters.update({
			"skip": (pagination["page_number"] - 1) * pagination["item_count"],
			"limit": pagination["item_count"],
			"order_by": [ "update_date descending" ],
		})

		job_query_parameters = { "limit": 1000, "order_by": [ "identifier ascending" ] }
		worker_query_parameters = { "limit": 1000, "order_by": [ "identifier ascending" ] }

		view_data = {
			"project": self._service_client.get("/project/{project_identifier}".format(**locals())),
			"job_collection": self._service_client.get("/project/{project_identifier}/job_collection".format(**locals()), parameters = job_query_parameters),
			"worker_collection": self._service_client.get("/worker_collection", parameters = worker_query_parameters),
			"status_collection": helpers.get_run_status_collection(),
			"run_collection": self._service_client.get("/project/{project_identifier}/run_collection".format(**locals()), parameters = query_parameters),
			"pagination": pagination,
		}

		helpers.add_display_names([ view_data["project"] ], view_data["job_collection"], view_data["run_collection"], [], view_data["worker_collection"])

		return flask.render_template("run/collection.html", title = "Runs", **view_data)


	def show(self, project_identifier: str, run_identifier: str) -> Any: # pylint: disable = unused-argument
		project = self._service_client.get("/project/{project_identifier}".format(**locals()))
		run = self._service_client.get("/project/{project_identifier}/run/{run_identifier}".format(**locals()))
		run_results = self._service_client.get("/project/{project_identifier}/run/{run_identifier}/results".format(**locals()))

		run["project_display_name"] = project["display_name"]

		job_route = "/project/{project}/job/{job}".format(project = project_identifier, job = run["job"])
		job = self._service_client.get_or_default(job_route, default_value = {})
		run["job_display_name"] = job.get("display_name", run["job"])

		if run["source"] is not None:
			if run["source"]["type"] == "schedule":
				schedule_route = "/project/{project}/schedule/{schedule}".format(project = project_identifier, schedule = run["source"]["identifier"])
				schedule = self._service_client.get_or_default(schedule_route, default_value = {})
				run["source"]["display_name"] = schedule.get("display_name", run["source"]["identifier"])
			if run["source"]["type"] == "user":
				user_route = "/user/{user}".format(user = run["source"]["identifier"])
				user = self._service_client.get_or_default(user_route, default_value = {})
				run["source"]["display_name"] = user.get("display_name", run["source"]["identifier"])

		if run["worker"] is not None:
			worker_route = "/worker/{worker}".format(worker = run["worker"])
			worker = self._service_client.get_or_default(worker_route, default_value = {})
			run["worker_display_name"] = worker.get("display_name", run["worker"])

		view_data = { "project": project, "run": run, "run_results": run_results }

		return flask.render_template("run/index.html", title = "Run " + run_identifier[:18], **view_data)


	def show_log(self, project_identifier: str, run_identifier: str) -> Any: # pylint: disable = unused-argument
		view_data = {
			"project": self._service_client.get("/project/{project_identifier}".format(**locals())),
			"run": self._service_client.get("/project/{project_identifier}/run/{run_identifier}".format(**locals())),
		}

		return flask.render_template("run/log.html", title = "Run " + run_identifier[:18], **view_data)


	def show_log_raw(self, project_identifier: str, run_identifier: str) -> Any: # pylint: disable = unused-argument
		log_text = self._service_client.get("/project/{project_identifier}/run/{run_identifier}/log".format(**locals()))
		content_disposition = "inline; filename=\"%s.log\"" % run_identifier
		return flask.Response(log_text, headers = { "Content-Disposition": content_disposition }, mimetype = "text/plain")


	def cancel(self, project_identifier: str, run_identifier: str) -> Any: # pylint: disable = unused-argument
		request_data = flask.request.form
		self._service_client.post("/project/{project_identifier}/run/{run_identifier}/cancel".format(**locals()), data = request_data)
		return flask.redirect(flask.request.referrer or flask.url_for("run_controller.show_collection", project_identifier = project_identifier))


	def abort(self, project_identifier: str, run_identifier: str) -> Any: # pylint: disable = unused-argument
		request_data = flask.request.form
		self._service_client.post("/project/{project_identifier}/run/{run_identifier}/abort".format(**locals()), data = request_data)
		return flask.redirect(flask.request.referrer or flask.url_for("run_controller.show_collection", project_identifier = project_identifier))


	def download_archive(self, project_identifier: str, run_identifier: str) -> Any: # pylint: disable = unused-argument
		archive_response = self._service_client.download("/project/{project_identifier}/run/{run_identifier}/download".format(**locals()))
		headers = { "Content-Disposition": archive_response.headers["Content-Disposition"] }
		mimetype = archive_response.headers["Content-Type"]
		return flask.Response(archive_response.content, headers = headers, mimetype = mimetype)
