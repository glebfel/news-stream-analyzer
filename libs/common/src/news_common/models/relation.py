from pydantic import BaseModel

from news_common.models.entity import EntityType


class Relation(BaseModel):
    post_id: str
    head: str
    head_type: EntityType
    tail: str
    tail_type: EntityType
    rel_type: str = "co_occurrence"
    weight: float = 1.0
    sentence: str | None = None
