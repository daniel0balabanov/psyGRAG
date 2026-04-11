from __future__ import annotations

import hashlib
import re

from app.models import Chunk, Document


SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def _chunk_id(doc_id: str, idx: int) -> str:
    return hashlib.sha256(f"{doc_id}:{idx}".encode("utf-8")).hexdigest()[:20]


def chunk_document(document: Document, chunk_size: int, chunk_overlap: int) -> list[Chunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap must be >= 0")

    sentences = [s.strip() for s in SENTENCE_SPLIT_RE.split(document.text) if s.strip()]
    if not sentences:
        return []

    chunks: list[Chunk] = []
    current: list[str] = []
    current_len = 0
    idx = 0

    for sentence in sentences:
        sentence_len = len(sentence)
        if current and current_len + sentence_len + 1 > chunk_size:
            text = " ".join(current).strip()
            chunks.append(
                Chunk(
                    chunk_id=_chunk_id(document.doc_id, idx),
                    doc_id=document.doc_id,
                    text=text,
                    source=document.source,
                    title=document.title,
                    metadata={
                        **(document.metadata or {}),
                        "chunk_index": idx,
                        "year": document.year,
                        "author": document.author,
                        "topic": document.topic,
                    },
                )
            )
            idx += 1
            if chunk_overlap > 0:
                overlap_chars = 0
                overlap_sentences: list[str] = []
                for prev in reversed(current):
                    overlap_chars += len(prev) + 1
                    overlap_sentences.append(prev)
                    if overlap_chars >= chunk_overlap:
                        break
                current = list(reversed(overlap_sentences))
                current_len = sum(len(s) for s in current) + max(0, len(current) - 1)
            else:
                current = []
                current_len = 0

        current.append(sentence)
        current_len += sentence_len + 1

    if current:
        text = " ".join(current).strip()
        chunks.append(
            Chunk(
                chunk_id=_chunk_id(document.doc_id, idx),
                doc_id=document.doc_id,
                text=text,
                source=document.source,
                title=document.title,
                metadata={
                    **(document.metadata or {}),
                    "chunk_index": idx,
                    "year": document.year,
                    "author": document.author,
                    "topic": document.topic,
                },
            )
        )

    return chunks
