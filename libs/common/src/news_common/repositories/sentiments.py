from typing import Any

from opensearchpy import AsyncOpenSearch

from news_common.clients.opensearch import bulk_index
from news_common.models.sentiment import Sentiment

INDEX = "sentiments"


class SentimentsRepository:
    def __init__(self, client: AsyncOpenSearch) -> None:
        self._client = client

    async def index_many(self, sentiments: list[Sentiment]) -> int:
        docs = [s.model_dump(mode="json") for s in sentiments]
        return await bulk_index(self._client, INDEX, docs, id_field="post_id")

    async def by_label_aggregation(self) -> dict[str, Any]:
        body = {"size": 0, "aggs": {"by_label": {"terms": {"field": "label"}}}}
        return await self._client.search(index=INDEX, body=body)
