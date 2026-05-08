import asyncio

from news_common import get_logger
from news_common.metrics import posts_dedup_total, posts_indexed_total
from news_common.models import NormalizedPost, RawPost
from news_common.repositories import PostsRepository

from processor.repositories.stream import StreamRepository
from processor.services.deduper import Deduper
from processor.services.normalizer import Normalizer

log = get_logger("processor.pipeline")
FLUSH_BATCH = 20


class ProcessorPipeline:
    def __init__(
        self,
        stream_repo: StreamRepository,
        posts_repo: PostsRepository,
        normalizer: Normalizer,
        deduper: Deduper,
    ) -> None:
        self._stream = stream_repo
        self._posts = posts_repo
        self._normalizer = normalizer
        self._deduper = deduper

    async def run(self, raw_streams: list[str]) -> None:
        await asyncio.gather(*(self._consume(s) for s in raw_streams))

    async def _consume(self, raw_stream: str) -> None:
        buffer: list[NormalizedPost] = []
        async for _, payload in self._stream.consume_raw(raw_stream):
            normalized = self._process_one(payload)
            if normalized is None:
                continue
            await self._stream.publish_clean(normalized)
            buffer.append(normalized)
            if len(buffer) >= FLUSH_BATCH:
                count = await self._posts.index_many(buffer)
                posts_indexed_total.inc(count)
                log.info("indexed", count=count, stream=raw_stream)
                buffer.clear()

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
