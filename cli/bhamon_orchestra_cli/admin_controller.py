import getpass
import logging


logger = logging.getLogger("AdminController")


def register_commands(subparsers):
	command_parser = subparsers.add_parser("create-authentication-token", help = "create a user authentication token")
	command_parser.set_defaults(handler = create_authentication_token)
	command_parser = subparsers.add_parser("delete-user", help = "delete a user")
	command_parser.set_defaults(handler = delete_user)
	command_parser = subparsers.add_parser("delete-worker", help = "delete a worker")
	command_parser.set_defaults(handler = delete_worker)
	command_parser = subparsers.add_parser("reset-administrator", help = "reset an administrator user")
	command_parser.set_defaults(handler = reset_administrator)


def create_authentication_token(application, arguments): # pylint: disable = unused-argument
	user = input("User: ")
	description = input("Description: ")
	return application.authentication_provider.create_token(user, description, None)


def delete_user(application, arguments): # pylint: disable = unused-argument
	user = input("User: ")
	application.user_provider.delete(user, application.authentication_provider, application.worker_provider)


def delete_worker(application, arguments): # pylint: disable = unused-argument
	worker = input("Worker: ")
	application.worker_provider.delete(worker, application.run_provider)


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
