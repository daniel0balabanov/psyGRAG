# Конфигурация (app/config.py)

Все настройки живут в классе `Settings` (pydantic-settings). Значения читаются из переменных окружения с префиксом `PSY_` или из файла `.env` в корне проекта.

## Переменные окружения

### Пути к данным

| Переменная | Дефолт | Назначение |
|---|---|---|
| `PSY_DATA_DIR` | `data` | Корневая папка данных |
| `PSY_CORPUS_DIR` | `data/corpus` | Исходные документы |
| `PSY_CHROMA_DIR` | `data/chroma` | Хранилище ChromaDB |
| `PSY_BM25_INDEX_PATH` | `data/bm25/index.pkl` | Сериализованный BM25-индекс |

### Ollama / LLM

| Переменная | Дефолт | Назначение |
|---|---|---|
| `PSY_OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | URL Ollama-сервера |
| `PSY_OLLAMA_MODEL` | `gemma4:e4b` | Тег модели |
| `PSY_OLLAMA_NUM_CTX` | `6144` | Размер контекстного окна (токены) |
| `PSY_OLLAMA_TEMPERATURE` | `0.1` | Температура генерации |
| `PSY_OLLAMA_NUM_PREDICT` | `1500` | Лимит токенов на ответ |
| `PSY_OLLAMA_TIMEOUT_S` | `120.0` | Таймаут HTTP-запроса к Ollama (сек) |
| `PSY_OLLAMA_MAX_CONTINUATIONS` | `2` | Макс. попыток продолжить обрезанный ответ |
| `PSY_OLLAMA_MAIN_GPU` | `1` | Индекс GPU для Ollama (0-based) |
| `PSY_OLLAMA_NUM_GPU` | `1` | Кол-во GPU для Ollama |

### Эмбеддинги

| Переменная | Дефолт | Назначение |
|---|---|---|
| `PSY_EMBEDDING_MODEL_NAME` | `BAAI/bge-m3` | HuggingFace-модель |
| `PSY_EMBEDDING_DEVICE` | `cuda:0` | GPU для эмбеддингов при **запросе** |
| `PSY_INDEXING_EMBEDDING_DEVICE` | `cuda:1` | GPU для эмбеддингов при **индексации** |
| `PSY_EMBEDDING_BATCH_SIZE` | `16` | Batch size при batch-кодировании |

### Reranker

| Переменная | Дефолт | Назначение |
|---|---|---|
| `PSY_RERANKER_ENABLED` | `true` | Включить/отключить cross-encoder |
| `PSY_RERANKER_MODEL_NAME` | `BAAI/bge-reranker-v2-m3` | HuggingFace-модель |
| `PSY_RERANKER_DEVICE` | `cuda:1` | GPU для reranker |

### Профиль

| Переменная | Дефолт | Назначение |
|---|---|---|
| `PSY_PROFILE_NAME` | `balanced` | Активный профиль извлечения (`fast`, `balanced`, `quality`) |

## Профили извлечения (RetrievalProfile)

Профиль управляет компромиссом между скоростью и качеством. Параметры влияют на размер чанков при индексации и глубину поиска при запросе.

| Параметр | fast | balanced | quality |
|---|---|---|---|
| `chunk_size` (chars) | 650 | 850 | 1000 |
| `chunk_overlap` (chars) | 70 | 120 | 160 |
| `dense_top_k` | 10 | 18 | 26 |
| `sparse_top_k` | 10 | 18 | 24 |
| `rerank_top_n` | 8 | 14 | 20 |
| `final_context_chunks` | 4 | 6 | 8 |
| `max_context_chars` | 7000 | 10000 | 14000 |

**Важно:** `chunk_size` и `chunk_overlap` применяются при **индексации** — смена профиля требует полной переиндексации корпуса. Остальные параметры применяются «на лету» при каждом запросе.

Активный профиль можно сменить через `PSY_PROFILE_NAME` или через `POST /index/rebuild` с полем `"profile"`.
