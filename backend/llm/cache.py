from __future__ import annotations

import time
from collections import OrderedDict
from threading import Lock
from typing import Any, Optional


class LLMResponseCache:
    """Small in-memory TTL cache for repeated LLM enrichment requests."""

    def __init__(self, max_size: int = 256, ttl_seconds: int = 300):
        self.max_size = max(1, int(max_size))
        self.ttl_seconds = max(1, int(ttl_seconds))
        self._items: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._lock = Lock()

    def _purge(self, now: float) -> None:
        expired = []
        for key, (expires_at, _value) in self._items.items():
            if expires_at <= now:
                expired.append(key)

        for key in expired:
            self._items.pop(key, None)

        while len(self._items) > self.max_size:
            self._items.popitem(last=False)

    def get(self, key: str) -> Optional[Any]:
        now = time.time()
        with self._lock:
            self._purge(now)
            item = self._items.get(key)
            if not item:
                return None

            expires_at, value = item
            if expires_at <= now:
                self._items.pop(key, None)
                return None

            self._items.move_to_end(key)
            return value

    def set(self, key: str, value: Any) -> None:
        now = time.time()
        expires_at = now + self.ttl_seconds
        with self._lock:
            self._items[key] = (expires_at, value)
            self._items.move_to_end(key)
            self._purge(now)
