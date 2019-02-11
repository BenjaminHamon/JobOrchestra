import setuptools


setuptools.setup(
	name = "bhamon-build-worker",
	version = "1.0",
	description = "Worker component for build service, responsible for executing builds",
	author = "Benjamin Hamon",
	author_email = "hamon.benjamin@gmail.com",
	url = "https://github.com/BenjaminHamon/BuildService",

	packages = [
		"bhamon_build_worker",
	],

	install_requires = [
		"filelock",
		"requests",
		"websockets",
	],
)