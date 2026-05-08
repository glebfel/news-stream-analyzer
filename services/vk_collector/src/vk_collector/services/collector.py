import asyncio
import time

from news_common import get_logger
from news_common.metrics import collector_cycle_seconds, posts_collected_total

from vk_collector.clients.exceptions import VKAuthError, VKError
from vk_collector.clients.token_pool import TokenPool
from vk_collector.clients.vk_api import VKApiClient
from vk_collector.repositories.cursor import LastSeenCursor
from vk_collector.repositories.stream import RawPostStreamRepository
from vk_collector.services.mock_generator import MockPostGenerator

log = get_logger("vk_collector.service")


class VKCollectorService:
    def __init__(
        self,
        stream_repo: RawPostStreamRepository,
        communities: list[str],
        poll_interval: int,
        cursor: LastSeenCursor | None = None,
    ) -> None:
        self._repo = stream_repo
        self._communities = communities
        self._poll_interval = poll_interval
        self._cursor = cursor

    async def run_real(self, tokens: list[str]) -> None:
        pool = TokenPool(tokens)
        log.info("vk_real_mode", tokens=pool.size, communities=len(self._communities))
        async with VKApiClient(pool) as client:
            while True:
                t0 = time.perf_counter()
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
                    fresh, max_id = await self._filter_fresh(community, posts)
                    if fresh:
                        await self._repo.publish_many(fresh)
                        posts_collected_total.labels(source="vk").inc(len(fresh))
                        if self._cursor is not None and max_id:
                            await self._cursor.set(community, max_id)
                    log.info("vk_batch", community=community, fetched=len(posts), new=len(fresh))
                collector_cycle_seconds.labels(source="vk").observe(time.perf_counter() - t0)
                await asyncio.sleep(self._poll_interval)

    async def _filter_fresh(self, community: str, posts: list) -> tuple[list, int]:
        if self._cursor is None:
            return list(posts), 0
        last_seen = await self._cursor.get(community)
        fresh: list = []
        max_id = last_seen
        for p in posts:
            num_id = LastSeenCursor.numeric_id(p.id)
            if num_id > last_seen:
                fresh.append(p)
                if num_id > max_id:
                    max_id = num_id
        return fresh, max_id

    async def run_mock(self) -> None:
        log.info("vk_mock_mode")
        gen = MockPostGenerator()
        while True:
            batch = gen.next_batch()
            await self._repo.publish_many(batch)
            posts_collected_total.labels(source="vk").inc(len(batch))
            log.info("vk_mock_batch", size=len(batch))
            await asyncio.sleep(self._poll_interval)
