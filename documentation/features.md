# Features

This page lists features currently available in Job Orchestra.


## General

* Architecture with several separated applications: website, service, master, worker.
* Implementation can be modified and extended by customizing dependency initialization and injection.
* Master and workers communicate over WebSocket.
* Support for MongoDB and SQL databases.


## Data organization

* Projects, jobs and schedules are configured during the master startup.
* Jobs, schedules and runs are regrouped under projects.
* Jobs, workers and users can be individually disabled.
* Runs can save arbitrary results from their execution, to be displayed in the website or used in database queries.
* Workers save data locally until the runs and data synchronization with the master complete.
* Run data can be transformed on retrieval by the service to update and enrich it.
* Run data can be downloaded as an archive.
* All data is stored in the database, except for log files which are stored directly on the file system.


## Execution

* Pipeline jobs schedule other jobs based on dependency rules.
* Job commands are constructed using Python string formatting and data available from the worker environment and the run current results.
* Runs can be distributed selectively to workers from code by matching properties between jobs and workers.
* Workers execute runs independently from the master after receiving the initial request.
* Workers continue executing active runs when disconnected from the master, with recovery on reconnection.
* Run data is transferred from the workers to the master continuously.
* Schedules are based on cron expressions and check for a single concurrent run.


## Security

* Users are created at runtime and can be assigned with roles which provide authorizations.
* Users login with a password then everything use tokens.
* User session tokens expire after a week, with their expiration refreshed once a day on website activity.
* Web requests are authenticated with tokens, and authorized based on the user owning the token.
* Workers register automatically with the master by authenticating with a user token.
* Passwords are stored hashed, with salt, using PBKDF2 with SHA-256 and a million iterations.
* Tokens are generated, with a secure random, as hexadecimal strings of 32 bytes and hashed with SHA-256.


## Website

* Website can be customized by overriding Jinja page templates and static files.
* Status for projects using revision control.
* Run log view for updates continuously until completion.
* Visualization for pipelines.
* Website pages are very lightweight (and barebone).
* Pagination, filtering and sort.
* Minimal JavaScript and not required.
