from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class Document:
    doc_id: str
    text: str
    source: str
    title: str | None = None
    author: str | None = None
    year: int | None = None
    topic: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(slots=True)
class Chunk:
    chunk_id: str
    doc_id: str
    text: str
    source: str
    title: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(slots=True)
class RetrievalHit:
    chunk_id: str
    score: float
    text: str
    source: str
    title: str | None = None
    metadata: dict[str, Any] | None = None
