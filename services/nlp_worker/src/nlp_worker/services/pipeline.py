import time

from news_common import get_logger
from news_common.clients.redis_bus import StreamBus
from news_common.metrics import (
    ner_entities_total,
    nlp_processed_total,
    nlp_processing_seconds,
    sentiment_predictions_total,
)
from news_common.models import Entity, NormalizedPost, Sentiment
from news_common.repositories import EntitiesRepository, SentimentsRepository

from nlp_worker.services.linker import EntityLinkerService
from nlp_worker.services.ner import NerService
from nlp_worker.services.relations import RelationExtractorService
from nlp_worker.services.sentiment import SentimentService

log = get_logger("nlp_worker.pipeline")
FLUSH_BATCH = 30


class NLPPipeline:
    def __init__(
        self,
        bus: StreamBus,
        ner: NerService,
        linker: EntityLinkerService,
        sentiment: SentimentService,
        relations: RelationExtractorService,
        entities_repo: EntitiesRepository,
        sentiments_repo: SentimentsRepository,
        clean_stream: str,
        enriched_stream: str,
        group: str,
        consumer: str,
    ) -> None:
        self._bus = bus
        self._ner = ner
        self._linker = linker
        self._sentiment = sentiment
        self._relations = relations
        self._entities_repo = entities_repo
        self._sentiments_repo = sentiments_repo
        self._clean_stream = clean_stream
        self._enriched_stream = enriched_stream
        self._group = group
        self._consumer = consumer

    async def run(self) -> None:
        ent_buffer: list[Entity] = []
        sent_buffer: list[Sentiment] = []

        async for _, payload in self._bus.consume(
            self._clean_stream, self._group, self._consumer, count=8, block_ms=2000
        ):
            t0 = time.perf_counter()
            post = NormalizedPost.model_validate(payload)
            entities = self._ner.extract(post.text_clean, post.id)
            channel = (post.metadata or {}).get("channel")
            for ent in entities:
                ner_entities_total.labels(entity_type=ent.type.value).inc()
                ent.source = post.source.value
                ent.channel = channel
            entities = await self._linker.link(entities)

            label, score = self._sentiment.predict(post.text_clean[:1000])
            sentiment_predictions_total.labels(label=label.value).inc()
            doc_sentiment = Sentiment(post_id=post.id, label=label, score=score)
            relations = self._relations.extract(post.text_clean, entities, post.id)

            await self._bus.publish(
                self._enriched_stream,
                {
                    "post": post.model_dump(mode="json"),
                    "entities": [e.model_dump(mode="json") for e in entities],
                    "sentiment": doc_sentiment.model_dump(mode="json"),
                    "relations": [r.model_dump(mode="json") for r in relations],
                },
            )

            ent_buffer.extend(entities)
            sent_buffer.append(doc_sentiment)

            if len(ent_buffer) >= FLUSH_BATCH:
                await self._entities_repo.index_many(ent_buffer)
                ent_buffer.clear()
            if len(sent_buffer) >= FLUSH_BATCH:
                await self._sentiments_repo.index_many(sent_buffer)
                sent_buffer.clear()

            nlp_processed_total.inc()
            nlp_processing_seconds.observe(time.perf_counter() - t0)
            log.info("processed", post_id=post.id, entities=len(entities), label=label.value)
