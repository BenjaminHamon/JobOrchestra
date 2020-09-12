import os
import sys

import setuptools

sys.path.insert(0, os.path.join(sys.path[0], ".."))

import development.configuration # pylint: disable = import-error, wrong-import-position
import development.environment # pylint: disable = import-error, wrong-import-position


environment_instance = development.environment.load_environment()
configuration_instance = development.configuration.load_configuration(environment_instance)
parameters = development.configuration.get_setuptools_parameters(configuration_instance)


parameters.update({
	"name": "bhamon-orchestra-worker",
	"description": "Worker component for Job Orchestra, responsible for executing runs",

	"packages": [
		"bhamon_orchestra_worker",
		"bhamon_orchestra_worker/revision_control",
	],

	"python_requires": "~= 3.7",
	"install_requires": [ "filelock ~= 3.0", "requests ~= 2.24", "websockets ~= 8.1" ],
})

setuptools.setup(**parameters)
