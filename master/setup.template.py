import setuptools


setuptools.setup(
	name = "bhamon-build-master",
	version = "{version}",
	description = "Master component for build service, responsible for supervising workers and builds",
	author = "{author}",
	author_email = "{author_email}",
	url = "{url}",

	packages = [ "bhamon_build_master" ],

	install_requires = [ "websockets" ],
)
