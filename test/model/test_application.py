""" Unit tests for Application """

import asyncio

import pytest

from bhamon_orchestra_model.application import AsyncioApplication

from ..mock_extensions import MockException


def test_run_success():
	""" Test run with a main function which succeeds """

	class DummyMain:

		def __init__(self) -> None:
			self.future = None

		async def run(self) -> None: # pylint: disable = no-self-use
			await asyncio.sleep(0.1)

		async def run_as_future(self) -> None:
			self.future = asyncio.ensure_future(self.run())
			await self.future

	main_instance = DummyMain()
	application_instance = AsyncioApplication(None, None)

	application_instance.run(main_instance.run_as_future())

	assert main_instance.future is not None
	assert main_instance.future.done()
	assert not main_instance.future.cancelled()
	assert main_instance.future.exception() is None


def test_run_cancellation():
	""" Test run with a main function which gets cancelled """

	class DummyMain:

		def __init__(self) -> None:
			self.future = None

		async def run(self) -> None: # pylint: disable = no-self-use
			await asyncio.sleep(1)

		async def run_as_future(self) -> None:
			self.future = asyncio.ensure_future(self.run())
			await asyncio.sleep(0.1)
			self.future.cancel()
			await self.future

	main_instance = DummyMain()
	application_instance = AsyncioApplication(None, None)

	application_instance.run(main_instance.run_as_future())

	assert main_instance.future is not None
	assert main_instance.future.done()
	assert main_instance.future.cancelled()

	with pytest.raises(asyncio.CancelledError):
		main_instance.future.exception()


def test_run_exception():
	""" Test run with a main function which raises an exception """

	class DummyMain:

		def __init__(self) -> None:
			self.future = None

		async def run(self) -> None: # pylint: disable = no-self-use
			raise MockException()

		async def run_as_future(self) -> None:
			self.future = asyncio.ensure_future(self.run())
			await self.future

	main_instance = DummyMain()
	application_instance = AsyncioApplication(None, None)

	with pytest.raises(MockException):
		application_instance.run(main_instance.run_as_future())

	assert main_instance.future is not None
	assert main_instance.future.done()
	assert not main_instance.future.cancelled()
	assert main_instance.future.exception() is not None
	assert isinstance(main_instance.future.exception(), MockException)
