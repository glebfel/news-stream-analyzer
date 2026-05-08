from typing import Any

from pydantic import BaseModel


class SearchResponse(BaseModel):
    total: int
    items: list[dict[str, Any]]


class EntityResponse(BaseModel):
    wikidata_id: str
    mentions: int
    items: list[dict[str, Any]]


class StatsResponse(BaseModel):
    posts_total: int
    by_source: list[dict[str, Any]]
    by_day: list[dict[str, Any]]
    by_sentiment: list[dict[str, Any]]


class TopEntitiesResponse(BaseModel):
    items: list[dict[str, Any]]


class SubgraphResponse(BaseModel):
    nodes: dict[str, dict[str, Any]]
    edges: list[dict[str, Any]]
