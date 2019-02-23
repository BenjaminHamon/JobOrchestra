import os
import sys

import setuptools


setup_directory = os.path.dirname(os.path.realpath(__file__))
workspace_directory = os.path.dirname(setup_directory)
sys.path.insert(0, os.path.join(workspace_directory, "scripts"))


import configuration # pylint: disable = import-error, wrong-import-position
import environment # pylint: disable = import-error, wrong-import-position


os.chdir(workspace_directory)

component_name = "bhamon-build-master"
environment_instance = environment.load_environment()
configuration_instance = configuration.load_configuration(environment_instance)

os.chdir(setup_directory)


component = next(c for c in configuration_instance["components"] if c["name"] == component_name)

setuptools.setup(
	name = component["name"],
	version = configuration_instance["project_version"]["full"],
	description = component["description"],
	author = configuration_instance["author"],
	author_email = configuration_instance["author_email"],
	url = configuration_instance["project_url"],

	packages = component["packages"],
	install_requires = component.get("install_requires", []),
)
