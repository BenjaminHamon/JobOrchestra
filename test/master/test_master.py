""" Unit tests for Master """

import asyncio
import logging
from unittest.mock import Mock

import pytest

from bhamon_orchestra_master.job_scheduler import JobScheduler
from bhamon_orchestra_master.master import Master
from bhamon_orchestra_master.supervisor import Supervisor

from ..mock_extensions import AsyncMock, CancellableAsyncMock, MockException


@pytest.mark.asyncio
async def test_run(caplog):
	""" Test run with dummy dependencies """

	job_scheduler_mock = Mock(spec = JobScheduler, run = AsyncMock())
	supervisor_mock = Mock(spec = Supervisor, run_server = AsyncMock())

	master_instance = Master(
		database_client_factory = None,
		project_provider = None,
		job_provider = None,
		schedule_provider = None,
		worker_provider = None,
		job_scheduler = job_scheduler_mock,
		supervisor = supervisor_mock)

	await master_instance.run()

	assert sum(1 for record in caplog.records if record.levelno == logging.WARNING) == 0
	assert sum(1 for record in caplog.records if record.levelno == logging.ERROR) == 0
	assert sum(1 for record in caplog.records if record.levelno == logging.CRITICAL) == 0


@pytest.mark.asyncio
async def test_run_cancel(caplog):
	""" Test run getting cancelled """

	job_scheduler_mock = Mock(spec = JobScheduler, run = CancellableAsyncMock())
	supervisor_mock = Mock(spec = Supervisor, run_server = CancellableAsyncMock())

	master_instance = Master(
		database_client_factory = None,
		project_provider = None,
		job_provider = None,
		schedule_provider = None,
		worker_provider = None,
		job_scheduler = job_scheduler_mock,
		supervisor = supervisor_mock)

	run_future = asyncio.ensure_future(master_instance.run())

	await asyncio.sleep(0.1)

	run_future.cancel()

	with pytest.raises(asyncio.CancelledError):
		await run_future

	assert sum(1 for record in caplog.records if record.levelno == logging.WARNING) == 0
	assert sum(1 for record in caplog.records if record.levelno == logging.ERROR) == 0
	assert sum(1 for record in caplog.records if record.levelno == logging.CRITICAL) == 0


@pytest.mark.asyncio
async def test_run_exception(caplog):
	""" Test run with a dependency raising an exception """

	job_scheduler_mock = Mock(spec = JobScheduler, run = AsyncMock())
	supervisor_mock = Mock(spec = Supervisor, run_server = AsyncMock())

	master_instance = Master(
		database_client_factory = None,
		project_provider = None,
		job_provider = None,
		schedule_provider = None,
		worker_provider = None,
		job_scheduler = job_scheduler_mock,
		supervisor = supervisor_mock)

	exception = MockException()
	job_scheduler_mock.run.side_effect = exception

	await master_instance.run()

	assert sum(1 for record in caplog.records if record.levelno == logging.WARNING) == 0
	assert sum(1 for record in caplog.records if record.levelno == logging.ERROR) == 1
	assert sum(1 for record in caplog.records if record.levelno == logging.CRITICAL) == 0

	error_record = next(record for record in caplog.records if record.levelno == logging.ERROR)

	assert error_record.msg == "Unhandled exception from job scheduler"
	assert error_record.exc_info[1] == exception
