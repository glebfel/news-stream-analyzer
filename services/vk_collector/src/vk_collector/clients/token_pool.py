import asyncio


class TokenPool:
    """Round-robin pool of VK service tokens.

    Each token has its own daily quota (5000 calls/day for service tokens),
    so rotating between N tokens multiplies the effective ceiling by N.
    """

    def __init__(self, tokens: list[str]) -> None:
        if not tokens:
            raise ValueError("TokenPool requires at least one token")
        self._tokens = tokens
        self._idx = 0
        self._lock = asyncio.Lock()

    async def next(self) -> str:
        async with self._lock:
            token = self._tokens[self._idx]
            self._idx = (self._idx + 1) % len(self._tokens)
            return token

    @property
    def size(self) -> int:
        return len(self._tokens)
