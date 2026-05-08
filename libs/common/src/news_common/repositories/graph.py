from neo4j import AsyncDriver, AsyncGraphDatabase

# Decay factor applied to existing edge weight on each new co-occurrence.
# Picked so that ~30 days without new mentions halve the weight; tunable.
DEFAULT_DECAY = 0.95

REL_TYPE = "MENTIONED_WITH"


def entity_key(text: str, etype: str) -> str:
    return f"{etype}::{text.lower()}"


UPSERT_ENTITIES_BATCH = """
UNWIND $items AS item
MERGE (e:Entity {key: item.key})
  ON CREATE SET e.text = item.text,
                e.type = item.type,
                e.wikidata_id = item.wikidata_id,
                e.first_seen = item.ts,
                e.mention_count = 1,
                e.aliases = [item.text]
  ON MATCH SET  e.last_seen = item.ts,
                e.mention_count = coalesce(e.mention_count, 0) + 1,
                e.aliases = CASE
                                WHEN item.text IN coalesce(e.aliases, [])
                                THEN e.aliases
                                ELSE coalesce(e.aliases, []) + item.text
                            END,
                e.wikidata_id = coalesce(e.wikidata_id, item.wikidata_id)
SET e.last_seen = item.ts
"""

UPSERT_RELATIONS_BATCH = f"""
UNWIND $items AS item
MATCH (a:Entity {{key: item.head_key}}), (b:Entity {{key: item.tail_key}})
MERGE (a)-[r:{REL_TYPE}]->(b)
  ON CREATE SET r.weight = item.window_factor,
                r.first_seen = item.ts,
                r.posts = [item.post_id],
                r.sentiment_sum = item.score,
                r.update_count = 1
  ON MATCH SET  r.weight = r.weight * $decay + item.window_factor,
                r.last_seen = item.ts,
                r.posts = CASE
                              WHEN item.post_id IN r.posts
                              THEN r.posts
                              ELSE r.posts + item.post_id
                          END,
                r.sentiment_sum = coalesce(r.sentiment_sum, 0) + item.score,
                r.update_count = coalesce(r.update_count, 0) + 1
"""

SUBGRAPH = f"""
MATCH (e:Entity)-[r:{REL_TYPE}]-(o:Entity)
WHERE toLower(e.text) = toLower($entity)
RETURN e, r, o
LIMIT $limit
"""


class GraphRepository:
    def __init__(self, url: str, user: str, password: str, decay: float = DEFAULT_DECAY) -> None:
        self._driver: AsyncDriver = AsyncGraphDatabase.driver(url, auth=(user, password))
        self._decay = decay

    async def close(self) -> None:
        await self._driver.close()

    async def upsert_entities_batch(self, items: list[dict]) -> None:
        """Bulk-upsert entities with mention_count + aliases accumulation.

        Each item must contain: key, text, type, wikidata_id, ts.
        """
        if not items:
            return
        async with self._driver.session() as session:
            await session.run(UPSERT_ENTITIES_BATCH, items=items)

    async def upsert_relations_batch(self, items: list[dict]) -> None:
        """Bulk-upsert MENTIONED_WITH relations with time-decay weighting.

        Each item must contain: head_key, tail_key, post_id, score, ts, window_factor.
        On match: w := w * decay + window_factor. On create: w := window_factor.
        """
        if not items:
            return
        async with self._driver.session() as session:
            await session.run(UPSERT_RELATIONS_BATCH, items=items, decay=self._decay)

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
                        "mention_count": n.get("mention_count", 0),
                        "aliases": n.get("aliases", []),
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
