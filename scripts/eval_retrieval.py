from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.pipeline.query_pipeline import QueryPipeline


def _token_overlap_ratio(answer: str, context_texts: list[str]) -> float:
    answer_tokens = set(answer.lower().split())
    if not answer_tokens:
        return 0.0
    context_tokens = set(" ".join(context_texts).lower().split())
    return len(answer_tokens & context_tokens) / len(answer_tokens)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate retrieval/generation performance")
    parser.add_argument("--dataset", required=True, help="Path to jsonl with {query, expected_sources[]}")
    parser.add_argument("--profile", choices=["fast", "balanced", "quality"], default=settings.profile_name)
    args = parser.parse_args()

    settings.profile_name = args.profile
    pipeline = QueryPipeline()

    rows = [json.loads(line) for line in Path(args.dataset).read_text(encoding="utf-8").splitlines() if line.strip()]
    recall_hits = 0
    latencies: list[float] = []
    faithfulness_scores: list[float] = []

    for row in rows:
        query = row["query"]
        expected_sources = set(row.get("expected_sources", []))

        started = time.perf_counter()
        result = pipeline.answer(query)
        elapsed = time.perf_counter() - started
        latencies.append(elapsed)

        got_sources = {citation["source"] for citation in result["citations"]}
        if expected_sources and (got_sources & expected_sources):
            recall_hits += 1

        # Heuristic faithfulness proxy: token overlap answer vs retrieved context snippets.
        faithfulness_scores.append(
            _token_overlap_ratio(result["answer"], [c.get("text", "") for c in result["citations"]])
        )

    total = len(rows) or 1
    report = {
        "profile": settings.profile_name,
        "queries": len(rows),
        "recall_at_k": recall_hits / total,
        "p50_latency_sec": sorted(latencies)[len(latencies) // 2] if latencies else 0.0,
        "p95_latency_sec": sorted(latencies)[int(max(0, len(latencies) * 0.95) - 1)] if latencies else 0.0,
        "faithfulness_proxy": sum(faithfulness_scores) / len(faithfulness_scores) if faithfulness_scores else 0.0,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
