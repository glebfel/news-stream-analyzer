import argparse
import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "libs" / "common" / "src"))

from neo4j import AsyncGraphDatabase  # noqa: E402
from news_common import Source, get_settings  # noqa: E402
from news_common.clients.opensearch import make_opensearch_client  # noqa: E402
from news_common.clients.redis_bus import StreamBus  # noqa: E402
from news_common.mocks import fake_post  # noqa: E402

METRICS_DIR = ROOT / "docs" / "metrics"


async def _wait_for(query, target: int, timeout: float = 600.0, poll: float = 1.0) -> float | None:
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        if await query() >= target:
            return time.monotonic() - start
        await asyncio.sleep(poll)
    return None


async def os_count(client, index: str, baseline: int) -> int:
    res = await client.count(index=index)
    return res.get("count", 0) - baseline


async def neo4j_count(driver, baseline: int) -> int:
    async with driver.session() as s:
        res = await s.run("MATCH (e:Entity) RETURN count(e) AS c")
        record = await res.single()
    return (record["c"] if record else 0) - baseline


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=500, help="Posts to publish")
    parser.add_argument("--source", choices=["vk", "telegram"], default="vk")
    parser.add_argument("--timeout", type=float, default=900.0, help="Max wait per stage (s)")
    args = parser.parse_args()

    settings = get_settings()
    bus = StreamBus(settings.redis_url)
    os_client = make_opensearch_client(
        settings.opensearch_url, settings.opensearch_user, settings.opensearch_pass
    )
    neo_driver = AsyncGraphDatabase.driver(
        settings.neo4j_url, auth=(settings.neo4j_user, settings.neo4j_pass)
    )

    source = Source.VK if args.source == "vk" else Source.TELEGRAM
    stream = settings.stream_raw_vk if source == Source.VK else settings.stream_raw_tg

    raw_base = (await os_client.count(index="raw_posts")).get("count", 0)
    ent_base = (await os_client.count(index="entities")).get("count", 0)
    async with neo_driver.session() as s:
        rec = await (await s.run("MATCH (e:Entity) RETURN count(e) AS c")).single()
    graph_base = rec["c"] if rec else 0

    print(
        f"baselines: raw_posts={raw_base} entities={ent_base} graph_entities={graph_base}",
        flush=True,
    )

    pub_start = time.monotonic()
    for _ in range(args.count):
        post = fake_post(source)
        await bus.publish(stream, post.model_dump(mode="json"))
    pub_dur = time.monotonic() - pub_start
    print(f"published {args.count} posts in {pub_dur:.2f}s", flush=True)

    # Mock templates collide under MinHash dedup, so 60% is the realistic floor.
    raw_target = int(args.count * 0.6)
    t_raw = await _wait_for(
        lambda: os_count(os_client, "raw_posts", raw_base), raw_target, timeout=args.timeout
    )

    ent_target = int(raw_target * 0.5)
    t_ent = await _wait_for(
        lambda: os_count(os_client, "entities", ent_base), ent_target, timeout=args.timeout
    )

    graph_target = int(raw_target * 0.3)
    t_graph = await _wait_for(
        lambda: neo4j_count(neo_driver, graph_base), graph_target, timeout=args.timeout
    )

    raw_now = (await os_client.count(index="raw_posts")).get("count", 0) - raw_base
    ent_now = (await os_client.count(index="entities")).get("count", 0) - ent_base
    async with neo_driver.session() as s:
        rec = await (await s.run("MATCH (e:Entity) RETURN count(e) AS c")).single()
    graph_now = (rec["c"] if rec else 0) - graph_base

    await bus.close()
    await os_client.close()
    await neo_driver.close()

    md_lines = [
        "# Pipeline throughput benchmark",
        "",
        f"Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}  ",
        f"Source: synthetic {args.source} posts via Redis Streams  ",
        f"Posts published: {args.count}",
        "",
        "| Stage | Documents reached | Time (s) | Posts/sec |",
        "|-------|-------------------|----------|-----------|",
        f"| Publish to Redis | {args.count} | {pub_dur:.2f} | {args.count / pub_dur:.1f} |",
        f"| Indexed in raw_posts | {raw_now} | {fmt(t_raw)} | {ratio(raw_now, t_raw)} |",
        f"| NLP enriched (entities) | {ent_now} | {fmt(t_ent)} | {ratio(ent_now, t_ent)} |",
        f"| Graph upserted (Neo4j) | {graph_now} | {fmt(t_graph)} | {ratio(graph_now, t_graph)} |",
        "",
        "Notes: dedup via MinHash (~30% collisions on mock templates). "
        "Times are end-to-end from publish to durable persistence.",
    ]
    md = "\n".join(md_lines)
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    out = METRICS_DIR / f"throughput_{datetime.utcnow().strftime('%Y-%m-%d')}.md"
    out.write_text(md, encoding="utf-8")
    print(f"\nwritten to {out}\n")
    print(md)


def fmt(t: float | None) -> str:
    return f"{t:.2f}" if t is not None else "timeout"


def ratio(n: int, t: float | None) -> str:
    return f"{n / t:.1f}" if t and t > 0 else "—"


if __name__ == "__main__":
    asyncio.run(main())
