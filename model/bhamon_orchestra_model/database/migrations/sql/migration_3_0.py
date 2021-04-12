import logging

from alembic.operations import Operations
from sqlalchemy.schema import Column
from sqlalchemy.schema import PrimaryKeyConstraint, ForeignKeyConstraint
from sqlalchemy.types import Boolean, String, JSON


logger = logging.getLogger("SqlMigration")

version = "3.0+427b2ed357"
date = "2021-03-13T10:26:24Z"


def upgrade(operations: Operations, simulate: bool = False) -> None:
	logger.info("Creating table 'project'")

	if not simulate:
		operations.create_table("project",
			Column("identifier", String, nullable = False),
			Column("display_name", String, nullable = False),
			Column("services", JSON, nullable = False),
			Column("creation_date", String, nullable = False),
			Column("update_date", String, nullable = False),
			PrimaryKeyConstraint("identifier"),
		)

	logger.info("Creating table 'job'")

	if not simulate:
		operations.create_table("job",
			Column("project", String, nullable = False),
			Column("identifier", String, nullable = False),
			Column("display_name", String, nullable = False),
			Column("description", String, nullable = False),
			Column("definition", JSON, nullable = False),
			Column("parameters", JSON, nullable = False),
			Column("properties", JSON, nullable = False),
			Column("is_enabled", Boolean, nullable = False),
			Column("creation_date", String, nullable = False),
			Column("update_date", String, nullable = False),
			PrimaryKeyConstraint("project", "identifier"),
			ForeignKeyConstraint([ "project" ], [ "project.identifier" ]),
		)

	logger.info("Creating table 'run'")

	if not simulate:
		operations.create_table("run",
			Column("project", String, nullable = False),
			Column("identifier", String, nullable = False),
			Column("job", String, nullable = False),
			Column("parameters", JSON, nullable = False),
			Column("source", JSON, nullable = False),
			Column("worker", String, nullable = True),
			Column("status", String, nullable = False),
			Column("start_date", String, nullable = True),
			Column("completion_date", String, nullable = True),
			Column("results", JSON, nullable = True),
			Column("should_cancel", Boolean, nullable = False),
			Column("should_abort", Boolean, nullable = False),
			Column("creation_date", String, nullable = False),
			Column("update_date", String, nullable = False),
			PrimaryKeyConstraint("project", "identifier"),
			ForeignKeyConstraint([ "project" ], [ "project.identifier" ]),
		)

	logger.info("Creating table 'schedule'")

	if not simulate:
		operations.create_table("schedule",
			Column("project", String, nullable = False),
			Column("identifier", String, nullable = False),
			Column("display_name", String, nullable = False),
			Column("job", String, nullable = False),
			Column("parameters", JSON, nullable = False),
			Column("expression", String, nullable = False),
			Column("is_enabled", Boolean, nullable = False),
			Column("last_run", String, nullable = True),
			Column("creation_date", String, nullable = False),
			Column("update_date", String, nullable = False),
			PrimaryKeyConstraint("project", "identifier"),
			ForeignKeyConstraint([ "project" ], [ "project.identifier" ]),
			ForeignKeyConstraint([ "project", "job" ], [ "job.project", "job.identifier" ]),
			ForeignKeyConstraint([ "project", "last_run" ], [ "run.project", "run.identifier" ]),
		)

	logger.info("Creating table 'user'")

	if not simulate:
		operations.create_table("user",
			Column("identifier", String, nullable = False),
			Column("display_name", String, nullable = False),
			Column("roles", JSON, nullable = False),
			Column("is_enabled", Boolean, nullable = False),
			Column("creation_date", String, nullable = False),
			Column("update_date", String, nullable = False),
			PrimaryKeyConstraint("identifier"),
		)

	logger.info("Creating table 'user_authentication'")

	if not simulate:
		operations.create_table("user_authentication",
			Column("identifier", String, nullable = False),
			Column("user", String, nullable = False),
			Column("type", String, nullable = False),
			Column("description", String, nullable = True),
			Column("hash_function", String, nullable = True),
			Column("hash_function_parameters", JSON, nullable = True),
			Column("hash_function_salt", String, nullable = True),
			Column("secret", String, nullable = True),
			Column("expiration_date", String, nullable = True),
			Column("creation_date", String, nullable = False),
			Column("update_date", String, nullable = False),
			PrimaryKeyConstraint("user", "identifier"),
			ForeignKeyConstraint([ "user" ], [ "user.identifier" ]),
		)

	logger.info("Creating table 'worker'")

	if not simulate:
		operations.create_table("worker",
			Column("identifier", String, nullable = False),
			Column("owner", String, nullable = False),
			Column("version", String, nullable = False),
			Column("display_name", String, nullable = False),
			Column("properties", JSON, nullable = False),
			Column("is_enabled", Boolean, nullable = False),
			Column("is_active", Boolean, nullable = False),
			Column("should_disconnect", Boolean, nullable = False),
			Column("creation_date", String, nullable = False),
			Column("update_date", String, nullable = False),
			PrimaryKeyConstraint("identifier"),
			ForeignKeyConstraint([ "owner" ], [ "user.identifier" ]),
		)
