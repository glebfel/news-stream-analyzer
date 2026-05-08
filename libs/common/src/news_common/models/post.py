from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Source(StrEnum):
    VK = "vk"
    TELEGRAM = "telegram"


class RawPost(BaseModel):
    id: str
    source: Source
    author: str | None = None
    channel: str | None = None
    text: str
    url: str | None = None
    posted_at: datetime
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    likes: int = 0
    reposts: int = 0
    views: int = 0


class NormalizedPost(BaseModel):
    id: str
    source: Source
    text: str
    text_clean: str
    tokens: list[str]
    lemmas: list[str]
    posted_at: datetime
    simhash: str
    metadata: dict = Field(default_factory=dict)
