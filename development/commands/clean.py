import glob
import logging
import os
import shutil
from typing import List


logger = logging.getLogger("Main")


def configure_argument_parser(environment, configuration, subparsers): # pylint: disable = unused-argument
	parser = subparsers.add_parser("clean", help = "clean the workspace")
	parser.set_defaults(func = run)


def run(environment, configuration, arguments): # pylint: disable = unused-argument
	clean_artifacts(configuration["artifact_directory"], configuration["components"], simulate = arguments.simulate)
	clean_cache(configuration["components"], simulate = arguments.simulate)
	clean_metadata(configuration["components"], simulate = arguments.simulate)


def clean_artifacts(artifact_directory: str, component_collection: List[dict], simulate: bool) -> None:
	logger.info("Cleaning artifacts")

	if os.path.exists(artifact_directory):
		logger.debug("Removing directory '%s'", artifact_directory)
		if not simulate:
			shutil.rmtree(artifact_directory)

	all_build_directories = []
	for component in component_collection:
		all_build_directories += [ os.path.join(component["path"], "build") ]
		all_build_directories += [ os.path.join(component["path"], "dist") ]

	all_build_directories.sort()

	for build_directory in all_build_directories:
		if os.path.exists(build_directory):
			logger.debug("Removing directory '%s'", build_directory)
			if not simulate:
				shutil.rmtree(build_directory)


def clean_cache(component_collection: List[dict], simulate: bool) -> None:
	logger.info("Cleaning cache")

	all_cache_directories = [ ".pytest_cache", os.path.join("test", "__pycache__") ]

	for component in component_collection:
		source_directory = os.path.join(component["path"], component["name"].replace("-", "_"))
		all_cache_directories += glob.glob(os.path.join(source_directory, "**", "__pycache__"), recursive = True)

	all_cache_directories.sort()

	for cache_directory in all_cache_directories:
		if os.path.exists(cache_directory):
			logger.debug("Removing directory '%s'", cache_directory)
			if not simulate:
				shutil.rmtree(cache_directory)


def clean_metadata(component_collection: List[dict], simulate: bool) -> None:
	logger.info("Cleaning metadata")

	for component in component_collection:
		source_directory = os.path.join(component["path"], component["name"].replace("-", "_"))
		metadata_file = os.path.join(source_directory, "__metadata__.py")
		if os.path.exists(metadata_file):
			logger.debug("Removing generated file '%s'", metadata_file)
			if not simulate:
				os.remove(metadata_file)
