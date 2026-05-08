import asyncio

from news_common import get_logger

from telegram_collector.clients.telegram_api import TelegramApiClient
from telegram_collector.repositories.stream import RawPostStreamRepository
from telegram_collector.services.mock_generator import MockPostGenerator

log = get_logger("telegram_collector.service")


class TelegramCollectorService:
    def __init__(
        self,
        stream_repo: RawPostStreamRepository,
        channels: list[str],
        poll_interval: int,
    ) -> None:
        self._repo = stream_repo
        self._channels = channels
        self._poll_interval = poll_interval

    async def run_real(self, api_id: int, api_hash: str, session_name: str) -> None:
        client = TelegramApiClient(api_id, api_hash, session_name)
        log.info("tg_started", channels=self._channels)
        await client.start(self._channels, self._on_message)

    async def run_mock(self) -> None:
        log.info("tg_mock_mode")
        gen = MockPostGenerator()
        while True:
            batch = gen.next_batch()
            await self._repo.publish_many(batch)
            log.info("tg_mock_batch", size=len(batch))
            await asyncio.sleep(self._poll_interval)

    async def _on_message(self, post) -> None:
        await self._repo.publish(post)
        log.info("tg_msg", channel=post.channel, post_id=post.id)
