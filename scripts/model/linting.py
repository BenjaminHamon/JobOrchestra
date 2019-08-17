import logging
import os
import subprocess


logger = logging.getLogger("Linting")


pylint_categories = [ "fatal", "error", "warning", "convention", "refactor" ]
pylint_message_separator = "|"
pylint_message_elements = [
	{ "key": "file_path", "pylint_field": "path" },
	{ "key": "line_in_file", "pylint_field": "line"},
	{ "key": "object", "pylint_field": "obj" },
	{ "key": "category", "pylint_field": "category" },
	{ "key": "identifier", "pylint_field": "symbol" },
	{ "key": "code", "pylint_field": "msg_id" },
	{ "key": "message", "pylint_field": "msg" },
]


def run_pylint(python_executable, target):
	pylint_command = [ python_executable, "-u", "-m", "pylint", target ]
	format_options = [ "--msg-template", pylint_message_separator.join([ "{" + element["pylint_field"] + "}" for element in pylint_message_elements ]) ]

	logger.info("+ %s", " ".join(pylint_command))
	process = subprocess.Popen(pylint_command + format_options, stdout = subprocess.PIPE, stderr = subprocess.STDOUT, universal_newlines = True)

	all_issues = _process_pylint_output(process.stdout)
	result_code = process.wait()
	success = result_code == 0

	issue_counts = {}
	for category in pylint_categories:
		issue_counts[category] = len([ issue for issue in all_issues if issue["category"] == category ])

	if success:
		logger.info("Linting succeeded for '%s'", target)
	else:
		logger.error("Linting failed for '%s' (%s)", target, ", ".join("%s: %s" % (key, value) for key, value in issue_counts.items() if value > 0))

	return { "success": success, "result_code": result_code, "issues": all_issues, "counts": issue_counts }


def _process_pylint_output(output):
	all_issues = []

	for line in output:
		line = line.rstrip()

		if pylint_message_separator in line:
			issue = _parse_pylint_issue(line)
			all_issues.append(issue)

			log_format = "(%s:%s) %s (%s, %s)"
			log_arguments = [ issue["file_path"], issue["line_in_file"], issue["message"],  issue["identifier"], issue["code"] ]

			if issue["category"] in [ "error", "fatal" ]:
				logger.error(log_format, *log_arguments)
			elif issue["category"] in [ "convention", "refactor", "warning" ]:
				logger.warning(log_format, *log_arguments)
			else:
				raise ValueError("Unhandled issue category '%s'" % issue["category"])

	return all_issues


def _parse_pylint_issue(line):
	result = {}

	message_elements = line.split(pylint_message_separator)
	for index, element in enumerate(pylint_message_elements):
		result[element["key"]] = message_elements[index]

	result["file_path"] = os.path.relpath(result["file_path"])

	return result
