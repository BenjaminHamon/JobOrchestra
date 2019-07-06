import re
import sys

import pytest


STATUS_CONTROL_C_EXIT = 0xC000013A # pylint: disable = invalid-name


def assert_multi_process(process_information_collection):
	__tracebackhide__ = True # pylint: disable = unused-variable

	for process_information in process_information_collection:
		process_information["result_code"] = process_information["process"].poll()
		process_information["stdout"] = process_information["process"].stdout.read().decode()
		process_information["stderr"] = process_information["process"].stderr.read().decode()

		if process_information["stdout"]:
			sys.stdout.write("  # %s\n" % process_information["identifier"])
			sys.stdout.write(process_information["stdout"])
			sys.stderr.write("\n")
		if process_information["stderr"]:
			sys.stderr.write("  # %s\n" % process_information["identifier"])
			sys.stderr.write(process_information["stderr"])
			sys.stderr.write("\n")

	for process_information in process_information_collection:
		if process_information["result_code"] is None:
			pytest.fail("Process %s did not complete" % process_information["identifier"])
		if process_information["result_code"] != process_information["expected_result_code"]:
			pytest.fail("Process %s completed with result code %s, expected %s"
				% (process_information["identifier"], process_information["result_code"], process_information["expected_result_code"]))
		assert_log(process_information["stderr"], process_information["log_format"], process_information["expected_messages"])


def assert_log(log_text, log_format, expected_messages = None, failure_log_levels = None):
	__tracebackhide__ = True # pylint: disable = unused-variable

	if expected_messages is None:
		expected_messages = []
	if failure_log_levels is None:
		failure_log_levels = [ "Warning", "Error", "Critical" ]

	log_format = log_format.replace("{levelname}", "{level}").replace("{name}", "{logger}")
	log_regex = r"^" + re.escape(log_format) + r"$"
	log_regex = log_regex.replace(r"\{level\}", r"(?P<level>[a-zA-Z]+)").replace(r"\{logger\}", r"(?P<logger>[a-zA-Z]+)").replace(r"\{message\}", r"(?P<message>.*)")

	all_issues = []
	log_messages = parse_log(log_text, log_regex)
	for message in expected_messages:
		if message not in log_messages:
			all_issues.append("Missing: " + log_format.format(**message))
	for message in log_messages:
		if message not in expected_messages and message["level"] in failure_log_levels:
			all_issues.append("Unexpected: " + log_format.format(**message))

	if any(all_issues):
		pytest.fail("Log is not as expected" + "\n" + "\n".join("  " + issue for issue in all_issues))


def parse_log(log_text, log_regex):
	all_messages = []
	for log_line in log_text.splitlines():
		log_match = re.search(log_regex, log_line)
		if log_match:
			message = log_match.groupdict()
			all_messages.append(message)
	return all_messages
