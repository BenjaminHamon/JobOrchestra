import asyncio
import logging
import platform
import signal
import sys
from typing import Any


logger = logging.getLogger("Application")


EXIT_SUCCESS = 0 # pylint: disable = invalid-name
EXIT_FAILURE = 1 # pylint: disable = invalid-name


class AsyncioApplication:
	""" Main class for an application running with asyncio """


	def __init__(self, title, version) -> None:
		self.title = title
		self.version = version

		self.should_shutdown = False
		self.shutdown_timeout_seconds = 30


	def run_as_standalone(self, future: Any) -> None:
		""" Run as a standalone application """

		if platform.system() == "Windows":
			signal.signal(signal.SIGBREAK, lambda signal_number, frame: self.shutdown()) # pylint: disable = no-member
		signal.signal(signal.SIGINT, lambda signal_number, frame: self.shutdown())
		signal.signal(signal.SIGTERM, lambda signal_number, frame: self.shutdown())

		if platform.system() == "Windows":
			asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy()) # pylint: disable = no-member

		exit_code = EXIT_SUCCESS

		logger.info("%s %s", self.title, self.version)

		try:
			self.run(future)
		except SystemExit as exception:
			exit_code = exception.code
			logger.info("SystemExit", exc_info = True)
		except: # pylint: disable = bare-except
			exit_code = EXIT_FAILURE
			logger.error("Unhandled exception", exc_info = True)

		logger.info("Exit with code %s", exit_code)

		sys.exit(exit_code)


	def run(self, main: Any) -> None:
		""" Run synchronously """

		asyncio.run(self.run_async(main))


	async def run_async(self, main: Any) -> None:
		""" Run asynchronously """

		main_future = asyncio.ensure_future(main)

		try:
			while not self.should_shutdown and not main_future.done():
				await asyncio.sleep(1)

		finally:
			if not main_future.done():
				main_future.cancel()

			try:
				await asyncio.wait_for(main_future, timeout = self.shutdown_timeout_seconds)
			except asyncio.CancelledError:
				pass

			if not main_future.done():
				raise RuntimeError("Main future did not complete")


	def shutdown(self) -> None:
		""" Request the application to shutdown """

		self.should_shutdown = True
