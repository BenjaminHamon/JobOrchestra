import json
import logging
import os
import platform
import sys
import urllib.parse


def create_default_environment():
	return {
		"logging_stream_level": "info",
		"logging_stream_format": "{asctime} [{levelname}][{name}] {message}",
		"logging_stream_date_format": "%Y-%m-%dT%H:%M:%S",
		"logging_stream_traceback": False,

		"logging_file_level": "debug",
		"logging_file_format": "{asctime} [{levelname}][{name}] {message}",
		"logging_file_date_format": "%Y-%m-%dT%H:%M:%S",
		"logging_file_traceback": True,
		"logging_file_mode": "w",
		"logging_file_paths": [],

		"logging_summary_format": "[{levelname}][{name}] {message}",
		"logging_summary_date_format": "%Y-%m-%dT%H:%M:%S",

		"python3_executable": sys.executable,

		"orchestra_service_url": "http://127.0.0.1:5902",
	}


def load_environment():
	environment_instance = create_default_environment()
	environment_instance.update(_load_environment_transform(os.path.join(os.path.expanduser("~"), "environment.json")))
	environment_instance.update(_load_environment_transform("environment.json"))
	return environment_instance


def _load_environment_transform(transform_file_path):
	if not os.path.exists(transform_file_path):
		return {}
	with open(transform_file_path, mode = "r", encoding = "utf-8") as transform_file:
		return json.load(transform_file)


def configure_logging(environment_instance, arguments):
	if arguments is not None and getattr(arguments, "verbosity", None) is not None:
		environment_instance["logging_stream_level"] = arguments.verbosity
	if arguments is not None and getattr(arguments, "verbosity", None) == "debug":
		environment_instance["logging_stream_traceback"] = True
	if arguments is not None and getattr(arguments, "log_file_verbosity", None) is not None:
		environment_instance["logging_file_level"] = arguments.log_file_verbosity
	if arguments is not None and getattr(arguments, "log_file", None) is not None:
		environment_instance["logging_file_paths"].append(arguments.log_file)

	environment_instance["logging_stream_levelno"] = logging.getLevelName(environment_instance["logging_stream_level"].upper())
	environment_instance["logging_file_levelno"] = logging.getLevelName(environment_instance["logging_file_level"].upper())

	logging.root.setLevel(logging.DEBUG)

	logging.addLevelName(logging.DEBUG, "Debug")
	logging.addLevelName(logging.INFO, "Info")
	logging.addLevelName(logging.WARNING, "Warning")
	logging.addLevelName(logging.ERROR, "Error")
	logging.addLevelName(logging.CRITICAL, "Critical")

	logging.getLogger("asyncio").setLevel(logging.INFO)
	logging.getLogger("filelock").setLevel(logging.WARNING)
	logging.getLogger("urllib3").setLevel(logging.INFO)
	logging.getLogger("websockets.protocol").setLevel(logging.INFO)
	logging.getLogger("werkzeug").setLevel(logging.WARNING)

	configure_log_stream(environment_instance, sys.stdout)
	for log_file_path in environment_instance["logging_file_paths"]:
		configure_log_file(environment_instance, log_file_path)


def configure_log_stream(environment_instance, stream):
	formatter = logging.Formatter(environment_instance["logging_stream_format"], environment_instance["logging_stream_date_format"], "{")
	stream_handler = logging.StreamHandler(stream)
	stream_handler.setLevel(environment_instance["logging_stream_levelno"])
	stream_handler.formatter = formatter
	logging.root.addHandler(stream_handler)


def configure_log_file(environment_instance, file_path):
	if os.path.dirname(file_path):
		os.makedirs(os.path.dirname(file_path), exist_ok = True)

	formatter = logging.Formatter(environment_instance["logging_file_format"], environment_instance["logging_file_date_format"], "{")
	file_handler = logging.FileHandler(file_path, mode = environment_instance["logging_file_mode"], encoding = "utf-8")
	file_handler.setLevel(environment_instance["logging_file_levelno"])
	file_handler.formatter = formatter
	logging.root.addHandler(file_handler)


def load_test_context_environment(temporary_directory, database_type):
	database_uri = get_test_context_database_uri(temporary_directory, database_type) if database_type is not None else None

	return {
		"master_address": "127.0.0.1",
		"master_port": 5901,
		"service_address": "127.0.0.1",
		"service_port": 5902,
		"website_address": "127.0.0.1",
		"website_port": 5903,
		"database_uri": database_uri,
	}


def get_test_context_database_uri(temporary_directory, database_type):
	run_identifier = os.path.basename(os.path.dirname(temporary_directory))
	database_name = "orchestra_test_%s" % run_identifier

	if database_type == "json":
		data_directory = os.path.abspath(os.path.join(temporary_directory, "master"))

		if platform.system() == "Windows":
			data_directory_as_uri_path = "/" + data_directory[:2] + urllib.parse.quote(data_directory[2:].replace("\\", "/"))
		else:
			data_directory_as_uri_path = urllib.parse.quote(data_directory)

		return "json://" + data_directory_as_uri_path

	if database_type == "mongo":
		return "mongodb://127.0.0.1:27017/" + database_name

	if database_type == "postgresql":
		return "postgresql:///" + database_name

	raise ValueError("Unsupported database type '%s'" % database_type)


def get_all_database_types():
	return [ "json", "mongo", "postgresql" ]
