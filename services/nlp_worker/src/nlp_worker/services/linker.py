import asyncio

from news_common.models import Entity

from nlp_worker.clients.wikidata import WikidataClient


class EntityLinkerService:
    def __init__(self, client: WikidataClient) -> None:
        self._client = client

    async def link(self, entities: list[Entity]) -> list[Entity]:
        if not entities:
            return entities
        qids = await asyncio.gather(*(self._client.search(e.text) for e in entities))
        for entity, qid in zip(entities, qids, strict=True):
            entity.wikidata_id = qid
        return entities
