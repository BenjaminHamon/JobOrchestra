""" Integration tests for web requests """

import os

import pytest
import requests

from bhamon_orchestra_website import helpers as website_helpers

from .. import assert_extensions
from . import context
from . import environment


log_format = environment.load_environment()["logging_stream_format"]


def get_all_user_parameters():
	return [
		pytest.param("auditor", [ "Auditor" ], id = "auditor"),
		pytest.param("viewer", [ "Viewer" ], id = "viewer"),
		pytest.param("guest", [], id = "guest"),
	]


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_service_response(tmpdir, database_type):
	""" Test if service responds successfully to a simple request """

	with context.OrchestraContext(tmpdir, database_type) as context_instance:
		service_process = context_instance.invoke_service()
		response = requests.get(context_instance.get_service_uri() + "/", timeout = 10)
		response.raise_for_status()

	assert_extensions.assert_multi_process([
		{ "process": service_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": log_format, "expected_messages": [] },
	])


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
@pytest.mark.parametrize("user_identifier, user_roles", get_all_user_parameters())
def test_service_response_with_authorization(tmpdir, database_type, user_identifier, user_roles):
	""" Test if service responds successfully to a simple request with authorization """

	with context.OrchestraContext(tmpdir, database_type) as context_instance:
		authentication = context_instance.configure_service_authentication(user_identifier, user_roles)
		service_process = context_instance.invoke_service()
		response = requests.get(context_instance.get_service_uri() + "/me", auth = authentication, timeout = 10)
		response.raise_for_status()

	assert_extensions.assert_multi_process([
		{ "process": service_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": log_format, "expected_messages": [] },
	])


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
@pytest.mark.parametrize("user_identifier, user_roles", get_all_user_parameters())
def test_service_routes(tmpdir, database_type, user_identifier, user_roles): # pylint: disable = too-many-locals
	""" Test if service responds successfully for accessible routes """

	with context.OrchestraContext(tmpdir, database_type) as context_instance:
		authentication = context_instance.configure_service_authentication(user_identifier, user_roles)

		with context_instance.database_client_factory() as database_client:
			user = context_instance.user_provider.create(database_client, "my_user", "MyUser")
			project = context_instance.project_provider.create_or_update(database_client, "examples", "Examples", {})
			job = context_instance.job_provider.create_or_update(database_client, "empty", "examples", "Empty", "", [], [], {})
			schedule = context_instance.schedule_provider.create_or_update(database_client, "empty_nightly", "examples", "Empty Nightly", "empty", {}, "0 0 * * *")
			worker = context_instance.worker_provider.create(database_client, "my_worker", "my_user", "0.0.0", "MyWorker")
			run = context_instance.run_provider.create(database_client, "examples", "empty", {}, { "type": "user", "identifier": "my_user" })
			context_instance.run_provider.update_status(database_client, run, worker = "my_worker")

		service_process = context_instance.invoke_service()

		response = requests.get(context_instance.get_service_uri() + "/me/routes", auth = authentication, timeout = 10)
		response.raise_for_status()

		route_collection = response.json()

		for route in route_collection:

			# Skip routes with external dependencies
			if route == "/admin/service/<service_identifier>":
				continue
			if route == "/project/<project_identifier>/repository":
				continue
			if route.startswith("/project/<project_identifier>/repository/"):
				continue
			if route == "/project/<project_identifier>/status":
				continue

			route = route.replace("<job_identifier>", job["identifier"])
			route = route.replace("<project_identifier>", project["identifier"])
			route = route.replace("<run_identifier>", run["identifier"])
			route = route.replace("<schedule_identifier>", schedule["identifier"])
			route = route.replace("<user_identifier>", user["identifier"])
			route = route.replace("<worker_identifier>", worker["identifier"])

			response = requests.get(context_instance.get_service_uri() + route, auth = authentication, timeout = 10)
			save_response(os.path.join(str(tmpdir), "service_responses"), route, response)
			response.raise_for_status()

	assert_extensions.assert_multi_process([
		{ "process": service_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": log_format, "expected_messages": [] },
	])


def test_website_response(tmpdir):
	""" Test if website responds successfully to a simple request """

	with context.OrchestraContext(tmpdir, None) as context_instance:
		website_process = context_instance.invoke_website()
		response = requests.get(context_instance.get_website_uri() + "/", timeout = 10)
		response.raise_for_status()

	assert_extensions.assert_multi_process([
		{ "process": website_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": log_format, "expected_messages": [] },
	])


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
@pytest.mark.parametrize("user_identifier, user_roles", get_all_user_parameters())
def test_website_response_with_authorization(tmpdir, database_type, user_identifier, user_roles):
	""" Test if website responds successfully to a simple request with authorization """

	with context.OrchestraContext(tmpdir, database_type) as context_instance:
		authentication = context_instance.configure_website_authentication(user_identifier, user_roles)

		service_process = context_instance.invoke_service()
		website_process = context_instance.invoke_website()

		session = requests.Session()
		response = session.post(context_instance.get_website_uri() + "/me/login", { "user": authentication[0], "password": authentication[1] }, timeout = 10)
		response.raise_for_status()
		response = session.get(context_instance.get_website_uri() + "/me", timeout = 10)
		response.raise_for_status()

	assert_extensions.assert_multi_process([
		{ "process": service_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": log_format, "expected_messages": [] },
		{ "process": website_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": log_format, "expected_messages": [] },
	])


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
@pytest.mark.parametrize("user_identifier, user_roles", get_all_user_parameters())
def test_website_pages(tmpdir, database_type, user_identifier, user_roles): # pylint: disable = too-many-locals
	""" Test if website responds successfully for accessible pages """

	with context.OrchestraContext(tmpdir, database_type) as context_instance:
		authentication = context_instance.configure_website_authentication(user_identifier, user_roles)

		with context_instance.database_client_factory() as database_client:
			user = context_instance.user_provider.create(database_client, "my_user", "MyUser")
			project = context_instance.project_provider.create_or_update(database_client, "examples", "Examples", {})
			job = context_instance.job_provider.create_or_update(database_client, "empty", "examples", "Empty", "", [], [], {})
			schedule = context_instance.schedule_provider.create_or_update(database_client, "empty_nightly", "examples", "Empty Nightly", "empty", {}, "0 0 * * *")
			worker = context_instance.worker_provider.create(database_client, "my_worker", "my_user", "0.0.0", "MyWorker")
			run = context_instance.run_provider.create(database_client, "examples", "empty", {}, { "type": "user", "identifier": "my_user" })
			context_instance.run_provider.update_status(database_client, run, worker = "my_worker")

		service_process = context_instance.invoke_service()
		website_process = context_instance.invoke_website()

		session = requests.Session()
		response = session.post(context_instance.get_website_uri() + "/me/login", { "user": authentication[0], "password": authentication[1] }, timeout = 10)
		response.raise_for_status()
		response = session.get(context_instance.get_website_uri() + "/me/routes", timeout = 10)
		response.raise_for_status()

		route_collection = response.json()

		for route in route_collection:

			# Skip routes with external dependencies
			if route == "/project/<project_identifier>/status":
				continue

			route = route.replace("<job_identifier>", job["identifier"])
			route = route.replace("<project_identifier>", project["identifier"])
			route = route.replace("<run_identifier>", run["identifier"])
			route = route.replace("<schedule_identifier>", schedule["identifier"])
			route = route.replace("<user_identifier>", user["identifier"])
			route = route.replace("<worker_identifier>", worker["identifier"])
			route = route.replace("<path:route>", "help")

			response = session.get(context_instance.get_website_uri() + route, timeout = 10)
			save_response(os.path.join(str(tmpdir), "website_responses"), route, response)
			response.raise_for_status()

	assert_extensions.assert_multi_process([
		{ "process": service_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": log_format, "expected_messages": [] },
		{ "process": website_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": log_format, "expected_messages": [] },
	])


def test_website_pipeline_view(tmpdir): # pylint: disable = too-many-locals
	""" Test if website successfully generates a pipeline view """

	database_type = "json"
	user_identifier = "viewer"
	user_roles = [ "Viewer" ]

	pipeline = {
		"elements": [
			{ "identifier": "stage_1_job_1", "job": "success" },
			{ "identifier": "stage_1_job_2", "job": "success" },
			{ "identifier": "stage_1_job_3", "job": "success" },

			{ "identifier": "stage_2_job_1", "job": "success", "after": [ { "element": "stage_1_job_1", "status": "succeeded" } ] },
			{ "identifier": "stage_2_job_2", "job": "success", "after": [ { "element": "stage_1_job_2", "status": "succeeded" } ] },
			{ "identifier": "stage_2_job_3", "job": "success", "after": [ { "element": "stage_1_job_3", "status": "succeeded" } ] },

			{ "identifier": "stage_3_job_1", "job": "success", "after": [ { "element": "stage_2_job_1", "status": "succeeded" } ] },
			{ "identifier": "stage_3_job_2", "job": "success", "after": [ { "element": "stage_2_job_2", "status": "succeeded" } ] },
			{ "identifier": "stage_3_job_3", "job": "success", "after": [ { "element": "stage_2_job_3", "status": "succeeded" } ] },
		],
	}

	with context.OrchestraContext(tmpdir, database_type) as context_instance:
		authentication = context_instance.configure_website_authentication(user_identifier, user_roles)

		with context_instance.database_client_factory() as database_client:
			project = context_instance.project_provider.create_or_update(database_client, "examples", "Examples", {})
			run = context_instance.run_provider.create(database_client, "examples", "pipeline", {}, { "type": None })

			pipeline["inner_runs"] = []
			for element in pipeline["elements"]:
				source = { "type": "run", "project": run["project"], "identifier": run["identifier"] }
				inner_run = context_instance.run_provider.create(database_client, run["project"], element["job"], {}, source)

				pipeline["inner_runs"].append({
					"identifier": inner_run["identifier"],
					"project": run["project"],
					"element": element["identifier"],
					"status": "succeeded",
				})

			context_instance.run_provider.set_results(database_client, run, { "pipeline": pipeline })

		service_process = context_instance.invoke_service()
		website_process = context_instance.invoke_website()

		session = requests.Session()
		response = session.post(context_instance.get_website_uri() + "/me/login", { "user": authentication[0], "password": authentication[1] }, timeout = 10)
		response.raise_for_status()

		route = "/project/" + project["identifier"] + "/run/" + run["identifier"]
		response = session.get(context_instance.get_website_uri() + route, timeout = 10)
		save_response(os.path.join(str(tmpdir), "website_responses"), route, response)
		response.raise_for_status()

		assert "<svg class=\"pipeline\"" in response.text

	assert_extensions.assert_multi_process([
		{ "process": service_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": log_format, "expected_messages": [] },
		{ "process": website_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": log_format, "expected_messages": [] },
	])


def save_response(output_directory: str, route: str, response: requests.Response) -> None:
	route_as_path = os.path.normpath(route.strip("/")) if route != "/" else "root"
	output_file_path = os.path.join(output_directory, route_as_path + website_helpers.get_file_extension(response.headers["content-type"]))
	os.makedirs(os.path.dirname(output_file_path), exist_ok = True)

	with open(output_file_path, mode = "wb") as output_file:
		output_file.write(response.content)
