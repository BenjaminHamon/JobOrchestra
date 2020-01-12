""" Integration tests for web requests """

import pytest
import requests

from .. import assert_extensions
from . import context
from . import environment


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_service_response(tmpdir, database_type):
	""" Test if service responds successfully to a simple request """

	with context.Context(tmpdir, database_type) as context_instance:
		service_process = context_instance.invoke_service()
		response = requests.get(context_instance.get_service_uri() + "/", timeout = 10)
		response.raise_for_status()

	assert_extensions.assert_multi_process([
		{ "process": service_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": environment.log_format, "expected_messages": [] },
	])


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_service_response_with_authorization(tmpdir, database_type):
	""" Test if service responds successfully to a simple request with authorization """

	with context.Context(tmpdir, database_type) as context_instance:
		authentication = context_instance.configure_service_authentication()
		service_process = context_instance.invoke_service()
		response = requests.get(context_instance.get_service_uri() + "/me", auth = authentication, timeout = 10)
		response.raise_for_status()

	assert_extensions.assert_multi_process([
		{ "process": service_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": environment.log_format, "expected_messages": [] },
	])


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_service_routes(tmpdir, database_type):
	""" Test if service responds successfully for accessible routes """

	with context.Context(tmpdir, database_type) as context_instance:
		authentication = context_instance.configure_service_authentication()

		project = context_instance.project_provider.create_or_update("examples")
		job = context_instance.job_provider.create_or_update("examples_empty", "examples", None, None, None, None, None)
		run = context_instance.run_provider.create("examples", "examples_empty", {})
		context_instance.run_provider.update_steps(run, [ { "index": 0, "name": "step_0", "status": "pending" } ])
		task = context_instance.task_provider.create("nothing", {})
		worker = context_instance.worker_provider.create("worker", None)
		user = context_instance.user_provider.create("user", "user")

		service_process = context_instance.invoke_service()

		response = requests.get(context_instance.get_service_uri() + "/me/routes", auth = authentication, timeout = 10)
		response.raise_for_status()

		route_collection = response.json()
		for route in route_collection:
			route = route.replace("<int:step_index>", "0")
			route = route.replace("<job_identifier>", job["identifier"])
			route = route.replace("<project_identifier>", project["identifier"])
			route = route.replace("<run_identifier>", run["identifier"])
			route = route.replace("<task_identifier>", task["identifier"])
			route = route.replace("<user_identifier>", user["identifier"])
			route = route.replace("<worker_identifier>", worker["identifier"])

			response = requests.get(context_instance.get_service_uri() + route, auth = authentication, timeout = 10)
			response.raise_for_status()

	assert_extensions.assert_multi_process([
		{ "process": service_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": environment.log_format, "expected_messages": [] },
	])


def test_website_response(tmpdir):
	""" Test if website responds successfully to a simple request """

	with context.Context(tmpdir, None) as context_instance:
		website_process = context_instance.invoke_website()
		response = requests.get(context_instance.get_website_uri() + "/", timeout = 10)
		response.raise_for_status()

	assert_extensions.assert_multi_process([
		{ "process": website_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": environment.log_format, "expected_messages": [] },
	])


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_website_response_with_authorization(tmpdir, database_type):
	""" Test if website responds successfully to a simple request with authorization """

	with context.Context(tmpdir, database_type) as context_instance:
		authentication = context_instance.configure_website_authentication()

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
def test_website_pages(tmpdir, database_type): # pylint: disable = too-many-locals
	""" Test if website responds successfully for accessible pages """

	with context.Context(tmpdir, database_type) as context_instance:
		authentication = context_instance.configure_website_authentication()

		project = context_instance.project_provider.create_or_update("examples")
		job = context_instance.job_provider.create_or_update("examples_empty", "examples", None, None, None, None, None)
		run = context_instance.run_provider.create("examples", "examples_empty", {})
		context_instance.run_provider.update_steps(run, [ { "index": 0, "name": "step_0", "status": "pending" } ])
		task = context_instance.task_provider.create("nothing", {})
		worker = context_instance.worker_provider.create("worker", None)
		user = context_instance.user_provider.create("user", "user")

		service_process = context_instance.invoke_service()
		website_process = context_instance.invoke_website()

		session = requests.Session()
		response = session.post(context_instance.get_website_uri() + "/me/login", { "user": authentication[0], "password": authentication[1] }, timeout = 10)
		response.raise_for_status()
		response = session.get(context_instance.get_website_uri() + "/me/routes", timeout = 10)
		response.raise_for_status()

		route_collection = response.json()
		for route in route_collection:
			route = route.replace("<int:step_index>", "0")
			route = route.replace("<job_identifier>", job["identifier"])
			route = route.replace("<project_identifier>", project["identifier"])
			route = route.replace("<run_identifier>", run["identifier"])
			route = route.replace("<task_identifier>", task["identifier"])
			route = route.replace("<user_identifier>", user["identifier"])
			route = route.replace("<worker_identifier>", worker["identifier"])
			route = route.replace("<path:route>", "help")

			response = session.get(context_instance.get_website_uri() + route, timeout = 10)
			response.raise_for_status()

	assert_extensions.assert_multi_process([
		{ "process": service_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": environment.log_format, "expected_messages": [] },
		{ "process": website_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": environment.log_format, "expected_messages": [] },
	])
