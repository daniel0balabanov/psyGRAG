from __future__ import annotations

from chromadb import PersistentClient

from app.models import Chunk, RetrievalHit


def _sanitize_metadata(raw: dict | None) -> dict:
    if not raw:
        return {}
    clean: dict = {}
    for key, value in raw.items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            clean[str(key)] = value
        else:
            clean[str(key)] = str(value)
    return clean


class ChromaStore:
    def __init__(self, path: str, collection_name: str = "psych_literature") -> None:
        self.client = PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(name=collection_name)

    _CHROMA_MAX_BATCH = 5000

    def add_chunks(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        if not chunks:
            return
        ids = [chunk.chunk_id for chunk in chunks]
        documents = [chunk.text for chunk in chunks]
        metadatas = [
            {
                "doc_id": chunk.doc_id,
                "source": chunk.source,
                "title": chunk.title or "",
                **_sanitize_metadata(chunk.metadata),
            }
            for chunk in chunks
        ]
        for start in range(0, len(chunks), self._CHROMA_MAX_BATCH):
            end = start + self._CHROMA_MAX_BATCH
            self.collection.add(
                ids=ids[start:end],
                documents=documents[start:end],
                metadatas=metadatas[start:end],
                embeddings=embeddings[start:end],
            )

    def query(self, embedding: list[float], top_k: int) -> list[RetrievalHit]:
        result = self.collection.query(query_embeddings=[embedding], n_results=top_k)
        ids = result.get("ids", [[]])[0]
        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        hits: list[RetrievalHit] = []
        for idx, chunk_id in enumerate(ids):
            metadata = metas[idx] if idx < len(metas) else {}
            distance = float(distances[idx]) if idx < len(distances) else 1.0
            hits.append(
                RetrievalHit(
                    chunk_id=chunk_id,
                    score=1.0 - distance,
                    text=docs[idx],
                    source=str(metadata.get("source", "")),
                    title=str(metadata.get("title", "")) or None,
                    metadata=metadata,
                )
            )
        return hits
