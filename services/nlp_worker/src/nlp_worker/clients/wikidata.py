from typing import Any

import httpx
from news_common import get_settings
from news_common.metrics import wikidata_cache_hits_total, wikidata_cache_misses_total

from nlp_worker.clients.wikidata_cache import WikidataRedisCache

WIKIDATA_API = "https://www.wikidata.org/w/api.php"


class WikidataClient:
    def __init__(self, client: httpx.AsyncClient, cache: WikidataRedisCache | None = None) -> None:
        self._client = client
        self._cache = cache

    async def search(self, text: str) -> str | None:
        if self._cache is not None:
            cached, qid = await self._cache.get(text)
            if cached:
                wikidata_cache_hits_total.inc()
                return qid

        wikidata_cache_misses_total.inc()
        qid = await self._search_remote(text)

        if self._cache is not None:
            await self._cache.set(text, qid)
        return qid

    async def _search_remote(self, text: str) -> str | None:
        params: dict[str, Any] = {
            "action": "wbsearchentities",
            "search": text,
            "language": "ru",
            "format": "json",
            "limit": 1,
        }
        try:
            resp = await self._client.get(
                WIKIDATA_API,
                params=params,
                headers={"User-Agent": get_settings().wikidata_user_agent},
                timeout=5,
            )
            data = resp.json()
        except Exception:
            return None
        results = data.get("search", [])
        return results[0]["id"] if results else None
