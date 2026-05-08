from fastapi import APIRouter, Depends

from api_gateway.deps import stats_service
from api_gateway.schemas.responses import StatsResponse
from api_gateway.services.stats import StatsService

router = APIRouter()


@router.get("/stats", response_model=StatsResponse)
async def stats(service: StatsService = Depends(stats_service)) -> StatsResponse:
    return await service.collect()
