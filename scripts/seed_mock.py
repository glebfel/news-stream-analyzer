import argparse
import asyncio

from news_common import Source, get_settings
from news_common.clients.redis_bus import StreamBus
from news_common.mocks import fake_post


async def main(count: int) -> None:
    settings = get_settings()
    bus = StreamBus(settings.redis_url)
    try:
        for i in range(count):
            source = Source.VK if i % 2 == 0 else Source.TELEGRAM
            stream = settings.stream_raw_vk if source == Source.VK else settings.stream_raw_tg
            await bus.publish(stream, fake_post(source).model_dump(mode="json"))
        print(f"published {count} mock posts")
    finally:
        await bus.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=200)
    args = parser.parse_args()
    asyncio.run(main(args.count))
