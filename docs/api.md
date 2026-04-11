# API (app/api/main.py)

FastAPI-приложение. Запускается через:

```bash
uvicorn app.api.main:app --host 0.0.0.0 --port 8000
```

## Startup

При старте (`@app.on_event("startup")`):
1. Создаются директории из `settings.ensure_dirs()`.
2. Вызывается `OllamaClient.warmup()` — модель загружается в VRAM.

`QueryPipeline` инициализируется лениво при первом обращении к `POST /query` (не при старте), поскольку требует загруженного BM25-индекса.

---

## Endpoints

### `GET /`

Возвращает UI из `app/static/index.html`. Клиентский код (`app/static/ui.ts` -> `app/static/ui.js`) отправляет запрос в `POST /query`, показывает ответ, список источников и debug-блок. Горячая клавиша: Ctrl+Enter / Cmd+Enter.

---

### `GET /health`

Проверяет доступность Ollama и ChromaDB. Ollama проверяется GET-запросом на `/api/tags` (таймаут 2.5 с), ChromaDB — через `PersistentClient.heartbeat()`.

**Ответ:**
```json
{
  "app": "psy-rag",
  "ollama_ok": true,
  "chroma_ok": true,
  "detail": { "ollama": "reachable", "chroma": "reachable" }
}
```

---

### `POST /query`

**Тело запроса:**
```json
{ "query": "Текст вопроса (от 3 до 2000 символов)" }
```

**Ответ:**
```json
{
  "answer": "...",
  "citations": [
    { "id": 1, "chunk_id": "...", "source": "data/corpus/...", "title": "...", "text": "..." }
  ],
  "debug": {
    "profile": "balanced",
    "dense_hits": 18,
    "sparse_hits": 18,
    "fused_hits": 24,
    "reranked_hits": 14,
    "used_retry": false,
    "used_fallback": false,
    "timings_sec": { "embed_query_sec": 0.12, "total_sec": 8.4, ... }
  }
}
```

**Коды ошибок:**
- `422` — ошибка валидации запроса (например, `query` короче 3 или длиннее 2000 символов).
- `503` — BM25-индекс не найден (нужна переиндексация).
- `500` — прочие ошибки пайплайна.

---

### `POST /index/rebuild`

Перестраивает оба индекса (ChromaDB + BM25) из документов корпуса.

**Тело запроса:**
```json
{
  "corpus_dir": "data/corpus",   // опционально, по умолчанию из settings
  "urls": ["https://..."],        // опционально, дополнительные URL
  "profile": "balanced"           // опционально, меняет активный профиль
}
```

После успешной переиндексации `pipeline` (глобальный `QueryPipeline`) сбрасывается в `None` — следующий запрос создаст его заново с обновлённым индексом.

**Ответ:**
```json
{ "status": "ok", "indexed": { "documents": 42, "chunks": 1850 }, "profile": "balanced" }
```

---

## Глобальное состояние

`pipeline: QueryPipeline | None` — единственный глобальный объект. Хранит загруженные модели (embedding, reranker) и BM25-индекс в памяти между запросами. Сбрасывается при переиндексации.
