"""Cache das queries dos bancos de origem (5 min), no padrão da v1 (fetch_data_with_cache).

Protege os bancos de origem e evita que o usuário espere a query pesada (LexPre: ~22 a 50 s):
  * fresco (até `ttl`): devolve da memória (L1), sem ir ao banco;
  * vencido na memória: tenta o Redis (L2, compartilhado e que sobrevive a restart/deploy);
  * vencido há pouco (até `ttl + stale_while_revalidate`): devolve o que tem NA HORA e renova em
    segundo plano; quem pedir depois já recebe o dado novo;
  * vencido há mais tempo (ou nunca buscado): espera a busca;
  * nunca duas buscas da mesma chave ao mesmo tempo, venham elas de pessoas, da renovação em
    segundo plano ou do aquecedor: todos esperam a mesma; grava no L1 e no L2;
  * banco fora do ar: devolve o último dado bom (L1 ou L2) até `stale_max_age` (igual à v1);
    depois, o erro;
  * o aquecedor (cache_warmer.py) renova antes de vencer, então a tela quase nunca espera.

Por que servir o vencido: trocar um filtro logo depois de a query vencer (o aquecedor nem sempre chega
antes) fazia a pessoa esperar a query inteira no banco. `meta.synced_at` continua dizendo a hora real.

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


def error_name(exc: BaseException) -> str:
    """Tipo do erro e, se houver, o da causa: 'SourceUnavailable (QueryCanceledError)'.

    Só os tipos: a mensagem pode trazer host ou usuário do banco.
    """
    cause = exc.__cause__
    return f"{type(exc).__name__} ({type(cause).__name__})" if cause else type(exc).__name__


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
        stale_while_revalidate: float = 600,
    ):
        self._store = store
        self._ttl = ttl
        self._stale_max_age = stale_max_age
        self._clock = clock
        self._shared: CacheService = shared or NullCache()
        self._shared_ttl: TtlFor = shared_ttl or (lambda _key: int(ttl))
        self._swr = stale_while_revalidate
        self._locks: dict[str, asyncio.Lock] = {}
        self._loading: dict[str, asyncio.Task[Entry]] = {}  # a busca em andamento de cada chave

    def fetched_at(self, key: str) -> float | None:
        """Quando o dado dessa chave veio do banco (None = ainda não buscado)."""
        entry = self._store.get(key)
        return entry.fetched_at if entry is not None else None

    def _age(self, entry: Entry) -> float:
        return self._clock() - entry.fetched_at

    def _fresh(self, entry: Entry | None) -> bool:
        return entry is not None and self._age(entry) < self._ttl

    def _servable(self, entry: Entry | None) -> bool:
        """Fresco ou vencido há pouco: vai para a tela na hora (o vencido é renovado em segundo plano)."""
        return entry is not None and self._age(entry) < self._ttl + self._swr

    async def _from_shared(self, key: str) -> Entry | None:
        value = await self._shared.get(key)
        return value if isinstance(value, Entry) else None

    async def get(self, key: str, load: Callable[[], Awaitable[Rows]]) -> Entry:
        """Memória se fresco; senão Redis se fresco; vencido há pouco = devolve e renova em segundo plano;
        senão espera a busca (uma por chave).

        Banco fora = último dado bom (o mais recente entre memória e Redis).
        """
        entry = self._store.get(key)
        if self._fresh(entry):
            return entry
        if self._servable(entry):
            self._renew_in_background(key, load, entry)
            return entry
        lock = self._locks.setdefault(key, asyncio.Lock())
        async with lock:
            entry = self._store.get(key)  # outra requisição pode ter buscado enquanto esperávamos
            if self._fresh(entry):
                return entry
            shared = await self._from_shared(key)
            if shared is not None and (entry is None or shared.fetched_at > entry.fetched_at):
                entry = shared  # o mais novo entre memória e Redis
                if self._servable(shared):
                    logger.info("%s: veio do Redis (de %s atrás)", key, seconds(self._age(shared)))
                    self._store.set(key, shared)
            if self._fresh(entry):
                return entry
            if self._servable(entry):
                self._renew_in_background(key, load, entry)
                return entry
            try:
                return await asyncio.shield(self._load_once(key, load))
            except Exception as exc:
                if entry is not None and self._age(entry) <= self._stale_max_age:
                    logger.warning(
                        "%s: banco falhou (%s); servindo o último dado bom, de %s atrás",
                        key,
                        error_name(exc),
                        seconds(self._age(entry)),
                    )
                    return entry
                raise

    async def refresh(self, key: str, load: Callable[[], Awaitable[Rows]]) -> Entry:
        """Aquecedor: busca sem segurar a trava (usuários seguem lendo o dado atual) e troca no fim.

        Se a chave já está sendo buscada (renovação em segundo plano), espera essa mesma busca.
        """
        return await asyncio.shield(self._load_once(key, load))

    async def wait_renewals(self) -> None:
        """Espera as buscas em andamento terminarem (testes)."""
        while self._loading:
            await asyncio.gather(*self._loading.values(), return_exceptions=True)

    def _renew_in_background(
        self, key: str, load: Callable[[], Awaitable[Rows]], served: Entry
    ) -> None:
        if key in self._loading:
            return  # já está renovando
        logger.info(
            "%s: vencido há %s; servindo o atual e renovando em segundo plano",
            key,
            seconds(self._age(served) - self._ttl),
        )
        self._load_once(key, load)

    def _load_once(self, key: str, load: Callable[[], Awaitable[Rows]]) -> asyncio.Task[Entry]:
        """A busca em andamento dessa chave ou, se não houver, uma nova (nunca duas juntas).

        É uma tarefa à parte: quem espera a busca usa `asyncio.shield`, então uma requisição cancelada
        (a pessoa desistiu) não cancela a busca que os outros estão esperando.
        """
        task = self._loading.get(key)
        if task is None:
            task = asyncio.create_task(self._load(key, load), name=f"source_cache:{key}")
            self._loading[key] = task
            task.add_done_callback(lambda done: self._loaded(key, done))
        return task

    def _loaded(self, key: str, task: asyncio.Task[Entry]) -> None:
        if self._loading.get(key) is task:
            del self._loading[key]
        if not task.cancelled():
            task.exception()  # já registrada em _load; lida aqui para o asyncio não reclamar

    async def _load(self, key: str, load: Callable[[], Awaitable[Rows]]) -> Entry:
        started = self._clock()
        logger.info("%s: buscando no banco...", key)
        try:
            data = await load()
        except Exception as exc:
            logger.warning(
                "%s: falhou após %s (%s)", key, seconds(self._clock() - started), error_name(exc)
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
