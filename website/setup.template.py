import setuptools


setuptools.setup(
	name = "bhamon-build-website",
	version = "{version}",
	description = "Website component for the build service, exposing a web interface for the master",
	author = "{author}",
	author_email = "{author_email}",
	url = "{url}",

	packages = [ "bhamon_build_website" ],

	install_requires = [ "flask", "requests" ],
)
