# Setup

A job orchestra instance includes several components, each with its process which could run on its own host, with its own environment. A typical setup includes a database, a master, a service, a website and several workers.


## Configuration

Each application needs to be set up by initializating its dependencies and configuration. You need to write entry point scripts, as well as the master configuration.

The master configuration must define the projects and jobs managed by the orchestra, and must be loaded in the database. Users can be created at runtime through the website. A first administrator user must be created using the CLI.

The [integration tests](../test/integration) use basic scripts and configuration, which can serve as an example. For a more complex use case, see the project [JobOrchestra-Configuration](https://github.com/BenjaminHamon/JobOrchestra-Configuration).


## Database

The project currently supports MongoDB and SQL databases, as well as a custom JSON database meant for development only. You can implement custom providers if you wish to use another database. To use MongoDB or a SQL database service, ensure you have a running and reachable instance and configure the master and service entry points to connect to it.


## Development

For a development environemnt, you should set up a local workspace with a python virtual environment in which you install the project packages. Then set up directories for the components you need: usually, a master, a service, a website, one or two workers.


## Production

For a production environment, you should start with a single server to host the master, the service and the website. If the need arises, the service and website can be easily scaled up by hosting them on several servers behind a load balancer.

How you manage your workers is up to you. You can set up as many machines as needed, or have an auto-scaling pool. Each machine may run one or several worker processes. Finally, the workers themselves should describe themselves to the master, this enables you to distribute jobs based on criteria such as operating system, available software, available resources, project authorizations.

The service and website are implemented with Flask, please refer to Flask documentation on [deployment](https://flask.palletsprojects.com/en/1.1.x/deploying/). Additionally, you should set up SSL and ensure you use secure protocols, HTTPS and WSS.
