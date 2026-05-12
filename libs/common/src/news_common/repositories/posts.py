from typing import Any

from opensearchpy import AsyncOpenSearch

from news_common.clients.opensearch import bulk_index
from news_common.models.post import NormalizedPost

INDEX = "raw_posts"


class PostsRepository:
    def __init__(self, client: AsyncOpenSearch) -> None:
        self._client = client

    async def index_many(self, posts: list[NormalizedPost]) -> int:
        docs = [p.model_dump(mode="json") for p in posts]
        return await bulk_index(self._client, INDEX, docs)

    async def search(
        self,
        query: str,
        size: int = 20,
        source: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "size": size,
            "query": {"bool": {"must": [{"match": {"text_clean": query}}]}},
            "sort": [{"posted_at": "desc"}],
        }
        if source:
            body["query"]["bool"]["filter"] = [{"term": {"source": source}}]
        return await self._client.search(index=INDEX, body=body)

    async def latest(self, size: int = 10) -> dict[str, Any]:
        body = {"size": size, "sort": [{"posted_at": "desc"}], "query": {"match_all": {}}}
        return await self._client.search(index=INDEX, body=body)

    async def stats(self) -> dict[str, Any]:
        body = {
            "size": 0,
            "aggs": {
                "by_source": {"terms": {"field": "source", "size": 10}},
                "by_day": {
                    "date_histogram": {
                        "field": "posted_at",
                        "calendar_interval": "day",
                        "time_zone": "+03:00",
                    }
                },
            },
        }
        return await self._client.search(index=INDEX, body=body)
