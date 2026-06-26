from __future__ import annotations

import logging

import requests


logger = logging.getLogger(__name__)
ChatMessage = dict[str, str]


class OllamaClient:
    def __init__(
        self,
        base_url: str,
        model: str,
        num_ctx: int = 4096,
        temperature: float = 0.1,
        num_predict: int = 512,
        timeout_s: float = 120.0,
        max_continuations: int = 2,
        main_gpu: int = 0,
        num_gpu: int = 1,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.num_ctx = num_ctx
        self.temperature = temperature
        self.num_predict = num_predict
        self.timeout_s = timeout_s
        self.max_continuations = max(0, max_continuations)
        self.main_gpu = main_gpu
        self.num_gpu = num_gpu

    def warmup(self) -> None:
        """Load the model GPU layers into VRAM by running a minimal generation."""
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": "hi"}],
            "stream": False,
            "keep_alive": -1,
            "options": {
                "num_predict": 1,
                "num_ctx": self.num_ctx,
                "main_gpu": self.main_gpu,
                "num_gpu": self.num_gpu,
            },
        }
        try:
            requests.post(f"{self.base_url}/api/chat", json=payload, timeout=120.0)
            logger.info("Ollama model warmed up: %s", self.model)
        except Exception as exc:
            logger.warning("Ollama warmup failed: %s", exc)

    def _generate_once(
        self,
        messages: list[ChatMessage],
        request_timeout: float,
        num_predict: int | None = None,
    ) -> dict:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "keep_alive": -1,
            "options": {
                "temperature": self.temperature,
                "num_ctx": self.num_ctx,
                "num_predict": num_predict if num_predict is not None else self.num_predict,
                "main_gpu": self.main_gpu,
                "num_gpu": self.num_gpu,
            },
        }
        response = requests.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=request_timeout,
        )
        if not response.ok:
            details = response.text.strip()
            try:
                error_body = response.json()
                details = str(error_body.get("error", details))
            except ValueError:
                pass
            logger.error(
                "Ollama chat failed: status=%s model=%s timeout_s=%s details=%s",
                response.status_code,
                self.model,
                request_timeout,
                details[:500],
            )
        response.raise_for_status()
        return response.json()

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        timeout_s: float | None = None,
        num_predict: int | None = None,
    ) -> str:
        request_timeout = self.timeout_s if timeout_s is None else timeout_s
        base_messages: list[ChatMessage] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        body = self._generate_once(base_messages, request_timeout, num_predict=num_predict)
        answer = str(body.get("message", {}).get("content", "")).strip()
        done_reason = str(body.get("done_reason", ""))

        for step in range(self.max_continuations):
            if done_reason != "length":
                break
            continuation_messages: list[ChatMessage] = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": answer},
                {
                    "role": "user",
                    "content": (
                        "Продолжи ответ с места остановки. Не повторяй уже сказанное. "
                        "Не начинай с вступления, продолжай по делу."
                    ),
                },
            ]
            logger.info(
                "Ollama response truncated by length; requesting continuation (%s/%s)",
                step + 1,
                self.max_continuations,
            )
            cont_body = self._generate_once(continuation_messages, request_timeout, num_predict=num_predict)
            cont_answer = str(cont_body.get("message", {}).get("content", "")).strip()
            if cont_answer:
                answer = f"{answer}\n{cont_answer}".strip()
            done_reason = str(cont_body.get("done_reason", ""))

        if not answer:
            logger.warning(
                "Ollama returned empty response: model=%s done_reason=%s prompt_chars=%s",
                self.model,
                done_reason,
                len(system_prompt) + len(user_prompt),
            )
        return answer
