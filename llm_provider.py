from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import httpx
from dotenv import load_dotenv
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_openai import ChatOpenAI

load_dotenv()

OPENAI_TIMEOUT_SECONDS = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "8"))
OPENAI_MAX_RETRIES = int(os.getenv("OPENAI_MAX_RETRIES", "1"))
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_HEALTH_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_HEALTH_TIMEOUT_SECONDS", "2"))
DEFAULT_OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DEFAULT_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "mxbai-embed-large")
DEFAULT_LOCAL_MODELS = (
    "qwen3:4b",
    "qwen3:8b",
    "gemma3:4b",
    "llama3:8b",
    "mistral:7b",
    "llama3.2:latest",
)


@dataclass
class GenerationResult:
    text: str
    provider: str
    errors: list[str]


class AllProvidersFailedError(RuntimeError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


def _coerce_text(result: Any) -> str:
    if hasattr(result, "content"):
        result = result.content
    if isinstance(result, str):
        return result.strip()
    return str(result).strip()


def _format_provider_error(provider: str, exc: Exception) -> str:
    return f"{provider}: {type(exc).__name__}: {exc}"


def is_openai_configured() -> bool:
    return bool(os.getenv("OPENAI_API_KEY", "").strip())


def get_local_model_candidates() -> tuple[str, ...]:
    configured_model = os.getenv("OLLAMA_RAG_MODEL", "").strip()
    ordered_models: list[str] = []
    installed_models = _get_installed_ollama_models()

    if configured_model:
        ordered_models.append(configured_model)

    preferred_models = list(DEFAULT_LOCAL_MODELS)
    if installed_models:
        preferred_models = [model_name for model_name in DEFAULT_LOCAL_MODELS if model_name in installed_models]
        preferred_models.extend([model_name for model_name in installed_models if model_name not in preferred_models])

    for model_name in preferred_models:
        if model_name not in ordered_models:
            ordered_models.append(model_name)

    return tuple(ordered_models)


@lru_cache(maxsize=8)
def get_openai_chat_llm(temperature: float = 0.2) -> ChatOpenAI:
    return ChatOpenAI(
        model=DEFAULT_OPENAI_MODEL,
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=temperature,
        timeout=OPENAI_TIMEOUT_SECONDS,
        max_retries=OPENAI_MAX_RETRIES,
    )


@lru_cache(maxsize=16)
def get_local_llm(model_name: str, temperature: float = 0.2) -> OllamaLLM:
    return OllamaLLM(model=model_name, temperature=temperature, base_url=OLLAMA_BASE_URL)


@lru_cache(maxsize=1)
def get_embed_model() -> OllamaEmbeddings:
    return OllamaEmbeddings(model=DEFAULT_EMBED_MODEL, base_url=OLLAMA_BASE_URL)


def invoke_with_fallback(prompt, variables: dict[str, Any], temperature: float = 0.2) -> GenerationResult:
    errors: list[str] = []

    if is_openai_configured():
        try:
            result = (prompt | get_openai_chat_llm(temperature=temperature)).invoke(variables)
            return GenerationResult(text=_coerce_text(result), provider="openai", errors=errors)
        except Exception as exc:  # pragma: no cover - depends on external service
            errors.append(_format_provider_error("openai", exc))
    else:
        errors.append("openai: OPENAI_API_KEY not configured")

    for model_name in get_local_model_candidates():
        try:
            result = (prompt | get_local_llm(model_name, temperature=temperature)).invoke(variables)
            return GenerationResult(text=_coerce_text(result), provider=f"ollama:{model_name}", errors=errors)
        except Exception as exc:  # pragma: no cover - depends on external service
            errors.append(_format_provider_error(f"ollama:{model_name}", exc))

    raise AllProvidersFailedError(errors)


def get_openai_health(probe: bool = False) -> dict[str, Any]:
    if not is_openai_configured():
        return {
            "provider": "openai",
            "status": "not_configured",
            "model": DEFAULT_OPENAI_MODEL,
        }

    if not probe:
        return {
            "provider": "openai",
            "status": "configured",
            "model": DEFAULT_OPENAI_MODEL,
        }

    try:
        result = get_openai_chat_llm(temperature=0).invoke("Reply with OK.")
        return {
            "provider": "openai",
            "status": "ok",
            "model": DEFAULT_OPENAI_MODEL,
            "response": _coerce_text(result),
        }
    except Exception as exc:  # pragma: no cover - depends on external service
        return {
            "provider": "openai",
            "status": "error",
            "model": DEFAULT_OPENAI_MODEL,
            "error": f"{type(exc).__name__}: {exc}",
        }


def get_ollama_server_health() -> dict[str, Any]:
    url = f"{OLLAMA_BASE_URL}/api/tags"
    try:
        response = httpx.get(url, timeout=OLLAMA_HEALTH_TIMEOUT_SECONDS)
        response.raise_for_status()
        payload = response.json()
        return {
            "provider": "ollama",
            "status": "ok",
            "base_url": OLLAMA_BASE_URL,
            "models": [item.get("name") for item in payload.get("models", [])],
        }
    except Exception as exc:  # pragma: no cover - depends on external service
        return {
            "provider": "ollama",
            "status": "error",
            "base_url": OLLAMA_BASE_URL,
            "error": f"{type(exc).__name__}: {exc}",
        }


@lru_cache(maxsize=1)
def _get_installed_ollama_models() -> tuple[str, ...]:
    health = get_ollama_server_health()
    if health.get("status") != "ok":
        return tuple()
    return tuple(
        model_name
        for model_name in health.get("models", [])
        if model_name and "embed" not in model_name.lower()
    )


def get_local_generation_health() -> dict[str, Any]:
    server_health = get_ollama_server_health()
    if server_health["status"] != "ok":
        return server_health

    errors: list[str] = []
    for model_name in get_local_model_candidates():
        try:
            result = get_local_llm(model_name, temperature=0).invoke("Reply with OK.")
            return {
                "provider": "ollama",
                "status": "ok",
                "model": model_name,
                "base_url": OLLAMA_BASE_URL,
                "response": _coerce_text(result),
            }
        except Exception as exc:  # pragma: no cover - depends on external service
            errors.append(_format_provider_error(model_name, exc))

    return {
        "provider": "ollama",
        "status": "error",
        "base_url": OLLAMA_BASE_URL,
        "tried_models": list(get_local_model_candidates()),
        "errors": errors,
    }
