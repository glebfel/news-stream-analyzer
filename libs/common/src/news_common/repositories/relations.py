from opensearchpy import AsyncOpenSearch

from news_common.clients.opensearch import bulk_index
from news_common.models.relation import Relation

INDEX = "relations"


class RelationsRepository:
    def __init__(self, client: AsyncOpenSearch) -> None:
        self._client = client

    async def index_many(self, relations: list[Relation]) -> int:
        docs = [r.model_dump(mode="json") for r in relations]
        return await bulk_index(self._client, INDEX, docs, id_field="post_id")
