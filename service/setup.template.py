import setuptools


setuptools.setup(
	name = "bhamon-build-service",
	version = "{version}",
	description = "Web service component for build service, exposing a web interface to interact with the master",
	author = "{author}",
	author_email = "{author_email}",
	url = "{url}",

	packages = [ "bhamon_build_service" ],

	install_requires = [ "flask" ],
)
