"""Bancos de origem para os dashboards: qual unidade é qual na fonte, e a busca das queries da v1.

  * SourceRefsRepo   pessoa -> funcionário na fonte (app.member_source_refs; ex.: nome no LexPre).
                     Unidade -> id na fonte (app.unit_source_refs) vem junto com o acesso (access.py).
  * PgSourceFetcher  roda uma query registrada em app/source_queries.py no banco de origem,
                     com as tentativas da v1 (run_with_connection_retry) e o limite de consultas por banco.
O cache de 5 min entra embrulhando o SourceFetcher (mesma interface), sem mudar os módulos.
"""

import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Annotated, Any, Protocol

import asyncpg
from fastapi import Depends, Request

from app.access import get_db_pool
from app.config import SOURCE_DATABASES
from app.dashboards.base import SourceFetcher
from app.database import (
    DatabaseManager,
    SourceUnavailable,
    fetch_read_only,
    fetch_read_only_if_changed,
    get_databases,
    run_with_connection_retry,
)
from app.source_cache import CachedSourceFetcher, SourceCache
from app.source_queries import QUERIES
from app.unit_scope import ordem_canonica, scoped_sql, split_scoped

if TYPE_CHECKING:
    from app.registered_sources import RegisteredSources
    from app.source_switch import SourceSwitch

# SourceUnavailable mora em app.database; segue importável daqui porque as cópias da v1 em
# app/analyses (que não editamos, para comparar linha a linha) importam de app.sources.
__all__ = ["SourceUnavailable"]


class SourceRefsRepo(Protocol):
    # A pessoa logada naquela organização, como aparece na fonte; None = vínculo ainda não feito.
    async def member_ref(self, user_id: str, org_id: str, source_db: str) -> str | None: ...

    # Das contas de anúncios da Meta da unidade (keys 'fb_...'), as que o Marketing já pode ler: as ligadas,
    # se TODAS as ligadas já têm o histórico completo; senão nenhuma (a unidade segue no banco ng).
    async def ads_ready(self, keys: list[str]) -> list[str]: ...


_MEMBER_REF_SQL = """
select r.ref
  from app.member_source_refs r
  join app.memberships m on m.id = r.membership_id
 where m.user_id = $1::uuid and m.org_id = $2::uuid and m.status = 'active' and r.source = $3
"""


# Conta pronta = o histórico da personalização atual já foi todo coletado (app.facebook_ads_sync_state,
# conjunto 'ads', app/facebook_ads_sync.py). Uma conta ainda carregando deixaria o gasto da unidade pela
# metade; a desligada na tela fica de fora.
_ADS_READY_SQL = """
select ds.key,
       ds.enabled,
       coalesce(s.backfill_done, false)
         and s.collect_version = coalesce((ds.config ->> 'collect_version')::int, 1) as ready
  from app.data_sources ds
  left join app.facebook_ads_sync_state s on s.source_id = ds.id and s.dataset = 'ads'
 where ds.key = any($1::text[]) and ds.active and ds.connector = 'facebook_ads'
 order by ds.key
"""


class PgSourceRefsRepo:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def member_ref(self, user_id: str, org_id: str, source_db: str) -> str | None:
        return await self._pool.fetchval(_MEMBER_REF_SQL, user_id, org_id, source_db)

    async def ads_ready(self, keys: list[str]) -> list[str]:
        if not keys:
            return []
        ligadas = [r for r in await self._pool.fetch(_ADS_READY_SQL, keys) if r["enabled"]]
        if not all(r["ready"] for r in ligadas):
            return []
        return [r["key"] for r in ligadas]


def get_source_refs_repo(pool: Annotated[asyncpg.Pool, Depends(get_db_pool)]) -> SourceRefsRepo:
    return PgSourceRefsRepo(pool)


