from enum import StrEnum

from pydantic import BaseModel

from news_common.models.entity import EntityType


class SentimentLabel(StrEnum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class Sentiment(BaseModel):
    post_id: str
    label: SentimentLabel
    score: float
    entity_text: str | None = None
    entity_type: EntityType | None = None
