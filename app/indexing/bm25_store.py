from __future__ import annotations

import pickle
import re
from dataclasses import dataclass
from pathlib import Path

from rank_bm25 import BM25Okapi

from app.models import Chunk, RetrievalHit


TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


@dataclass(slots=True)
class BM25Payload:
    corpus_tokens: list[list[str]]
    chunks: list[Chunk]


class BM25Store:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._bm25: BM25Okapi | None = None
        self._chunks: list[Chunk] = []
        self._corpus_tokens: list[list[str]] = []

    def build(self, chunks: list[Chunk]) -> None:
        tokens = [_tokenize(chunk.text) for chunk in chunks]
        self._bm25 = BM25Okapi(tokens)
        self._chunks = chunks
        self._corpus_tokens = tokens

    def save(self) -> None:
        if self._bm25 is None:
            raise RuntimeError("BM25 index is not built")
        payload = BM25Payload(corpus_tokens=self._corpus_tokens, chunks=self._chunks)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("wb") as file:
            pickle.dump(payload, file)

    def load(self) -> None:
        with self.path.open("rb") as file:
            payload: BM25Payload = pickle.load(file)  # noqa: S301
        self._bm25 = BM25Okapi(payload.corpus_tokens)
        self._chunks = payload.chunks
        self._corpus_tokens = payload.corpus_tokens

    def query(self, text: str, top_k: int) -> list[RetrievalHit]:
        if self._bm25 is None:
            raise RuntimeError("BM25 index is not available")
        query_tokens = _tokenize(text)
        scores = self._bm25.get_scores(query_tokens)
        ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)[:top_k]
        hits: list[RetrievalHit] = []
        for idx, score in ranked:
            chunk = self._chunks[idx]
            hits.append(
                RetrievalHit(
                    chunk_id=chunk.chunk_id,
                    score=float(score),
                    text=chunk.text,
                    source=chunk.source,
                    title=chunk.title,
                    metadata=chunk.metadata,
                )
            )
        return hits
