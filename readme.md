# Job Orchestra


## Overview

Job Orchestra is a toolkit for building a service which manages distributed job execution across a computer network.
A common use for it would be in a continuous integration pipeline.

The project is open source software. See [About](about.md) for more information.


## Development

The project include commands to automate development related tasks. They are exposed by the `development/main.py` script. Check the script help, using the `--help` option, for information about commands. You can also run commands with the `--simulate` option to check their behavior before actually running them.


To set up a workspace for development, create a `python3` virtual environment, then run the `develop` command. This will install the project dependencies and packages in your python environment.

```
python3 ./development/main.py develop
```

Check out the [Documentation](documentation) for more information.


## Instance Setup

A job orchestra instance includes several components, each with its process which could run on its own host, with its own environment. A typical setup includes a master, a service, a website and several workers.

You need to write entry point scripts for all the components, as well as the master configuration. The test suite includes an example used by [integration tests](test/integration).

For the database, the project currently supports MongoDB, as well as a custom JSON database meant for development only. You can implement custom providers if you wish to use another database. To use MongoDB, ensure you have a running and reachable MongoDB instance and configure the master and service entry points to connect to it.

For development, you can set up a local workspace with a python virtual environment in which you install the project packages. Then set up directories for the components you need: a master, a service, a website, one or two workers. Depending on what you are working on, you could run only a subset of them, or you may need more.
