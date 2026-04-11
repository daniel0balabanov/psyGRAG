from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

from app.models import Document


YEAR_RE = re.compile(r"(19|20)\d{2}")


def infer_year(text: str, fallback: str = "") -> int | None:
    sample = f"{fallback}\n{text[:1200]}"
    match = YEAR_RE.search(sample)
    if not match:
        return None
    return int(match.group(0))


def infer_source_name(source: str) -> str:
    if source.startswith("http://") or source.startswith("https://"):
        parsed = urlparse(source)
        return parsed.netloc
    return Path(source).name


def normalize_document_metadata(document: Document) -> Document:
    metadata = dict(document.metadata or {})
    metadata["source_name"] = infer_source_name(document.source)
    metadata["char_count"] = len(document.text)
    metadata["word_count"] = len(document.text.split())
    metadata.setdefault("domain", "psychology")

    if document.year is None:
        year = infer_year(document.text, fallback=document.title or "")
    else:
        year = document.year

    return Document(
        doc_id=document.doc_id,
        text=document.text,
        source=document.source,
        title=document.title,
        author=document.author,
        year=year,
        topic=document.topic,
        metadata=metadata,
    )
