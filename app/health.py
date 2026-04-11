from __future__ import annotations

from dataclasses import dataclass, asdict

import requests
from chromadb import PersistentClient

from app.config import settings


@dataclass(slots=True)
class HealthStatus:
    app: str
    ollama_ok: bool
    chroma_ok: bool
    detail: dict[str, str]

    def to_dict(self) -> dict:
        return asdict(self)


def check_ollama(timeout_s: float = 2.5) -> tuple[bool, str]:
    try:
        response = requests.get(f"{settings.ollama_base_url}/api/tags", timeout=timeout_s)
        if response.ok:
            return True, "reachable"
        return False, f"HTTP {response.status_code}"
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def check_chroma() -> tuple[bool, str]:
    try:
        client = PersistentClient(path=str(settings.chroma_dir))
        client.heartbeat()
        return True, "reachable"
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def run_health_checks() -> HealthStatus:
    ollama_ok, ollama_detail = check_ollama()
    chroma_ok, chroma_detail = check_chroma()
    return HealthStatus(
        app=settings.app_name,
        ollama_ok=ollama_ok,
        chroma_ok=chroma_ok,
        detail={"ollama": ollama_detail, "chroma": chroma_detail},
    )
