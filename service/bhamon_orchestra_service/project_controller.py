import logging

import flask
import requests

from bhamon_orchestra_model.revision_control.github import GitHubClient


logger = logging.getLogger("ProjectController")


def get_count():
	return flask.jsonify(flask.current_app.project_provider.count())


def get_collection():
	query_parameters = {
		"skip": max(flask.request.args.get("skip", default = 0, type = int), 0),
		"limit": max(min(flask.request.args.get("limit", default = 100, type = int), 1000), 0),
		"order_by": [ tuple(x.split(" ")) for x in flask.request.args.getlist("order_by") ],
	}

	return flask.jsonify(flask.current_app.project_provider.get_list(**query_parameters))


def get(project_identifier):
	return flask.jsonify(flask.current_app.project_provider.get(project_identifier))


def get_repository(project_identifier):
	project = flask.current_app.project_provider.get(project_identifier)
	revision_control_client = _create_revision_control_client(project["services"]["revision_control"])

	query_parameters = {
		"repository": project["services"]["revision_control"]["repository"],
	}

	return flask.jsonify(revision_control_client.get_repository(**query_parameters))



def get_branch_collection(project_identifier):
	project = flask.current_app.project_provider.get(project_identifier)
	revision_control_client = _create_revision_control_client(project["services"]["revision_control"])

	query_parameters = {
		"repository": project["services"]["revision_control"]["repository"],
	}

	return flask.jsonify(revision_control_client.get_branch_list(**query_parameters))


def get_revision_collection(project_identifier):
	project = flask.current_app.project_provider.get(project_identifier)
	revision_control_client = _create_revision_control_client(project["services"]["revision_control"])

	query_parameters = {
		"repository": project["services"]["revision_control"]["repository"],
		"branch": flask.request.args.get("branch", default = None),
		"limit": max(min(flask.request.args.get("limit", default = 20, type = int), 100), 1),
	}

	return flask.jsonify(revision_control_client.get_revision_list(**query_parameters))


def get_revision(project_identifier, revision_reference):
	project = flask.current_app.project_provider.get(project_identifier)
	revision_control_client = _create_revision_control_client(project["services"]["revision_control"])

	query_parameters = {
		"repository": project["services"]["revision_control"]["repository"],
		"revision": revision_reference,
	}

	return flask.jsonify(revision_control_client.get_revision(**query_parameters))


def get_revision_status(project_identifier, revision_reference):
	project = flask.current_app.project_provider.get(project_identifier)
	repository = project["services"]["revision_control"]["repository"]
	revision_control_client = _create_revision_control_client(project["services"]["revision_control"])
	revision = revision_control_client.get_revision(repository, revision_reference)
	revision_runs = []
	revision_status = "unknown"

	run_query_parameters = {
		"project": project_identifier,
		"limit": max(min(flask.request.args.get("run_limit", default = 1000, type = int), 10000), 100),
		"order_by": [("update_date", "descending")],
	}

	run_collection = flask.current_app.run_provider.get_list_as_documents(**run_query_parameters)

	for run in run_collection:
		revision_identifier = run.get("results", {}).get("revision_control", {}).get("revision", None)
		if revision_identifier is None and run["status"] in [ "pending", "running" ]:
			try:
				revision_identifier = revision_control_client.get_revision(repository, run["parameters"]["revision"])["identifier"]
			except requests.HTTPError:
				logger.warning("Failed to resolve project '%s' revision '%s'", project_identifier, run["parameters"]["revision"], exc_info = True)

		if revision_identifier == revision["identifier"]:
			revision_runs.append(run)

	if len(revision_runs) == 0:
		revision_status = "unknown"
	elif any(run["status"] in [ "failed", "aborted", "exception" ] for run in revision_runs):
		revision_status = "failed"
	elif any(run["status"] in [ "pending", "running" ] for run in revision_runs):
		revision_status = "pending"
	elif all(run["status"] in [ "succeeded" ] for run in revision_runs):
		revision_status = "succeeded"

	result = {
		"reference": revision_reference,
		"identifier": revision["identifier"],
		"identifier_short": revision["identifier_short"],
		"runs": revision_runs,
		"status": revision_status,
	}

	return flask.jsonify(result)


def get_project_status(project_identifier):
	project = flask.current_app.project_provider.get(project_identifier)
	repository = project["services"]["revision_control"]["repository"]
	revision_control_client = _create_revision_control_client(project["services"]["revision_control"])

	revision_query_parameters = {
		"repository": repository,
		"branch": flask.request.args.get("branch", default = None),
		"limit": max(min(flask.request.args.get("revision_limit", default = 20, type = int), 100), 1),
	}

	run_query_parameters = {
		"project": project_identifier,
		"limit": max(min(flask.request.args.get("run_limit", default = 1000, type = int), 10000), 100),
		"order_by": [("update_date", "descending")],
	}

	revision_collection = revision_control_client.get_revision_list(**revision_query_parameters)
	run_collection = flask.current_app.run_provider.get_list_as_documents(**run_query_parameters)

	revision_dictionary = { revision["identifier"]: revision for revision in revision_collection }
	for revision in revision_collection:
		revision["runs"] = []

	for run in run_collection:
		revision_identifier = run.get("results", {}).get("revision_control", {}).get("revision", None)
		if revision_identifier is None and run["status"] in [ "pending", "running" ]:
			try:
				revision_identifier = revision_control_client.get_revision(repository, run["parameters"]["revision"])["identifier"]
			except requests.HTTPError:
				logger.warning("Failed to resolve project '%s' revision '%s'", project_identifier, run["parameters"]["revision"], exc_info = True)

		revision = revision_dictionary.get(revision_identifier)
		if revision is not None:
			revision["runs"].append(run)

	return flask.jsonify(revision_collection)


def _create_revision_control_client(service):
	if service["type"] == "github":
		return GitHubClient(flask.current_app.config.get("GITHUB_ACCESS_TOKEN", None))
	raise ValueError("Unsupported service '%s'" % service["type"])
