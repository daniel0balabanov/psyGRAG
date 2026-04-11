# Ингестия документов (app/ingest/)

Модуль отвечает за загрузку, парсинг, нормализацию метаданных и нарезку документов на чанки перед индексацией.

## Поток данных

```
файлы / URL
     │
     ▼
ingest/service.py        ← точка входа
     │
     ├─ parsers.py       ← чтение файлов и веб-статей → Document
     ├─ metadata.py      ← нормализация полей Document
     └─ chunker.py       ← разбивка Document → [Chunk, ...]
```

---

## Парсеры (app/ingest/parsers.py)

Каждый парсер принимает путь к файлу или URL и возвращает `Document`.

| Формат | Функция | Библиотека |
|---|---|---|
| `.txt`, `.md` | `parse_txt` | встроенный `open` |
| `.pdf` | `parse_pdf` | `pypdf` |
| `.docx` | `parse_docx` | `python-docx` |
| `.epub` | `parse_epub` | `ebooklib` + BeautifulSoup |
| `.html`, `.htm` | `parse_html_file` | BeautifulSoup |
| URL | `parse_web_article` | `trafilatura` + fallback на `requests`+BS4 |

Функция `parse_path(path)` — диспетчер по расширению файла.  
Функция `iter_supported_files(root)` — рекурсивный обход директории, возвращает только поддерживаемые файлы.

### doc_id

Каждому документу присваивается стабильный `doc_id` — первые 16 символов SHA-256 от строки `"<формат>:<путь>"`. Повторная индексация одного файла даёт тот же ID.

### topic

Тема документа (`topic`) определяется из имени **родительской директории** файла. Например, файл `data/corpus/depression/paper.pdf` получит `topic="depression"`.

---

## Нормализация метаданных (app/ingest/metadata.py)

После парсинга каждый `Document` проходит через `normalize_document_metadata`, которая:

- Добавляет `source_name` — домен URL или имя файла.
- Добавляет `char_count` и `word_count`.
- Устанавливает `domain = "psychology"` (если не задано иное).
- Инферирует `year` из первых 1200 символов текста и заголовка с помощью regex `(19|20)\d{2}`.

---

## Чанкинг (app/ingest/chunker.py)

Функция `chunk_document(document, chunk_size, chunk_overlap)` разбивает текст на перекрывающиеся чанки с учётом границ предложений.

### Алгоритм

1. Текст разбивается на предложения по паттерну `(?<=[.!?])\s+`.
2. Предложения набираются в текущий чанк до превышения `chunk_size` (в символах).
3. При переполнении чанк сохраняется, и из его **конца** берётся перекрытие (`chunk_overlap` символов) — отступ назад по предложениям для сохранения контекста.
4. Процесс повторяется до конца документа.

### chunk_id

Стабильный ID: первые 20 символов SHA-256 от строки `"<doc_id>:<index>"`.

### Метаданные чанка

Каждый `Chunk` наследует из `Document`: `source`, `title`, а также `chunk_index`, `year`, `author`, `topic` в поле `metadata`.

### Параметры профиля

| Профиль | chunk_size | chunk_overlap |
|---|---|---|
| fast | 650 | 70 |
| balanced | 850 | 120 |
| quality | 1000 | 160 |
