import glob
import logging
import os
import shutil


logger = logging.getLogger("Main")


def configure_argument_parser(environment, configuration, subparsers): # pylint: disable = unused-argument
	parser = subparsers.add_parser("clean", help = "clean the workspace")
	parser.set_defaults(func = run)


def run(environment, configuration, arguments): # pylint: disable = unused-argument
	clean(configuration, arguments.simulate)


def clean(configuration, simulate):
	logger.info("Cleaning the workspace")
	print("")

	directories_to_clean = [ ".artifacts", ".pytest_cache", os.path.join("test", "__pycache__"), "test_results" ]

	for component in configuration["components"]:
		directories_to_clean += [ os.path.join(component["path"], "build") ]
		directories_to_clean += [ os.path.join(component["path"], "dist") ]
		directories_to_clean += [ os.path.join(component["path"], component["name"].replace("-", "_") + ".egg-info") ]
		directories_to_clean += glob.glob(os.path.join(component["path"], component["name"].replace("-", "_"), "**", "__pycache__"), recursive = True)

	directories_to_clean.sort()

	for directory in directories_to_clean:
		if os.path.exists(directory):
			logger.info("Removing directory '%s'", directory)
			if not simulate:
				shutil.rmtree(directory)

	for component in configuration["components"]:
		metadata_file = os.path.join(component["path"], component["name"].replace("-", "_"), "__metadata__.py")
		if os.path.exists(metadata_file):
			logger.info("Removing generated file '%s'", metadata_file)
			if not simulate:
				os.remove(metadata_file)
