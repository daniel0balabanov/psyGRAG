# Документация

| Файл | Содержание |
|---|---|
| [config.md](config.md) | Все переменные окружения, профили и их параметры |
| [ingest.md](ingest.md) | Парсинг файлов/URL, нормализация метаданных, алгоритм чанкинга |
| [indexing.md](indexing.md) | EmbeddingService (BGE-M3), ChromaStore, BM25Store |
| [retrieval_pipeline.md](retrieval_pipeline.md) | RRF-слияние, cross-encoder reranking, полная схема пайплайна |
| [generation.md](generation.md) | OllamaClient, continuation, промпты |
| [api.md](api.md) | FastAPI endpoints, формат запросов/ответов, startup |
| [scripts.md](scripts.md) | CLI: индексация, оценка качества, сравнение профилей |
| [ui.md](ui.md) | UI-слой, структура static-файлов, TS-сборка и UX-поведение |
| [prompt_safety.md](prompt_safety.md) | Защита от prompt injection и формат user message |

## UI и TypeScript

- UI-страница: `app/static/index.html`
- Клиентская логика: `app/static/ui.ts` (сборка в `app/static/ui.js`)
- Стили: `app/static/styles.css`
- Команда сборки UI: `npm run build:ui`
