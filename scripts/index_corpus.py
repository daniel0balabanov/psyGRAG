from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.ingest.service import ingest_local_corpus, ingest_urls
from app.pipeline.index_pipeline import IndexPipeline


def read_urls(path: Path) -> list[str]:
    if not path.exists():
        return []
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    return [line for line in lines if line and not line.startswith("#")]


def main() -> None:
    parser = argparse.ArgumentParser(description="Index psychology literature corpus")
    parser.add_argument("--corpus-dir", default=str(settings.corpus_dir))
    parser.add_argument("--urls-file", default="")
    parser.add_argument("--profile", choices=["fast", "balanced", "quality"], default=settings.profile_name)
    args = parser.parse_args()

    settings.profile_name = args.profile
    corpus_dir = Path(args.corpus_dir)
    local_documents = ingest_local_corpus(corpus_dir)

    web_documents = []
    if args.urls_file:
        urls = read_urls(Path(args.urls_file))
        web_documents = ingest_urls(urls)

    documents = local_documents + web_documents
    pipeline = IndexPipeline()
    stats = pipeline.build_indexes(documents)

    print(
        f"Indexed {stats['documents']} documents into {stats['chunks']} chunks "
        f"(profile={settings.profile_name})."
    )


if __name__ == "__main__":
    main()
