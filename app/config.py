from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RetrievalProfile(BaseModel):
    chunk_size: int
    chunk_overlap: int
    dense_top_k: int
    sparse_top_k: int
    rerank_top_n: int
    final_context_chunks: int
    max_context_chars: int


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PSY_", extra="ignore", env_file=".env", env_file_encoding="utf-8")

    app_name: str = "psy-rag"
    data_dir: Path = Path("data")
    corpus_dir: Path = Path("data/corpus")
    chroma_dir: Path = Path("data/chroma")
    bm25_index_path: Path = Path("data/bm25/index.pkl")

    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "gemma4:12b"
    ollama_num_ctx: int = 16384
    ollama_temperature: float = 0.1
    ollama_num_predict: int = 3000
    ollama_num_predict_focused: int = 1500
    ollama_timeout_s: float = 180.0
    ollama_max_continuations: int = 3
    ollama_main_gpu: int = 1
    ollama_num_gpu: int = 1

    embedding_model_name: str = "BAAI/bge-m3"
    embedding_device: str = "cuda:0"
    indexing_embedding_device: str = "cuda:1"
    embedding_batch_size: int = 16

    reranker_enabled: bool = True
    reranker_model_name: str = "BAAI/bge-reranker-v2-m3"
    reranker_device: str = "cuda:1"

    profile_name: str = "balanced"

    profiles: dict[str, RetrievalProfile] = Field(
        default_factory=lambda: {
            "fast": RetrievalProfile(
                chunk_size=650,
                chunk_overlap=70,
                dense_top_k=10,
                sparse_top_k=10,
                rerank_top_n=8,
                final_context_chunks=4,
                max_context_chars=7000,
            ),
            "balanced": RetrievalProfile(
                chunk_size=850,
                chunk_overlap=120,
                dense_top_k=18,
                sparse_top_k=18,
                rerank_top_n=14,
                final_context_chunks=6,
                max_context_chars=10000,
            ),
            "quality": RetrievalProfile(
                chunk_size=1000,
                chunk_overlap=160,
                dense_top_k=26,
                sparse_top_k=24,
                rerank_top_n=20,
                final_context_chunks=8,
                max_context_chars=14000,
            ),
        }
    )

    @property
    def profile(self) -> RetrievalProfile:
        if self.profile_name not in self.profiles:
            raise ValueError(f"Unknown profile: {self.profile_name}")
        return self.profiles[self.profile_name]

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.corpus_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.bm25_index_path.parent.mkdir(parents=True, exist_ok=True)


settings = Settings()
