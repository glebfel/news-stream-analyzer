import asyncio

from news_common import get_logger

from vk_collector.clients.exceptions import VKAuthError, VKError
from vk_collector.clients.token_pool import TokenPool
from vk_collector.clients.vk_api import VKApiClient
from vk_collector.repositories.stream import RawPostStreamRepository
from vk_collector.services.mock_generator import MockPostGenerator

log = get_logger("vk_collector.service")


class VKCollectorService:
    def __init__(
        self,
        stream_repo: RawPostStreamRepository,
        communities: list[str],
        poll_interval: int,
    ) -> None:
        self._repo = stream_repo
        self._communities = communities
        self._poll_interval = poll_interval

    async def run_real(self, tokens: list[str]) -> None:
        pool = TokenPool(tokens)
        log.info("vk_real_mode", tokens=pool.size, communities=len(self._communities))
        seen: set[str] = set()
        async with VKApiClient(pool) as client:
            while True:
                try:
                    batches = await client.wall_get_many(self._communities, count=50)
                except VKAuthError as exc:
                    log.error("vk_auth_failed", error=str(exc))
                    raise
                except VKError as exc:
                    log.warning("vk_cycle_failed", error=str(exc))
                    await asyncio.sleep(self._poll_interval)
                    continue
                except Exception as exc:
                    log.error("vk_cycle_unexpected", error=str(exc))
                    await asyncio.sleep(self._poll_interval)
                    continue

                for community, posts in batches.items():
                    fresh = [p for p in posts if p.id not in seen]
                    seen.update(p.id for p in fresh)
                    await self._repo.publish_many(fresh)
                    log.info("vk_batch", community=community, fetched=len(posts), new=len(fresh))
                await asyncio.sleep(self._poll_interval)

    async def run_mock(self) -> None:
        log.info("vk_mock_mode")
        gen = MockPostGenerator()
        while True:
            batch = gen.next_batch()
            await self._repo.publish_many(batch)
            log.info("vk_mock_batch", size=len(batch))
            await asyncio.sleep(self._poll_interval)
