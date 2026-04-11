# Local Psychology Literature RAG

Локальная система анализа психологической литературы на базе:
- Ollama + Gemma (генерация),
- BGE-M3 (эмбеддинги),
- ChromaDB (dense retrieval),
- BM25 (sparse retrieval),
- RRF + cross-encoder reranking (advanced RAG).

## 1) Установка

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm install
npm run build:ui
```

## 2) Подготовка моделей

1. Установите и запустите Ollama.
2. Загрузите модель Gemma (укажите ваш tag в `PSY_OLLAMA_MODEL`).
3. Для embedding/rerank модели будут скачаны автоматически через Hugging Face при первом запуске.

## 3) Переменные окружения (пример)

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

## 4) Индексация корпуса

Положите файлы в `data/corpus` (поддержка: PDF, EPUB, DOCX, TXT, HTML).

```bash
python3 -m scripts.index_corpus --profile balanced --corpus-dir data/corpus
```

С URL-источниками:

```bash
python3 -m scripts.index_corpus --profile balanced --corpus-dir data/corpus --urls-file data/urls.txt
```

## 5) Запуск API

```bash
uvicorn app.api.main:app --host 0.0.0.0 --port 8000
```

UI доступен на `GET /` и отдается из `app/static/`.

### Разработка UI (TypeScript)

- Исходник UI: `app/static/ui.ts`
- Скомпилированный файл: `app/static/ui.js`
- Стили и разметка: `app/static/styles.css`, `app/static/index.html`

Пересобрать UI после изменений:

```bash
npm run build:ui
```

### Полезные endpoints
- `GET /health` — проверка Ollama/Chroma.
- `POST /index/rebuild` — переиндексация.
- `POST /query` — вопрос-ответ с цитированием.

`POST /query` принимает `query` длиной от 3 до 2000 символов.

## 6) Оценка retrieval/latency

Подготовьте JSONL:

```json
{"query":"What are core signs of burnout?","expected_sources":["data/corpus/burnout.pdf"]}
```

Запуск:

```bash
python3 -m scripts.eval_retrieval --dataset data/eval.jsonl --profile balanced
```

Выход: `recall_at_k`, `p50/p95 latency`, `faithfulness_proxy`.

Сравнение профилей:

```bash
python3 -m scripts.tune_profiles --dataset examples/eval_template.jsonl
```

## 7) Рекомендации по dual-GPU (18GB)

- Для вашей конфигурации (слот 1: RTX 2060, слот 2: RTX 5070) держите LLM, embeddings и reranker на RTX 5070 (`PSY_OLLAMA_MAIN_GPU=1`, `PSY_EMBEDDING_DEVICE=cuda:1`, `PSY_RERANKER_DEVICE=cuda:1`).
- При OOM: переключите reranker на RTX 2060 (`PSY_RERANKER_DEVICE=cuda:0`) или CPU (`PSY_RERANKER_DEVICE=cpu`).
