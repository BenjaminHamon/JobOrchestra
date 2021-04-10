import math
from typing import List, Optional

import cron_descriptor
import flask


cron_descriptor_options = cron_descriptor.Options()
cron_descriptor_options.use_24hour_time_format = True


def none_if_empty(value: str) -> Optional[str]:
	if value == "":
		return None
	return value


def describe_cron_expression(expression: str) -> str:
	return cron_descriptor.get_description(expression, cron_descriptor_options)


def truncate_text(value: str, length_limit: int) -> str:
	if len(value) <= length_limit:
		return value

	ellipsis_mark = "..."
	truncated_value = value
	length_limit -= len(ellipsis_mark)

	for separator in [ " ", "_", "-" ]:
		while len(truncated_value) > length_limit and separator in truncated_value:
			truncated_value = truncated_value[:truncated_value.rfind(separator)]
	if len(truncated_value) > length_limit:
		truncated_value = truncated_value[:length_limit]

	if len(truncated_value) < len(value):
		return truncated_value + ellipsis_mark
	return truncated_value


def get_pagination(item_total: int, url_arguments: dict) -> dict:
	item_count = max(min(flask.request.args.get("item_count", default = 100, type = int), 1000), 10)
	page_total = max(int(math.ceil(item_total / item_count)), 1)
	page_number = max(min(flask.request.args.get("page", default = 1, type = int), page_total), 1)

	return {
		"page_number": page_number,
		"page_total": page_total,
		"item_count": item_count,
		"item_total": item_total,
		"url_arguments": url_arguments,
	}


def get_run_status_collection() -> List[str]:
	return [ "pending", "running", "succeeded", "failed", "exception", "aborted", "skipped", "cancelled" ]



def get_error_message(status_code: int) -> str: # pylint: disable = too-many-return-statements
	if status_code == 400:
		return "Bad request"
	if status_code == 401:
		return "Unauthorized"
	if status_code == 403:
		return "Forbidden"
	if status_code == 404:
		return "Page not found"
	if status_code == 405:
		return "Method not allowed"

	if status_code == 500:
		return "Internal server error"
	if status_code == 503:
		return "Service unavailable"

	if 400 <= status_code < 500:
		return "Client error"
	if 500 <= status_code < 600:
		return "Server error"
	return "Unknown error"


def get_file_extension(content_type: str) -> str:
	content_type = content_type.split(";")[0]

	if content_type == "application/javascript":
		return ".js"
	if content_type == "application/json":
		return ".json"
	if content_type == "application/zip":
		return ".zip"
	if content_type == "text/html":
		return ".html"
	if content_type == "text/plain":
		return ".txt"

	raise ValueError("Unsupported content type: '%s'" % content_type)


def add_display_names(project_collection: List[dict], job_collection: List[dict],
		run_collection: List[dict], schedule_collection: List[dict], worker_collection: List[dict]):

	for job in job_collection:
		project = next((x for x in project_collection if x["identifier"] == job["project"]), {})
		job["project_display_name"] = project.get("display_name", job["project"])

	for run in run_collection:
		project = next((x for x in project_collection if x["identifier"] == run["project"]), {})
		job = next((x for x in job_collection if x["project"] == run["project"] and x["identifier"] == run["job"]), {})
		worker = next((x for x in worker_collection if x["identifier"] == run["worker"]), {})
		run["project_display_name"] = project.get("display_name", run["project"])
		run["job_display_name"] = job.get("display_name", run["job"])
		run["worker_display_name"] = worker.get("display_name", run["worker"])

	for schedule in schedule_collection:
		project = next((x for x in project_collection if x["identifier"] == schedule["project"]), {})
		job = next((x for x in job_collection if x["project"] == schedule["project"] and x["identifier"] == schedule["job"]), {})
		schedule["project_display_name"] = project.get("display_name", schedule["project"])
		schedule["job_display_name"] = job.get("display_name", schedule["job"])
