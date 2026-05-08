from news_common import get_logger, get_settings, setup_logging
from news_common.clients.redis_bus import StreamBus
from news_common.repositories.graph import GraphRepository

from graph_builder.services.graph_writer import GraphWriterService

log = get_logger("graph_builder.runner")


async def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_level, service="graph_builder")

    bus = StreamBus(settings.redis_url)
    repo = GraphRepository(settings.neo4j_url, settings.neo4j_user, settings.neo4j_pass)
    writer = GraphWriterService(repo)

    try:
        async for _, payload in bus.consume(
            settings.stream_enriched, "graph", "g1", count=8, block_ms=2000
        ):
            try:
                await writer.write_payload(payload)
            except Exception as exc:
                log.error(
                    "graph_write_failed", error=str(exc), post_id=payload.get("post", {}).get("id")
                )
                continue
            log.info(
                "graph_updated",
                post_id=payload["post"]["id"],
                entities=len(payload["entities"]),
                relations=len(payload.get("relations", [])),
            )
    finally:
        await repo.close()
        await bus.close()
