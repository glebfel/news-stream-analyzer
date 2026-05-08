"""Persistent per-community cursor for the VK collector.

After a restart the collector resumes from the last seen post id, instead of
re-publishing the most recent N posts that have already gone through the
pipeline.
"""

from redis.asyncio import Redis

KEY_PREFIX = "vk:last_seen:"


class LastSeenCursor:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def get(self, community: str) -> int:
        raw = await self._redis.get(f"{KEY_PREFIX}{community}")
        return int(raw) if raw else 0

    async def set(self, community: str, post_id: int) -> None:
        await self._redis.set(f"{KEY_PREFIX}{community}", str(post_id))

    @staticmethod
    def numeric_id(post_id: str) -> int:
        """Extract the numeric VK post id from our `vk_<domain>_<num>` format."""
        try:
            return int(post_id.rsplit("_", 1)[-1])
        except ValueError:
            return 0
