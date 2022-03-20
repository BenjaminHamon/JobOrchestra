""" Unit tests for ProcessWatcher """

import asyncio
import platform
import signal
import time

import pytest

from bhamon_orchestra_worker.process_exception import ProcessException
from bhamon_orchestra_worker.process_watcher import ProcessWatcher


@pytest.fixture
def event_loop():
	if platform.system() == "Windows":
		asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy()) # pylint: disable = no-member

	loop = asyncio.get_event_loop_policy().new_event_loop()
	yield loop
	loop.close()


async def test_run_success():
	process_watcher_instance = ProcessWatcher()

	await process_watcher_instance.run("context", [ "python", "-c", "pass" ])

	assert process_watcher_instance.process is not None
	assert process_watcher_instance.process.returncode == 0
	assert not process_watcher_instance.is_running()


async def test_run_failure():
	process_watcher_instance = ProcessWatcher()

	with pytest.raises(ProcessException) as exception:
		await process_watcher_instance.run("context", [ "python", "-c", "raise RuntimeError" ])
		assert exception.exit_code == 1

	assert process_watcher_instance.process is not None
	assert process_watcher_instance.process.returncode == 1
	assert not process_watcher_instance.is_running()


async def test_termination():
	termination_exit_code = - signal.SIGTERM
	if platform.system() == "Windows":
		termination_exit_code = 0xC000013A # STATUS_CONTROL_C_EXIT

	process_watcher_instance = ProcessWatcher()

	await process_watcher_instance.start("context", [ "python", "-c", "import time; time.sleep(10)" ])

	assert process_watcher_instance.process is not None
	assert process_watcher_instance.process.returncode is None
	assert process_watcher_instance.is_running()

	time.sleep(0.1)

	await process_watcher_instance.terminate("Interrupt")

	assert process_watcher_instance.process is not None
	assert process_watcher_instance.process.returncode == termination_exit_code
	assert not process_watcher_instance.is_running()


async def test_output():

	output_lines = []

	process_watcher_instance = ProcessWatcher()
	process_watcher_instance.output_handler = output_lines.append

	await process_watcher_instance.run("context", [ "python", "-c", "print('hello')" ])

	assert output_lines == [ "hello" ]


async def test_output_unicode():

	output_lines = []

	process_watcher_instance = ProcessWatcher()
	process_watcher_instance.output_handler = output_lines.append

	await process_watcher_instance.run("context", [ "python", "-c", "print('… é ² √ 👍')" ])

	assert output_lines == [ "… é ² √ 👍" ]
