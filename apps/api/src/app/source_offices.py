"""Escritórios do LexPre e do LexFlow para o Conectar fonte. Só a TI da LexGroup usa.

  * OfficesRepo          banco da plataforma: quem é TI da LexGroup (app_private.is_source_admin) e
                         quais escritórios já estão ligados a uma unidade (app.unit_source_refs).
  * ProductOfficeReader  banco do produto: id, nome e atividade de cada escritório, com cache de
                         10 min (a consulta conta linhas no banco de produção).
  * build_offices        junta os dois no formato da tela.
A ligação em si é a RPC api.link_product_office (o front chama direto no Supabase).
"""

import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Annotated, Literal, Protocol

import asyncpg
from fastapi import Depends, Request
from pydantic import BaseModel

from app.access import get_db_pool
from app.database import (
    DatabaseManager,
    fetch_read_only,
    get_databases,
    run_with_connection_retry,
)

Product = Literal["lexpre", "lexflow"]

# Os 3 escritórios do LexFlow que os dashboards já conhecem ficam ligados pelo código da v1, não pelo
# id do banco. Mesmo mapa de app_private.product_ref (migration 20261117100000_conectar_fonte.sql).
LEXFLOW_LEGACY_REFS = {"NG": "20", "LA": "21", "RJ": "27"}

# Uma linha por escritório: ref (id no banco), nome e um número de atividade para a TI reconhecer.
_OFFICES_SQL: dict[str, str] = {
    "lexpre": """
        select e.id::text as ref, e.nome as name, coalesce(a.n, 0)::int as activity
          from public.escritorio e
          left join (select l.escritorio_id, count(*) as n
                       from public.log_setor_demanda l
                      where l.data >= now() - interval '30 days'
                      group by l.escritorio_id) a on a.escritorio_id = e.id
         order by e.nome
    """,
    "lexflow": """
        select ea.id::text as ref, ea.razao_social as name, coalesce(p.n, 0)::int as activity
          from public.escritorio_assinante ea
          left join (select p.id_escritorio_assinante, count(*) as n
                       from public.processo p
                      group by p.id_escritorio_assinante) p on p.id_escritorio_assinante = ea.id
         order by ea.razao_social
    """,
}

ACTIVITY_LABEL: dict[str, str] = {
    "lexpre": "movimentações nos últimos 30 dias",
    "lexflow": "processos",
}


@dataclass(frozen=True)
class OfficeRow:
    ref: str
    name: str
    activity: int


@dataclass(frozen=True)
class LinkedUnit:
    org: str
    unit: str
    unit_name: str


# --- Saída ------------------------------------------------------------------


class LinkedOut(BaseModel):
    org: str
    unit: str
    unitName: str


class OfficeOut(BaseModel):
    ref: str
    name: str
    activity: int
    linkedTo: LinkedOut | None


class OfficesOut(BaseModel):
    product: str
    activityLabel: str
    offices: list[OfficeOut]


def build_offices(product: str, rows: list[OfficeRow], linked: dict[str, LinkedUnit]) -> OfficesOut:
    """Cada escritório com a unidade a que já está ligado (de qualquer organização), ou None."""
    by_db_id = {
        (LEXFLOW_LEGACY_REFS.get(ref, ref) if product == "lexflow" else ref): unit
        for ref, unit in linked.items()
    }
    return OfficesOut(
        product=product,
        activityLabel=ACTIVITY_LABEL[product],
        offices=[
            OfficeOut(
                ref=row.ref,
                name=row.name,
                activity=row.activity,
                linkedTo=(
                    LinkedOut(org=u.org, unit=u.unit, unitName=u.unit_name)
                    if (u := by_db_id.get(row.ref)) is not None
                    else None
                ),
            )
            for row in rows
        ],
    )


# --- Banco da plataforma -------------------------------------------------------


class OfficesRepo(Protocol):
    async def is_source_admin(self, user_id: str) -> bool: ...

    async def linked(self, product: str) -> dict[str, LinkedUnit]: ...


_IS_ADMIN_SQL = "select app_private.is_source_admin($1::uuid)"

_LINKED_SQL = """
select r.ref, o.name as org, u.code as unit, u.name as unit_name
  from app.unit_source_refs r
  join app.units u on u.id = r.unit_id
  join app.organizations o on o.id = u.org_id
 where r.source = $1
"""


class PgOfficesRepo:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def is_source_admin(self, user_id: str) -> bool:
        return bool(await self._pool.fetchval(_IS_ADMIN_SQL, user_id))

    async def linked(self, product: str) -> dict[str, LinkedUnit]:
        rows = await self._pool.fetch(_LINKED_SQL, product)
        return {
            r["ref"]: LinkedUnit(org=r["org"], unit=r["unit"], unit_name=r["unit_name"])
            for r in rows
        }


def get_offices_repo(pool: Annotated[asyncpg.Pool, Depends(get_db_pool)]) -> OfficesRepo:
    return PgOfficesRepo(pool)


# --- Banco do produto ------------------------------------------------------------

OfficeFetch = Callable[[str], Awaitable[list[OfficeRow]]]


class ProductOfficeReader:
    """Lê os escritórios de um produto e guarda por `ttl_seconds` (por réplica)."""

    def __init__(
        self,
        fetch: OfficeFetch,
        ttl_seconds: float = 600,
        clock: Callable[[], float] = time.monotonic,
    ):
        self._fetch = fetch
        self._ttl = ttl_seconds
        self._clock = clock
        self._cache: dict[str, tuple[float, list[OfficeRow]]] = {}

    async def __call__(self, product: str) -> list[OfficeRow]:
        hit = self._cache.get(product)
        if hit is not None and self._clock() - hit[0] < self._ttl:
            return hit[1]
        rows = await self._fetch(product)
        self._cache[product] = (self._clock(), rows)
        return rows


def office_fetch(manager: DatabaseManager) -> OfficeFetch:
    """Busca no banco do produto em transação só leitura; banco desligado ou fora = SourceUnavailable."""

    async def fetch(product: str) -> list[OfficeRow]:
        rows = await run_with_connection_retry(
            manager,
            product,
            lambda conn: fetch_read_only(conn, _OFFICES_SQL[product]),
            operation_name=f"offices_{product}",
        )
        return [OfficeRow(ref=r["ref"], name=r["name"], activity=r["activity"]) for r in rows]

    return fetch


def get_office_reader(
    request: Request,
    manager: Annotated[DatabaseManager, Depends(get_databases)],
) -> OfficeFetch:
    """Um leitor por aplicação: o cache de 10 min vale entre as requisições."""
    reader = getattr(request.app.state, "office_reader", None)
    if reader is None:
        reader = ProductOfficeReader(office_fetch(manager))
        request.app.state.office_reader = reader
    return reader
