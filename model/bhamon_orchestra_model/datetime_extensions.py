import datetime
import re


timedelta_regex = re.compile(r"^((?P<weeks>[0-9]+)w)?((?P<days>[0-9]+)d)?((?P<hours>[0-9]+)h)?((?P<minutes>[0-9]+)m)?((?P<seconds>[0-9]+)s)?$")


def parse_timedelta(value_string: str) -> datetime.timedelta:
	timedelta_match = timedelta_regex.search(value_string.replace(" ", ""))
	if not timedelta_match:
		raise ValueError("Invalid timedelta value: '%s'" % value_string)
	return datetime.timedelta( ** { key: int(value) for key, value in timedelta_match.groupdict().items() if value is not None })
