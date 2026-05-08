from collections.abc import AsyncIterator
from typing import Any

from news_common.clients.redis_bus import StreamBus
from news_common.models import NormalizedPost


class StreamRepository:
    def __init__(self, bus: StreamBus, group: str, consumer: str, clean_stream: str) -> None:
        self._bus = bus
        self._group = group
        self._consumer = consumer
        self._clean_stream = clean_stream

    async def consume_raw(self, stream: str) -> AsyncIterator[tuple[str, dict[str, Any]]]:
        async for msg_id, payload in self._bus.consume(
            stream, self._group, self._consumer, count=32, block_ms=2000
        ):
            yield msg_id, payload

    async def publish_clean(self, post: NormalizedPost) -> str:
        return await self._bus.publish(self._clean_stream, post.model_dump(mode="json"))
