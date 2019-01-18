import setuptools


setuptools.setup(
	name = "bhamon-build-website",
	version = "1.0",
	description = "Website component for the build service, exposing a web interface for the master",
	author = "Benjamin Hamon",
	author_email = "hamon.benjamin@gmail.com",

	packages = [
		"bhamon_build_website",
	],

	install_requires = [
		"flask",
		"requests",
	],
)
