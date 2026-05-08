from news_common.repositories import PostsRepository

from api_gateway.schemas.responses import SearchResponse


class SearchService:
    def __init__(self, repo: PostsRepository) -> None:
        self._repo = repo

    async def search_posts(self, query: str, size: int, source: str | None) -> SearchResponse:
        res = await self._repo.search(query=query, size=size, source=source)
        items = [h["_source"] for h in res["hits"]["hits"]]
        return SearchResponse(total=res["hits"]["total"]["value"], items=items)
