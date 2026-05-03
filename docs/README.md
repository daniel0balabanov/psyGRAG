# Documentation

| File | Contents |
|---|---|
| [config.md](config.md) | All environment variables, profiles, and their parameters |
| [ingest.md](ingest.md) | File/URL parsing, metadata normalization, chunking algorithm |
| [indexing.md](indexing.md) | EmbeddingService (BGE-M3), ChromaStore, BM25Store |
| [retrieval_pipeline.md](retrieval_pipeline.md) | RRF fusion, cross-encoder reranking, full pipeline diagram |
| [generation.md](generation.md) | OllamaClient, continuation, prompts |
| [api.md](api.md) | FastAPI endpoints, request/response format, startup |
| [scripts.md](scripts.md) | CLI: indexing, retrieval evaluation, profile comparison |
| [ui.md](ui.md) | UI layer, static file structure, TS build, and UX behavior |
| [prompt_safety.md](prompt_safety.md) | Prompt injection protection and user message format |

## UI and TypeScript

- UI page: `app/static/index.html`
- Client logic: `app/static/ui.ts` (compiled to `app/static/ui.js`)
- Styles: `app/static/styles.css`
- Build command: `npm run build:ui`
