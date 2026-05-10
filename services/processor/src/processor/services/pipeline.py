import asyncio
import contextlib
import time

from news_common import get_logger
from news_common.metrics import posts_dedup_total, posts_indexed_total
from news_common.models import NormalizedPost, RawPost
from news_common.repositories import PostsRepository

from processor.repositories.stream import StreamRepository
from processor.services.deduper import Deduper
from processor.services.normalizer import Normalizer

log = get_logger("processor.pipeline")


class ProcessorPipeline:
    def __init__(
        self,
        stream_repo: StreamRepository,
        posts_repo: PostsRepository,
        normalizer: Normalizer,
        deduper: Deduper,
        flush_every: int = 20,
        flush_seconds: float = 5.0,
    ) -> None:
        self._stream = stream_repo
        self._posts = posts_repo
        self._normalizer = normalizer
        self._deduper = deduper
        self._flush_every = flush_every
        self._flush_seconds = flush_seconds
        self._buffers: dict[str, list[NormalizedPost]] = {}
        self._last_flush: dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def run(self, raw_streams: list[str]) -> None:
        timer = asyncio.create_task(self._timer_loop(raw_streams))
        try:
            await asyncio.gather(*(self._consume(s) for s in raw_streams))
        finally:
            timer.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await timer
            for s in raw_streams:
                await self._flush(s)

    async def _consume(self, raw_stream: str) -> None:
        self._buffers[raw_stream] = []
        self._last_flush[raw_stream] = time.monotonic()
        async for _, payload in self._stream.consume_raw(raw_stream):
            normalized = self._process_one(payload)
            if normalized is None:
                continue
            await self._stream.publish_clean(normalized)
            async with self._lock:
                self._buffers[raw_stream].append(normalized)
                if len(self._buffers[raw_stream]) >= self._flush_every:
                    await self._flush_locked(raw_stream)

    async def _timer_loop(self, raw_streams: list[str]) -> None:
        # Forces a flush even when the post rate is low (nights, weekends), so
        # `/latest` and the dashboard feed don't lag minutes behind the live pipeline.
        while True:
            await asyncio.sleep(self._flush_seconds)
            async with self._lock:
                for s in raw_streams:
                    if self._buffers.get(s) and (
                        time.monotonic() - self._last_flush.get(s, 0) >= self._flush_seconds
                    ):
                        await self._flush_locked(s)

    async def _flush(self, raw_stream: str) -> None:
        async with self._lock:
            await self._flush_locked(raw_stream)

    async def _flush_locked(self, raw_stream: str) -> None:
        buffer = self._buffers.get(raw_stream) or []
        self._last_flush[raw_stream] = time.monotonic()
        if not buffer:
            return
        snapshot = buffer[:]
        buffer.clear()
        try:
            count = await self._posts.index_many(snapshot)
            posts_indexed_total.inc(count)
            log.info("indexed", count=count, stream=raw_stream)
        except Exception as exc:
            log.error("index_failed", stream=raw_stream, size=len(snapshot), error=str(exc))

    def _process_one(self, payload: dict) -> NormalizedPost | None:
        post = RawPost.model_validate(payload)
        cleaned = self._normalizer.clean(post.text)
        if not cleaned:
            return None
        tokens, lemmas = self._normalizer.tokenize(cleaned)
        if self._deduper.is_duplicate(post.id, lemmas):
            posts_dedup_total.labels(outcome="dup").inc()
            log.info("dup_skip", post_id=post.id)
            return None
        posts_dedup_total.labels(outcome="kept").inc()
        return NormalizedPost(
            id=post.id,
            source=post.source,
            text=post.text,
            text_clean=cleaned,
            tokens=tokens,
            lemmas=lemmas,
            posted_at=post.posted_at,
            simhash=Deduper.simhash_hex(lemmas),
            metadata={
                "channel": post.channel,
                "url": post.url,
                "likes": post.likes,
                "reposts": post.reposts,
                "views": post.views,
            },
        )
