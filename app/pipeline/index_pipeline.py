from __future__ import annotations

from app.config import settings
from app.indexing.bm25_store import BM25Store
from app.indexing.chroma_store import ChromaStore
from app.indexing.embeddings import EmbeddingService
from app.ingest.chunker import chunk_document
from app.models import Document


class IndexPipeline:
    def __init__(self) -> None:
        settings.ensure_dirs()
        self.profile = settings.profile
        self.embedding_service = EmbeddingService(
            model_name=settings.embedding_model_name,
            device=settings.indexing_embedding_device,
            batch_size=settings.embedding_batch_size,
        )
        self.chroma_store = ChromaStore(path=str(settings.chroma_dir))
        self.bm25_store = BM25Store(path=settings.bm25_index_path)

    def build_indexes(self, documents: list[Document]) -> dict:
        all_chunks = []
        for document in documents:
            chunks = chunk_document(
                document,
                chunk_size=self.profile.chunk_size,
                chunk_overlap=self.profile.chunk_overlap,
            )
            all_chunks.extend(chunks)

        if not all_chunks:
            return {"documents": len(documents), "chunks": 0}

        embeddings = self.embedding_service.embed_texts([chunk.text for chunk in all_chunks])
        self.chroma_store.add_chunks(all_chunks, embeddings)

        self.bm25_store.build(all_chunks)
        self.bm25_store.save()

        return {"documents": len(documents), "chunks": len(all_chunks)}
