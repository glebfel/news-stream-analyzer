from enum import StrEnum

from pydantic import BaseModel


class EntityType(StrEnum):
    PER = "PER"
    ORG = "ORG"
    LOC = "LOC"
    EVENT = "EVENT"
    DATE = "DATE"


class Entity(BaseModel):
    post_id: str
    text: str
    type: EntityType
    span_start: int
    span_end: int
    wikidata_id: str | None = None
    confidence: float = 1.0
    source: str | None = None
    channel: str | None = None
