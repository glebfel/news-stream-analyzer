"""Persistent Redis-backed cache for Wikidata entity linking results.

Survives nlp-worker restarts and is shared across replicas.
Uses a sentinel value to distinguish 'definitely no match' from 'not yet cached',
since None already means 'no QID returned'.
"""

from typing import Final

from redis.asyncio import Redis

KEY_PREFIX = "wd:"
NO_MATCH_SENTINEL: Final = "__none__"


class WikidataRedisCache:
    def __init__(self, redis_url: str, ttl_seconds: int = 86400 * 30) -> None:
        self._redis: Redis = Redis.from_url(redis_url, decode_responses=True)
        self._ttl = ttl_seconds

    async def get(self, text: str) -> tuple[bool, str | None]:
        """Return (cached?, qid_or_none).

        - (False, None): not in cache, caller should query Wikidata
        - (True, "Q42"): cached hit
        - (True, None): cached miss (Wikidata returned no match for this text)
        """
        val = await self._redis.get(self._key(text))
        if val is None:
            return False, None
        if val == NO_MATCH_SENTINEL:
            return True, None
        return True, val

    async def set(self, text: str, qid: str | None) -> None:
        await self._redis.set(self._key(text), qid or NO_MATCH_SENTINEL, ex=self._ttl)

    async def close(self) -> None:
        await self._redis.aclose()

    @staticmethod
    def _key(text: str) -> str:
        return f"{KEY_PREFIX}{text.lower()}"
