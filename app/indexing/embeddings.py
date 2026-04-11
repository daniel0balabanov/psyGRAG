from __future__ import annotations

from typing import Iterable

from sentence_transformers import SentenceTransformer


class EmbeddingService:
    def __init__(self, model_name: str, device: str, batch_size: int = 16) -> None:
        self.model = SentenceTransformer(model_name, device=device)
        self.batch_size = batch_size

    def embed_texts(self, texts: Iterable[str]) -> list[list[float]]:
        vectors = self.model.encode(
            list(texts),
            batch_size=self.batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return vectors.tolist()

    def embed_query(self, text: str) -> list[float]:
        vector = self.model.encode(text, normalize_embeddings=True, show_progress_bar=False)
        return vector.tolist()
