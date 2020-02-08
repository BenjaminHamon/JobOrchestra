import math

import cron_descriptor
import flask


cron_descriptor_options = cron_descriptor.Options()
cron_descriptor_options.use_24hour_time_format = True


def none_if_empty(value):
	if value == "":
		return None
	return value


def get_pagination(item_total):
	item_count = max(min(flask.request.args.get("item_count", default = 100, type = int), 1000), 10)
	page_total = max(int(math.ceil(item_total / item_count)), 1)
	page_number = max(min(flask.request.args.get("page", default = 1, type = int), page_total), 1)
	return { "page_number": page_number, "page_total": page_total, "item_count": item_count, "item_total": item_total}


def strip_pagination_arguments(arguments):
	return { k: v for k, v in arguments.items() if k not in [ "page", "item_count" ] }


def describe_cron_expression(expression):
	return cron_descriptor.get_description(expression, cron_descriptor_options)


def get_error_message(status_code): # pylint: disable = too-many-return-statements
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
