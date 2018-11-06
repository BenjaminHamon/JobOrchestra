import setuptools


setuptools.setup(
	name = "bhamon-build-service",
	version = "1.0",
	description = "Web service component for build service, exposing a web interface to interact with the master",
	author = "Benjamin Hamon",
	author_email = "hamon.benjamin@gmail.com",

	packages = [
		"bhamon_build_service",
	]
)