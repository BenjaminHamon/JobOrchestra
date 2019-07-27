import datetime
import re


timedelta_regex = re.compile(r"^((?P<weeks>[0-9]+)w)?((?P<days>[0-9]+)d)?((?P<hours>[0-9]+)h)?((?P<minutes>[0-9]+)m)?((?P<seconds>[0-9]+)s)?$")


def parse_timedelta(value_string):
	timedelta_match = timedelta_regex.search(value_string.replace(" ", ""))
	if not timedelta_match:
		raise ValueError("Invalid timedelta value: '%s'" % value_string)
	return datetime.timedelta( ** { key: int(value) for key, value in timedelta_match.groupdict().items() if value is not None })


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
