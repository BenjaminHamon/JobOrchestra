import math

import flask


def get_pagination(item_total):
	item_count = max(min(flask.request.args.get("item_count", default = 100, type = int), 1000), 10)
	page_total = max(int(math.ceil(item_total / item_count)), 1)
	page_number = max(min(flask.request.args.get("page", default = 1, type = int), page_total), 1)
	return { "page_number": page_number, "page_total": page_total, "item_count": item_count, "item_total": item_total}


def strip_pagination_arguments(arguments):
	return { k: v for k, v in arguments.items() if k not in [ "page", "item_count" ] }
