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
	"name": "bhamon-build-master",
	"description": "Master component for build service, responsible for supervising workers and builds",
	"packages": [ "bhamon_build_master" ],
	"python_requires": "~= 3.5",
	"install_requires": [ "websockets ~= 7.0" ],
})

setuptools.setup(**parameters)
