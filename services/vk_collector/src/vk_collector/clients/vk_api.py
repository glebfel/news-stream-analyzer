from datetime import datetime
from typing import Any

import aiohttp
from news_common import get_logger
from news_common.models import RawPost, Source
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from vk_collector.clients.exceptions import (
    VKError,
    VKRateLimitError,
    VKTransientError,
    from_vk_response,
)
from vk_collector.clients.rate_limiter import AsyncRateLimiter
from vk_collector.clients.token_pool import TokenPool

VK_API = "https://api.vk.com/method"
VK_API_VERSION = "5.199"

EXECUTE_BATCH_LIMIT = 25  # VK hard limit on nested calls per execute

log = get_logger("vk_collector.client")


class VKApiClient:
    def __init__(self, tokens: TokenPool, rate_per_second: float = 3.0) -> None:
        self._tokens = tokens
        self._session: aiohttp.ClientSession | None = None
        self._limiter = AsyncRateLimiter(rate_per_second)

    async def __aenter__(self) -> "VKApiClient":
        self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30, connect=10))
        return self

    async def __aexit__(self, *args: object) -> None:
        if self._session:
            await self._session.close()

    async def wall_get(self, domain: str, count: int = 50) -> list[RawPost]:
        params = {"domain": domain, "count": count}
        data = await self._call("wall.get", params)
        items = data.get("response", {}).get("items", [])
        return [self._to_post(item, domain) for item in items if item.get("text")]

    async def wall_get_many(self, domains: list[str], count: int = 50) -> dict[str, list[RawPost]]:
        """Fetch wall posts for multiple domains using `execute` batching.

        VK's `execute` method runs up to 25 nested API calls in a single request,
        consuming one quota unit per execute (vs N units for naive looping).
        """
        result: dict[str, list[RawPost]] = {}
        for chunk_start in range(0, len(domains), EXECUTE_BATCH_LIMIT):
            chunk = domains[chunk_start : chunk_start + EXECUTE_BATCH_LIMIT]
            data = await self._call("execute", {"code": _build_execute_code(chunk, count)})
            responses = data.get("response", []) or []
            for domain, response in zip(chunk, responses, strict=False):
                if not response or response is False:
                    log.warning("execute_subcall_failed", community=domain)
                    result[domain] = []
                    continue
                items = response.get("items", []) if isinstance(response, dict) else []
                result[domain] = [self._to_post(item, domain) for item in items if item.get("text")]
        return result

    async def _call(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        async for attempt in AsyncRetrying(
            retry=retry_if_exception_type(
                (VKRateLimitError, VKTransientError, aiohttp.ClientError)
            ),
            wait=wait_exponential(multiplier=1, min=1, max=30),
            stop=stop_after_attempt(5),
            reraise=True,
        ):
            with attempt:
                return await self._call_once(method, params)
        raise VKError(0, "unreachable")

    async def _call_once(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        assert self._session is not None
        await self._limiter.acquire()
        token = await self._tokens.next()
        full_params = {**params, "access_token": token, "v": VK_API_VERSION}
        async with self._session.get(f"{VK_API}/{method}", params=full_params) as resp:
            if resp.status >= 500:
                raise VKTransientError(resp.status, f"HTTP {resp.status}")
            data = await resp.json()
        if "error" in data:
            err = from_vk_response(data["error"])
            log.warning("vk_api_error", method=method, code=err.code, msg=err.message)
            raise err
        return data

    @staticmethod
    def _to_post(item: dict, domain: str) -> RawPost:
        return RawPost(
            id=f"vk_{domain}_{item['id']}",
            source=Source.VK,
            author=str(item.get("from_id", "")),
            channel=domain,
            text=item["text"],
            url=f"https://vk.com/{domain}?w=wall{item.get('owner_id', '')}_{item['id']}",
            posted_at=datetime.utcfromtimestamp(item["date"]),
            likes=item.get("likes", {}).get("count", 0),
            reposts=item.get("reposts", {}).get("count", 0),
            views=item.get("views", {}).get("count", 0),
        )


def _build_execute_code(domains: list[str], count: int) -> str:
    """Build VKScript that calls API.wall.get for each domain and returns array of responses."""
    parts = [f'API.wall.get({{"domain": "{d}", "count": {count}}})' for d in domains]
    return f"return [{', '.join(parts)}];"
