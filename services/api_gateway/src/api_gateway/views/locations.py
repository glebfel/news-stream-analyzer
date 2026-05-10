from fastapi import APIRouter, Depends, Query

from api_gateway.deps import locations_service
from api_gateway.services.locations import LocationsService

router = APIRouter()


@router.get("/locations")
async def locations(
    size: int = Query(30, ge=5, le=100),
    service: LocationsService = Depends(locations_service),
) -> list[dict]:
    return await service.top_with_coords(size=size)
