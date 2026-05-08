from typing import Any

from opensearchpy import AsyncOpenSearch


def make_opensearch_client(url: str, user: str = "", password: str = "") -> AsyncOpenSearch:
    auth = (user, password) if user else None
    return AsyncOpenSearch(
        hosts=[url],
        http_auth=auth,
        use_ssl=url.startswith("https"),
        verify_certs=False,
        ssl_show_warn=False,
    )


async def bulk_index(
    client: AsyncOpenSearch,
    index: str,
    docs: list[dict[str, Any]],
    id_field: str = "id",
) -> int:
    if not docs:
        return 0
    body: list[dict[str, Any]] = []
    for d in docs:
        action: dict[str, Any] = {"index": {"_index": index}}
        if id_field in d:
            action["index"]["_id"] = d[id_field]
        body.append(action)
        body.append(d)
    resp = await client.bulk(body=body, refresh=False)
    return sum(1 for item in resp.get("items", []) if next(iter(item.values()))["status"] < 300)
