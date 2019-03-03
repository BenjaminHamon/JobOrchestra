import setuptools


setuptools.setup(
	name = "bhamon-build-worker",
	version = "{version}",
	description = "Worker component for build service, responsible for executing builds",
	author = "{author}",
	author_email = "{author_email}",
	url = "{url}",

	packages = [ "bhamon_build_worker" ],

	install_requires = [ "filelock", "requests", "websockets" ],
)
