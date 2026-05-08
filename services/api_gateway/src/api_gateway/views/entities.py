from fastapi import APIRouter, Depends, Query

from api_gateway.deps import entities_service
from api_gateway.schemas.responses import EntityResponse, TopEntitiesResponse
from api_gateway.services.entities import EntitiesService

router = APIRouter()


@router.get("/entity/{wikidata_id}", response_model=EntityResponse)
async def entity_by_id(
    wikidata_id: str,
    service: EntitiesService = Depends(entities_service),
) -> EntityResponse:
    return await service.by_wikidata(wikidata_id)


@router.get("/top_entities", response_model=TopEntitiesResponse)
async def top_entities(
    etype: str | None = None,
    size: int = Query(20, ge=1, le=200),
    service: EntitiesService = Depends(entities_service),
) -> TopEntitiesResponse:
    return await service.top(etype=etype, size=size)
