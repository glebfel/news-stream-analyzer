from news_common import get_logger
from news_common.repositories.graph import GraphRepository, entity_key

log = get_logger("graph_builder.writer")


class GraphWriterService:
    def __init__(self, repo: GraphRepository) -> None:
        self._repo = repo

    async def write_payload(self, payload: dict) -> None:
        post_id: str = payload["post"]["id"]
        ts: str = payload["post"]["posted_at"]
        score = self._signed_score(payload.get("sentiment") or {})

        for ent in payload["entities"]:
            await self._repo.upsert_entity(
                key=entity_key(ent["text"], ent["type"]),
                text=ent["text"],
                etype=ent["type"],
                wikidata_id=ent.get("wikidata_id"),
                ts=ts,
            )
        for rel in payload.get("relations", []):
            await self._repo.upsert_relation(
                head_key=entity_key(rel["head"], rel["head_type"]),
                tail_key=entity_key(rel["tail"], rel["tail_type"]),
                post_id=post_id,
                score=score,
                ts=ts,
            )

    @staticmethod
    def _signed_score(sentiment: dict) -> float:
        if not sentiment:
            return 0.0
        label = sentiment.get("label")
        score = sentiment.get("score", 0.0)
        if label == "positive":
            return score
        if label == "negative":
            return -score
        return 0.0
