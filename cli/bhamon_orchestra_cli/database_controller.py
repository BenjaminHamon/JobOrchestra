import logging


logger = logging.getLogger("DatabaseController")


def register_commands(subparsers):
	command_parser = subparsers.add_parser("initialize-database", help = "initialize the database")
	command_parser.add_argument("--simulate", action = "store_true", help = "perform a simulation (dry-run)")
	command_parser.set_defaults(handler = initialize_database)

	command_parser = subparsers.add_parser("upgrade-database", help = "upgrade the database")
	command_parser.add_argument("--simulate", action = "store_true", help = "perform a simulation (dry-run)")
	command_parser.set_defaults(handler = upgrade_database)


def initialize_database(application, arguments):
	application.database_administration.initialize(simulate = arguments.simulate)


def upgrade_database(application, arguments):
	application.database_administration.upgrade(simulate = arguments.simulate)
