import setuptools


setuptools.setup(
	name = "bhamon-build-service",
	version = "1.0",
	description = "Web service component for build service, exposing a web interface to interact with the master",
	author = "Benjamin Hamon",
	author_email = "hamon.benjamin@gmail.com",
	url = "https://github.com/BenjaminHamon/BuildService",

	packages = [
		"bhamon_build_service",
	],

	install_requires = [
		"flask",
	],
)