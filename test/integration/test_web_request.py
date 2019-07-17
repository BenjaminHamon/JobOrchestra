""" Integration tests for web requests """

import requests

from .. import assert_extensions
from . import context
from . import environment


def test_service_response(tmpdir):
	""" Test if service responds successfully to a simple request """

	with context.Context(tmpdir) as context_instance:
		service_process = context_instance.invoke_service()
		response = requests.get(context_instance.get_service_uri() + "/")
		response.raise_for_status()

	assert_extensions.assert_multi_process([
		{ "identifier": "service", "process": service_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": environment.log_format, "expected_messages": [] },
	])


def test_website_response(tmpdir):
	""" Test if website responds successfully to a simple request """

	with context.Context(tmpdir) as context_instance:
		website_process = context_instance.invoke_website()
		response = requests.get(context_instance.get_website_uri() + "/")
		response.raise_for_status()

	assert_extensions.assert_multi_process([
		{ "identifier": "website", "process": website_process, "expected_result_code": assert_extensions.get_flask_exit_code(), "log_format": environment.log_format, "expected_messages": [] },
	])
