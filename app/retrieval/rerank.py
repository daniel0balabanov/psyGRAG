from __future__ import annotations

from sentence_transformers import CrossEncoder

from app.models import RetrievalHit


class Reranker:
    def __init__(self, model_name: str, device: str) -> None:
        self.model = CrossEncoder(model_name, device=device)

    def rerank(self, query: str, hits: list[RetrievalHit], top_n: int) -> list[RetrievalHit]:
        if not hits:
            return []
        pairs = [(query, hit.text) for hit in hits]
        scores = self.model.predict(pairs).tolist()
        rescored: list[RetrievalHit] = []
        for hit, score in zip(hits, scores, strict=True):
            rescored.append(
                RetrievalHit(
                    chunk_id=hit.chunk_id,
                    score=float(score),
                    text=hit.text,
                    source=hit.source,
                    title=hit.title,
                    metadata=hit.metadata,
                )
            )
        rescored.sort(key=lambda item: item.score, reverse=True)
        return rescored[:top_n]
