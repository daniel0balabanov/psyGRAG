# Local Psychology Literature RAG

A local system for analyzing psychology literature powered by:
- Ollama + Gemma (generation)
- BGE-M3 (embeddings)
- ChromaDB (dense retrieval)
- BM25 (sparse retrieval)
- RRF + cross-encoder reranking (advanced RAG)

## 1) Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm install
npm run build:ui
```

## 2) Model Setup

1. Install and start Ollama.
2. Pull your Gemma model (set your tag via `PSY_OLLAMA_MODEL`).
3. Embedding and reranker models are downloaded automatically from Hugging Face on first run.

## 3) Environment Variables (example)

```bash
export PSY_OLLAMA_BASE_URL="http://127.0.0.1:11434"
export PSY_OLLAMA_MODEL="gemma4:e4b"
export PSY_PROFILE_NAME="balanced"
export PSY_OLLAMA_TIMEOUT_S=300
export PSY_OLLAMA_MAX_CONTINUATIONS=2
export PSY_EMBEDDING_DEVICE="cuda:1"
export PSY_RERANKER_DEVICE="cuda:1"
export PSY_OLLAMA_MAIN_GPU=1
export PSY_OLLAMA_NUM_GPU=1
```

## 4) Indexing the Corpus

Place files in `data/corpus` (supported formats: PDF, EPUB, DOCX, TXT, HTML).

```bash
python3 -m scripts.index_corpus --profile balanced --corpus-dir data/corpus
```

With URL sources:

```bash
python3 -m scripts.index_corpus --profile balanced --corpus-dir data/corpus --urls-file data/urls.txt
```

## 5) Starting the API

```bash
uvicorn app.api.main:app --host 0.0.0.0 --port 8000
```

The UI is available at `GET /` and served from `app/static/`.

### UI Development (TypeScript)

- UI source: `app/static/ui.ts`
- Compiled output: `app/static/ui.js`
- Styles and markup: `app/static/styles.css`, `app/static/index.html`

Rebuild the UI after making changes:

```bash
npm run build:ui
```

### Useful Endpoints
- `GET /health` — Ollama/Chroma health check.
- `POST /index/rebuild` — rebuild indexes.
- `POST /query` — question answering with citations.

`POST /query` accepts a `query` between 3 and 2000 characters.

## 6) Retrieval / Latency Evaluation

Prepare a JSONL dataset:

```json
{"query":"What are core signs of burnout?","expected_sources":["data/corpus/burnout.pdf"]}
```

Run:

```bash
python3 -m scripts.eval_retrieval --dataset data/eval.jsonl --profile balanced
```

Output: `recall_at_k`, `p50/p95 latency`, `faithfulness_proxy`.

Compare profiles:

```bash
python3 -m scripts.tune_profiles --dataset examples/eval_template.jsonl
```

## 7) Dual-GPU Recommendations

- For a two-GPU setup (slot 0: RTX 2060, slot 1: RTX 5070), keep the LLM, embeddings, and reranker on the RTX 5070 (`PSY_OLLAMA_MAIN_GPU=1`, `PSY_EMBEDDING_DEVICE=cuda:1`, `PSY_RERANKER_DEVICE=cuda:1`).
- If OOM: move the reranker to the RTX 2060 (`PSY_RERANKER_DEVICE=cuda:0`) or CPU (`PSY_RERANKER_DEVICE=cpu`).
