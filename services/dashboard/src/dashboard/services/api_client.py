from typing import Any

import httpx


class ApiClient:
    def __init__(self, base_url: str, timeout: float = 15.0) -> None:
        self._base = base_url.rstrip("/")
        self._timeout = timeout

    def get(self, path: str, **params: Any) -> dict[str, Any]:
        with httpx.Client(timeout=self._timeout) as client:
            resp = client.get(f"{self._base}{path}", params=params)
            resp.raise_for_status()
            return resp.json()

    def search(self, q: str, size: int = 20, source: str | None = None) -> dict[str, Any]:
        return self.get("/search", q=q, size=size, source=source or None)

    def latest(self, size: int = 10) -> dict[str, Any]:
        return self.get("/latest", size=size)

    def stats(self) -> dict[str, Any]:
        return self.get("/stats")

    def top_entities(self, etype: str | None = None, size: int = 30) -> dict[str, Any]:
        return self.get("/top_entities", etype=etype or None, size=size)

    def subgraph(self, entity: str, limit: int = 80) -> dict[str, Any]:
        return self.get("/graph/subgraph", entity=entity, limit=limit)

    def suggest(self, q: str, size: int = 10) -> list[str]:
        with httpx.Client(timeout=self._timeout) as client:
            resp = client.get(f"{self._base}/suggest", params={"q": q, "size": size})
            resp.raise_for_status()
            return resp.json()

    def sankey(
        self, channels: int = 8, per_channel: int = 5, etype: str | None = None
    ) -> list[dict[str, Any]]:
        with httpx.Client(timeout=self._timeout) as client:
            resp = client.get(
                f"{self._base}/sankey",
                params={"channels": channels, "per_channel": per_channel, "etype": etype},
            )
            resp.raise_for_status()
            return resp.json()

    def locations(self, size: int = 30) -> list[dict[str, Any]]:
        with httpx.Client(timeout=self._timeout * 3) as client:
            resp = client.get(f"{self._base}/locations", params={"size": size})
            resp.raise_for_status()
            return resp.json()
