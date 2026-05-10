from news_common.repositories import EntitiesRepository

from api_gateway.schemas.responses import EntityResponse, TopEntitiesResponse


class EntitiesService:
    def __init__(self, repo: EntitiesRepository) -> None:
        self._repo = repo

    async def by_wikidata(self, wikidata_id: str) -> EntityResponse:
        res = await self._repo.find_by_wikidata(wikidata_id)
        items = [h["_source"] for h in res["hits"]["hits"]]
        return EntityResponse(wikidata_id=wikidata_id, mentions=len(items), items=items)

    async def top(self, etype: str | None, size: int) -> TopEntitiesResponse:
        res = await self._repo.top(etype=etype, size=size)
        return TopEntitiesResponse(items=res["aggregations"]["top"]["buckets"])

    async def suggest(self, q: str, size: int) -> list[str]:
        res = await self._repo.suggest(prefix=q, size=size)
        buckets = res["aggregations"]["top"]["buckets"]
        return [b["key"] for b in buckets]
