"""Cache das queries dos bancos de origem (5 min), no padrão da v1 (fetch_data_with_cache).

Protege os bancos de origem e evita que o usuário espere a query pesada (LexPre: ~22 a 50 s):
  * fresco (até `ttl`): devolve da memória, sem ir ao banco;
  * vencido: UMA busca por chave, mesmo com várias pessoas abrindo juntas (trava por chave);
  * banco fora do ar: devolve o último dado bom até `stale_max_age` (igual à v1); depois, o erro;
  * o aquecedor (cache_warmer.py) renova antes de vencer, então a tela quase nunca espera.

Peças trocáveis:
  * CacheStore    onde guarda (MemoryStore hoje; Redis depois, com a mesma interface);
  * SourceCache   as regras acima (independe de banco);
  * CachedSourceFetcher  o SourceFetcher com cache, que os módulos de dashboard usam sem saber.
"""

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Protocol

from app.dashboards.base import SourceFetcher

logger = logging.getLogger(__name__)

Rows = list[dict[str, Any]]
Clock = Callable[[], float]


@dataclass(frozen=True)
class Entry:
    data: Rows
    fetched_at: float  # epoch (s) da busca no banco


class CacheStore(Protocol):
    def get(self, key: str) -> Entry | None: ...

    def set(self, key: str, entry: Entry) -> None: ...


class MemoryStore:
    """Na memória do processo, com limite de chaves (sai a buscada há mais tempo)."""

    def __init__(self, max_entries: int = 64):
        self._max = max_entries
        self._data: dict[str, Entry] = {}

    def get(self, key: str) -> Entry | None:
        return self._data.get(key)

    def set(self, key: str, entry: Entry) -> None:
        self._data[key] = entry
        while len(self._data) > self._max:
            oldest = min(self._data, key=lambda k: self._data[k].fetched_at)
            del self._data[oldest]


class SourceCache:
    def __init__(
        self,
        store: CacheStore,
        ttl: float = 300,
        stale_max_age: float = 3600,
        clock: Clock = time.time,
    ):
        self._store = store
        self._ttl = ttl
        self._stale_max_age = stale_max_age
        self._clock = clock
        self._locks: dict[str, asyncio.Lock] = {}

    def fetched_at(self, key: str) -> float | None:
        """Quando o dado dessa chave veio do banco (None = ainda não buscado)."""
        entry = self._store.get(key)
        return entry.fetched_at if entry is not None else None

    def _fresh(self, entry: Entry | None) -> bool:
        return entry is not None and self._clock() - entry.fetched_at < self._ttl

    async def get(self, key: str, load: Callable[[], Awaitable[Rows]]) -> Entry:
        """Do cache se fresco; senão busca (uma vez por chave); banco fora = último dado bom."""
        entry = self._store.get(key)
        if self._fresh(entry):
            return entry
        lock = self._locks.setdefault(key, asyncio.Lock())
        async with lock:
            entry = self._store.get(key)  # outra requisição pode ter buscado enquanto esperávamos
            if self._fresh(entry):
                return entry
            try:
                return await self._load(key, load)
            except Exception as exc:
                if entry is not None and self._clock() - entry.fetched_at <= self._stale_max_age:
                    logger.warning(
                        "[cache] '%s' vencido servido após falha: %s", key, type(exc).__name__
                    )
                    return entry
                raise

    async def refresh(self, key: str, load: Callable[[], Awaitable[Rows]]) -> Entry:
        """Aquecedor: busca sem segurar a trava (usuários seguem lendo o dado atual) e troca no fim."""
        return await self._load(key, load)

    async def _load(self, key: str, load: Callable[[], Awaitable[Rows]]) -> Entry:
        started = self._clock()
        data = await load()
        entry = Entry(data=data, fetched_at=self._clock())
        self._store.set(key, entry)
        logger.info("[cache] '%s': %d linhas em %.1fs", key, len(data), entry.fetched_at - started)
        return entry


class CachedSourceFetcher:
    """SourceFetcher com cache. Guarda quando cada dado veio do banco, para o `meta.synced_at`."""

    def __init__(self, cache: SourceCache, inner: SourceFetcher, db_name: str):
        self._cache = cache
        self._inner = inner
        self._db = db_name
        self._fetched: list[float] = []

    async def fetch(self, query_name: str) -> Rows:
        entry = await self._cache.get(
            f"{self._db}:{query_name}", lambda: self._inner.fetch(query_name)
        )
        self._fetched.append(entry.fetched_at)
        return entry.data

    def synced_at(self) -> float | None:
        """Quando veio do banco o dado MAIS ANTIGO usado nesta requisição (None = nada buscado)."""
        return min(self._fetched) if self._fetched else None
