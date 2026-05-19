import hashlib
import json
import time
from typing import Any


def make_cache_key(model: str, messages: list, temperature: float) -> str:
    """Ключ = SHA-256(model + temperature + messages). Без timestamp и request_id."""
    raw = model + str(temperature) + json.dumps(messages, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class LLMCache:
    """In-memory кеш ответов LLM."""

    def __init__(self, ttl_seconds: int = 3600):
        self.ttl_seconds = ttl_seconds
        self._store: dict[str, tuple[Any, float]] = {}
        self.hits = 0
        self.misses = 0

    def get(self, model: str, messages: list, temperature: float) -> Any | None:
        key = make_cache_key(model, messages, temperature)
        item = self._store.get(key)
        if item is None:
            self.misses += 1
            return None

        response, expires_at = item
        if time.time() > expires_at:
            del self._store[key]
            self.misses += 1
            return None

        self.hits += 1
        return response

    def set(self, model: str, messages: list, temperature: float, response: Any) -> None:
        key = make_cache_key(model, messages, temperature)
        expires_at = time.time() + self.ttl_seconds
        self._store[key] = (response, expires_at)

    def stats(self) -> float:
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return round(self.hits / total * 100, 2)


class RedisLLMCache:
    """Тот же интерфейс, хранение в Redis (JSON)."""

    def __init__(self, redis_client, ttl_seconds: int = 3600, key_prefix: str = "llm:"):
        self.redis = redis_client
        self.ttl_seconds = ttl_seconds
        self.key_prefix = key_prefix
        self.hits = 0
        self.misses = 0

    def get(self, model: str, messages: list, temperature: float) -> Any | None:
        key = self.key_prefix + make_cache_key(model, messages, temperature)
        raw = self.redis.get(key)
        if raw is None:
            self.misses += 1
            return None

        self.hits += 1
        return json.loads(raw)

    def set(self, model: str, messages: list, temperature: float, response: Any) -> None:
        key = self.key_prefix + make_cache_key(model, messages, temperature)
        self.redis.setex(key, self.ttl_seconds, json.dumps(response, ensure_ascii=False))

    def stats(self) -> float:
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return round(self.hits / total * 100, 2)
