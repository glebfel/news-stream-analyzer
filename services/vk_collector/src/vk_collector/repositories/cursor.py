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
        try:
            return int(post_id.rsplit("_", 1)[-1])
        except ValueError:
            return 0
