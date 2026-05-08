from fastapi import APIRouter, Depends, Query

from api_gateway.deps import graph_service
from api_gateway.schemas.responses import SubgraphResponse
from api_gateway.services.graph import GraphService

router = APIRouter()


@router.get("/graph/subgraph", response_model=SubgraphResponse)
async def subgraph(
    entity: str,
    limit: int = Query(50, ge=1, le=300),
    service: GraphService = Depends(graph_service),
) -> SubgraphResponse:
    return await service.subgraph(entity=entity, limit=limit)
