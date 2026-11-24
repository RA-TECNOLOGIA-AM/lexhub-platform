"""Organização e unidade pela URL, checagem de acesso no servidor e auditoria.

A regra de acesso fica no banco (`app_private.dashboard_scope`, coberta pelos testes
em supabase/tests). A API só resolve slug/código para ids, chama a função e nega
quando ela devolve NULL. Organização inexistente e "sem acesso" dão a mesma resposta,
para não revelar quais organizações existem.

Modo suporte: com o cabeçalho X-Support-Session válido, `require_org`/`require_dashboard`
respondem como o membro da sessão (`resolve_support`); o "só leitura" fica em
app/support_guard.py.
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Annotated, Any, NoReturn, Protocol

import asyncpg
from fastapi import Depends, HTTPException, Path, Request, status

from app.auth import CurrentUser, get_current_user
from app.clock import get_now
from app.platform_db import get_db_pool
from app.support import SupportRepo, get_support_repo

OrgSlug = Annotated[str, Path(pattern=r"^[a-z0-9][a-z0-9-]{1,62}$")]
UnitCode = Annotated[str, Path(pattern=r"^[A-Z0-9_]{2,16}$")]
DashboardKey = Annotated[str, Path(pattern=r"^[a-z0-9][a-z0-9_-]{1,62}$")]


@dataclass(frozen=True)
class ResolvedAccess:
    org_id: str
    unit_id: str
    scope: str | None  # 'all' | 'own' | None (sem acesso)
    timezone: str = "America/Manaus"  # fuso da unidade (app.units.timezone)
    # Por unidade: owner/admin/gestor/controller veem a comissão de todos; exportar = dashboards.export.
    can_see_commission: bool = False
    can_export: bool = False
    # id da unidade em cada banco de origem (app.unit_source_refs): {'lexpre': '1', ...}
    source_refs: dict[str, str] = field(default_factory=dict)


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


SUPPORT_HEADER = "X-Support-Session"


@dataclass(frozen=True)
class SupportContext:
    """Modo suporte: quem pede (actor) navega como o membro da sessão, só leitura."""

    session_id: str
    actor: CurrentUser
    target_membership_id: str
    target_user_id: str
    org_id: str

    @property
    def member(self) -> CurrentUser:
        """O usuário efetivo das rotas: o membro, sem e-mail nem claims (não vêm do token)."""
        return CurrentUser(user_id=self.target_user_id, email=None, claims={})


@dataclass(frozen=True)
class DashboardAccess:
    user: CurrentUser
    org_slug: str
    unit_code: str
    dashboard_key: str
    org_id: str
    unit_id: str
    scope: str
    timezone: str = "America/Manaus"
    can_see_commission: bool = False
    can_export: bool = False
    source_refs: dict[str, str] = field(default_factory=dict)
    support: SupportContext | None = None  # em suporte, `user` é o membro


@dataclass(frozen=True)
class OrgAccess:
    user: CurrentUser
    org_slug: str
    org_id: str
    support: SupportContext | None = None  # em suporte, `user` é o membro


class AccessRepo(Protocol):
    async def resolve_org(self, user_id: str, org_slug: str) -> str | None: ...

    async def resolve_access(
        self, user_id: str, org_slug: str, unit_code: str, dashboard_key: str
    ) -> ResolvedAccess | None: ...

    async def insert_audit(self, entry: AuditEntry) -> None: ...


# Id da organização só se a pessoa for membro ativo dela (e ela estiver ativa).
_ORG_SQL = """
select o.id::text
  from app.organizations o
  join app.memberships m on m.org_id = o.id and m.user_id = $1::uuid and m.status = 'active'
 where o.slug = $2 and o.active
"""

_RESOLVE_SQL = """
select o.id::text as org_id,
       u.id::text as unit_id,
       app_private.dashboard_scope($1::uuid, u.id, $4) as scope,
       u.timezone,
       (app_private.has_unit_permission($1::uuid, u.id, 'org.dashboards.all')
        or app_private.has_unit_permission($1::uuid, u.id, 'unit.dashboards.all')) as can_see_commission,
       app_private.dashboard_can_export($1::uuid, u.id, $4) as can_export,  -- exceção da pessoa só vê
       coalesce((select jsonb_object_agg(r.source, r.ref) from app.unit_source_refs r
                  where r.unit_id = u.id), '{}'::jsonb)::text as source_refs
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

    async def resolve_org(self, user_id, org_slug):
        return await self._pool.fetchval(_ORG_SQL, user_id, org_slug)

    async def resolve_access(self, user_id, org_slug, unit_code, dashboard_key):
        row = await self._pool.fetchrow(_RESOLVE_SQL, user_id, org_slug, unit_code, dashboard_key)
        if row is None:
            return None
        return ResolvedAccess(
            org_id=row["org_id"],
            unit_id=row["unit_id"],
            scope=row["scope"],
            timezone=row["timezone"],
            can_see_commission=row["can_see_commission"],
            can_export=row["can_export"],
            source_refs=json.loads(row["source_refs"]),
        )

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


async def deny_org(
    request: Request, user: CurrentUser, repo: AccessRepo, org_slug: str | None
) -> NoReturn:
    """403 de organização, auditado. Igual para inexistente, sem acesso ou sem organização."""
    await repo.insert_audit(
        audit_entry(
            request,
            user,
            "org.access_denied",
            target_type="org",
            target_id=org_slug,
            metadata={"org": org_slug},
        )
    )
    raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Sem acesso")


