"""Catálogo do hub (`GET /orgs/{org}/dashboards`): só o que a pessoa pode abrir, por unidade.

Dividido em duas partes trocáveis:
  * CatalogRepo     só lê o banco (PgCatalogRepo em produção, um falso nos testes);
  * build_catalog   monta a resposta (função pura).
Quem vê o quê é a regra do banco (app_private.dashboard_scope); exportar e comissão vêm
das permissões (app_private.has_unit_permission), nunca de nomes de papel.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Protocol

import asyncpg
from fastapi import Depends
from pydantic import BaseModel

from app.access import get_db_pool

EXPORT = "dashboards.export"
SEE_ALL_ORG = "org.dashboards.all"  # owner, admin
SEE_ALL_UNIT = "unit.dashboards.all"  # gestor, controller


# --- O que o banco devolve -------------------------------------------------


@dataclass(frozen=True)
class DashboardUnitRow:
    """Um dashboard liberado para a pessoa numa unidade."""

    key: str
    title: str
    area: str
    desc: str
    source: str
    max_delay_min: int
    unit_code: str
    can_export: bool
    can_see_commission: bool


@dataclass(frozen=True)
class UpcomingRow:
    title: str
    area: str


class CatalogRepo(Protocol):
    async def list_available(self, user_id: str, org_id: str) -> list[DashboardUnitRow]: ...

    async def list_upcoming(self) -> list[UpcomingRow]: ...


# --- Resposta (tipo DashboardCatalog do front) -----------------------------


class DashboardSummaryOut(BaseModel):
    key: str
    title: str
    area: str
    desc: str
    units: list[str]
    source: str
    synced_at: datetime | None  # null até o cache de 5 min existir
    max_delay_min: int
    can_export: bool
    can_see_commission: bool


class UpcomingOut(BaseModel):
    title: str
    area: str


class DashboardCatalogOut(BaseModel):
    available: list[DashboardSummaryOut]
    upcoming: list[UpcomingOut]


# --- Regras ----------------------------------------------------------------


def build_catalog(
    rows: list[DashboardUnitRow],
    upcoming: list[UpcomingRow],
    synced_at: dict[str, datetime] | None = None,
) -> DashboardCatalogOut:
    """Junta as linhas (dashboard x unidade) num card por dashboard, na ordem em que vieram.

    can_export e can_see_commission só valem se valerem em TODAS as unidades do card: o botão
    nunca aparece numa unidade em que a API negaria (a exportação confere de novo, por unidade).
    """
    cards: dict[str, DashboardSummaryOut] = {}
    for r in rows:
        card = cards.get(r.key)
        if card is None:
            cards[r.key] = DashboardSummaryOut(
                key=r.key,
                title=r.title,
                area=r.area,
                desc=r.desc,
                units=[r.unit_code],
                source=r.source,
                synced_at=(synced_at or {}).get(r.key),
                max_delay_min=r.max_delay_min,
                can_export=r.can_export,
                can_see_commission=r.can_see_commission,
            )
            continue
        card.units.append(r.unit_code)
        card.can_export = card.can_export and r.can_export
        card.can_see_commission = card.can_see_commission and r.can_see_commission
    return DashboardCatalogOut(
        available=list(cards.values()),
        upcoming=[UpcomingOut(title=u.title, area=u.area) for u in upcoming],
    )


# --- Banco -----------------------------------------------------------------

# Uma linha por (dashboard, unidade) em que a pessoa tem acesso; ordem do hub.
_AVAILABLE_SQL = """
select d.key, d.name as title, d.area, coalesce(d.description, '') as "desc",
       d.source, d.max_delay_min, u.code as unit_code,
       app_private.has_unit_permission($1::uuid, u.id, $3) as can_export,
       (app_private.has_unit_permission($1::uuid, u.id, $4)
        or app_private.has_unit_permission($1::uuid, u.id, $5)) as can_see_commission
  from app.org_dashboards od
  join app.units u             on u.id = od.unit_id and u.active
  join app.dashboard_catalog d on d.key = od.dashboard_key and d.active and d.status = 'available'
 where od.org_id = $2::uuid
   and od.enabled
   and app_private.dashboard_scope($1::uuid, u.id, d.key) is not null
 order by d.sort_order, d.name, u.code
"""

_UPCOMING_SQL = """
select d.name as title, d.area
  from app.dashboard_catalog d
 where d.active and d.status = 'upcoming'
 order by d.sort_order, d.name
"""


class PgCatalogRepo:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def list_available(self, user_id: str, org_id: str) -> list[DashboardUnitRow]:
        rows = await self._pool.fetch(
            _AVAILABLE_SQL, user_id, org_id, EXPORT, SEE_ALL_ORG, SEE_ALL_UNIT
        )
        return [DashboardUnitRow(**dict(r)) for r in rows]

    async def list_upcoming(self) -> list[UpcomingRow]:
        return [UpcomingRow(**dict(r)) for r in await self._pool.fetch(_UPCOMING_SQL)]


def get_catalog_repo(pool: Annotated[asyncpg.Pool, Depends(get_db_pool)]) -> CatalogRepo:
    return PgCatalogRepo(pool)
