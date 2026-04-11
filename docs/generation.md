# Генерация ответов (app/generation/)

## OllamaClient (app/generation/ollama_client.py)

HTTP-клиент для взаимодействия с локальным Ollama-сервером через `/api/chat`.

### Параметры конструктора

| Параметр | Env | Дефолт | Назначение |
|---|---|---|---|
| `base_url` | `PSY_OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Адрес Ollama |
| `model` | `PSY_OLLAMA_MODEL` | `gemma4:e4b` | Тег модели |
| `num_ctx` | `PSY_OLLAMA_NUM_CTX` | `6144` | Контекстное окно (токены) |
| `temperature` | `PSY_OLLAMA_TEMPERATURE` | `0.1` | Низкая температура для фактических ответов |
| `num_predict` | `PSY_OLLAMA_NUM_PREDICT` | `1500` | Лимит токенов на один ответ |
| `timeout_s` | `PSY_OLLAMA_TIMEOUT_S` | `120.0` | Таймаут HTTP-запроса (сек) |
| `max_continuations` | `PSY_OLLAMA_MAX_CONTINUATIONS` | `2` | Макс. попыток продолжения |
| `main_gpu` | `PSY_OLLAMA_MAIN_GPU` | `1` | GPU index для Ollama |
| `num_gpu` | `PSY_OLLAMA_NUM_GPU` | `1` | Кол-во GPU |

### Методы

**`warmup()`** — при старте FastAPI вызывается автоматически. Отправляет минимальный запрос (`num_predict=1`) с `keep_alive=-1`, чтобы загрузить веса модели в VRAM заранее. Ошибка warmup не прерывает запуск сервера (только `WARNING` в логах).

**`generate(system_prompt, user_prompt, timeout_s=None) → str`** — основной метод. Отправляет отдельные сообщения `system` и `user`, получает ответ.

### Логика continuation

Ollama может обрезать ответ по `num_predict` (поле `done_reason == "length"`). В этом случае `generate` автоматически отправляет дополнительные запросы (до `max_continuations` раз), сохраняя исходные `system/user` сообщения, добавляя текущий черновик (`assistant`) и короткую инструкцию продолжить. Финальный ответ — конкатенация всех частей.

### Промпты (app/pipeline/query_pipeline.py)

Два промпта — основной и retry (используется при пустом ответе):

- **Основной**: `system` задает правила ответа; `user` содержит структурированные блоки `<user_question>` и `<retrieved_context>`.
- **Retry**: более строгая версия с требованием inline-ссылок `[1]`, `[2]`, применяется с уменьшенным контекстом (≤ 2500 символов, топ-3 чанка).
- **Fallback**: если оба промпта дали пустой ответ — возвращается текстовая заглушка с перечислением найденных источников.

Все промпты на русском языке. `think: false` передаётся в Ollama, чтобы отключить режим внутреннего рассуждения (thinking mode) у моделей, которые его поддерживают.
