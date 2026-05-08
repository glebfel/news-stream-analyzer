import asyncio
import time


class AsyncRateLimiter:
    """Simple token-bucket-like limiter: at most `rate` calls per second."""

    def __init__(self, rate: float) -> None:
        self._min_interval = 1.0 / rate
        self._last_call: float = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            wait = self._min_interval - (now - self._last_call)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_call = time.monotonic()
