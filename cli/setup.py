import os
import sys

import setuptools

sys.path.insert(0, os.path.join(sys.path[0], ".."))

import scripts.configuration # pylint: disable = wrong-import-position
import scripts.environment # pylint: disable = wrong-import-position


environment_instance = scripts.environment.load_environment()
configuration_instance = scripts.configuration.load_configuration(environment_instance)
parameters = scripts.configuration.get_setuptools_parameters(configuration_instance)


parameters.update({
	"name": "bhamon-build-cli",
	"description": "Command line interpreter component for build service, to interact with the master from a terminal",
	"packages": [ "bhamon_build_cli" ],
	"python_requires": "~= 3.5",
})

setuptools.setup(**parameters)
