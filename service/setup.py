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
	"name": "bhamon-orchestra-service",
	"description": "Web service component for Job Orchestra, exposing a web interface to interact with the master",
	"packages": [ "bhamon_orchestra_service" ],
	"python_requires": "~= 3.7",
	"install_requires": [ "flask ~= 1.1.2" ],
})

setuptools.setup(**parameters)
