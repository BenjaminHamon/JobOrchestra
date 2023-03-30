import functools
from typing import Callable

from bhamon_orchestra_master.job_scheduler import JobScheduler
from bhamon_orchestra_master.master import Master
from bhamon_orchestra_master.protocol import WebSocketServerProtocol
from bhamon_orchestra_master.supervisor import Supervisor
from bhamon_orchestra_master.worker_selector import WorkerSelector
from bhamon_orchestra_model.database.database_client import DatabaseClient
from bhamon_orchestra_model.database.file_data_storage import FileDataStorage
from bhamon_orchestra_model.date_time_provider import DateTimeProvider
from bhamon_orchestra_model.job_provider import JobProvider
from bhamon_orchestra_model.project_provider import ProjectProvider
from bhamon_orchestra_model.run_provider import RunProvider
from bhamon_orchestra_model.schedule_provider import ScheduleProvider
from bhamon_orchestra_model.users.authentication_provider import AuthenticationProvider
from bhamon_orchestra_model.users.authorization_provider import AuthorizationProvider
from bhamon_orchestra_model.users.user_provider import UserProvider
from bhamon_orchestra_model.worker_provider import WorkerProvider


def create_application( # pylint: disable = too-many-locals
		database_client_factory: Callable[[], DatabaseClient], file_storage_path: str):

	data_storage = FileDataStorage(file_storage_path)
	date_time_provider = DateTimeProvider()

	authentication_provider = AuthenticationProvider(date_time_provider)
	authorization_provider = AuthorizationProvider()
	job_provider = JobProvider(date_time_provider)
	project_provider = ProjectProvider(date_time_provider)
	run_provider = RunProvider(data_storage, date_time_provider)
	schedule_provider = ScheduleProvider(date_time_provider)
	user_provider = UserProvider(date_time_provider)
	worker_provider = WorkerProvider(date_time_provider)

	protocol_factory = functools.partial(
		WebSocketServerProtocol,
		database_client_factory = database_client_factory,
		user_provider = user_provider,
		authentication_provider = authentication_provider,
		authorization_provider = authorization_provider,
	)

	supervisor = Supervisor(
		protocol_factory = protocol_factory,
		database_client_factory = database_client_factory,
		worker_provider = worker_provider,
		run_provider = run_provider,
	)

	worker_selector = WorkerSelector(
		database_client_factory = database_client_factory,
		worker_provider = worker_provider,
		supervisor = supervisor,
	)

	job_scheduler = JobScheduler(
		database_client_factory = database_client_factory,
		job_provider = job_provider,
		run_provider = run_provider,
		schedule_provider = schedule_provider,
		supervisor = supervisor,
		worker_selector = worker_selector,
		date_time_provider = date_time_provider,
	)

	master = Master(
		database_client_factory = database_client_factory,
		project_provider = project_provider,
		job_provider = job_provider,
		schedule_provider = schedule_provider,
		worker_provider = worker_provider,
		job_scheduler = job_scheduler,
		supervisor = supervisor,
	)

	return master
