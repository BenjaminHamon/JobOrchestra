import os
import sys

import setuptools

sys.path.insert(0, os.path.join(sys.path[0], ".."))

import development.configuration # pylint: disable = import-error, wrong-import-position
import development.environment # pylint: disable = import-error, wrong-import-position


environment_instance = development.environment.load_environment()
configuration_instance = development.configuration.load_configuration(environment_instance)
parameters = development.configuration.get_setuptools_parameters(configuration_instance)


resource_patterns = [
	"static/**/*.css",
	"static/**/*.eot",
	"static/**/*.js",
	"static/**/*.mjs",
	"static/**/*.svg",
	"static/**/*.ttf",
	"static/**/*.woff",
	"static/**/*.woff2",
	"templates/**/*.html",
]

parameters.update({
	"name": "bhamon-orchestra-website",
	"description": "Website component for Job Orchestra, exposing a web interface for the master",
	"packages": [ "bhamon_orchestra_website" ],
	"python_requires": "~= 3.7",
	"install_requires": [ "cron-descriptor ~= 1.2", "flask ~= 1.1", "requests ~= 2.24" ],
	"package_data": { "bhamon_orchestra_website": development.configuration.list_package_data("bhamon_orchestra_website", resource_patterns) },
})

setuptools.setup(**parameters)
