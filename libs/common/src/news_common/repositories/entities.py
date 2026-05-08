from typing import Any

from opensearchpy import AsyncOpenSearch

from news_common.clients.opensearch import bulk_index
from news_common.models.entity import Entity

INDEX = "entities"


class EntitiesRepository:
    def __init__(self, client: AsyncOpenSearch) -> None:
        self._client = client

    async def index_many(self, entities: list[Entity]) -> int:
        docs = [e.model_dump(mode="json") for e in entities]
        return await bulk_index(self._client, INDEX, docs, id_field="post_id")

    async def find_by_wikidata(self, wikidata_id: str, size: int = 100) -> dict[str, Any]:
        body = {"size": size, "query": {"term": {"wikidata_id": wikidata_id}}}
        return await self._client.search(index=INDEX, body=body)

    async def top(self, etype: str | None = None, size: int = 20) -> dict[str, Any]:
        body: dict[str, Any] = {
            "size": 0,
            "aggs": {"top": {"terms": {"field": "text.keyword", "size": size}}},
        }
        if etype:
            body["query"] = {"term": {"type": etype}}
        return await self._client.search(index=INDEX, body=body)
