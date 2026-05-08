from neo4j import AsyncDriver, AsyncGraphDatabase


def entity_key(text: str, etype: str) -> str:
    return f"{etype}::{text.lower()}"


UPSERT_ENTITY = """
MERGE (e:Entity {key: $key})
ON CREATE SET e.text = $text, e.type = $type, e.wikidata_id = $wikidata_id, e.first_seen = $ts
SET e.last_seen = $ts
"""

UPSERT_RELATION = """
MATCH (a:Entity {key: $head_key}), (b:Entity {key: $tail_key})
MERGE (a)-[r:CO_OCCURS]->(b)
ON CREATE SET r.weight = 1.0, r.first_seen = $ts, r.posts = [$post_id], r.sentiment_sum = $score
ON MATCH SET r.weight = r.weight + 1.0, r.last_seen = $ts,
              r.posts = CASE WHEN $post_id IN r.posts THEN r.posts ELSE r.posts + $post_id END,
              r.sentiment_sum = coalesce(r.sentiment_sum, 0) + $score
"""

SUBGRAPH = """
MATCH (e:Entity)-[r:CO_OCCURS]-(o:Entity)
WHERE toLower(e.text) = toLower($entity)
RETURN e, r, o
LIMIT $limit
"""


class GraphRepository:
    def __init__(self, url: str, user: str, password: str) -> None:
        self._driver: AsyncDriver = AsyncGraphDatabase.driver(url, auth=(user, password))

    async def close(self) -> None:
        await self._driver.close()

    async def upsert_entity(
        self, key: str, text: str, etype: str, wikidata_id: str | None, ts: str
    ) -> None:
        async with self._driver.session() as session:
            await session.run(
                UPSERT_ENTITY, key=key, text=text, type=etype, wikidata_id=wikidata_id, ts=ts
            )

    async def upsert_relation(
        self, head_key: str, tail_key: str, post_id: str, score: float, ts: str
    ) -> None:
        async with self._driver.session() as session:
            await session.run(
                UPSERT_RELATION,
                head_key=head_key,
                tail_key=tail_key,
                post_id=post_id,
                score=score,
                ts=ts,
            )

    async def subgraph(self, entity: str, limit: int = 50) -> tuple[dict, list]:
        nodes: dict[str, dict] = {}
        edges: list[dict] = []
        async with self._driver.session() as session:
            result = await session.run(SUBGRAPH, entity=entity, limit=limit)
            async for rec in result:
                for n in (rec["e"], rec["o"]):
                    nodes[n["key"]] = {
                        "text": n["text"],
                        "type": n["type"],
                        "wikidata_id": n.get("wikidata_id"),
                    }
                edges.append(
                    {
                        "head": rec["e"]["key"],
                        "tail": rec["o"]["key"],
                        "weight": rec["r"]["weight"],
                        "sentiment": rec["r"].get("sentiment_sum", 0.0),
                    }
                )
        return nodes, edges
