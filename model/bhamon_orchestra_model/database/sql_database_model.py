from sqlalchemy.schema import MetaData, Table, Column
from sqlalchemy.schema import PrimaryKeyConstraint, ForeignKeyConstraint
from sqlalchemy.types import Boolean, String, JSON


metadata = MetaData()

project = Table("project", metadata,
	Column("identifier", String, nullable = False),
	Column("display_name", String, nullable = False),
	Column("services", JSON, nullable = False),
	Column("creation_date", String, nullable = False),
	Column("update_date", String, nullable = False),
	PrimaryKeyConstraint("identifier"),
)

job = Table("job", metadata,
	Column("project", String, nullable = False),
	Column("identifier", String, nullable = False),
	Column("display_name", String, nullable = False),
	Column("description", String, nullable = False),
	Column("steps", JSON, nullable = False),
	Column("parameters", JSON, nullable = False),
	Column("properties", JSON, nullable = False),
	Column("is_enabled", Boolean, nullable = False),
	Column("creation_date", String, nullable = False),
	Column("update_date", String, nullable = False),
	PrimaryKeyConstraint("project", "identifier"),
	ForeignKeyConstraint([ "project" ], [ "project.identifier" ]),
)

run = Table("run", metadata,
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
	# No ForeignKeyConstraint on job, since it can be deleted
	# No ForeignKeyConstraint on worker, since it can be deleted
)

schedule = Table("schedule", metadata,
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

user = Table("user", metadata,
	Column("identifier", String, nullable = False),
	Column("display_name", String, nullable = False),
	Column("roles", JSON, nullable = False),
	Column("is_enabled", Boolean, nullable = False),
	Column("creation_date", String, nullable = False),
	Column("update_date", String, nullable = False),
	PrimaryKeyConstraint("identifier"),
)

user_authentication = Table("user_authentication", metadata,
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

worker = Table("worker", metadata,
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
