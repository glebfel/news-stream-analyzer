from fastapi import APIRouter, Depends, Query

from api_gateway.deps import search_service
from api_gateway.schemas.responses import SearchResponse
from api_gateway.services.search import SearchService

router = APIRouter()


@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1),
    size: int = Query(20, ge=1, le=100),
    source: str | None = None,
    service: SearchService = Depends(search_service),
) -> SearchResponse:
    return await service.search_posts(query=q, size=size, source=source)


@router.get("/latest", response_model=SearchResponse)
async def latest(
    size: int = Query(10, ge=1, le=50),
    service: SearchService = Depends(search_service),
) -> SearchResponse:
    return await service.latest(size=size)
