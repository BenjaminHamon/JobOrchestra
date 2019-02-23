import logging
import os
import shutil


def configure_argument_parser(environment, configuration, subparsers): # pylint: disable=unused-argument
	return subparsers.add_parser("clean", help = "clean the workspace")


def run(environment, configuration, arguments): # pylint: disable=unused-argument
	clean(configuration, arguments.simulate)


def clean(configuration, simulate):
	logging.info("Cleaning the workspace")
	logging.info("")

	directories_to_clean = [
		{ "display_name": "Build", "path": ".build" },
	]

	for component in configuration["components"]:
		for package in component["packages"]:
			directories_to_clean += [ { "display_name": "Python cache", "path": os.path.join(component["path"], package, "__pycache__") } ]

	directories_to_clean += [
		{ "display_name": "Python cache", "path": os.path.join("test", "__pycache__") },
		{ "display_name": "Pytest cache", "path": ".pytest_cache" },
		{ "display_name": "Test results", "path": "test_results" },
	]

	for directory in directories_to_clean:
		if os.path.exists(directory["path"]):
			logging.info("Removing directory '%s' (Path: '%s')", directory["display_name"], directory["path"])
			if not simulate:
				shutil.rmtree(directory["path"])

	for component in configuration["components"]:
		setup_script = os.path.join(component["path"], "setup.py")
		if os.path.exists(setup_script):
			logging.info("Removing generated script '%s'", setup_script)
			if not simulate:
				os.remove(setup_script)
