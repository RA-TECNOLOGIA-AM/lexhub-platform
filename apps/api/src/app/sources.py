"""Bancos de origem para os dashboards: qual unidade é qual na fonte, e a busca das queries da v1.

  * SourceRefsRepo   quem é quem na fonte: unidade -> id (app.unit_source_refs; NG -> lexpre -> "1")
                     e pessoa -> funcionário (app.member_source_refs; ex.: nome do funcionário no LexPre).
  * PgSourceFetcher  roda uma query registrada em app/source_queries.py no banco de origem,
                     com as tentativas da v1 (run_with_connection_retry) e o limite de consultas por banco.
O cache de 5 min entra embrulhando o SourceFetcher (mesma interface), sem mudar os módulos.
"""

import time
from collections.abc import Callable
from typing import Annotated, Any, Protocol

import asyncpg
from fastapi import Depends, Request

from app.access import get_db_pool
from app.dashboards.base import SourceFetcher
from app.database import DatabaseManager, get_databases, run_with_connection_retry
from app.source_cache import CachedSourceFetcher, SourceCache
from app.source_queries import QUERIES


class SourceUnavailable(Exception):
    """Banco de origem desligado ou fora do ar (ex.: LexPre fora da rede da empresa)."""


class SourceRefsRepo(Protocol):
    async def unit_ref(self, unit_id: str, source_db: str) -> str | None: ...

    # A pessoa logada naquela organização, como aparece na fonte; None = vínculo ainda não feito.
    async def member_ref(self, user_id: str, org_id: str, source_db: str) -> str | None: ...


_UNIT_REF_SQL = """
select r.ref from app.unit_source_refs r where r.unit_id = $1::uuid and r.source = $2
"""

_MEMBER_REF_SQL = """
select r.ref
  from app.member_source_refs r
  join app.memberships m on m.id = r.membership_id
 where m.user_id = $1::uuid and m.org_id = $2::uuid and m.status = 'active' and r.source = $3
"""


class PgSourceRefsRepo:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def unit_ref(self, unit_id: str, source_db: str) -> str | None:
        return await self._pool.fetchval(_UNIT_REF_SQL, unit_id, source_db)

    async def member_ref(self, user_id: str, org_id: str, source_db: str) -> str | None:
        return await self._pool.fetchval(_MEMBER_REF_SQL, user_id, org_id, source_db)


def get_source_refs_repo(pool: Annotated[asyncpg.Pool, Depends(get_db_pool)]) -> SourceRefsRepo:
    return PgSourceRefsRepo(pool)


class PgSourceFetcher:
    def __init__(self, manager: DatabaseManager, db_name: str, queries: dict[str, dict] = QUERIES):
        self._manager = manager
        self._db = db_name
        self._queries = queries
        self._fetched: list[float] = []

    async def fetch(self, query_name: str) -> list[dict[str, Any]]:
        spec = self._queries[query_name]  # KeyError = query não copiada da v1: erro de programação
        if spec["database"] != self._db:
            raise ValueError(f"Query {query_name} é do banco {spec['database']}, não de {self._db}")
        try:
            rows = await run_with_connection_retry(
                self._manager,
                self._db,
                lambda conn: conn.fetch(spec["query"]),
                operation_name=query_name,
            )
        except ValueError as exc:  # pool não inicializado (banco off ou down na subida)
            raise SourceUnavailable(self._db) from exc
        self._fetched.append(time.time())
        return [dict(r) for r in rows]

    def synced_at(self) -> float | None:
        return min(self._fetched) if self._fetched else None


SourceFactory = Callable[[str], SourceFetcher]


def get_source_cache(request: Request) -> SourceCache:
    return request.app.state.source_cache


def get_source_factory(
    manager: Annotated[DatabaseManager, Depends(get_databases)],
    cache: Annotated[SourceCache, Depends(get_source_cache)],
) -> SourceFactory:
    """Dependency: db_name -> SourceFetcher daquele banco de origem, com o cache de 5 min."""
    return lambda db_name: CachedSourceFetcher(cache, PgSourceFetcher(manager, db_name), db_name)
