import scripts.commands.artifact
import scripts.commands.clean
import scripts.commands.distribute


def configure_argument_parser(environment, configuration, subparsers): # pylint: disable = unused-argument
	return subparsers.add_parser("release", help = "build a package for release")


def run(environment, configuration, arguments): # pylint: disable = unused-argument
	arguments.distribute_commands = [ "setup", "package" ]

	arguments.parameters = {}
	arguments.artifact = "package"
	arguments.artifact_commands = [ "package", "verify" ]

	if arguments.simulate:
		arguments.artifact_commands = [ "package" ]

	scripts.commands.clean.run(environment, configuration, arguments)
	print("")
	scripts.commands.distribute.run(environment, configuration, arguments)
	print("")
	scripts.commands.artifact.run(environment, configuration, arguments)
