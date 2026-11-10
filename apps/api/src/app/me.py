"""Quem está logado (`GET /me`): organizações, unidades, papel e o que pode fazer.

Dividido em três partes trocáveis:
  * MeRepo        só lê o banco (PgMeRepo em produção, um falso nos testes);
  * pick_org      escolhe a organização pedida (ou a padrão) entre as da pessoa;
  * build_me      monta a resposta a partir do que o banco devolveu (função pura).
As permissões vêm de app.role_permissions; nenhum nome de papel fica fixo aqui.
"""

from dataclasses import dataclass
from typing import Annotated, Protocol

import asyncpg
from fastapi import Depends
from pydantic import BaseModel

from app.access import get_db_pool

# Permissões (app.role_permissions) que decidem o que a pessoa pode fazer.
SEE_ALL_ORG = "org.dashboards.all"  # owner, admin: todas as unidades
SEE_ALL_UNIT = "unit.dashboards.all"  # gestor, controller: tudo da unidade
EXPORT = "dashboards.export"


# --- O que o banco devolve -------------------------------------------------


@dataclass(frozen=True)
class OrgRow:
    id: str
    slug: str
    name: str
    unit_count: int


@dataclass(frozen=True)
class UnitRow:
    code: str
    name: str
    role_name: str | None  # cargo nesta unidade; None = vê pela organização (owner/admin)
    permissions: frozenset[str]


@dataclass(frozen=True)
class MembershipRow:
    full_name: str
    role_name: str  # papel na organização ("Desenvolvedor", "Membro"...)
    permissions: frozenset[str]
    units: tuple[UnitRow, ...]  # só as unidades que a pessoa vê


class MeRepo(Protocol):
    async def list_orgs(self, user_id: str) -> list[OrgRow]: ...

    async def membership(self, user_id: str, org_id: str) -> MembershipRow | None: ...


# --- Resposta (tipo Me do front) -------------------------------------------


class UserOut(BaseModel):
    name: str
    initials: str
    role_label: str
    can_export: bool
    can_see_commission: bool
    platform_staff: bool


class OrgOut(BaseModel):
    slug: str
    name: str
    sub: str


class UnitOut(BaseModel):
    code: str
    name: str


class MeOut(BaseModel):
    user: UserOut
    org: OrgOut
    units: list[UnitOut]
    orgs: list[OrgOut]


# --- Regras ----------------------------------------------------------------


def pick_org(orgs: list[OrgRow], slug: str | None) -> OrgRow | None:
    """Sem slug: a padrão (a primeira; o banco ordena pela última usada). Com slug: só se for membro."""
    if slug is None:
        return orgs[0] if orgs else None
    return next((o for o in orgs if o.slug == slug), None)


def initials(name: str) -> str:
    """'Luís Tápia' -> 'LT'; 'Ana' -> 'A'."""
    parts = name.split()
    if not parts:
        return ""
    first, last = parts[0], parts[-1]
    return (first[0] + (last[0] if len(parts) > 1 else "")).upper()


def org_sub(unit_count: int) -> str:
    """Linha de baixo no seletor de organização. Plano ainda não existe no banco."""
    return "1 unidade" if unit_count == 1 else f"{unit_count} unidades"


def role_label(m: MembershipRow) -> str:
    """Owner/admin: o papel na organização. Os demais: os cargos nas unidades ('Gestor · Leitor')."""
    if SEE_ALL_ORG in m.permissions:
        return m.role_name
    names = list(dict.fromkeys(u.role_name for u in m.units if u.role_name))
    return " · ".join(names) or m.role_name


def _has_any(m: MembershipRow, wanted: set[str]) -> bool:
    return bool(wanted & m.permissions) or any(wanted & u.permissions for u in m.units)


def build_me(
    orgs: list[OrgRow], current: OrgRow, m: MembershipRow, *, platform_staff: bool
) -> MeOut:
    def org_out(o: OrgRow) -> OrgOut:
        return OrgOut(slug=o.slug, name=o.name, sub=org_sub(o.unit_count))

    return MeOut(
        user=UserOut(
            name=m.full_name,
            initials=initials(m.full_name),
            role_label=role_label(m),
            can_export=_has_any(m, {EXPORT}),
            # Igual à v1 (Gestor e Desenvolvedor): quem vê tudo da organização ou da unidade.
            can_see_commission=_has_any(m, {SEE_ALL_ORG, SEE_ALL_UNIT}),
            platform_staff=platform_staff,
        ),
        org=org_out(current),
        units=[UnitOut(code=u.code, name=u.name) for u in m.units],
        orgs=[org_out(o) for o in orgs],
    )


# --- Banco -----------------------------------------------------------------

_ORGS_SQL = """
select o.id::text as id, o.slug, o.name,
       (select count(*) from app.units u where u.org_id = o.id and u.active)::int as unit_count
  from app.memberships m
  join app.organizations o on o.id = m.org_id and o.active
 where m.user_id = $1::uuid and m.status = 'active'
 order by m.last_seen_at desc nulls last, o.name
"""

_MEMBERSHIP_SQL = """
select m.id::text as id, m.full_name, r.name as role_name,
       coalesce(array_agg(rp.permission) filter (where rp.permission is not null), '{}') as permissions
  from app.memberships m
  join app.roles r on r.key = m.role_key
  left join app.role_permissions rp on rp.role_key = m.role_key
 where m.user_id = $1::uuid and m.org_id = $2::uuid and m.status = 'active'
 group by m.id, m.full_name, r.name
"""

# $3 = vê todas as unidades (owner/admin); senão, só as unidades em que tem cargo.
_UNITS_SQL = """
select u.code, u.name, r.name as role_name,
       coalesce(array_agg(rp.permission) filter (where rp.permission is not null), '{}') as permissions
  from app.units u
  left join app.membership_units mu on mu.unit_id = u.id and mu.membership_id = $2::uuid
  left join app.roles r             on r.key = mu.role_key
  left join app.role_permissions rp on rp.role_key = mu.role_key
 where u.org_id = $1::uuid and u.active
   and ($3 or mu.membership_id is not null)
 group by u.code, u.name, r.name, r.sort_order
 order by u.name
"""


class PgMeRepo:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def list_orgs(self, user_id: str) -> list[OrgRow]:
        rows = await self._pool.fetch(_ORGS_SQL, user_id)
        return [OrgRow(**dict(r)) for r in rows]

    async def membership(self, user_id: str, org_id: str) -> MembershipRow | None:
        row = await self._pool.fetchrow(_MEMBERSHIP_SQL, user_id, org_id)
        if row is None:
            return None
        permissions = frozenset(row["permissions"])
        units = await self._pool.fetch(_UNITS_SQL, org_id, row["id"], SEE_ALL_ORG in permissions)
        return MembershipRow(
            full_name=row["full_name"],
            role_name=row["role_name"],
            permissions=permissions,
            units=tuple(
                UnitRow(
                    code=u["code"],
                    name=u["name"],
                    role_name=u["role_name"],
                    permissions=frozenset(u["permissions"]),
                )
                for u in units
            ),
        )


def get_me_repo(pool: Annotated[asyncpg.Pool, Depends(get_db_pool)]) -> MeRepo:
    return PgMeRepo(pool)
