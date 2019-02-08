import setuptools


setuptools.setup(
	name = "bhamon-build-master",
	version = "1.0",
	description = "Master component for build service, responsible for supervising workers and builds",
	author = "Benjamin Hamon",
	author_email = "hamon.benjamin@gmail.com",
	url = "https://github.com/BenjaminHamon/BuildService",

	packages = [
		"bhamon_build_master",
	],

	install_requires = [
		"websockets",
	],
)