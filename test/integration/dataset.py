import datetime

from bhamon_orchestra_model.database.database_client import DatabaseClient


def import_dataset(database_client: DatabaseClient, dataset: dict) -> None:
	all_tables = []
	all_tables += [ "user", "user_authentication" ]
	all_tables += [ "project", "job", "run", "schedule", "worker" ]

	for table in all_tables:
		if len(dataset[table]) > 0:
			database_client.insert_many(table, dataset[table])


def export_dataset(database_client: DatabaseClient) -> dict:
	all_tables = []
	all_tables += [ "user", "user_authentication" ]
	all_tables += [ "project", "job", "run", "schedule", "worker" ]

	dataset = {}
	for table in all_tables:
		dataset[table] = database_client.find_many(table, {})

	return dataset


simple_dataset = {

	"user": [
		{
			"identifier": "my_user",
			"display_name": "My User",
			"roles": [],
			"is_enabled": True,
			"creation_date": datetime.datetime(2020, 1, 1, 0, 0, 0, tzinfo = datetime.timezone.utc),
			"update_date": datetime.datetime(2020, 1, 1, 0, 0, 0, tzinfo = datetime.timezone.utc),
		},
	],

	"user_authentication" : [],

	"project": [
		{
			"identifier": "my_project",
			"display_name": "My Project",
			"services": {},
			"creation_date": datetime.datetime(2020, 1, 1, 0, 0, 0, tzinfo = datetime.timezone.utc),
			"update_date": datetime.datetime(2020, 1, 1, 0, 0, 0, tzinfo = datetime.timezone.utc),
		},
	],

	"job": [
		{
			"project": "my_project",
			"identifier": "my_job",
			"display_name": "My Job",
			"description": "My job description",
			"definition": {},
			"parameters": [],
			"properties": {},
			"is_enabled": True,
			"creation_date": datetime.datetime(2020, 1, 1, 0, 0, 0, tzinfo = datetime.timezone.utc),
			"update_date": datetime.datetime(2020, 1, 1, 0, 0, 0, tzinfo = datetime.timezone.utc),
		},
	],

	"run": [
		{
			"identifier": "my_run",
			"project": "my_project",
			"job": "my_job",
			"parameters": {},
			"source": { "type": "user", "identifier": "my_user" },
			"worker": "my_worker",
			"status": "succeeded",
			"start_date": datetime.datetime(2020, 1, 1, 0, 0, 0, tzinfo = datetime.timezone.utc),
			"completion_date": datetime.datetime(2020, 1, 1, 0, 0, 0, tzinfo = datetime.timezone.utc),
			"results": {},
			"should_cancel": False,
			"should_abort": False,
			"creation_date": datetime.datetime(2020, 1, 1, 0, 0, 0, tzinfo = datetime.timezone.utc),
			"update_date": datetime.datetime(2020, 1, 1, 0, 0, 0, tzinfo = datetime.timezone.utc),
		},
	],

	"schedule": [
		{
			"project": "my_project",
			"identifier": "my_schedule",
			"display_name": "My Schedule",
			"job": "my_job",
			"parameters": {},
			"expression": "* * * * *",
			"is_enabled": False,
			"last_run": None,
			"creation_date": datetime.datetime(2020, 1, 1, 0, 0, 0, tzinfo = datetime.timezone.utc),
			"update_date": datetime.datetime(2020, 1, 1, 0, 0, 0, tzinfo = datetime.timezone.utc),
		},
	],

	"worker": [
		{
			"identifier": "worker",
			"owner": "my_user",
			"version": "0.0.0",
			"display_name": "My Worker",
			"properties": {},
			"is_enabled": False,
			"is_active": False,
			"should_disconnect": False,
			"creation_date": datetime.datetime(2020, 1, 1, 0, 0, 0, tzinfo = datetime.timezone.utc),
			"update_date": datetime.datetime(2020, 1, 1, 0, 0, 0, tzinfo = datetime.timezone.utc),
		},
	],

}


simple_dataset_3_0 = {

	"user": [
		{
			"identifier": "my_user",
			"display_name": "My User",
			"roles": [],
			"is_enabled": True,
			"creation_date": "2020-01-01T00:00:00Z",
			"update_date": "2020-01-01T00:00:00Z",
		},
	],

	"user_authentication" : [],

	"project": [
		{
			"identifier": "my_project",
			"display_name": "My Project",
			"services": {},
			"creation_date": "2020-01-01T00:00:00Z",
			"update_date": "2020-01-01T00:00:00Z",
		},
	],

	"job": [
		{
			"project": "my_project",
			"identifier": "my_job",
			"display_name": "My Job",
			"description": "My job description",
			"definition": {},
			"parameters": [],
			"properties": {},
			"is_enabled": True,
			"creation_date": "2020-01-01T00:00:00Z",
			"update_date": "2020-01-01T00:00:00Z",
		},
	],

	"run": [
		{
			"identifier": "my_run",
			"project": "my_project",
			"job": "my_job",
			"parameters": {},
			"source": { "type": "user", "identifier": "my_user" },
			"worker": "my_worker",
			"status": "succeeded",
			"start_date": "2020-01-01T00:00:00Z",
			"completion_date": "2020-01-01T00:00:00Z",
			"results": {},
			"should_cancel": False,
			"should_abort": False,
			"creation_date": "2020-01-01T00:00:00Z",
			"update_date": "2020-01-01T00:00:00Z",
		},
	],

	"schedule": [
		{
			"project": "my_project",
			"identifier": "my_schedule",
			"display_name": "My Schedule",
			"job": "my_job",
			"parameters": {},
			"expression": "* * * * *",
			"is_enabled": False,
			"last_run": None,
			"creation_date": "2020-01-01T00:00:00Z",
			"update_date": "2020-01-01T00:00:00Z",
		},
	],

	"worker": [
		{
			"identifier": "worker",
			"owner": "my_user",
			"version": "0.0.0",
			"display_name": "My Worker",
			"properties": {},
			"is_enabled": False,
			"is_active": False,
			"should_disconnect": False,
			"creation_date": "2020-01-01T00:00:00Z",
			"update_date": "2020-01-01T00:00:00Z",
		},
	],

}
