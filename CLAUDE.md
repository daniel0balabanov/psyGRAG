# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Common Commands

**Start the API server:**
```bash
uvicorn app.api.main:app --host 0.0.0.0 --port 8000
```

**Index corpus documents:**
```bash
python3 -m scripts.index_corpus --profile balanced --corpus-dir data/corpus
# With web sources:
python3 -m scripts.index_corpus --profile balanced --corpus-dir data/corpus --urls-file data/urls.txt
```

**Evaluate retrieval quality:**
```bash
python3 -m scripts.eval_retrieval --dataset data/eval.jsonl --profile balanced
```

**Compare retrieval profiles:**
```bash
python3 -m scripts.tune_profiles --dataset examples/eval_template.jsonl
```

## Architecture

The system is a local RAG pipeline for psychology literature with two main workflows: **indexing** and **querying**.

### Indexing flow
`scripts/index_corpus.py` → `ingest/service.py` (parse files/URLs) → `ingest/chunker.py` (split into `Chunk` objects) → `IndexPipeline` (`app/pipeline/index_pipeline.py`) → writes to ChromaDB (dense vectors via `BAAI/bge-m3`) + BM25 pickle file.

### Query flow
`POST /query` → `QueryPipeline.answer()` (`app/pipeline/query_pipeline.py`):
1. Embed query with `EmbeddingService` (`BAAI/bge-m3`, `cuda:0` by default)
2. Dense retrieval from ChromaDB
3. Sparse retrieval from BM25Store (lazy-loaded)
4. Reciprocal Rank Fusion (`app/retrieval/hybrid.py`)
5. Cross-encoder reranking (`BAAI/bge-reranker-v2-m3`, `cuda:1`) via `app/retrieval/rerank.py`
6. Prompt construction + Ollama generation (`gemma4:e4b`)
7. Auto-retry with shorter context if empty response; fallback to sources-only answer

### Key modules
- `app/config.py` — `Settings` (env prefix `PSY_`), three built-in `RetrievalProfile`s: `fast`, `balanced`, `quality`
- `app/models.py` — `Document`, `Chunk`, `RetrievalHit` dataclasses
- `app/ingest/parsers.py` — PDF, EPUB, DOCX, TXT, HTML, and web URL parsing
- `app/indexing/` — `EmbeddingService`, `ChromaStore`, `BM25Store`
- `app/generation/ollama_client.py` — Ollama HTTP client with continuation support

### Data layout
- `data/corpus/` — source documents (PDF, EPUB, DOCX, TXT, HTML)
- `data/chroma/` — ChromaDB persistent storage
- `data/bm25/index.pkl` — serialized BM25 index
- `examples/eval_template.jsonl` — template for evaluation datasets

## Configuration

All settings use the `PSY_` env prefix (or `.env` file). Key variables:

| Variable | Default | Purpose |
|---|---|---|
| `PSY_OLLAMA_MODEL` | `gemma4-12b-128k:latest` | LLM model tag |
| `PSY_PROFILE_NAME` | `balanced` | Retrieval profile |
| `PSY_EMBEDDING_DEVICE` | `cuda:0` | GPU for query-time embeddings |
| `PSY_INDEXING_EMBEDDING_DEVICE` | `cuda:1` | GPU for indexing embeddings |
| `PSY_RERANKER_DEVICE` | `cuda:1` | GPU for cross-encoder reranker |
| `PSY_OLLAMA_MAIN_GPU` | `1` | Ollama primary GPU index |

## Dual-GPU Setup (RTX 2060 + RTX 5070)

- `cuda:0` = RTX 2060 (query-time embeddings)
- `cuda:1` = RTX 5070 (indexing embeddings, reranker, Ollama LLM)
- If OOM: move reranker to `cuda:0` or `cpu` via `PSY_RERANKER_DEVICE`
- Disable reranker entirely with `PSY_RERANKER_ENABLED=false`

## API Endpoints

- `GET /` — web UI
- `GET /health` — Ollama + ChromaDB health check
- `POST /query` — `{"query": "..."}` → answer with citations and debug timings
- `POST /index/rebuild` — `{"corpus_dir": "...", "urls": [...], "profile": "..."}` → rebuild indexes
