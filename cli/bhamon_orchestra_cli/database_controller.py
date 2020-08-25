import logging

import bhamon_orchestra_model.database.import_export as database_import_export


logger = logging.getLogger("DatabaseController")


def register_commands(subparsers):
	command_parser = subparsers.add_parser("initialize-database", help = "initialize the database")
	command_parser.add_argument("--simulate", action = "store_true", help = "perform a simulation (dry-run)")
	command_parser.set_defaults(handler = initialize_database)

	command_parser = subparsers.add_parser("upgrade-database", help = "upgrade the database")
	command_parser.add_argument("--simulate", action = "store_true", help = "perform a simulation (dry-run)")
	command_parser.set_defaults(handler = upgrade_database)

	command_parser = subparsers.add_parser("import-database", help = "import the database")
	command_parser.add_argument("--simulate", action = "store_true", help = "perform a simulation (dry-run)")
	command_parser.add_argument("--source", required = True, help = "set the source directory")
	command_parser.set_defaults(handler = import_database)

	command_parser = subparsers.add_parser("export-database", help = "export the database")
	command_parser.add_argument("--simulate", action = "store_true", help = "perform a simulation (dry-run)")
	command_parser.add_argument("--output", required = True, help = "set the output directory")
	command_parser.set_defaults(handler = export_database)


def initialize_database(application, arguments):
	with application.database_administration_factory() as database_administration:
		database_administration.initialize(simulate = arguments.simulate)


def upgrade_database(application, arguments):
	with application.database_administration_factory() as database_administration:
		database_administration.upgrade(simulate = arguments.simulate)


def import_database(application, arguments):
	with application.database_client_factory() as database_client:
		database_import_export.import_database(database_client, arguments.source, simulate = arguments.simulate)


def export_database(application, arguments):
	with application.database_client_factory() as database_client:
		database_import_export.export_database(database_client, arguments.output, simulate = arguments.simulate)
