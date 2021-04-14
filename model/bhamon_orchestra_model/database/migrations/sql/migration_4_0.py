import logging

from alembic.operations import Operations
import dateutil.parser
from sqlalchemy.schema import Column, MetaData, Table
from sqlalchemy.types import String

from bhamon_orchestra_model.database.sql_types import UtcDateTime


logger = logging.getLogger("SqlMigration")

version = "4.0"
date = None


def upgrade(operations: Operations, simulate: bool = False) -> None:
	convert_datetimes(operations, "project", "creation_date", nullable = False, simulate = simulate)
	convert_datetimes(operations, "project", "update_date", nullable = False, simulate = simulate)
	convert_datetimes(operations, "job", "creation_date", nullable = False, simulate = simulate)
	convert_datetimes(operations, "job", "update_date", nullable = False, simulate = simulate)
	convert_datetimes(operations, "run", "start_date", nullable = True, simulate = simulate)
	convert_datetimes(operations, "run", "completion_date", nullable = True, simulate = simulate)
	convert_datetimes(operations, "run", "creation_date", nullable = False, simulate = simulate)
	convert_datetimes(operations, "run", "update_date", nullable = False, simulate = simulate)
	convert_datetimes(operations, "schedule", "creation_date", nullable = False, simulate = simulate)
	convert_datetimes(operations, "schedule", "update_date", nullable = False, simulate = simulate)
	convert_datetimes(operations, "user", "creation_date", nullable = False, simulate = simulate)
	convert_datetimes(operations, "user", "update_date", nullable = False, simulate = simulate)
	convert_datetimes(operations, "user_authentication", "expiration_date", nullable = True, simulate = simulate)
	convert_datetimes(operations, "user_authentication", "creation_date", nullable = False, simulate = simulate)
	convert_datetimes(operations, "user_authentication", "update_date", nullable = False, simulate = simulate)
	convert_datetimes(operations, "worker", "creation_date", nullable = False, simulate = simulate)
	convert_datetimes(operations, "worker", "update_date", nullable = False, simulate = simulate)


def convert_datetimes(operations: Operations, table: str, column: str, nullable: bool, simulate: bool = False) -> None:
	logger.info("Converting datetime column '%s.%s'", table, column)

	connection = operations.get_bind()

	table_columns = [
		Column("identifier", String),
		Column(column, String),
		Column(column + "_converting", String),
	]

	if simulate:
		table_columns.remove(table_columns[2])

	table = Table(table, MetaData(), *table_columns)

	if not simulate:
		operations.add_column(table.name, Column(column + "_converting", UtcDateTime, nullable = True))

	select_query = table.select()
	table_rows = connection.execute(select_query).fetchall()

	for row in table_rows:
		if row[column] is not None:
			update_values = { column + "_converting": dateutil.parser.parse(row[column]) }
			update_query = table.update().where(table.c.identifier == row.identifier).values(update_values)

			if not simulate:
				connection.execute(update_query)

	if not simulate:
		operations.drop_column(table.name, column)
		operations.alter_column(table.name, column + "_converting", new_column_name = column, nullable = nullable)
