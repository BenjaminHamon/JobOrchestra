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
	"name": "bhamon-orchestra-cli",
	"description": "Command line interpreter component for Job Orchestra, to interact with the master from a terminal",
	"packages": [ "bhamon_orchestra_cli" ],
	"python_requires": "~= 3.5",
})

setuptools.setup(**parameters)
