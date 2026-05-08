from collections.abc import AsyncIterator
from typing import Any

import orjson
from redis.asyncio import Redis


class StreamBus:
    def __init__(self, url: str) -> None:
        self.client: Redis = Redis.from_url(url, decode_responses=True)

    async def publish(self, stream: str, payload: dict[str, Any]) -> str:
        return await self.client.xadd(stream, {"data": orjson.dumps(payload).decode()})

    async def ensure_group(self, stream: str, group: str) -> None:
        try:
            await self.client.xgroup_create(stream, group, id="0", mkstream=True)
        except Exception as exc:
            if "BUSYGROUP" not in str(exc):
                raise

    async def consume(
        self,
        stream: str,
        group: str,
        consumer: str,
        block_ms: int = 5000,
        count: int = 16,
    ) -> AsyncIterator[tuple[str, dict[str, Any]]]:
        await self.ensure_group(stream, group)
        while True:
            resp = await self.client.xreadgroup(
                group, consumer, {stream: ">"}, count=count, block=block_ms
            )
            if not resp:
                continue
            for _, messages in resp:
                for msg_id, fields in messages:
                    payload = orjson.loads(fields["data"])
                    yield msg_id, payload
                    await self.client.xack(stream, group, msg_id)

    async def close(self) -> None:
        await self.client.aclose()
