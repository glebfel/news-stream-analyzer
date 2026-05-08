from news_common import get_settings, setup_logging
from news_common.clients.opensearch import make_opensearch_client
from news_common.clients.redis_bus import StreamBus
from news_common.repositories import PostsRepository

from processor.repositories.stream import StreamRepository
from processor.services.deduper import Deduper
from processor.services.normalizer import Normalizer
from processor.services.pipeline import ProcessorPipeline


async def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_level, service="processor")

    bus = StreamBus(settings.redis_url)
    os_client = make_opensearch_client(
        settings.opensearch_url, settings.opensearch_user, settings.opensearch_pass
    )
    stream_repo = StreamRepository(
        bus, group="processor", consumer="p1", clean_stream=settings.stream_clean
    )
    posts_repo = PostsRepository(os_client)
    pipeline = ProcessorPipeline(stream_repo, posts_repo, Normalizer(), Deduper(threshold=0.85))

    try:
        await pipeline.run([settings.stream_raw_vk, settings.stream_raw_tg])
    finally:
        await bus.close()
        await os_client.close()
