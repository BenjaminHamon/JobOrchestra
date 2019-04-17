import logging
import os
import shutil


def configure_argument_parser(environment, configuration, subparsers): # pylint: disable=unused-argument
	return subparsers.add_parser("clean", help = "clean the workspace")


def run(environment, configuration, arguments): # pylint: disable=unused-argument
	clean(configuration, arguments.simulate)


def clean(configuration, simulate):
	logging.info("Cleaning the workspace")
	print("")

	directories_to_clean = [ ".pytest_cache", "build_results", "test_results", os.path.join("test", "__pycache__") ]

	for component in configuration["components"]:
		directories_to_clean.append(os.path.join(component["path"], "build"))
		directories_to_clean.append(os.path.join(component["path"], "dist"))
		for package in component["packages"]:
			directories_to_clean.append(os.path.join(component["path"], package, "__pycache__"))
			directories_to_clean.append(os.path.join(component["path"], package + ".egg-info"))

	directories_to_clean.sort()

	for directory in directories_to_clean:
		if os.path.exists(directory):
			logging.info("Removing directory '%s'", directory)
			if not simulate:
				shutil.rmtree(directory)
