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
		response = session.get(context_instance.get_website_uri() + "/", timeout = 10)
		response.raise_for_status()

	assert_extensions.assert_multi_process([
		{ "process": service_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": environment.log_format, "expected_messages": [] },
		{ "process": website_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": environment.log_format, "expected_messages": [] },
	])


@pytest.mark.parametrize("database_type", environment.get_all_database_types())
def test_website_pages(tmpdir, database_type):
	""" Test if website responds successfully for accessible pages """

	with context.Context(tmpdir, database_type) as context_instance:
		authentication = context_instance.configure_website_authentication()

		providers = context_instance.instantiate_providers()
		job = providers["job"].create_or_update("job_test", None, None, None, None, None)
		build = providers["build"].create(job["identifier"], {})
		providers["build"].update_steps(build, [ { "index": 0, "name": "step_0", "status": "pending" } ])
		worker = providers["worker"].create("worker", None)

		service_process = context_instance.invoke_service()
		website_process = context_instance.invoke_website()

		session = requests.Session()
		response = session.post(context_instance.get_website_uri() + "/me/login", { "user": authentication[0], "password": authentication[1] }, timeout = 10)
		response.raise_for_status()
		response = session.get(context_instance.get_website_uri() + "/me/routes", timeout = 10)
		response.raise_for_status()

		route_collection = response.json()
		for route in route_collection:
			route = route.replace("<build_identifier>", build["identifier"])
			route = route.replace("<int:step_index>", "0")
			route = route.replace("<job_identifier>", job["identifier"])
			route = route.replace("<worker_identifier>", worker["identifier"])

			response = session.get(context_instance.get_website_uri() + route, timeout = 10)
			response.raise_for_status()

	assert_extensions.assert_multi_process([
		{ "process": service_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": environment.log_format, "expected_messages": [] },
		{ "process": website_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": environment.log_format, "expected_messages": [] },
	])
