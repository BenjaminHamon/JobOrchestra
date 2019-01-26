import math

import flask


def get_pagination(item_total):
	item_count = max(min(flask.request.args.get("item_count", default = 100, type = int), 1000), 10)
	page_number = max(flask.request.args.get("page", default = 1, type = int), 1)
	page_total = int(math.ceil(item_total / item_count))
	return { "page_number": page_number, "page_total": page_total, "item_count": item_count, "item_total": item_total}
