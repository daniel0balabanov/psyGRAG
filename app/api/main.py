from __future__ import annotations

import logging
from pathlib import Path
import time

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.config import settings
from app.generation.ollama_client import OllamaClient
from app.health import run_health_checks
from app.ingest.service import ingest_local_corpus, ingest_urls
from app.pipeline.index_pipeline import IndexPipeline
from app.pipeline.query_pipeline import QueryPipeline


logger = logging.getLogger(__name__)


class QueryRequest(BaseModel):
    query: str = Field(min_length=3, max_length=2000)


class QueryResponse(BaseModel):
    overview: str
    self_help: str
    therapist: str
    citations: list[dict]
    debug: dict


class ReindexRequest(BaseModel):
    corpus_dir: str | None = None
    urls: list[str] = Field(default_factory=list)
    profile: str | None = None


app = FastAPI(title="Psychology Literature RAG")
pipeline: QueryPipeline | None = None
static_dir = Path(__file__).resolve().parent.parent / "static"


@app.on_event("startup")
def startup() -> None:
    settings.ensure_dirs()
    OllamaClient(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        num_ctx=settings.ollama_num_ctx,
        temperature=settings.ollama_temperature,
        num_predict=settings.ollama_num_predict,
        timeout_s=settings.ollama_timeout_s,
        max_continuations=settings.ollama_max_continuations,
        main_gpu=settings.ollama_main_gpu,
        num_gpu=settings.ollama_num_gpu,
    ).warmup()


app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/health")
def health() -> dict:
    return run_health_checks().to_dict()


@app.get("/", response_class=FileResponse)
def ui() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.post("/index/rebuild")
def rebuild_index(payload: ReindexRequest) -> dict:
    global pipeline
    if payload.profile is not None:
        if payload.profile not in settings.profiles:
            raise HTTPException(status_code=400, detail=f"Unknown profile: {payload.profile}")
        settings.profile_name = payload.profile

    corpus_path = settings.corpus_dir if payload.corpus_dir is None else Path(payload.corpus_dir)
    local_documents = ingest_local_corpus(corpus_path)
    web_documents = ingest_urls(payload.urls)
    pipeline_index = IndexPipeline()
    stats = pipeline_index.build_indexes(local_documents + web_documents)
    pipeline = None
    return {"status": "ok", "indexed": stats, "profile": settings.profile_name}


@app.post("/query", response_model=QueryResponse)
def query(payload: QueryRequest) -> QueryResponse:
    global pipeline
    started = time.perf_counter()
    logger.warning("api /query started (query_chars=%s)", len(payload.query))
    try:
        if pipeline is None:
            pipeline = QueryPipeline()
        result = pipeline.answer(payload.query)
        logger.info(
            "api /query completed in %.3fs (query_chars=%s)",
            time.perf_counter() - started,
            len(payload.query),
        )
        return QueryResponse(**result)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"BM25 index not found. Run indexing first: {exc}",
        ) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("api /query failed after %.3fs", time.perf_counter() - started)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
