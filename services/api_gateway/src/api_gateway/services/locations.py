from typing import Any

import httpx
from news_common.repositories import EntitiesRepository
from redis.asyncio import Redis

WIKIDATA_API = "https://www.wikidata.org/w/api.php"
USER_AGENT = "news-stream-analyzer/1.0 (https://github.com/glebfel/news-stream-analyzer)"
COORDS_KEY = "wd_coords:"
SENTINEL_NONE = "__none__"
TTL_SECONDS = 30 * 86400
WBGETENTITIES_BATCH = 50


class WikidataCoordsClient:
    @staticmethod
    async def fetch(qids: list[str]) -> dict[str, tuple[float, float] | None]:
        # Wikidata's public SPARQL endpoint is slow/unreliable; the REST
        # wbgetentities API answers in 100ms and accepts up to 50 QIDs per call.
        out: dict[str, tuple[float, float] | None] = {q: None for q in qids}
        if not qids:
            return out
        async with httpx.AsyncClient(
            timeout=15,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        ) as client:
            for start in range(0, len(qids), WBGETENTITIES_BATCH):
                batch = qids[start : start + WBGETENTITIES_BATCH]
                try:
                    resp = await client.get(
                        WIKIDATA_API,
                        params={
                            "action": "wbgetentities",
                            "ids": "|".join(batch),
                            "props": "claims",
                            "format": "json",
                        },
                    )
                    resp.raise_for_status()
                    data = resp.json()
                except (TimeoutError, httpx.HTTPError, ValueError):
                    continue
                for qid, entity in (data.get("entities") or {}).items():
                    coords = WikidataCoordsClient._extract(entity)
                    if coords is not None:
                        out[qid] = coords
        return out

    @staticmethod
    def _extract(entity: dict) -> tuple[float, float] | None:
        for claim in (entity.get("claims") or {}).get("P625", []):
            value = ((claim.get("mainsnak") or {}).get("datavalue") or {}).get("value") or {}
            lat = value.get("latitude")
            lon = value.get("longitude")
            if isinstance(lat, int | float) and isinstance(lon, int | float):
                return float(lat), float(lon)
        return None


class WikidataCoordsCache:
    def __init__(self, redis_url: str, ttl_seconds: int = TTL_SECONDS) -> None:
        self._redis: Redis = Redis.from_url(redis_url, decode_responses=True)
        self._ttl = ttl_seconds

    async def close(self) -> None:
        await self._redis.aclose()

    async def get_many(self, qids: list[str]) -> dict[str, tuple[float, float] | None]:
        out: dict[str, tuple[float, float] | None] = {}
        if not qids:
            return out
        raws = await self._redis.mget(f"{COORDS_KEY}{q}" for q in qids)
        for qid, raw in zip(qids, raws, strict=True):
            if raw is None:
                continue
            if raw == SENTINEL_NONE:
                out[qid] = None
                continue
            try:
                lat_s, lon_s = raw.split(",", 1)
                out[qid] = (float(lat_s), float(lon_s))
            except ValueError:
                out[qid] = None
        return out

    async def set_many(self, items: dict[str, tuple[float, float] | None]) -> None:
        if not items:
            return
        pipe = self._redis.pipeline()
        for qid, latlon in items.items():
            value = f"{latlon[0]},{latlon[1]}" if latlon else SENTINEL_NONE
            pipe.set(f"{COORDS_KEY}{qid}", value, ex=self._ttl)
        await pipe.execute()


class LocationsService:
    def __init__(
        self,
        entities_repo: EntitiesRepository,
        cache: WikidataCoordsCache,
        client: WikidataCoordsClient,
    ) -> None:
        self._repo = entities_repo
        self._cache = cache
        self._client = client

    async def top_with_coords(self, size: int) -> list[dict[str, Any]]:
        agg = await self._repo.top(etype="LOC", size=size * 3)
        buckets = agg["aggregations"]["top"]["buckets"]
        names = [b["key"] for b in buckets]
        counts = {b["key"]: b["doc_count"] for b in buckets}
        qids_by_name = await self._repo.wikidata_ids_for(names, etype="LOC")
        unique_qids = list({q for q in qids_by_name.values() if q})
        coords = await self._coords_for(unique_qids)
        out: list[dict[str, Any]] = []
        for name in names:
            qid = qids_by_name.get(name)
            if not qid:
                continue
            latlon = coords.get(qid)
            if not latlon:
                continue
            out.append(
                {
                    "text": name,
                    "wikidata_id": qid,
                    "lat": latlon[0],
                    "lon": latlon[1],
                    "mention_count": counts[name],
                }
            )
            if len(out) >= size:
                break
        return out

    async def _coords_for(self, qids: list[str]) -> dict[str, tuple[float, float] | None]:
        cached = await self._cache.get_many(qids)
        missing = [q for q in qids if q not in cached]
        if missing:
            fetched = await self._client.fetch(missing)
            await self._cache.set_many(fetched)
            cached.update(fetched)
        return cached
