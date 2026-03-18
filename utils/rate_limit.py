from __future__ import annotations

import os
import time
from dataclasses import dataclass
from threading import Lock

import redis
from dotenv import load_dotenv
from fastapi import HTTPException, Request, Response

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").strip().lower() not in {"0", "false", "no"}

_memory_counters: dict[str, int] = {}
_memory_lock = Lock()


@dataclass(frozen=True)
class RateLimitRule:
    scope: str
    limit: int
    window_seconds: int
    detail: str


def _get_redis_client() -> redis.Redis | None:
    try:
        client = redis.from_url(REDIS_URL, decode_responses=True)
        client.ping()
        return client
    except Exception:
        return None


def _get_client_identifier(request: Request) -> str:
    for header_name in ("cf-connecting-ip", "x-real-ip", "x-forwarded-for"):
        header_value = request.headers.get(header_name, "").strip()
        if header_value:
            return header_value.split(",")[0].strip()

    if request.client and request.client.host:
        return request.client.host

    return "anonymous"


def _consume_memory_counter(rule: RateLimitRule, identifier: str) -> tuple[bool, int, int]:
    now = int(time.time())
    bucket = now // rule.window_seconds
    key = f"{rule.scope}:{identifier}:{bucket}"

    with _memory_lock:
        stale_prefix = f"{rule.scope}:{identifier}:"
        stale_keys = [existing_key for existing_key in _memory_counters if existing_key.startswith(stale_prefix) and existing_key != key]
        for stale_key in stale_keys:
            _memory_counters.pop(stale_key, None)

        current = _memory_counters.get(key, 0) + 1
        _memory_counters[key] = current

    remaining = max(rule.limit - current, 0)
    retry_after = max(rule.window_seconds - (now % rule.window_seconds), 1)
    return current <= rule.limit, remaining, retry_after


def _consume_redis_counter(rule: RateLimitRule, identifier: str, client: redis.Redis) -> tuple[bool, int, int]:
    now = int(time.time())
    bucket = now // rule.window_seconds
    key = f"ratelimit:{rule.scope}:{identifier}:{bucket}"

    count = int(client.incr(key))
    ttl = int(client.ttl(key))

    if ttl < 0:
        client.expire(key, rule.window_seconds)
        ttl = rule.window_seconds

    remaining = max(rule.limit - count, 0)
    retry_after = max(ttl, 1)
    return count <= rule.limit, remaining, retry_after


def enforce_rate_limit(request: Request, response: Response, rule: RateLimitRule) -> None:
    if not RATE_LIMIT_ENABLED or rule.limit <= 0 or rule.window_seconds <= 0:
        return

    identifier = _get_client_identifier(request)
    client = _get_redis_client()

    if client is None:
        allowed, remaining, retry_after = _consume_memory_counter(rule, identifier)
        backend = "memory"
    else:
        allowed, remaining, retry_after = _consume_redis_counter(rule, identifier, client)
        backend = "redis"

    response.headers["X-RateLimit-Limit"] = str(rule.limit)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Window"] = str(rule.window_seconds)
    response.headers["X-RateLimit-Backend"] = backend

    if allowed:
        return

    response.headers["Retry-After"] = str(retry_after)
    raise HTTPException(status_code=429, detail=rule.detail)


def reset_rate_limit_state() -> None:
    with _memory_lock:
        _memory_counters.clear()
