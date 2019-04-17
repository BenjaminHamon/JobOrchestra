import os
import sys

import setuptools

sys.path.insert(0, os.path.join(sys.path[0], ".."))

import scripts.configuration # pylint: disable = wrong-import-position
import scripts.environment # pylint: disable = wrong-import-position


environment_instance = scripts.environment.load_environment()
configuration_instance = scripts.configuration.load_configuration(environment_instance)
parameters = scripts.configuration.get_setuptools_parameters(configuration_instance)


resource_patterns = [ 'static/**/*.css', 'static/**/*.js', 'templates/**/*.html' ]

parameters.update({
	"name": "bhamon-build-website",
	"description": "Website component for the build service, exposing a web interface for the master",
	"packages": [ "bhamon_build_website" ],
	"python_requires": "~= 3.5",
	"install_requires": [ "flask ~= 1.0", "requests ~= 2.21" ],
	"package_data": { "bhamon_build_website": scripts.configuration.list_package_data("bhamon_build_website", resource_patterns) },
})

setuptools.setup(**parameters)
