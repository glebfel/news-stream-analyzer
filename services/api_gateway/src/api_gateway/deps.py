from fastapi import Request
from news_common.repositories import EntitiesRepository, PostsRepository, SentimentsRepository
from news_common.repositories.graph import GraphRepository

from api_gateway.services.entities import EntitiesService
from api_gateway.services.graph import GraphService
from api_gateway.services.search import SearchService
from api_gateway.services.stats import StatsService


def search_service(request: Request) -> SearchService:
    return SearchService(PostsRepository(request.app.state.os_client))


def stats_service(request: Request) -> StatsService:
    posts = PostsRepository(request.app.state.os_client)
    sentiments = SentimentsRepository(request.app.state.os_client)
    return StatsService(posts, sentiments)


def entities_service(request: Request) -> EntitiesService:
    return EntitiesService(EntitiesRepository(request.app.state.os_client))


def graph_service(request: Request) -> GraphService:
    repo: GraphRepository = request.app.state.graph_repo
    return GraphService(repo)
