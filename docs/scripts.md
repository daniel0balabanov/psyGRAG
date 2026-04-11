# CLI-скрипты (scripts/)

Все скрипты запускаются как модули из корня проекта:

```bash
python3 -m scripts.<имя_скрипта> [аргументы]
```

---

## index_corpus.py

Индексирует локальный корпус и/или веб-ссылки. Строит ChromaDB и BM25-индекс.

```bash
python3 -m scripts.index_corpus [--corpus-dir PATH] [--urls-file PATH] [--profile PROFILE]
```

| Аргумент | Дефолт | Описание |
|---|---|---|
| `--corpus-dir` | `data/corpus` | Директория с документами |
| `--urls-file` | — | Текстовый файл с URL (по одному на строку, `#` — комментарий) |
| `--profile` | `balanced` | Профиль индексации (`fast`, `balanced`, `quality`) |

Выводит количество проиндексированных документов и чанков.

**Важно:** профиль определяет `chunk_size` и `chunk_overlap` — после смены профиля индекс необходимо перестраивать полностью.

---

## eval_retrieval.py

Оценивает качество retrieval и генерации на датасете запросов.

```bash
python3 -m scripts.eval_retrieval --dataset PATH [--profile PROFILE]
```

**Формат датасета** (JSONL, одна запись на строку):
```json
{"query": "Какие техники помогают при тревожности?", "expected_sources": ["data/corpus/anxiety.pdf"]}
```

**Метрики в выводе:**

| Метрика | Описание |
|---|---|
| `recall_at_k` | Доля запросов, где хотя бы один ожидаемый источник попал в citations |
| `p50_latency_sec` | Медианная задержка ответа |
| `p95_latency_sec` | 95-й перцентиль задержки |
| `faithfulness_proxy` | Доля токенов ответа, встречающихся в контексте (эвристика) |

Пример вывода:
```json
{
  "profile": "balanced",
  "queries": 20,
  "recall_at_k": 0.85,
  "p50_latency_sec": 7.2,
  "p95_latency_sec": 12.4,
  "faithfulness_proxy": 0.61
}
```

---

## tune_profiles.py

Прогоняет один датасет через все три профиля (`fast`, `balanced`, `quality`) и сравнивает метрики.

```bash
python3 -m scripts.tune_profiles --dataset PATH
```

Выводит JSON-массив с тремя отчётами (по одному на профиль). Удобно для выбора профиля под конкретный корпус и железо.

**Метрики:** `recall_at_k`, `mean_latency_sec`, `p95_latency_sec`.

**Примечание:** скрипт создаёт три отдельных `QueryPipeline` (по одному на профиль), каждый загружает модели заново — выполнение занимает значительное время.
