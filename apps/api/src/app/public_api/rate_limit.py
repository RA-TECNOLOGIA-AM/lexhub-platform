"""Limite de chamadas por chave da API pública (janela deslizante, em memória do processo)."""

import time
from collections import deque
from collections.abc import Callable


class RateLimiter:
    def __init__(
        self,
        limit: int = 60,
        window_s: float = 60.0,
        monotonic: Callable[[], float] = time.monotonic,
    ):
        self.limit = limit
        self._window = window_s
        self._now = monotonic
        self._hits: dict[str, deque[float]] = {}

    def hit(self, key_id: str) -> bool:
        """Registra uma chamada; False = passou do limite (a chamada não conta)."""
        now = self._now()
        hits = self._hits.setdefault(key_id, deque())
        while hits and now - hits[0] >= self._window:
            hits.popleft()
        if len(hits) >= self.limit:
            return False
        hits.append(now)
        return True
