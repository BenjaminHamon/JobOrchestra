import getpass
import logging


logger = logging.getLogger("AdminController")


def register_commands(subparsers):
	command_parser = subparsers.add_parser("reload-configuration", help = "reload the master configuration")
	command_parser.set_defaults(handler = reload_configuration)
	command_parser = subparsers.add_parser("reset-administrator", help = "reset an administrator user")
	command_parser.set_defaults(handler = reset_administrator)


def reload_configuration(application, arguments): # pylint: disable = unused-argument
	task = application.task_provider.create("reload_configuration", {})
	return { "task_identifier": task["identifier"] }


def reset_administrator(application, arguments): # pylint: disable = unused-argument
	identifier = input("Identifier: ")
	display_name = input("Display name: ")
	password = getpass.getpass("Password: ")

	user = application.user_provider.get(identifier)
	roles = application.authorization_provider.get_administrator_roles()

	if user is None:
		user = application.user_provider.create(identifier, display_name)
	application.user_provider.update_identity(user, display_name)
	application.user_provider.update_roles(user, roles)
	application.user_provider.update_status(user, is_enabled = True)
	application.authentication_provider.set_password(identifier, password)

	return user