class PgSourceFetcher:
    def __init__(self, manager: DatabaseManager, db_name: str, queries: dict[str, dict] = QUERIES):
        self._manager = manager
        self._db = db_name
        self._queries = queries
        self._fetched: list[float] = []

    def _sql(self, query_name: str) -> str:
        """O SQL de uma query registrada; 'nome@escritorio' = a mesma query só com as linhas daquele
        escritório (app/unit_scope.py)."""
        base, escritorio = split_scoped(query_name)
        spec = self._queries[base]  # KeyError = query não copiada da v1: erro de programação
        if spec["database"] != self._db:
            raise ValueError(f"Query {base} é do banco {spec['database']}, não de {self._db}")
        if escritorio is None:
            return spec["query"]
        return scoped_sql(base, spec["query"], escritorio)

    async def fetch(self, query_name: str) -> list[dict[str, Any]]:
        """Banco desligado, fora do ar ou lento demais = SourceUnavailable (ver app/database.py)."""
        sql = self._sql(query_name)
        rows = await run_with_connection_retry(
            self._manager,
            self._db,
            lambda conn: fetch_read_only(conn, sql),
            operation_name=query_name,
        )
        self._fetched.append(time.time())
        return ordem_canonica(query_name, [dict(r) for r in rows])

    async def fetch_if_changed(
        self, query_name: str, known: str | None
    ) -> tuple[list[dict[str, Any]] | None, str]:
        """Só baixa se mudou (ver app/database.py, fetch_read_only_if_changed): (linhas, impressão
        digital); linhas None = o resultado no banco é igual ao de `known`, nada foi baixado."""
        sql = self._sql(query_name)
        rows, fingerprint = await run_with_connection_retry(
            self._manager,
            self._db,
            lambda conn: fetch_read_only_if_changed(conn, sql, known),
            operation_name=query_name,
        )
        self._fetched.append(time.time())
        if rows is None:
            return None, fingerprint
        return ordem_canonica(query_name, [dict(r) for r in rows]), fingerprint

    def synced_at(self) -> float | None:
        return min(self._fetched) if self._fetched else None


SourceFactory = Callable[[str], SourceFetcher]


def get_source_cache(request: Request) -> SourceCache:
    return request.app.state.source_cache


class _NoPlatformDb:
    """Fonte da tela sem o banco da plataforma (API de teste local sem DATABASE_URL): indisponível."""

    def __init__(self, db_name: str):
        self._db = db_name

    async def fetch(self, query_name: str) -> list[dict[str, Any]]:
        raise SourceUnavailable(self._db)

    def synced_at(self) -> float | None:
        return None


def source_fetcher(
    manager: DatabaseManager, db_name: str, registered: "RegisteredSources | None" = None
) -> SourceFetcher:
    """O leitor de uma fonte, sem cache: banco do .env (Postgres) ou fonte com o segredo cifrado no banco
    da plataforma (banco próprio ou planilha, inclusive as antigas sheets_financeiro_*;
    app/registered_sources.py)."""
    from app.registered_sources import RegisteredSourceFetcher

    if db_name in SOURCE_DATABASES:
        return PgSourceFetcher(manager, db_name)
    if registered is None:
        return _NoPlatformDb(db_name)
    return RegisteredSourceFetcher(registered, db_name)


def get_registered_sources(request: Request) -> "RegisteredSources | None":
    """As fontes conectadas pela tela (None sem o banco da plataforma)."""
    return getattr(request.app.state, "registered_sources", None)


def get_source_switch(request: Request) -> "SourceSwitch | None":
    """O liga/desliga das fontes (None sem o banco da plataforma)."""
    return getattr(request.app.state, "source_switch", None)


def build_source_factory(
    manager: DatabaseManager,
    cache: SourceCache,
    registered: "RegisteredSources | None",
    switch: "SourceSwitch | None",
) -> SourceFactory:
    """db_name -> SourceFetcher com o cache de 5 min. Fonte da tela passa antes pelo liga/desliga
    (por fora do cache: desligada não serve nem o último dado bom)."""
    from app.source_switch import GuardedSourceFetcher

    def factory(db_name: str) -> SourceFetcher:
        cached = CachedSourceFetcher(cache, source_fetcher(manager, db_name, registered), db_name)
        if db_name in SOURCE_DATABASES or switch is None:
            return cached
        return GuardedSourceFetcher(switch, cached, db_name)

    return factory


def get_source_factory(
    manager: Annotated[DatabaseManager, Depends(get_databases)],
    cache: Annotated[SourceCache, Depends(get_source_cache)],
    # Any: o FastAPI lê estas anotações em tempo de execução (os tipos só existem no TYPE_CHECKING).
    registered: Annotated[Any, Depends(get_registered_sources)],
    switch: Annotated[Any, Depends(get_source_switch)],
) -> SourceFactory:
    """Dependency: db_name -> SourceFetcher daquela fonte (banco ou planilha), com o cache de 5 min."""
    return build_source_factory(manager, cache, registered, switch)
