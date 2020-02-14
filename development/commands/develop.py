import logging
import os
import subprocess


logger = logging.getLogger("Main")


def configure_argument_parser(environment, configuration, subparsers): # pylint: disable = unused-argument
	parser = subparsers.add_parser("develop", help = "setup workspace for development")
	parser.set_defaults(func = run)


def run(environment, configuration, arguments): # pylint: disable = unused-argument
	python_executable = environment["python3_executable"]
	python_package_repository = environment.get("python_package_repository_web_url", None)

	logger.info("Installing development toolkit")
	development_toolkit_package = configuration["development_toolkit"].format(revision = configuration["development_toolkit_revision"])
	install_packages(python_executable, python_package_repository, [ development_toolkit_package ], arguments.simulate)
	print("")

	if len(configuration.get("development_dependencies", [])) > 0:
		logger.info("Installing development dependencies")
		install_packages(python_executable, python_package_repository, configuration["development_dependencies"], arguments.simulate)
		print("")

	if len(configuration.get("project_dependencies", [])) > 0:
		logger.info("Installing project dependencies")
		install_packages(python_executable, python_package_repository, configuration["project_dependencies"], arguments.simulate)
		print("")

	for component in configuration["components"]:
		setup_component(configuration, component, arguments.simulate)
	print("")

	logger.info("Installing project packages")
	development_package_collection = [ os.path.join(".", component["path"]) for component in configuration["components"] ]
	install_packages(python_executable, python_package_repository, development_package_collection, arguments.simulate)


def install_packages(python_executable, python_package_repository, package_collection, simulate):
	install_command = [ python_executable, "-m", "pip", "install", "--upgrade" ]
	install_command += [ "--extra-index", python_package_repository ] if python_package_repository is not None else []

	for package in package_collection:
		install_command += [ "--editable", package ] if os.path.isdir(package) else [ package ]

	logger.info("+ %s", " ".join(("'" + x + "'") if " " in x else x for x in install_command))
	if not simulate:
		subprocess.check_call(install_command)


def setup_component(configuration, component, simulate):
	logger.info("Generating metadata for '%s'", component["name"])

	metadata_file_path = os.path.join(component["path"], component["name"].replace("-", "_"), "__metadata__.py")
	metadata_content = ""
	metadata_content += "__copyright__ = \"%s\"\n" % configuration["copyright"]
	metadata_content += "__version__ = \"%s\"\n" % configuration["project_version"]["full"]
	metadata_content += "__date__ = \"%s\"\n" % configuration["project_version"]["date"]

	if not simulate:
		with open(metadata_file_path, "w", encoding = "utf-8") as metadata_file:
			metadata_file.writelines(metadata_content)
