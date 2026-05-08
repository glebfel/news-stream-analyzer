from contextlib import asynccontextmanager

from fastapi import FastAPI
from news_common import get_settings, setup_logging
from news_common.clients.opensearch import make_opensearch_client
from news_common.repositories.graph import GraphRepository

from api_gateway.views import entities, graph, health, search, stats


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(settings.log_level, service="api_gateway")
    app.state.os_client = make_opensearch_client(
        settings.opensearch_url, settings.opensearch_user, settings.opensearch_pass
    )
    app.state.graph_repo = GraphRepository(
        settings.neo4j_url, settings.neo4j_user, settings.neo4j_pass
    )
    try:
        yield
    finally:
        await app.state.os_client.close()
        await app.state.graph_repo.close()


app = FastAPI(title="News Stream Analyzer API", version="0.1.0", lifespan=lifespan)

for module in (health, search, stats, entities, graph):
    app.include_router(module.router)
