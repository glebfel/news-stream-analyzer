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

    async def suggest(self, prefix: str, size: int = 10) -> dict[str, Any]:
        body: dict[str, Any] = {
            "size": 0,
            "query": {"match_phrase_prefix": {"text": {"query": prefix, "max_expansions": 50}}},
            "aggs": {"top": {"terms": {"field": "text.keyword", "size": size}}},
        }
        return await self._client.search(index=INDEX, body=body)

    async def wikidata_ids_for(
        self, names: list[str], etype: str | None = None
    ) -> dict[str, str | None]:
        if not names:
            return {}
        body: dict[str, Any] = {
            "size": 0,
            "query": {
                "bool": {
                    "must": [
                        {"terms": {"text.keyword": names}},
                        {"exists": {"field": "wikidata_id"}},
                    ]
                }
            },
            "aggs": {
                "by_text": {
                    "terms": {"field": "text.keyword", "size": len(names)},
                    "aggs": {
                        "sample": {
                            "top_hits": {"size": 1, "_source": {"includes": ["wikidata_id"]}}
                        }
                    },
                }
            },
        }
        if etype:
            body["query"]["bool"]["must"].append({"term": {"type": etype}})
        res = await self._client.search(index=INDEX, body=body)
        out: dict[str, str | None] = {n: None for n in names}
        for bucket in res["aggregations"]["by_text"]["buckets"]:
            hits = bucket["sample"]["hits"]["hits"]
            if hits:
                out[bucket["key"]] = hits[0]["_source"].get("wikidata_id")
        return out

    async def by_channel(
        self, channels: int = 8, per_channel: int = 5, etype: str | None = None
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "size": 0,
            "query": {"exists": {"field": "channel"}},
            "aggs": {
                "channels": {
                    "terms": {"field": "channel.keyword", "size": channels},
                    "aggs": {
                        "top": {"terms": {"field": "text.keyword", "size": per_channel}},
                    },
                }
            },
        }
        if etype:
            body["query"] = {
                "bool": {
                    "must": [{"exists": {"field": "channel"}}, {"term": {"type": etype}}],
                }
            }
        return await self._client.search(index=INDEX, body=body)
