# Индексирование (app/indexing/)

Модуль содержит три компонента хранилища: эмбеддинги, ChromaDB (dense) и BM25 (sparse). Все три используются в `IndexPipeline` при построении индексов и в `QueryPipeline` при поиске.

---

## EmbeddingService (app/indexing/embeddings.py)

Обёртка над `sentence-transformers` для получения векторных представлений.

**Модель по умолчанию:** `BAAI/bge-m3` — мультиязычная (100+ языков, включая русский), 1024-мерные векторы.

| Метод | Назначение |
|---|---|
| `embed_texts(texts)` | Batch-кодирование списка строк → `list[list[float]]`. Используется при индексации. |
| `embed_query(text)` | Кодирование одной строки → `list[float]`. Используется при запросе. |

Все векторы нормализуются (`normalize_embeddings=True`), что позволяет использовать косинусное сходство через скалярное произведение.

Два разных устройства конфигурируются отдельно:
- `PSY_EMBEDDING_DEVICE` — для `QueryPipeline` (query-time, обычно `cuda:0`)
- `PSY_INDEXING_EMBEDDING_DEVICE` — для `IndexPipeline` (batch, обычно `cuda:1`)

---

## ChromaStore (app/indexing/chroma_store.py)

Векторная БД для dense retrieval. Использует `chromadb.PersistentClient` — данные сохраняются на диск в `data/chroma/`.

Коллекция по умолчанию: `psych_literature`.

| Метод | Назначение |
|---|---|
| `add_chunks(chunks, embeddings)` | Записывает чанки с векторами. Батчи по 5000 (лимит Chroma). |
| `query(embedding, top_k)` | Возвращает `top_k` ближайших `RetrievalHit` по косинусному расстоянию. |

**Score:** `1.0 - distance` (чем выше — тем ближе к запросу).

Метаданные, записываемые в Chroma: `doc_id`, `source`, `title`, плюс все поля из `Chunk.metadata`. Значения `None` отфильтровываются (Chroma их не принимает), остальные нескалярные значения приводятся к `str`.

---

## BM25Store (app/indexing/bm25_store.py)

Sparse retrieval на основе `BM25Okapi` из библиотеки `rank_bm25`.

| Метод | Назначение |
|---|---|
| `build(chunks)` | Строит индекс по токенам всех чанков. |
| `save()` | Сериализует индекс и список чанков в `data/bm25/index.pkl` через `pickle`. |
| `load()` | Десериализует индекс из pickle. В `QueryPipeline` вызывается лениво при первом запросе. |
| `query(text, top_k)` | Токенизирует запрос, считает BM25-скоры, возвращает `top_k` `RetrievalHit`. |

**Токенизация:** `\w+` (unicode), lowercase. Без стемминга — работает для смешанных русско-английских текстов.

### Жизненный цикл индекса

- Строится один раз при `IndexPipeline.build_indexes()`.
- Файл `index.pkl` перезаписывается при каждой переиндексации.
- В `QueryPipeline` загружается в память при первом запросе и удерживается в RAM на всё время жизни процесса (`_bm25_loaded = True`).
- Если файл отсутствует при запросе — `FileNotFoundError` → API возвращает HTTP 503.
