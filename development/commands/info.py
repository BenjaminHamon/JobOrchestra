import json
import logging


logger = logging.getLogger("Main")


def configure_argument_parser(environment, configuration, subparsers): # pylint: disable = unused-argument
	parser = subparsers.add_parser("info", help = "show the project information")
	parser.set_defaults(func = run)


def run(environment, configuration, arguments): # pylint: disable = unused-argument
	logger.info("Version:\n%s", json.dumps(configuration["project_version"], indent = 4))
