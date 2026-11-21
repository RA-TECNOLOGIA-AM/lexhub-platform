"""Cache das queries dos bancos de origem (5 min), no padrão da v1 (fetch_data_with_cache).

Protege os bancos de origem e evita que o usuário espere a query (as do banco NG são as mais lentas):
  * fresco (até `ttl`): devolve da memória (L1), sem ir ao banco;
  * vencido na memória: tenta o Redis (L2, compartilhado e que sobrevive a restart/deploy);
  * vencido há pouco (até `ttl + stale_while_revalidate`): devolve o que tem NA HORA e renova em
    segundo plano; quem pedir depois já recebe o dado novo;
  * vencido há mais tempo (ou nunca buscado): espera a busca;
  * nunca duas buscas da mesma chave ao mesmo tempo, venham elas de pessoas, da renovação em
    segundo plano ou do aquecedor: todos esperam a mesma; grava no L1 e no L2;
  * banco fora do ar: devolve o último dado bom (L1 ou L2) até `stale_max_age` (igual à v1);
    depois, o erro;
  * o aquecedor (cache_warmer.py) renova antes de vencer o que alguém leu há pouco (`read_within`),
    então a tela em uso quase nunca espera;
  * validade por banco (`ttl_by_db`): o LexFlow (Supabase, egress cobrado) fica mais tempo;
  * "só baixa se mudou" nos bancos de `probe_dbs`: na renovação, o banco devolve primeiro uma impressão
    digital do resultado (uma linha); igual à da versão guardada, o dado é mantido e só o relógio anda
    (nada é baixado). Ver `PgSourceFetcher.fetch_if_changed` em app/sources.py.

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
from collections.abc import Awaitable, Callable, Collection, Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from app.cache import CacheService, NullCache
from app.dashboards.base import SourceFetcher
from app.logs import seconds

logger = logging.getLogger(__name__)

Rows = list[dict[str, Any]]
Clock = Callable[[], float]
TtlFor = Callable[[str], int]
# Busca condicional: recebe a impressão digital da versão guardada (None = nenhuma) e devolve
# (linhas, impressão digital do que está no banco); linhas None = igual à guardada, nada foi baixado.
LoadIfChanged = Callable[[str | None], Awaitable[tuple[Rows | None, str]]]

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


def _milhar(n: int) -> str:
    """12345 -> '12.345'."""
    return f"{n:,}".replace(",", ".")


def db_of(key: str) -> str:
    """O banco de uma chave 'banco:query'."""
    return key.split(":", 1)[0]


def ttl_by_query(heavy_ttl: int, default_ttl: int) -> TtlFor:
    """TTL no Redis por chave 'banco:query' (regra `_redis_ttl` da v1)."""

    def ttl_for(key: str) -> int:
        return heavy_ttl if key.split(":", 1)[-1] in HEAVY_QUERIES else default_ttl

    return ttl_for


def shared_ttl_covering(base: TtlFor, ttl_by_db: Mapping[str, float], swr: float) -> TtlFor:
    """TTL no Redis: o de `base`, mas a chave de um banco com validade própria (`ttl_by_db`) dura no
    Redis pelo menos essa validade + o stale-while-revalidate, para sobreviver a um deploy."""

    def ttl_for(key: str) -> int:
        own = ttl_by_db.get(db_of(key))
        return base(key) if own is None else max(base(key), int(own + swr))

    return ttl_for


@dataclass(frozen=True)
class Entry:
    data: Rows
    fetched_at: float  # epoch (s) em que o banco confirmou este dado (busca ou conferência)
    # Impressão digital do resultado no banco (só nos bancos com "só baixa se mudou"); None = sem.
    fingerprint: str | None = None
    # Epoch (s) em que este dado foi baixado; None = fetched_at. Uma conferência sem mudança mantém a
    # versão, então os cálculos guardados (app/result_memo.py) continuam valendo.
    version: float | None = None

    @property
    def data_version(self) -> float:
        return self.fetched_at if self.version is None else self.version


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
        ttl_by_db: Mapping[str, float] | None = None,
        probe_dbs: Collection[str] = (),
        stats_every: float = 3600,
    ):
        self._store = store
        # Resumo no log do que saiu dos bancos (egress), a cada `stats_every` s: banco -> contadores.
        self._stats_every = stats_every
        self._stats: dict[str, dict[str, int]] = {}
        self._stats_since = clock()
        self._ttl = ttl
        self._ttl_by_db = dict(ttl_by_db or {})
        self._probe_dbs = frozenset(probe_dbs)
        self._stale_max_age = stale_max_age
        self._clock = clock
        self._shared: CacheService = shared or NullCache()
        self._shared_ttl: TtlFor = shared_ttl or (lambda key: int(self.ttl_of(key)))
        self._swr = stale_while_revalidate
        self._locks: dict[str, asyncio.Lock] = {}
        self._loading: dict[str, asyncio.Task[Entry]] = {}  # a busca em andamento de cada chave
        # Última leitura de cada chave por um pedido (`get`); a renovação do aquecedor não conta.
        self._last_read: dict[str, float] = {}

    def read_within(self, key: str, seconds: float) -> bool:
        """Algum pedido leu essa chave nos últimos `seconds` (o aquecedor só renova essas)."""
        last = self._last_read.get(key)
        return last is not None and self._clock() - last <= seconds

    def fetched_at(self, key: str) -> float | None:
        """Quando o dado dessa chave veio do banco (None = ainda não buscado)."""
        entry = self._store.get(key)
        return entry.fetched_at if entry is not None else None

    def ttl_of(self, key: str) -> float:
        """Validade da chave 'banco:query': a do banco (`ttl_by_db`) ou a padrão."""
        return self._ttl_by_db.get(db_of(key), self._ttl)

    def _age(self, entry: Entry) -> float:
        return self._clock() - entry.fetched_at

    def _fresh(self, key: str, entry: Entry | None) -> bool:
        return entry is not None and self._age(entry) < self.ttl_of(key)

    def _servable(self, key: str, entry: Entry | None) -> bool:
        """Fresco ou vencido há pouco: vai para a tela na hora (o vencido é renovado em segundo plano)."""
        return entry is not None and self._age(entry) < self.ttl_of(key) + self._swr

    def _probe(self, key: str, changed: LoadIfChanged | None) -> LoadIfChanged | None:
        """A busca condicional, só nos bancos de `probe_dbs` (nos outros, a busca de sempre)."""
        return changed if db_of(key) in self._probe_dbs else None

    async def _from_shared(self, key: str) -> Entry | None:
        value = await self._shared.get(key)
        return value if isinstance(value, Entry) else None

    async def get(
        self,
        key: str,
        load: Callable[[], Awaitable[Rows]],
        changed: LoadIfChanged | None = None,
    ) -> Entry:
        """Memória se fresco; senão Redis se fresco; vencido há pouco = devolve e renova em segundo plano;
        senão espera a busca (uma por chave).

        Banco fora = último dado bom (o mais recente entre memória e Redis).
        `changed`: a busca condicional ("só baixa se mudou"), usada nos bancos de `probe_dbs`.
        """
        self._last_read[key] = self._clock()
        changed = self._probe(key, changed)
        entry = self._store.get(key)
        if self._fresh(key, entry):
            return entry
        if self._servable(key, entry):
            self._renew_in_background(key, load, entry, changed)
            return entry
        lock = self._locks.setdefault(key, asyncio.Lock())
        async with lock:
            entry = self._store.get(key)  # outra requisição pode ter buscado enquanto esperávamos
            if self._fresh(key, entry):
                return entry
            shared = await self._from_shared(key)
            if shared is not None and (entry is None or shared.fetched_at > entry.fetched_at):
                entry = shared  # o mais novo entre memória e Redis
                if self._servable(key, shared):
                    logger.info("%s: veio do Redis (de %s atrás)", key, seconds(self._age(shared)))
                    self._store.set(key, shared)
            if self._fresh(key, entry):
                return entry
            if self._servable(key, entry):
                self._renew_in_background(key, load, entry, changed)
                return entry
            try:
                # Mesmo vencido há muito, o dado guardado serve de base para a conferência: se o
                # banco disser que nada mudou, nada é baixado.
                return await asyncio.shield(self._load_once(key, load, changed, entry))
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

    async def refresh(
        self,
        key: str,
        load: Callable[[], Awaitable[Rows]],
        changed: LoadIfChanged | None = None,
    ) -> Entry:
        """Aquecedor: busca sem segurar a trava (usuários seguem lendo o dado atual) e troca no fim.

        Se a chave já está sendo buscada (renovação em segundo plano), espera essa mesma busca.
        """
        changed = self._probe(key, changed)
        return await asyncio.shield(self._load_once(key, load, changed, self._store.get(key)))

    async def wait_renewals(self) -> None:
        """Espera as buscas em andamento terminarem (testes)."""
        while self._loading:
            await asyncio.gather(*self._loading.values(), return_exceptions=True)

    def _renew_in_background(
        self,
        key: str,
        load: Callable[[], Awaitable[Rows]],
        served: Entry,
        changed: LoadIfChanged | None = None,
    ) -> None:
        if key in self._loading:
            return  # já está renovando
        logger.info(
            "%s: vencido há %s; servindo o atual e renovando em segundo plano",
            key,
            seconds(self._age(served) - self.ttl_of(key)),
        )
        self._load_once(key, load, changed, served)

    def _load_once(
        self,
        key: str,
        load: Callable[[], Awaitable[Rows]],
        changed: LoadIfChanged | None = None,
        known: Entry | None = None,
    ) -> asyncio.Task[Entry]:
        """A busca em andamento dessa chave ou, se não houver, uma nova (nunca duas juntas).

        É uma tarefa à parte: quem espera a busca usa `asyncio.shield`, então uma requisição cancelada
        (a pessoa desistiu) não cancela a busca que os outros estão esperando.
        `known`: o dado guardado que a busca condicional (`changed`) compara com o banco.
        """
        task = self._loading.get(key)
        if task is None:
            task = asyncio.create_task(
                self._load(key, load, changed, known), name=f"source_cache:{key}"
            )
            self._loading[key] = task
            task.add_done_callback(lambda done: self._loaded(key, done))
        return task

    def _loaded(self, key: str, task: asyncio.Task[Entry]) -> None:
        if self._loading.get(key) is task:
            del self._loading[key]
        if not task.cancelled():
            task.exception()  # já registrada em _load; lida aqui para o asyncio não reclamar

    async def _load(
        self,
        key: str,
        load: Callable[[], Awaitable[Rows]],
        changed: LoadIfChanged | None = None,
        known: Entry | None = None,
    ) -> Entry:
        started = self._clock()
        # A conferência compara com o dado mais novo que se tem (memória; ou o do Redis que `get` achou).
        stored = self._store.get(key)
        if known is None or (stored is not None and stored.fetched_at > known.fetched_at):
            known = stored
        base = known if known is not None and known.fingerprint is not None else None
        logger.info("%s: %s no banco...", key, "conferindo" if changed and base else "buscando")
        try:
            if changed is None:
                data, fingerprint = await load(), None
            else:
                data, fingerprint = await changed(base.fingerprint if base else None)
        except Exception as exc:
            logger.warning(
                "%s: falhou após %s (%s)", key, seconds(self._clock() - started), error_name(exc)
            )
            raise
        if data is None and base is None:
            # Busca condicional que não devolveu linhas sem ter com o que comparar: não deveria
            # acontecer; baixa do jeito de sempre em vez de guardar um dado que não existe.
            logger.warning("%s: conferência sem dado guardado; buscando tudo", key)
            data, fingerprint = await load(), None
        if data is None:
            # O banco confirmou que nada mudou: o mesmo dado, conferido agora (nada foi baixado).
            entry = Entry(
                data=base.data,
                fetched_at=self._clock(),
                fingerprint=fingerprint,
                version=base.data_version,
            )
        else:
            entry = Entry(data=data, fetched_at=self._clock(), fingerprint=fingerprint)
        self._store.set(key, entry)
        await self._shared.set(
            key, entry, self._shared_ttl(key)
        )  # nunca levanta (ver app/cache.py)
        if data is None:
            logger.info(
                "%s: sem mudança, nada baixado; conferido em %s (vale por %s)",
                key,
                seconds(entry.fetched_at - started),
                seconds(self.ttl_of(key)),
            )
        else:
            logger.info(
                "%s: %s linhas em %s (vale por %s)",
                key,
                _milhar(len(data)),
                seconds(entry.fetched_at - started),
                seconds(self.ttl_of(key)),
            )
        self._count(key, None if data is None else len(data))
        return entry

    def _count(self, key: str, rows: int | None) -> None:
        """Conta o que saiu do banco (rows) ou a conferência sem mudança (None) e, passado `stats_every`,
        escreve o resumo no log e zera. É por ele que se acompanha o egress sem o painel do Supabase."""
        s = self._stats.setdefault(db_of(key), {"baixadas": 0, "linhas": 0, "sem_mudanca": 0})
        if rows is None:
            s["sem_mudanca"] += 1
        else:
            s["baixadas"] += 1
            s["linhas"] += rows
        decorrido = self._clock() - self._stats_since
        if decorrido < self._stats_every:
            return
        partes = [
            f"{db}: {c['baixadas']} baixadas ({_milhar(c['linhas'])} linhas), "
            f"{c['sem_mudanca']} conferidas sem mudança"
            for db, c in sorted(self._stats.items())
        ]
        logger.info("Bancos de origem nos últimos %s: %s", seconds(decorrido), "; ".join(partes))
        self._stats = {}
        self._stats_since = self._clock()


class CachedSourceFetcher:
    """SourceFetcher com cache. Guarda quando cada dado veio do banco, para o `meta.synced_at`."""

    def __init__(self, cache: SourceCache, inner: SourceFetcher, db_name: str):
        self._cache = cache
        self._inner = inner
        self._db = db_name
        self._fetched: list[float] = []
        # (query, versão do dado) de cada leitura, na ordem: a memória dos cálculos (app/result_memo.py)
        # guarda de que versão dos dados cada resultado saiu.
        self.reads: list[tuple[str, float]] = []

    async def fetch(self, query_name: str) -> Rows:
        return (await self._read(query_name)).data

    async def version(self, query_name: str) -> float:
        """Quando foi baixado o dado que `fetch` devolveria agora (conta como leitura). Uma conferência
        sem mudança não muda a versão."""
        return (await self._read(query_name)).data_version

    async def _read(self, query_name: str) -> Entry:
        # Busca condicional, se a fonte souber fazer (o cache só usa nos bancos de probe_dbs).
        if_changed = getattr(self._inner, "fetch_if_changed", None)
        changed = (lambda known: if_changed(query_name, known)) if callable(if_changed) else None
        entry = await self._cache.get(
            f"{self._db}:{query_name}", lambda: self._inner.fetch(query_name), changed
        )
        self._fetched.append(entry.fetched_at)
        self.reads.append((query_name, entry.data_version))
        return entry

    def synced_at(self) -> float | None:
        """Quando veio do banco o dado MAIS ANTIGO usado nesta requisição (None = nada buscado)."""
        return min(self._fetched) if self._fetched else None
