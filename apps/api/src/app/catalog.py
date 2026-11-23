"""Catálogo do hub (`GET /orgs/{org}/dashboards`): só o que a pessoa pode abrir, por unidade.

Dividido em duas partes trocáveis:
  * CatalogRepo     só lê o banco (PgCatalogRepo em produção, um falso nos testes);
  * build_catalog   monta a resposta (função pura).
Quem vê o quê é a regra do banco (app_private.dashboard_scope); exportar e comissão vêm
das permissões (app_private.has_unit_permission), nunca de nomes de papel.

Ligar/desligar um dashboard numa unidade (só o Desenvolvedor, permissão dashboards.toggle): o banco
decide e audita (app_private.set_dashboard_enabled, migration 20261118130000). Desligado some para
todos; o Desenvolvedor continua recebendo a unidade, marcada em `disabled_units`.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Protocol

import asyncpg
from fastapi import Depends
from pydantic import BaseModel

from app.access import get_db_pool

SEE_ALL_ORG = "org.dashboards.all"  # owner, admin
SEE_ALL_UNIT = "unit.dashboards.all"  # gestor, controller
TOGGLE = "dashboards.toggle"  # admin (Desenvolvedor): liga/desliga dashboard na unidade


class ToggleNotAllowed(Exception):
    """Quem pediu não pode ligar/desligar dashboards nesta unidade. A mensagem vai para a tela."""


class DashboardMissing(Exception):
    """O dashboard não existe (ou não está no catálogo) nesta unidade."""


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
    enabled: bool = True  # False só chega para quem pode religar (Desenvolvedor)
    can_toggle: bool = False


@dataclass(frozen=True)
class UpcomingRow:
    title: str
    area: str


class CatalogRepo(Protocol):
    async def list_available(self, user_id: str, org_id: str) -> list[DashboardUnitRow]: ...

    async def list_upcoming(self) -> list[UpcomingRow]: ...

    # Estado final (True = ligado). ToggleNotAllowed / DashboardMissing quando o banco recusa.
    async def set_enabled(
        self, user_id: str, org_slug: str, unit_code: str, dashboard_key: str, enabled: bool
    ) -> bool: ...


# --- Resposta (tipo DashboardCatalog do front) -----------------------------


class DashboardSummaryOut(BaseModel):
    key: str
    title: str
    area: str
    desc: str
    units: list[str]
    source: str
    # Última leitura boa da fonte do card (qualquer dashboard dela): o banco respondeu, então todos os
    # cards da mesma fonte mostram a mesma hora. null = a fonte ainda não foi lida ("Atualiza ao abrir").
    synced_at: datetime | None
    # Banco de origem (app/dashboards, source_db): o front acerta todos os cards da mesma fonte quando um
    # dashboard dela abre, sem buscar o catálogo de novo. null = dashboard sem módulo na API.
    source_key: str | None = None
    max_delay_min: int
    can_export: bool
    can_see_commission: bool
    disabled_units: list[str] = []  # unidades em que está desligado (só o Desenvolvedor recebe)
    can_toggle: bool = False  # mostra o menu de ligar/desligar no card


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
    source_key: dict[str, str] | None = None,
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
                source_key=(source_key or {}).get(r.key),
                max_delay_min=r.max_delay_min,
                can_export=r.can_export,
                can_see_commission=r.can_see_commission,
                disabled_units=[] if r.enabled else [r.unit_code],
                can_toggle=r.can_toggle,
            )
            continue
        card.units.append(r.unit_code)
        if not r.enabled:
            card.disabled_units.append(r.unit_code)
        card.can_export = card.can_export and r.can_export
        card.can_see_commission = card.can_see_commission and r.can_see_commission
        card.can_toggle = card.can_toggle and r.can_toggle
    return DashboardCatalogOut(
        available=list(cards.values()),
        upcoming=[UpcomingOut(title=u.title, area=u.area) for u in upcoming],
    )


# --- Banco -----------------------------------------------------------------

# Uma linha por (dashboard, unidade) em que a pessoa tem acesso; ordem do hub.
# Desligado na unidade só volta para quem pode religar (o dashboard_scope também deixa).
_AVAILABLE_SQL = """
select d.key, d.name as title, d.area, coalesce(d.description, '') as "desc",
       d.source, d.max_delay_min, u.code as unit_code,
       app_private.dashboard_can_export($1::uuid, u.id, d.key) as can_export,
       (app_private.has_unit_permission($1::uuid, u.id, $3)
        or app_private.has_unit_permission($1::uuid, u.id, $4)) as can_see_commission,
       od.enabled,
       x.can_toggle
  from app.org_dashboards od
  join app.units u             on u.id = od.unit_id and u.active
  join app.dashboard_catalog d on d.key = od.dashboard_key and d.active and d.status = 'available'
  cross join lateral (select app_private.has_unit_permission($1::uuid, u.id, $5) as can_toggle) x
 where od.org_id = $2::uuid
   and (od.enabled or x.can_toggle)
   and app_private.dashboard_scope($1::uuid, u.id, d.key) is not null
 order by d.sort_order, d.name, u.code
"""

_SET_ENABLED_SQL = "select app_private.set_dashboard_enabled($1::uuid, $2, $3, $4, $5)"

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
            _AVAILABLE_SQL, user_id, org_id, SEE_ALL_ORG, SEE_ALL_UNIT, TOGGLE
        )
        return [DashboardUnitRow(**dict(r)) for r in rows]

    async def list_upcoming(self) -> list[UpcomingRow]:
        return [UpcomingRow(**dict(r)) for r in await self._pool.fetch(_UPCOMING_SQL)]

    async def set_enabled(self, user_id, org_slug, unit_code, dashboard_key, enabled) -> bool:
        try:
            return await self._pool.fetchval(
                _SET_ENABLED_SQL, user_id, org_slug, unit_code, dashboard_key, enabled
            )
        except asyncpg.InsufficientPrivilegeError as exc:  # 42501
            raise ToggleNotAllowed(exc.message) from exc
        except asyncpg.RaiseError as exc:  # P0001
            raise DashboardMissing(exc.message) from exc


def get_catalog_repo(pool: Annotated[asyncpg.Pool, Depends(get_db_pool)]) -> CatalogRepo:
    return PgCatalogRepo(pool)