# --- Modo suporte: o usuário efetivo -----------------------------------------


def _support_expired() -> HTTPException:
    return HTTPException(status.HTTP_409_CONFLICT, detail="support_expired")


async def end_support(
    request: Request,
    actor: CurrentUser,
    support: SupportRepo,
    audit: AccessRepo,
    *,
    session_id: str,
    org_id: str,
    target_membership_id: str,
    reason: str,
) -> None:
    """Encerra a sessão e audita support.ended só se foi este pedido que encerrou (com o motivo
    que o banco aplicou: 'expired' se já tinha vencido)."""
    applied = await support.end(session_id, reason)
    if applied is not None:
        await audit.insert_audit(
            audit_entry(
                request,
                actor,
                "support.ended",
                org_id=org_id,
                target_type="membership",
                target_id=target_membership_id,
                metadata={"session": session_id, "end_reason": applied},
            )
        )


async def resolve_support(
    request: Request,
    user: CurrentUser,
    org_id: str,
    support: SupportRepo,
    audit: AccessRepo,
    now: datetime,
) -> SupportContext | None:
    """Lê X-Support-Session. Sem o cabeçalho: None (nada muda).

    Não confia no pg_cron: vencida (expires_at <= agora) ou encerrada vale como inválida aqui.
      * sessão inexistente, de outra pessoa ou de outra organização: 403 "Sem acesso";
      * vencida ou encerrada: encerra ('expired', audita se fechou agora) e 409 support_expired;
      * quem pede deixou de ser Owner/Dev: encerra ('exit', audita) e 403 "Sem acesso".
    """
    raw = request.headers.get(SUPPORT_HEADER)
    if raw is None:
        return None
    try:
        session_id = str(uuid.UUID(raw))
    except ValueError:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Sem acesso") from None
    session = await support.get(session_id)
    if session is None or session.actor_user_id != user.user_id or session.org_id != org_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Sem acesso")
    where = {
        "session_id": session.id,
        "org_id": session.org_id,
        "target_membership_id": session.target_membership_id,
    }
    if session.ended_at is not None or session.expires_at <= now:
        await end_support(request, user, support, audit, reason="expired", **where)
        raise _support_expired()
    if not await support.can_support(user.user_id, org_id):
        await end_support(request, user, support, audit, reason="exit", **where)
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Sem acesso")
    return SupportContext(
        session_id=session.id,
        actor=user,
        target_membership_id=session.target_membership_id,
        target_user_id=session.target_user_id,
        org_id=session.org_id,
    )


async def _support_for(
    request: Request,
    user: CurrentUser,
    org_slug: str,
    repo: AccessRepo,
    support: SupportRepo,
    now: datetime,
) -> SupportContext | None:
    """A sessão de suporte válida deste pedido, com o membro ainda na organização; None sem o
    cabeçalho. Quem pede precisa ser membro da organização (403 auditado, como no require_org)."""
    if SUPPORT_HEADER not in request.headers:
        return None
    org_id = await repo.resolve_org(user.user_id, org_slug)
    if org_id is None:
        await deny_org(request, user, repo, org_slug)
    ctx = await resolve_support(request, user, org_id, support, repo, now)
    if await repo.resolve_org(ctx.target_user_id, org_slug) is None:
        # Membro desativado (ou fora da organização) durante a sessão: acabou.
        await end_support(
            request,
            user,
            support,
            repo,
            session_id=ctx.session_id,
            org_id=ctx.org_id,
            target_membership_id=ctx.target_membership_id,
            reason="expired",
        )
        raise _support_expired()
    return ctx


Support = Annotated[SupportRepo, Depends(get_support_repo)]
Now = Annotated[datetime, Depends(get_now)]


async def require_org(
    request: Request,
    org_slug: OrgSlug,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    repo: Annotated[AccessRepo, Depends(get_repo)],
    support: Support,
    now: Now,
) -> OrgAccess:
    """Dependency das rotas /orgs/{org_slug}/...: 401 sem login, 403 se não for membro (auditado).

    Em modo suporte (X-Support-Session válido), `user` passa a ser o membro da sessão."""
    ctx = await _support_for(request, user, org_slug, repo, support, now)
    if ctx is not None:
        return OrgAccess(user=ctx.member, org_slug=org_slug, org_id=ctx.org_id, support=ctx)
    org_id = await repo.resolve_org(user.user_id, org_slug)
    if org_id is None:
        await deny_org(request, user, repo, org_slug)
    return OrgAccess(user=user, org_slug=org_slug, org_id=org_id)


async def require_dashboard(
    request: Request,
    org_slug: OrgSlug,
    unit_code: UnitCode,
    dashboard_key: DashboardKey,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    repo: Annotated[AccessRepo, Depends(get_repo)],
    support: Support,
    now: Now,
) -> DashboardAccess:
    """Dependency das rotas de dashboard: 401 sem login, 403 sem acesso (auditado).

    Em modo suporte, o acesso é o do membro da sessão, e a negação não é auditada em nome dele."""
    ctx = await _support_for(request, user, org_slug, repo, support, now)
    if ctx is not None:
        user = ctx.member
    resolved = await repo.resolve_access(user.user_id, org_slug, unit_code, dashboard_key)
    if resolved is None or resolved.scope is None:
        if ctx is not None:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Sem acesso")
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
        timezone=resolved.timezone,
        can_see_commission=resolved.can_see_commission,
        can_export=resolved.can_export and ctx is None,  # suporte é só leitura
        source_refs=resolved.source_refs,
        support=ctx,
    )
