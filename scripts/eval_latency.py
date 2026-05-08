"""Measure API endpoint latency (p50 / p95 / p99) on a live deployment.

Hits each endpoint N times sequentially and computes percentiles. Run against
local dev (default http://localhost:8000) or production
(--base-url https://news.example/api).

Usage:
    uv run python scripts/eval_latency.py [--n 200] [--base-url URL]
"""

from __future__ import annotations

import argparse
import contextlib
import statistics
import time
from datetime import datetime
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
METRICS_DIR = ROOT / "docs" / "metrics"


ENDPOINTS = [
    ("GET /health", lambda c, base: c.get(f"{base}/health")),
    ("GET /stats", lambda c, base: c.get(f"{base}/stats")),
    (
        "GET /search?q=Россия",
        lambda c, base: c.get(f"{base}/search", params={"q": "Россия", "size": 20}),
    ),
    (
        "GET /top_entities?etype=ORG",
        lambda c, base: c.get(f"{base}/top_entities", params={"etype": "ORG", "size": 20}),
    ),
    (
        "GET /graph/subgraph?entity=Москва",
        lambda c, base: c.get(f"{base}/graph/subgraph", params={"entity": "Москва", "limit": 50}),
    ),
]


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    idx = min(len(s) - 1, max(0, round((p / 100) * (len(s) - 1))))
    return s[idx]


def measure(client: httpx.Client, name: str, fn, base: str, n: int) -> dict:
    samples: list[float] = []
    errors = 0
    for _ in range(n):
        t0 = time.perf_counter()
        try:
            r = fn(client, base)
            r.raise_for_status()
        except Exception:
            errors += 1
            continue
        samples.append((time.perf_counter() - t0) * 1000)
    return {
        "name": name,
        "n": n,
        "ok": len(samples),
        "errors": errors,
        "p50": percentile(samples, 50),
        "p95": percentile(samples, 95),
        "p99": percentile(samples, 99),
        "mean": statistics.fmean(samples) if samples else 0.0,
        "min": min(samples) if samples else 0.0,
        "max": max(samples) if samples else 0.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=200, help="Requests per endpoint")
    parser.add_argument("--base-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--warmup", type=int, default=5, help="Warmup requests per endpoint")
    args = parser.parse_args()

    METRICS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Probing {args.base_url} with N={args.n} per endpoint...", flush=True)
    rows: list[dict] = []
    with httpx.Client(timeout=15) as client:
        for name, fn in ENDPOINTS:
            print(f"  warmup {name}...", flush=True)
            for _ in range(args.warmup):
                with contextlib.suppress(Exception):
                    fn(client, args.base_url)
            print(f"  measuring {name}...", flush=True)
            rows.append(measure(client, name, fn, args.base_url, args.n))

    md_lines = [
        "# API endpoint latency",
        "",
        f"Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}  ",
        f"Base URL: {args.base_url}  ",
        f"Requests per endpoint: {args.n} (after {args.warmup} warmup)",
        "",
        "| Endpoint | OK / N | mean (ms) | p50 (ms) | p95 (ms) | p99 (ms) | min | max |",
        "|----------|--------|-----------|----------|----------|----------|-----|-----|",
    ]
    for r in rows:
        md_lines.append(
            f"| `{r['name']}` | {r['ok']}/{r['n']} | {r['mean']:.1f} | {r['p50']:.1f} | "
            f"{r['p95']:.1f} | {r['p99']:.1f} | {r['min']:.1f} | {r['max']:.1f} |"
        )
    if any(r["errors"] for r in rows):
        md_lines += [
            "",
            "Errors observed:",
            *[f"- {r['name']}: {r['errors']} failed" for r in rows if r["errors"]],
        ]
    md = "\n".join(md_lines)
    out = METRICS_DIR / f"latency_{datetime.utcnow().strftime('%Y-%m-%d')}.md"
    out.write_text(md, encoding="utf-8")
    print(f"\nwritten to {out}\n")
    print(md)


if __name__ == "__main__":
    main()
