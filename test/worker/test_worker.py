""" Unit tests for Worker """

import asyncio
import logging
from unittest.mock import Mock

import pytest

from bhamon_orchestra_worker.master_client import MasterClient
from bhamon_orchestra_worker.worker import Worker
from bhamon_orchestra_worker.worker_storage import WorkerStorage

from ..mock_extensions import AsyncMock, CancellableAsyncMock, MockException


@pytest.mark.asyncio
async def test_run(caplog):
	""" Test run with dummy dependencies """

	worker_storage_mock = Mock(spec = WorkerStorage)
	master_client_mock = Mock(spec = MasterClient, run = AsyncMock())

	worker_storage_mock.list_runs.return_value = []

	worker_instance = Worker(
		storage = worker_storage_mock,
		master_client = master_client_mock,
		display_name = None,
		properties = None,
		executor_script = None,
	)

	await worker_instance.run()

	assert sum(1 for record in caplog.records if record.levelno == logging.WARNING) == 0
	assert sum(1 for record in caplog.records if record.levelno == logging.ERROR) == 0
	assert sum(1 for record in caplog.records if record.levelno == logging.CRITICAL) == 0


@pytest.mark.asyncio
async def test_run_cancel(caplog):
	""" Test run getting cancelled """

	worker_storage_mock = Mock(spec = WorkerStorage)
	master_client_mock = Mock(spec = MasterClient, run = CancellableAsyncMock())

	worker_storage_mock.list_runs.return_value = []

	worker_instance = Worker(
		storage = worker_storage_mock,
		master_client = master_client_mock,
		display_name = None,
		properties = None,
		executor_script = None,
	)

	run_future = asyncio.ensure_future(worker_instance.run())

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

	worker_storage_mock = Mock(spec = WorkerStorage)
	master_client_mock = Mock(spec = MasterClient, run = AsyncMock())

	worker_storage_mock.list_runs.return_value = []

	worker_instance = Worker(
		storage = worker_storage_mock,
		master_client = master_client_mock,
		display_name = None,
		properties = None,
		executor_script = None,
	)

	exception = MockException()
	master_client_mock.run.side_effect = exception

	await worker_instance.run()

	assert sum(1 for record in caplog.records if record.levelno == logging.WARNING) == 0
	assert sum(1 for record in caplog.records if record.levelno == logging.ERROR) == 1
	assert sum(1 for record in caplog.records if record.levelno == logging.CRITICAL) == 0

	error_record = next(record for record in caplog.records if record.levelno == logging.ERROR)

	assert error_record.msg == "Unhandled exception from master client"
	assert error_record.exc_info[1] == exception
