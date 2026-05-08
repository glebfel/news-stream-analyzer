"""Schema migration runner for OpenSearch and Neo4j.

Conventions:
  infra/migrations/opensearch/V###__<name>.json
  infra/migrations/neo4j/V###__<name>.cypher

State is stored in:
  - OpenSearch index `news_migrations` (one doc per applied version)
  - Neo4j nodes `(:Migration {version, applied_at})`

Re-running is idempotent: already-applied versions are skipped.
"""

from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path

from neo4j import AsyncGraphDatabase
from news_common import get_settings
from news_common.clients.opensearch import make_opensearch_client
from opensearchpy.exceptions import NotFoundError

ROOT = Path(__file__).resolve().parents[1]
OS_DIR = ROOT / "infra" / "migrations" / "opensearch"
NEO_DIR = ROOT / "infra" / "migrations" / "neo4j"

OS_STATE_INDEX = "news_migrations"
VERSION_RE = re.compile(r"V(\d+)__.+\.(json|cypher)")


def parse_version(path: Path) -> int:
    m = VERSION_RE.match(path.name)
    if not m:
        raise ValueError(f"Bad migration filename: {path.name}")
    return int(m.group(1))


async def applied_opensearch(client) -> set[int]:
    try:
        res = await client.search(
            index=OS_STATE_INDEX, body={"size": 1000, "query": {"match_all": {}}}
        )
    except NotFoundError:
        await client.indices.create(
            index=OS_STATE_INDEX,
            body={
                "mappings": {
                    "properties": {"version": {"type": "integer"}, "applied_at": {"type": "date"}}
                }
            },
        )
        return set()
    return {h["_source"]["version"] for h in res["hits"]["hits"]}


async def apply_opensearch_migration(client, path: Path) -> None:
    version = parse_version(path)
    spec = json.loads(path.read_text())
    action = spec["action"]
    if action == "create_index":
        index = spec["index"]
        if not await client.indices.exists(index=index):
            await client.indices.create(index=index, body=spec["body"])
    elif action == "update_mapping":
        await client.indices.put_mapping(index=spec["index"], body=spec["body"])
    else:
        raise ValueError(f"Unknown migration action: {action}")
    await client.index(
        index=OS_STATE_INDEX,
        id=str(version),
        body={"version": version, "name": path.stem, "applied_at": datetime.utcnow().isoformat()},
        refresh=True,
    )
    print(f"[opensearch] V{version:03d} {path.stem} applied")


async def run_opensearch() -> None:
    settings = get_settings()
    client = make_opensearch_client(
        settings.opensearch_url, settings.opensearch_user, settings.opensearch_pass
    )
    try:
        applied = await applied_opensearch(client)
        files = sorted(OS_DIR.glob("V*.json"), key=parse_version)
        for f in files:
            v = parse_version(f)
            if v in applied:
                print(f"[opensearch] V{v:03d} skip (already applied)")
                continue
            await apply_opensearch_migration(client, f)
    finally:
        await client.close()


async def applied_neo4j(driver) -> set[int]:
    async with driver.session() as session:
        res = await session.run("MATCH (m:Migration) RETURN m.version AS v")
        return {rec["v"] async for rec in res}


async def apply_neo4j_migration(driver, path: Path) -> None:
    version = parse_version(path)
    statements = [s.strip() for s in path.read_text().split(";") if s.strip()]
    async with driver.session() as session:
        for stmt in statements:
            await session.run(stmt)
        await session.run(
            "CREATE (:Migration {version: $v, name: $n, applied_at: $t})",
            v=version,
            n=path.stem,
            t=datetime.utcnow().isoformat(),
        )
    print(f"[neo4j] V{version:03d} {path.stem} applied")


async def run_neo4j() -> None:
    settings = get_settings()
    driver = AsyncGraphDatabase.driver(
        settings.neo4j_url, auth=(settings.neo4j_user, settings.neo4j_pass)
    )
    try:
        applied = await applied_neo4j(driver)
        files = sorted(NEO_DIR.glob("V*.cypher"), key=parse_version)
        for f in files:
            v = parse_version(f)
            if v in applied:
                print(f"[neo4j] V{v:03d} skip (already applied)")
                continue
            await apply_neo4j_migration(driver, f)
    finally:
        await driver.close()


async def main() -> None:
    await run_opensearch()
    await run_neo4j()


if __name__ == "__main__":
    asyncio.run(main())
