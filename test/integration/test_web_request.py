""" Integration tests for web requests """

import pytest
import requests

from .. import assert_extensions
from . import context
from . import environment


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
		{ "process": service_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": environment.log_format, "expected_messages": [] },
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
		{ "process": service_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": environment.log_format, "expected_messages": [] },
	])


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
@pytest.mark.parametrize("user_identifier, user_roles", get_all_user_parameters())
def test_service_routes(tmpdir, database_type, user_identifier, user_roles): # pylint: disable = too-many-locals
	""" Test if service responds successfully for accessible routes """

	with context.OrchestraContext(tmpdir, database_type) as context_instance:
		authentication = context_instance.configure_service_authentication(user_identifier, user_roles)

		project = context_instance.project_provider.create_or_update("examples", "Examples", {})
		job = context_instance.job_provider.create_or_update("empty", "examples", "Empty", None, None, None, [], None)
		schedule = context_instance.schedule_provider.create_or_update("empty_nightly", "examples", "Empty Nightly", "empty", None, "0 0 * * *")
		run = context_instance.run_provider.create("examples", "empty", {}, { "type": "user", "identifier": "my_user" })
		context_instance.run_provider.update_status(run, worker = "my_worker")
		context_instance.run_provider.update_steps(run, [ { "index": 0, "name": "step_0", "status": "pending" } ])
		worker = context_instance.worker_provider.create("my_worker", "my_user", None, "MyWorker")
		user = context_instance.user_provider.create("my_user", "MyUser")

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

			route = route.replace("<int:step_index>", "0")
			route = route.replace("<job_identifier>", job["identifier"])
			route = route.replace("<project_identifier>", project["identifier"])
			route = route.replace("<run_identifier>", run["identifier"])
			route = route.replace("<schedule_identifier>", schedule["identifier"])
			route = route.replace("<user_identifier>", user["identifier"])
			route = route.replace("<worker_identifier>", worker["identifier"])

			response = requests.get(context_instance.get_service_uri() + route, auth = authentication, timeout = 10)
			response.raise_for_status()

	assert_extensions.assert_multi_process([
		{ "process": service_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": environment.log_format, "expected_messages": [] },
	])


def test_website_response(tmpdir):
	""" Test if website responds successfully to a simple request """

	with context.OrchestraContext(tmpdir, None) as context_instance:
		website_process = context_instance.invoke_website()
		response = requests.get(context_instance.get_website_uri() + "/", timeout = 10)
		response.raise_for_status()

	assert_extensions.assert_multi_process([
		{ "process": website_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": environment.log_format, "expected_messages": [] },
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
		{ "process": service_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": environment.log_format, "expected_messages": [] },
		{ "process": website_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": environment.log_format, "expected_messages": [] },
	])


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
@pytest.mark.parametrize("user_identifier, user_roles", get_all_user_parameters())
def test_website_pages(tmpdir, database_type, user_identifier, user_roles): # pylint: disable = too-many-locals
	""" Test if website responds successfully for accessible pages """

	with context.OrchestraContext(tmpdir, database_type) as context_instance:
		authentication = context_instance.configure_website_authentication(user_identifier, user_roles)

		project = context_instance.project_provider.create_or_update("examples", "Examples", {})
		job = context_instance.job_provider.create_or_update("empty", "examples", "Empty", None, None, None, [], None)
		schedule = context_instance.schedule_provider.create_or_update("empty_nightly", "examples", "Empty Nightly", "empty", None, "0 0 * * *")
		run = context_instance.run_provider.create("examples", "empty", {}, { "type": "user", "identifier": "my_user" })
		context_instance.run_provider.update_status(run, worker = "my_worker")
		context_instance.run_provider.update_steps(run, [ { "index": 0, "name": "step_0", "status": "pending" } ])
		worker = context_instance.worker_provider.create("my_worker", "my_user", None, "MyWorker")
		context_instance.run_provider.update_status(run, worker = worker["identifier"])
		user = context_instance.user_provider.create("my_user", "MyUser")

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

			route = route.replace("<int:step_index>", "0")
			route = route.replace("<job_identifier>", job["identifier"])
			route = route.replace("<project_identifier>", project["identifier"])
			route = route.replace("<run_identifier>", run["identifier"])
			route = route.replace("<schedule_identifier>", schedule["identifier"])
			route = route.replace("<user_identifier>", user["identifier"])
			route = route.replace("<worker_identifier>", worker["identifier"])
			route = route.replace("<path:route>", "help")

			response = session.get(context_instance.get_website_uri() + route, timeout = 10)
			response.raise_for_status()

	assert_extensions.assert_multi_process([
		{ "process": service_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": environment.log_format, "expected_messages": [] },
		{ "process": website_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": environment.log_format, "expected_messages": [] },
	])
