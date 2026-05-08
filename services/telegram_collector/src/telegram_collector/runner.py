from news_common import get_settings, setup_logging
from news_common.clients.redis_bus import StreamBus

from telegram_collector.repositories.stream import RawPostStreamRepository
from telegram_collector.services.collector import TelegramCollectorService


async def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_level, service="telegram_collector")

    bus = StreamBus(settings.redis_url)
    repo = RawPostStreamRepository(bus, settings.stream_raw_tg)
    service = TelegramCollectorService(
        stream_repo=repo,
        channels=settings.tg_channels_list,
        poll_interval=settings.vk_poll_interval,
    )

    try:
        if settings.collector_mode == "real" and settings.tg_api_id and settings.tg_api_hash:
            await service.run_real(
                int(settings.tg_api_id), settings.tg_api_hash, settings.tg_session_name
            )
        else:
            await service.run_mock()
    finally:
        await bus.close()
