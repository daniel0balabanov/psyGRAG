from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.pipeline.query_pipeline import QueryPipeline


def _run_profile(dataset: list[dict], profile: str) -> dict:
    settings.profile_name = profile
    pipeline = QueryPipeline()
    latencies: list[float] = []
    recall_hits = 0

    for row in dataset:
        started = time.perf_counter()
        result = pipeline.answer(row["query"])
        latencies.append(time.perf_counter() - started)
        expected = set(row.get("expected_sources", []))
        got = {c["source"] for c in result["citations"]}
        if expected and expected.intersection(got):
            recall_hits += 1

    count = len(dataset) or 1
    p95 = sorted(latencies)[int(max(0, len(latencies) * 0.95) - 1)] if latencies else 0.0
    return {
        "profile": profile,
        "queries": len(dataset),
        "recall_at_k": recall_hits / count,
        "mean_latency_sec": statistics.fmean(latencies) if latencies else 0.0,
        "p95_latency_sec": p95,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare retrieval profiles on one dataset")
    parser.add_argument("--dataset", required=True, help="jsonl path with query + expected_sources")
    args = parser.parse_args()

    dataset = [
        json.loads(line)
        for line in Path(args.dataset).read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    reports = [_run_profile(dataset, profile) for profile in ("fast", "balanced", "quality")]
    print(json.dumps(reports, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
