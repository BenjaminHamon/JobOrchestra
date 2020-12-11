import asyncio
from unittest.mock import MagicMock


class MockException(Exception):
	pass


# AsyncMock is new in Python 3.8
class AsyncMock(MagicMock):
	async def __call__(self, *args, **kwargs): # pylint: disable = invalid-overridden-method, useless-super-delegation
		return super().__call__(*args, **kwargs)


class CancellableAsyncMock(AsyncMock): # pylint: disable = too-many-ancestors
	async def __call__(self, *args, **kwargs):
		await asyncio.sleep(1)
		return await super().__call__(*args, **kwargs)
