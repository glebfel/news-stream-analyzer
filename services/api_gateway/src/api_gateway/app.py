from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from news_common import get_settings, setup_logging
from news_common.clients.opensearch import make_opensearch_client
from news_common.metrics import service_up
from news_common.repositories import EntitiesRepository
from news_common.repositories.graph import GraphRepository
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from api_gateway.services.locations import (
    LocationsService,
    WikidataCoordsCache,
    WikidataCoordsClient,
)
from api_gateway.views import entities, graph, health, locations, search, stats


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    setup_logging(settings.log_level, service="api_gateway")
    service_up.labels(service="api_gateway").set(1)
    app.state.os_client = make_opensearch_client(
        settings.opensearch_url, settings.opensearch_user, settings.opensearch_pass
    )
    app.state.graph_repo = GraphRepository(
        settings.neo4j_url, settings.neo4j_user, settings.neo4j_pass
    )
    app.state.coords_cache = WikidataCoordsCache(settings.redis_url)
    app.state.locations_service = LocationsService(
        EntitiesRepository(app.state.os_client),
        app.state.coords_cache,
        WikidataCoordsClient(),
    )
    try:
        yield
    finally:
        service_up.labels(service="api_gateway").set(0)
        await app.state.os_client.close()
        await app.state.graph_repo.close()
        await app.state.coords_cache.close()


app = FastAPI(title="News Stream Analyzer API", version="0.1.0", lifespan=lifespan)

for module in (health, search, stats, entities, graph, locations):
    app.include_router(module.router)


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
