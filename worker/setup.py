import os
import sys

import setuptools

sys.path.insert(0, os.path.join(sys.path[0], ".."))

import development.configuration # pylint: disable = wrong-import-position
import development.environment # pylint: disable = wrong-import-position


environment_instance = development.environment.load_environment()
configuration_instance = development.configuration.load_configuration(environment_instance)
parameters = development.configuration.get_setuptools_parameters(configuration_instance)


parameters.update({
	"name": "bhamon-build-worker",
	"description": "Worker component for build service, responsible for executing builds",
	"packages": [ "bhamon_build_worker" ],
	"python_requires": "~= 3.5",
	"install_requires": [ "filelock ~= 3.0", "requests ~= 2.21", "websockets ~= 7.0" ],
})

setuptools.setup(**parameters)
