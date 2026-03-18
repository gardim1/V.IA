from __future__ import annotations

import os
import time
from threading import Lock
from typing import Any

import redis
from dotenv import load_dotenv
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory

load_dotenv()

CHAT_TTL_SECONDS = int(os.getenv("CHAT_TTL_SECONDS", "2592000"))
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
REDIS_CONNECT_TIMEOUT_SECONDS = float(os.getenv("REDIS_CONNECT_TIMEOUT_SECONDS", "0.5"))
REDIS_RETRY_COOLDOWN_SECONDS = float(os.getenv("REDIS_RETRY_COOLDOWN_SECONDS", "5"))

_memory_histories: dict[str, InMemoryChatMessageHistory] = {}
_memory_lock = Lock()
_last_redis_failure_at = 0.0


def _get_memory_history(session_id: str) -> InMemoryChatMessageHistory:
    with _memory_lock:
        if session_id not in _memory_histories:
            _memory_histories[session_id] = InMemoryChatMessageHistory()
        return _memory_histories[session_id]


def _get_redis_client() -> redis.Redis | None:
    global _last_redis_failure_at

    if _last_redis_failure_at:
        elapsed = time.time() - _last_redis_failure_at
        if elapsed < REDIS_RETRY_COOLDOWN_SECONDS:
            return None

    try:
        client = redis.from_url(
            REDIS_URL,
            decode_responses=False,
            socket_connect_timeout=REDIS_CONNECT_TIMEOUT_SECONDS,
            socket_timeout=REDIS_CONNECT_TIMEOUT_SECONDS,
        )
        client.ping()
        _last_redis_failure_at = 0.0
        return client
    except Exception:
        _last_redis_failure_at = time.time()
        return None


class SafeChatHistory:
    def __init__(self, session_id: str):
        self.session_id = session_id or "anon"

    def _get_redis_history(self) -> RedisChatMessageHistory | None:
        client = _get_redis_client()
        if client is None:
            return None

        try:
            client.expire(f"message_store:{self.session_id}", CHAT_TTL_SECONDS)
        except Exception:
            return None

        return RedisChatMessageHistory(
            session_id=self.session_id,
            url=REDIS_URL,
            ttl=CHAT_TTL_SECONDS,
        )

    def _preferred_backend(self):
        return self._get_redis_history() or _get_memory_history(self.session_id)

    @property
    def backend(self) -> str:
        return "redis" if self._get_redis_history() is not None else "memory"

    @property
    def messages(self):
        history = self._preferred_backend()
        try:
            return history.messages
        except Exception:
            return _get_memory_history(self.session_id).messages

    def add_user_message(self, message: str) -> None:
        history = self._preferred_backend()
        try:
            history.add_user_message(message)
        except Exception:
            _get_memory_history(self.session_id).add_user_message(message)

    def add_ai_message(self, message: str) -> None:
        history = self._preferred_backend()
        try:
            history.add_ai_message(message)
        except Exception:
            _get_memory_history(self.session_id).add_ai_message(message)

    def clear(self) -> None:
        history = self._preferred_backend()
        try:
            history.clear()
        finally:
            _get_memory_history(self.session_id).clear()


def get_history(session_id: str) -> SafeChatHistory:
    return SafeChatHistory(session_id)


def clear_history(session_id: str) -> dict[str, Any]:
    history = get_history(session_id)
    existed = bool(history.messages)
    history.clear()
    return {"deleted": existed, "backend": history.backend}


def get_redis_health() -> dict[str, Any]:
    client = _get_redis_client()
    if client is None:
        return {
            "provider": "redis",
            "status": "error",
            "url": REDIS_URL,
            "error": "Redis unavailable. Using in-memory history fallback.",
        }

    return {
        "provider": "redis",
        "status": "ok",
        "url": REDIS_URL,
        "ttl_seconds": CHAT_TTL_SECONDS,
    }


redis_client = _get_redis_client()
