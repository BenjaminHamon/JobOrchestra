import logging

import flask

from bhamon_orchestra_model.revision_control.github import GitHubRepositoryClient


logger = logging.getLogger("ProjectController")


def get_project_count():
	return flask.jsonify(flask.current_app.project_provider.count())


def get_project_collection():
	query_parameters = {
		"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
		"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
		"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
	}

	return flask.jsonify(flask.current_app.project_provider.get_list(**query_parameters))


def get_project(project_identifier):
	return flask.jsonify(flask.current_app.project_provider.get(project_identifier))


def get_project_jobs(project_identifier):
	query_parameters = {
		"project": project_identifier,
		"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
		"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
		"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
	}

	return flask.jsonify(flask.current_app.job_provider.get_list(**query_parameters))


def get_project_runs(project_identifier):
	query_parameters = {
		"project": project_identifier,
		"status": flask.request.args.get("status", default = None),
		"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
		"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
		"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
	}

	return flask.jsonify(flask.current_app.run_provider.get_list(**query_parameters))


def get_project_branches(project_identifier):
	project = flask.current_app.project_provider.get(project_identifier)
	revision_control_client = _create_revision_control_client(project["services"]["revision_control"])
	return flask.jsonify(revision_control_client.get_branch_list())


def get_project_revisions(project_identifier):
	project = flask.current_app.project_provider.get(project_identifier)
	revision_control_client = _create_revision_control_client(project["services"]["revision_control"])

	query_parameters = {
		"branch": flask.request.args.get("branch", default = None),
		"limit": max(min(flask.request.args.get("limit", default = 20, type = int), 100), 1),
	}

	return flask.jsonify(revision_control_client.get_revision_list(**query_parameters))


def _create_revision_control_client(service):
	if service["type"] == "github":
		access_token = flask.current_app.config.get("GITHUB_ACCESS_TOKEN", None)
		return GitHubRepositoryClient(service["owner"], service["repository"], access_token)
	raise ValueError("Unsupported service '%s'" % service["type"])
