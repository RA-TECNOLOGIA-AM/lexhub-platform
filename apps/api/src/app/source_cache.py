"""Cache das queries dos bancos de origem (5 min), no padrão da v1 (fetch_data_with_cache).

Protege os bancos de origem e evita que o usuário espere a query pesada (LexPre: ~22 a 50 s):
  * fresco (até `ttl`): devolve da memória (L1), sem ir ao banco;
  * vencido na memória: tenta o Redis (L2, compartilhado e que sobrevive a restart/deploy);
  * vencido nos dois: UMA busca por chave, mesmo com várias pessoas abrindo juntas (trava por chave),
    e grava no L1 e no L2;
  * banco fora do ar: devolve o último dado bom (L1 ou L2) até `stale_max_age` (igual à v1);
    depois, o erro;
  * o aquecedor (cache_warmer.py) renova antes de vencer, então a tela quase nunca espera.

Diferença para a v1: o dado do Redis só vale como "fresco" se `fetched_at` estiver dentro do `ttl`
(a v1 aceitava qualquer coisa ainda no Redis e reiniciava o relógio, podendo servir dado de 15 min).

Peças trocáveis:
  * CacheStore    L1, na memória do processo (MemoryStore);
  * CacheService  L2 compartilhado (RedisCache, ou NullCache = desligado), ver app/cache.py;
  * SourceCache   as regras acima (independe de banco);
  * CachedSourceFetcher  o SourceFetcher com cache, que os módulos de dashboard usam sem saber.
"""

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Protocol

from app.cache import CacheService, NullCache
from app.dashboards.base import SourceFetcher
from app.logs import seconds

logger = logging.getLogger(__name__)

Rows = list[dict[str, Any]]
Clock = Callable[[], float]
TtlFor = Callable[[str], int]

# Queries pesadas da v1 (HEAVY_DB_QUERIES): ficam mais tempo no Redis (CACHE_TTL_HEAVY),
# cobrindo o intervalo entre dois ciclos do aquecedor.
HEAVY_QUERIES: frozenset[str] = frozenset(
    {
        "comercial_geral_NG",
        "comercial_geral_LA",
        "actions_NG_2",
        "andamento_processual_NG",
        "andamento_processual_LA",
    }
)


def ttl_by_query(heavy_ttl: int, default_ttl: int) -> TtlFor:
    """TTL no Redis por chave 'banco:query' (regra `_redis_ttl` da v1)."""

    def ttl_for(key: str) -> int:
        return heavy_ttl if key.split(":", 1)[-1] in HEAVY_QUERIES else default_ttl

    return ttl_for


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
        shared: CacheService | None = None,
        shared_ttl: TtlFor | None = None,
    ):
        self._store = store
        self._ttl = ttl
        self._stale_max_age = stale_max_age
        self._clock = clock
        self._shared: CacheService = shared or NullCache()
        self._shared_ttl: TtlFor = shared_ttl or (lambda _key: int(ttl))
        self._locks: dict[str, asyncio.Lock] = {}

    def fetched_at(self, key: str) -> float | None:
        """Quando o dado dessa chave veio do banco (None = ainda não buscado)."""
        entry = self._store.get(key)
        return entry.fetched_at if entry is not None else None

    def _fresh(self, entry: Entry | None) -> bool:
        return entry is not None and self._clock() - entry.fetched_at < self._ttl

    async def _from_shared(self, key: str) -> Entry | None:
        value = await self._shared.get(key)
        return value if isinstance(value, Entry) else None

    async def get(self, key: str, load: Callable[[], Awaitable[Rows]]) -> Entry:
        """Memória se fresco; senão Redis se fresco; senão busca (uma vez por chave).

        Banco fora = último dado bom (o mais recente entre memória e Redis).
        """
        entry = self._store.get(key)
        if self._fresh(entry):
            return entry
        lock = self._locks.setdefault(key, asyncio.Lock())
        async with lock:
            entry = self._store.get(key)  # outra requisição pode ter buscado enquanto esperávamos
            if self._fresh(entry):
                return entry
            shared = await self._from_shared(key)
            if shared is not None:
                if self._fresh(shared):
                    logger.info(
                        "%s: veio do Redis (de %s atrás)",
                        key,
                        seconds(self._clock() - shared.fetched_at),
                    )
                    self._store.set(key, shared)
                    return shared
                if entry is None or shared.fetched_at > entry.fetched_at:
                    entry = shared  # melhor candidato a "último dado bom"
            try:
                return await self._load(key, load)
            except Exception as exc:
                if entry is not None and self._clock() - entry.fetched_at <= self._stale_max_age:
                    logger.warning(
                        "%s: banco falhou (%s); servindo o último dado bom, de %s atrás",
                        key,
                        type(exc).__name__,
                        seconds(self._clock() - entry.fetched_at),
                    )
                    return entry
                raise

    async def refresh(self, key: str, load: Callable[[], Awaitable[Rows]]) -> Entry:
        """Aquecedor: busca sem segurar a trava (usuários seguem lendo o dado atual) e troca no fim."""
        return await self._load(key, load)

    async def _load(self, key: str, load: Callable[[], Awaitable[Rows]]) -> Entry:
        started = self._clock()
        logger.info("%s: buscando no banco...", key)
        try:
            data = await load()
        except Exception as exc:
            logger.warning(
                "%s: falhou após %s (%s)", key, seconds(self._clock() - started), type(exc).__name__
            )
            raise
        entry = Entry(data=data, fetched_at=self._clock())
        self._store.set(key, entry)
        await self._shared.set(
            key, entry, self._shared_ttl(key)
        )  # nunca levanta (ver app/cache.py)
        logger.info(
            "%s: %s linhas em %s (vale por %s)",
            key,
            f"{len(data):,}".replace(",", "."),
            seconds(entry.fetched_at - started),
            seconds(self._ttl),
        )
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
