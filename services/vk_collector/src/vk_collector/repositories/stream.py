from news_common.clients.redis_bus import StreamBus
from news_common.models import RawPost


class RawPostStreamRepository:
    def __init__(self, bus: StreamBus, stream: str) -> None:
        self._bus = bus
        self._stream = stream

    async def publish(self, post: RawPost) -> str:
        return await self._bus.publish(self._stream, post.model_dump(mode="json"))

    async def publish_many(self, posts: list[RawPost]) -> int:
        for post in posts:
            await self.publish(post)
        return len(posts)
