import asyncio
import contextlib
import time

from news_common import get_logger
from news_common.metrics import graph_buffer_depth, graph_flush_size, graph_flush_total
from news_common.repositories.graph import GraphRepository, entity_key

log = get_logger("graph_builder.writer")


class GraphWriterService:
    """Buffers entities/relations across enriched messages and flushes them to
    Neo4j as bulk UNWIND queries.

    Flush triggers:
      - buffered entities reach `flush_every`
      - last flush was more than `flush_seconds` ago
      - explicit `flush()` (called on shutdown)
    """

    def __init__(
        self,
        repo: GraphRepository,
        flush_every: int = 100,
        flush_seconds: float = 2.0,
    ) -> None:
        self._repo = repo
        self._flush_every = flush_every
        self._flush_seconds = flush_seconds
        self._entities: list[dict] = []
        self._relations: list[dict] = []
        self._last_flush = time.monotonic()
        self._lock = asyncio.Lock()
        self._timer_task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the background timer that flushes idle buffers."""
        if self._timer_task is None:
            self._timer_task = asyncio.create_task(self._timer_loop())

    async def stop(self) -> None:
        """Cancel the timer and drain remaining buffers."""
        if self._timer_task is not None:
            self._timer_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._timer_task
            self._timer_task = None
        await self.flush()

    async def _timer_loop(self) -> None:
        while True:
            await asyncio.sleep(self._flush_seconds)
            try:
                async with self._lock:
                    if time.monotonic() - self._last_flush >= self._flush_seconds:
                        await self._flush_locked()
            except Exception as exc:
                log.error("graph_timer_flush_failed", error=str(exc))

    async def write_payload(self, payload: dict) -> None:
        post_id: str = payload["post"]["id"]
        ts: str = payload["post"]["posted_at"]
        score = self._signed_score(payload.get("sentiment") or {})

        async with self._lock:
            for ent in payload["entities"]:
                self._entities.append(
                    {
                        "key": entity_key(ent["text"], ent["type"]),
                        "text": ent["text"],
                        "type": ent["type"],
                        "wikidata_id": ent.get("wikidata_id"),
                        "ts": ts,
                    }
                )
            for rel in payload.get("relations", []):
                self._relations.append(
                    {
                        "head_key": entity_key(rel["head"], rel["head_type"]),
                        "tail_key": entity_key(rel["tail"], rel["tail_type"]),
                        "post_id": post_id,
                        "score": score,
                        "ts": ts,
                        "window_factor": float(rel.get("weight", 1.0)),
                    }
                )

            graph_buffer_depth.labels(kind="entities").set(len(self._entities))
            graph_buffer_depth.labels(kind="relations").set(len(self._relations))
            if self._should_flush():
                await self._flush_locked()

    async def flush(self) -> None:
        async with self._lock:
            await self._flush_locked()

    def _should_flush(self) -> bool:
        return (
            len(self._entities) >= self._flush_every
            or len(self._relations) >= self._flush_every
            or time.monotonic() - self._last_flush >= self._flush_seconds
        )

    async def _flush_locked(self) -> None:
        if not self._entities and not self._relations:
            self._last_flush = time.monotonic()
            return
        entities = self._entities[:]
        relations = self._relations[:]
        self._entities.clear()
        self._relations.clear()
        self._last_flush = time.monotonic()
        await self._repo.upsert_entities_batch(entities)
        await self._repo.upsert_relations_batch(relations)
        graph_flush_total.inc()
        graph_flush_size.labels(kind="entities").observe(len(entities))
        graph_flush_size.labels(kind="relations").observe(len(relations))
        graph_buffer_depth.labels(kind="entities").set(0)
        graph_buffer_depth.labels(kind="relations").set(0)
        log.info("graph_flush", entities=len(entities), relations=len(relations))

    @staticmethod
    def _signed_score(sentiment: dict) -> float:
        if not sentiment:
            return 0.0
        label = sentiment.get("label")
        score = sentiment.get("score", 0.0)
        if label == "positive":
            return score
        if label == "negative":
            return -score
        return 0.0
