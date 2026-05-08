from news_common.models import Entity

from nlp_worker.clients.wikidata import WikidataClient


class EntityLinkerService:
    def __init__(self, client: WikidataClient) -> None:
        self._client = client

    async def link(self, entities: list[Entity]) -> list[Entity]:
        for entity in entities:
            entity.wikidata_id = await self._client.search(entity.text)
        return entities
