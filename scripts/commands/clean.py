import logging
import os
import shutil


def configure_argument_parser(environment, configuration, subparsers): # pylint: disable=unused-argument
	return subparsers.add_parser("clean", help = "clean the workspace")


def run(environment, configuration, arguments): # pylint: disable=unused-argument
	clean(configuration["packages"], arguments.simulate)


def clean(package_collection, simulate):
	logging.info("Cleaning the workspace")
	logging.info("")

	directories_to_clean = []
	for package in package_collection:
		directories_to_clean += [ { "display_name": "Python cache", "path": package + "/__pycache__" } ]

	directories_to_clean += [
		{ "display_name": "Python cache", "path": "test/__pycache__" },
		{ "display_name": "Pytest cache", "path": ".pytest_cache" },
		{ "display_name": "Test results", "path": "test_results" },
	]

	for directory in directories_to_clean:
		if os.path.exists(directory["path"]):
			logging.info("Removing directory '%s' (Path: '%s')", directory["display_name"], directory["path"])
			if not simulate:
				shutil.rmtree(directory["path"])
