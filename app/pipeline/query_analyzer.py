from __future__ import annotations

import logging
import re

from app.generation.ollama_client import OllamaClient


logger = logging.getLogger(__name__)

# Valid query types and which generation sections they map to.
# overview / general → all 3 sections, full num_predict
# self_help          → only self_help, focused num_predict
# therapist          → only therapist, focused num_predict
# techniques         → self_help + therapist, focused num_predict
VALID_TYPES = frozenset({"overview", "self_help", "therapist", "techniques", "general"})

SECTION_MAP: dict[str, list[str]] = {
    "overview":   ["overview", "self_help", "therapist"],
    "general":    ["overview", "self_help", "therapist"],
    "techniques": ["self_help", "therapist"],
    "self_help":  ["self_help"],
    "therapist":  ["therapist"],
}

_SYSTEM_PROMPT = (
    "Ты — классификатор запросов по психологии. "
    "Определи тип запроса и ответь ТОЛЬКО одним словом из списка:\n"
    "- overview — пользователь хочет обзор темы (что это, механизмы, причины)\n"
    "- self_help — пользователь хочет техники/упражнения для самостоятельного применения клиентом\n"
    "- therapist — пользователь хочет клинические стратегии или рекомендации для терапевта\n"
    "- techniques — пользователь хочет техники/методы (без указания кому предназначены)\n"
    "- general — всё остальное\n\n"
    "Ответь ТОЛЬКО одним словом из: overview, self_help, therapist, techniques, general"
)


class QueryAnalyzer:
    def __init__(self, ollama_client: OllamaClient) -> None:
        self._client = ollama_client

    def classify(self, query: str) -> str:
        raw = ""
        try:
            raw = self._client.generate(
                system_prompt=_SYSTEM_PROMPT,
                user_prompt=f"Запрос: {query}",
                num_predict=500,
                timeout_s=60.0,
            )
            for word in re.split(r"\W+", raw.lower()):
                if word in VALID_TYPES:
                    logger.info("query_analyzer: '%s' → %s", query[:60], word)
                    return word
            logger.warning("query_analyzer: no valid type in response %r, defaulting to 'general'", raw[:80])
        except Exception as exc:
            logger.warning("query_analyzer: error classifying query: %s", exc)
        return "general"
