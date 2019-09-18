import logging
import os
import subprocess


logger = logging.getLogger("Main")


def configure_argument_parser(environment, configuration, subparsers): # pylint: disable = unused-argument
	return subparsers.add_parser("develop", help = "setup workspace for development")


def run(environment, configuration, arguments): # pylint: disable = unused-argument
	install_development_toolkit(environment["python3_executable"], configuration["development_toolkit"], configuration["development_toolkit_revision"], arguments.simulate)
	print("")

	install_dependencies(environment["python3_executable"], configuration["development_dependencies"], arguments.simulate)
	print("")

	for component in configuration["components"]:
		setup_component(configuration, component, arguments.simulate)
	print("")

	for component in configuration["components"]:
		install_component(environment["python3_executable"], component, arguments.simulate)
		print("")


def install_development_toolkit(python_executable, source, revision, simulate):
	logger.info("Installing development toolkit")

	install_command = [ python_executable, "-m", "pip", "install", "--upgrade" ]
	if os.path.isdir(source):
		install_command += [ "--editable", source ]
	else:
		install_command += [ source.format(revision = revision) ]

	logger.info("+ %s", " ".join(install_command))
	if not simulate:
		subprocess.check_call(install_command)


def install_dependencies(python_executable, dependency_collection, simulate):
	logger.info("Installing development dependencies")

	install_command = [ python_executable, "-m", "pip", "install", "--upgrade" ] + dependency_collection
	logger.info("+ %s", " ".join(install_command))
	if not simulate:
		subprocess.check_call(install_command)


def setup_component(configuration, component, simulate):
	logger.info("Generating metadata for '%s'", component["name"])

	metadata_file_path = os.path.join(component["path"], component["packages"][0], "__metadata__.py")
	metadata_content = ""
	metadata_content += "__copyright__ = \"%s\"\n" % configuration["copyright"]
	metadata_content += "__version__ = \"%s\"\n" % configuration["project_version"]["full"]
	metadata_content += "__date__ = \"%s\"\n" % configuration["project_version"]["date"]

	if not simulate:
		with open(metadata_file_path, "w", encoding = "utf-8") as metadata_file:
			metadata_file.writelines(metadata_content)


def install_component(python_executable, component, simulate):
	logger.info("Installing development package for '%s'", component["name"])

	install_command = [ python_executable, "-m", "pip", "install", "--upgrade", "--editable", os.path.join(".", component["path"]) ]
	logger.info("+ %s", " ".join(install_command))
	if not simulate:
		subprocess.check_call(install_command)
