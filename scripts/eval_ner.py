import argparse
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "libs" / "common" / "src"))
sys.path.insert(0, str(ROOT / "services" / "nlp_worker" / "src"))

from news_common.models import EntityType  # noqa: E402
from nlp_worker.services.ner import NerService  # noqa: E402

DATA_DIR = ROOT / "data" / "factRuEval-2016"
REPO_URL = "https://github.com/dialogue-evaluation/factRuEval-2016.git"
METRICS_DIR = ROOT / "docs" / "metrics"

TYPE_MAP = {
    "Person": EntityType.PER,
    "Org": EntityType.ORG,
    "Location": EntityType.LOC,
    "LocOrg": EntityType.LOC,
    "Project": EntityType.ORG,
}


def ensure_corpus() -> None:
    if DATA_DIR.exists():
        return
    DATA_DIR.parent.mkdir(parents=True, exist_ok=True)
    print(f"cloning factRuEval-2016 → {DATA_DIR} ...", flush=True)
    subprocess.run(
        ["git", "clone", "--depth", "1", REPO_URL, str(DATA_DIR)],
        check=True,
    )


def parse_spans(path: Path) -> dict[int, tuple[int, int]]:
    out: dict[int, tuple[int, int]] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        parts = re.split(r"\s+", line)
        if len(parts) < 4:
            continue
        try:
            sid = int(parts[0])
            start = int(parts[2])
            length = int(parts[3])
        except ValueError:
            continue
        out[sid] = (start, start + length)
    return out


def parse_objects(
    path: Path, spans: dict[int, tuple[int, int]]
) -> list[tuple[EntityType, int, int]]:
    out: list[tuple[EntityType, int, int]] = []
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        head = line.split("#", 1)[0].strip()
        if not head:
            continue
        parts = re.split(r"\s+", head)
        if len(parts) < 3:
            continue
        raw_type = parts[1]
        etype = TYPE_MAP.get(raw_type)
        if etype is None:
            continue
        try:
            span_ids = [int(p) for p in parts[2:]]
        except ValueError:
            continue
        ranges = [spans[s] for s in span_ids if s in spans]
        if not ranges:
            continue
        start = min(r[0] for r in ranges)
        end = max(r[1] for r in ranges)
        out.append((etype, start, end))
    return out


def load_documents(split_dir: Path) -> list[tuple[str, list[tuple[EntityType, int, int]]]]:
    docs = []
    for txt in sorted(split_dir.glob("*.txt")):
        text = txt.read_text(encoding="utf-8")
        spans = parse_spans(txt.with_suffix(".spans"))
        gold = parse_objects(txt.with_suffix(".objects"), spans)
        docs.append((text, gold))
    return docs


def predict(ner: NerService, text: str) -> list[tuple[EntityType, int, int]]:
    return [(e.type, e.span_start, e.span_end) for e in ner.extract(text, post_id="eval")]


def score(
    gold_by_type: dict[EntityType, set],
    pred_by_type: dict[EntityType, set],
) -> dict[EntityType, dict[str, float]]:
    out: dict[EntityType, dict[str, float]] = {}
    for etype in (EntityType.PER, EntityType.ORG, EntityType.LOC):
        gold = gold_by_type.get(etype, set())
        pred = pred_by_type.get(etype, set())
        tp = len(gold & pred)
        fp = len(pred - gold)
        fn = len(gold - pred)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        out[etype] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "support": tp + fn,
        }
    return out


def aggregate_micro(per_type: dict[EntityType, dict[str, float]]) -> dict[str, float]:
    tp = sum(per_type[t]["tp"] for t in per_type)
    fp = sum(per_type[t]["fp"] for t in per_type)
    fn = sum(per_type[t]["fn"] for t in per_type)
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    return {"precision": p, "recall": r, "f1": 2 * p * r / (p + r) if (p + r) else 0.0}


def render_markdown(results: dict[str, dict], total_docs: int) -> str:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    lines = [
        "# NER evaluation on factRuEval-2016",
        "",
        f"Date: {today}  ",
        f"Documents evaluated: {total_docs}  ",
        "NER backend: Natasha (NewsNERTagger)  ",
        "Match policy: exact span match (entity-level)",
        "",
    ]
    for split, res in results.items():
        per_type = res["per_type"]
        micro = res["micro"]
        lines += [
            f"## {split}",
            "",
            "| Type | Precision | Recall | F1 | TP | FP | FN | Support |",
            "|------|-----------|--------|-----|-----|-----|-----|---------|",
        ]
        for etype, m in per_type.items():
            lines.append(
                f"| {etype.value} | {m['precision']:.3f} | {m['recall']:.3f} | {m['f1']:.3f} | "
                f"{m['tp']} | {m['fp']} | {m['fn']} | {m['support']} |"
            )
        lines += [
            "",
            f"**Micro-averaged:** precision={micro['precision']:.3f} "
            f"recall={micro['recall']:.3f} F1={micro['f1']:.3f}",
            "",
        ]
    return "\n".join(lines)


def evaluate_split(name: str, docs, ner: NerService, limit: int | None) -> dict:
    if limit:
        docs = docs[:limit]
    gold_total: dict[EntityType, set] = defaultdict(set)
    pred_total: dict[EntityType, set] = defaultdict(set)
    for i, (text, gold) in enumerate(docs):
        for etype, s, e in gold:
            gold_total[etype].add((i, s, e))
        for etype, s, e in predict(ner, text):
            pred_total[etype].add((i, s, e))
    per_type = score(gold_total, pred_total)
    return {"per_type": per_type, "micro": aggregate_micro(per_type), "n_docs": len(docs)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="Limit N documents per split")
    args = parser.parse_args()

    ensure_corpus()
    METRICS_DIR.mkdir(parents=True, exist_ok=True)

    ner = NerService()
    print("NerService loaded; evaluating...", flush=True)

    splits = [
        ("devset", DATA_DIR / "devset"),
        ("testset", DATA_DIR / "testset"),
    ]

    results: dict[str, dict] = {}
    total_docs = 0
    for name, path in splits:
        if not path.exists():
            print(f"skip {name}: directory missing")
            continue
        docs = load_documents(path)
        print(f"{name}: {len(docs)} documents")
        results[name] = evaluate_split(name, docs, ner, args.limit)
        total_docs += results[name]["n_docs"]

    md = render_markdown(results, total_docs)
    out_path = METRICS_DIR / f"ner_{datetime.utcnow().strftime('%Y-%m-%d')}.md"
    out_path.write_text(md, encoding="utf-8")
    print(f"\nwritten to {out_path}\n")
    print(md)


if __name__ == "__main__":
    main()
