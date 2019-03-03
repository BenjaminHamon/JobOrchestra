import glob
import os

import setuptools


def list_package_data(package, pattern_collection):
	all_files = []
	for pattern in pattern_collection:
		all_files += glob.glob(package + "/" + pattern, recursive = True)
	return [ os.path.relpath(path, package) for path in all_files ]


resource_patterns = [ 'static/**/*.css', 'static/**/*.js', 'templates/**/*.html' ]

setuptools.setup(
	name = "bhamon-build-website",
	version = "{version}",
	description = "Website component for the build service, exposing a web interface for the master",
	author = "{author}",
	author_email = "{author_email}",
	url = "{url}",

	packages = [ "bhamon_build_website" ],
	package_data = { "bhamon_build_website": list_package_data("bhamon_build_website", resource_patterns) },

	install_requires = [ "flask", "requests" ],
)
