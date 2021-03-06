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
	"name": "bhamon-orchestra-model",
	"description": "Model library for Job Orchestra",

	"packages": [
		"bhamon_orchestra_model",
		"bhamon_orchestra_model/database",
		"bhamon_orchestra_model/network",
		"bhamon_orchestra_model/revision_control",
	],

	"python_requires": "~= 3.5",
	"install_requires": [ "python-dateutil ~= 2.8", "python2-secrets ~= 1.0 ; python_version < '3.6'" ],
})

setuptools.setup(**parameters)
