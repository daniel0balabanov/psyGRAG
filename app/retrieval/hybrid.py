from __future__ import annotations

from collections import defaultdict

from app.models import RetrievalHit


def reciprocal_rank_fusion(
    ranked_lists: list[list[RetrievalHit]],
    rrf_k: int = 60,
) -> list[RetrievalHit]:
    score_map: dict[str, float] = defaultdict(float)
    hit_map: dict[str, RetrievalHit] = {}

    for ranked_hits in ranked_lists:
        for rank, hit in enumerate(ranked_hits, start=1):
            score_map[hit.chunk_id] += 1.0 / (rrf_k + rank)
            hit_map[hit.chunk_id] = hit

    fused = sorted(score_map.items(), key=lambda item: item[1], reverse=True)
    results: list[RetrievalHit] = []
    for chunk_id, score in fused:
        base_hit = hit_map[chunk_id]
        results.append(
            RetrievalHit(
                chunk_id=chunk_id,
                score=score,
                text=base_hit.text,
                source=base_hit.source,
                title=base_hit.title,
                metadata=base_hit.metadata,
            )
        )
    return results
