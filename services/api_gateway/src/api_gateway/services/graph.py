from news_common.repositories.graph import GraphRepository

from api_gateway.schemas.responses import SubgraphResponse


class GraphService:
    def __init__(self, repo: GraphRepository) -> None:
        self._repo = repo

    async def subgraph(self, entity: str, limit: int) -> SubgraphResponse:
        nodes, edges = await self._repo.subgraph(entity=entity, limit=limit)
        return SubgraphResponse(nodes=nodes, edges=edges)
