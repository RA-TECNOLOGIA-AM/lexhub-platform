"""Organização e unidade pela URL, checagem de acesso no servidor e auditoria.

A regra de acesso fica no banco (`app_private.dashboard_scope`, coberta pelos testes
em supabase/tests). A API só resolve slug/código para ids, chama a função e nega
quando ela devolve NULL. Organização inexistente e "sem acesso" dão a mesma resposta,
para não revelar quais organizações existem.
"""

import json
from dataclasses import dataclass, field
from typing import Annotated, Any, Protocol

import asyncpg
from fastapi import Depends, HTTPException, Path, Request, status

from app.auth import CurrentUser, get_current_user

OrgSlug = Annotated[str, Path(pattern=r"^[a-z0-9][a-z0-9-]{1,62}$")]
UnitCode = Annotated[str, Path(pattern=r"^[A-Z0-9_]{2,16}$")]
DashboardKey = Annotated[str, Path(pattern=r"^[a-z0-9][a-z0-9_-]{1,62}$")]


@dataclass(frozen=True)
class ResolvedAccess:
    org_id: str
    unit_id: str
    scope: str | None  # 'all' | 'own' | None (sem acesso)


@dataclass(frozen=True)
class AuditEntry:
    action: str
    actor_user_id: str | None
    org_id: str | None = None
    target_type: str | None = None
    target_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    ip: str | None = None
    user_agent: str | None = None


@dataclass(frozen=True)
class DashboardAccess:
    user: CurrentUser
    org_slug: str
    unit_code: str
    dashboard_key: str
    org_id: str
    unit_id: str
    scope: str


class AccessRepo(Protocol):
    async def resolve_access(
        self, user_id: str, org_slug: str, unit_code: str, dashboard_key: str
    ) -> ResolvedAccess | None: ...

    async def insert_audit(self, entry: AuditEntry) -> None: ...


_RESOLVE_SQL = """
select o.id::text as org_id,
       u.id::text as unit_id,
       app_private.dashboard_scope($1::uuid, u.id, $4) as scope
  from app.organizations o
  join app.units u on u.org_id = o.id
 where o.slug = $2 and u.code = $3 and o.active and u.active
"""

_AUDIT_SQL = """
insert into app.audit_log
    (org_id, actor_user_id, action, target_type, target_id, metadata, ip, user_agent)
values ($1::uuid, $2::uuid, $3, $4, $5, $6::jsonb, $7::inet, $8)
"""


class PgAccessRepo:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def resolve_access(self, user_id, org_slug, unit_code, dashboard_key):
        row = await self._pool.fetchrow(_RESOLVE_SQL, user_id, org_slug, unit_code, dashboard_key)
        if row is None:
            return None
        return ResolvedAccess(org_id=row["org_id"], unit_id=row["unit_id"], scope=row["scope"])

    async def insert_audit(self, entry: AuditEntry) -> None:
        await self._pool.execute(
            _AUDIT_SQL,
            entry.org_id,
            entry.actor_user_id,
            entry.action,
            entry.target_type,
            entry.target_id,
            json.dumps(entry.metadata),
            entry.ip,
            entry.user_agent,
        )


def get_db_pool(request: Request) -> asyncpg.Pool:
    """Pool do banco da V2 (DATABASE_URL). Sem banco configurado, a rota responde 503."""
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="Banco indisponível")
    return pool


def get_repo(pool: Annotated[asyncpg.Pool, Depends(get_db_pool)]) -> AccessRepo:
    return PgAccessRepo(pool)


def audit_entry(request: Request, user: CurrentUser | None, action: str, **kw) -> AuditEntry:
    return AuditEntry(
        action=action,
        actor_user_id=user.user_id if user else None,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        **kw,
    )


async def require_dashboard(
    request: Request,
    org_slug: OrgSlug,
    unit_code: UnitCode,
    dashboard_key: DashboardKey,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    repo: Annotated[AccessRepo, Depends(get_repo)],
) -> DashboardAccess:
    """Dependency das rotas de dashboard: 401 sem login, 403 sem acesso (auditado)."""
    resolved = await repo.resolve_access(user.user_id, org_slug, unit_code, dashboard_key)
    if resolved is None or resolved.scope is None:
        await repo.insert_audit(
            audit_entry(
                request,
                user,
                "dashboard.access_denied",
                org_id=resolved.org_id if resolved else None,
                target_type="dashboard",
                target_id=dashboard_key,
                metadata={"org": org_slug, "unit": unit_code},
            )
        )
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Sem acesso")
    return DashboardAccess(
        user=user,
        org_slug=org_slug,
        unit_code=unit_code,
        dashboard_key=dashboard_key,
        org_id=resolved.org_id,
        unit_id=resolved.unit_id,
        scope=resolved.scope,
    )
