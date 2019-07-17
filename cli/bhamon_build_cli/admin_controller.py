def register_commands(subparsers):
	command_parser = subparsers.add_parser("reload-configuration", help = "reload the master configuration")
	command_parser.set_defaults(handler = reload_configuration)


def reload_configuration(application, arguments): # pylint: disable = unused-argument
	task = application.task_provider.create("reload_configuration", {})
	return { "task_identifier": task["identifier"] }
