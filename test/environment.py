import logging
import sys


log_format = "[{levelname}][{name}] {message}"


def configure_logging(log_level):
	logging.basicConfig(level = log_level, format = log_format, style = "{")
	logging.addLevelName(logging.DEBUG, "Debug")
	logging.addLevelName(logging.INFO, "Info")
	logging.addLevelName(logging.WARNING, "Warning")
	logging.addLevelName(logging.ERROR, "Error")
	logging.addLevelName(logging.CRITICAL, "Critical")

	logging.getLogger('filelock').setLevel(logging.WARNING)
	logging.getLogger('urllib3').setLevel(logging.INFO)
	logging.getLogger('websockets.protocol').setLevel(logging.INFO)


def load_environment():
	return {
		"python3_executable": sys.executable,
	}
