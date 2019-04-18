import logging
import os
import shutil


logger = logging.getLogger("Main")


def configure_argument_parser(environment, configuration, subparsers): # pylint: disable=unused-argument
	return subparsers.add_parser("clean", help = "clean the workspace")


def run(environment, configuration, arguments): # pylint: disable=unused-argument
	clean(configuration, arguments.simulate, arguments.results)


def clean(configuration, simulate, result_file_path):
	logger.info("Cleaning the workspace")
	print("")

	directories_to_clean = [ ".pytest_cache", os.path.join("test", "__pycache__") ]

	for component in configuration["components"]:
		directories_to_clean.append(os.path.join(component["path"], "build"))
		directories_to_clean.append(os.path.join(component["path"], "dist"))
		for package in component["packages"]:
			directories_to_clean.append(os.path.join(component["path"], package, "__pycache__"))
			directories_to_clean.append(os.path.join(component["path"], package + ".egg-info"))

	directories_to_clean.sort()

	for directory in directories_to_clean:
		if os.path.exists(directory):
			logger.info("Removing directory '%s'", directory)
			if not simulate:
				shutil.rmtree(directory)

	if os.path.isdir("build_results"):
		for build_identifier in os.listdir("build_results"):
			if os.sep + build_identifier + os.sep in result_file_path:
				continue
			logger.info("Removing build results for '%s'", build_identifier)
			if not simulate:
				shutil.rmtree(os.path.join("build_results", build_identifier))

	if os.path.isdir("test_results"):
		for run_identifier in os.listdir("test_results"):
			logger.info("Removing test results for '%s'", run_identifier)
			if not simulate:
				shutil.rmtree(os.path.join("test_results", run_identifier))
