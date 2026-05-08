from news_common import get_settings, setup_logging
from news_common.clients.redis_bus import StreamBus
from news_common.metrics import start_metrics_server

from vk_collector.repositories.cursor import LastSeenCursor
from vk_collector.repositories.stream import RawPostStreamRepository
from vk_collector.services.collector import VKCollectorService


async def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_level, service="vk_collector")
    start_metrics_server(settings.metrics_port, service="vk_collector")

    bus = StreamBus(settings.redis_url)
    repo = RawPostStreamRepository(bus, settings.stream_raw_vk)
    cursor = LastSeenCursor(bus.client)
    service = VKCollectorService(
        stream_repo=repo,
        communities=settings.vk_communities_list,
        poll_interval=settings.vk_poll_interval,
        cursor=cursor,
    )

    tokens = settings.vk_tokens_list

    try:
        if settings.collector_mode == "real" and tokens:
            await service.run_real(tokens)
        else:
            await service.run_mock()
    finally:
        await bus.close()
