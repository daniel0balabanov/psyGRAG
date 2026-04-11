from __future__ import annotations

from pathlib import Path
from typing import Iterable
import logging

from app.ingest.metadata import normalize_document_metadata
from app.ingest.parsers import iter_supported_files, parse_path, parse_web_article
from app.models import Document

logger = logging.getLogger(__name__)


def ingest_local_corpus(corpus_dir: Path) -> list[Document]:
    documents: list[Document] = []
    for path in iter_supported_files(corpus_dir):
        try:
            parsed = parse_path(path)
            normalized = normalize_document_metadata(parsed)
            if normalized.text.strip():
                documents.append(normalized)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Skipping unreadable file %s: %s", path, exc)
    return documents


def ingest_urls(urls: Iterable[str]) -> list[Document]:
    documents: list[Document] = []
    for url in urls:
        try:
            parsed = parse_web_article(url)
            normalized = normalize_document_metadata(parsed)
            if normalized.text.strip():
                documents.append(normalized)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Skipping unreadable url %s: %s", url, exc)
    return documents
