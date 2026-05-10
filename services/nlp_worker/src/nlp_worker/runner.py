import httpx
from news_common import get_settings, setup_logging
from news_common.clients.opensearch import make_opensearch_client
from news_common.clients.redis_bus import StreamBus
from news_common.metrics import start_metrics_server
from news_common.repositories import EntitiesRepository, SentimentsRepository

from nlp_worker.clients.wikidata import WikidataClient
from nlp_worker.clients.wikidata_cache import WikidataRedisCache
from nlp_worker.services.linker import EntityLinkerService
from nlp_worker.services.ner import NerService
from nlp_worker.services.pipeline import NLPPipeline
from nlp_worker.services.relations import RelationExtractorService
from nlp_worker.services.sentiment import build_sentiment_service


async def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_level, service="nlp_worker")
    start_metrics_server(settings.metrics_port, service="nlp_worker")

    bus = StreamBus(settings.redis_url)
    os_client = make_opensearch_client(
        settings.opensearch_url, settings.opensearch_user, settings.opensearch_pass
    )
    wikidata_cache = WikidataRedisCache(
        settings.redis_url, ttl_seconds=settings.vk_wikidata_cache_ttl
    )

    async with httpx.AsyncClient() as http:
        pipeline = NLPPipeline(
            bus=bus,
            ner=NerService(),
            linker=EntityLinkerService(WikidataClient(http, cache=wikidata_cache)),
            sentiment=build_sentiment_service(settings.nlp_mode),
            relations=RelationExtractorService(),
            entities_repo=EntitiesRepository(os_client),
            sentiments_repo=SentimentsRepository(os_client),
            clean_stream=settings.stream_clean,
            enriched_stream=settings.stream_enriched,
            group="nlp",
            consumer="n1",
        )
        try:
            await pipeline.run()
        finally:
            await bus.close()
            await os_client.close()
            await wikidata_cache.close()
