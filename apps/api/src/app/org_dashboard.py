"""Dashboard da organização (scope 'org' no catálogo, ex.: Estratégico Geral): acesso no servidor.

Um dashboard comum é de uma unidade (`require_dashboard`). O da organização junta as unidades em que está
ligado (app.org_dashboards) numa tela só, e só Owner e Desenvolvedor o veem. A regra continua no banco
(app_private.dashboard_access_explain: scope 'org' = só org.dashboards.all); aqui a API só pergunta, por
unidade, e nega se faltar alguma:

  * dashboard que não existe, não é 'org' ou não está ligado em nenhuma unidade: 403 (não revela o que existe);
  * a pessoa não vê TODAS as unidades dele: 403 auditado (dashboard.access_denied, unit 'GERAL').

Dividido em partes trocáveis: OrgDashboardRepo só lê o banco (PgOrgDashboardRepo em produção, um falso nos
testes); require_org_dashboard é a dependency das rotas (app/routes/org_dashboards.py).
"""

from dataclasses import dataclass
from typing import Annotated, Protocol

import asyncpg
from fastapi import Depends, HTTPException, Request, status

from app.access import (
    AccessRepo,
    DashboardKey,
    Now,
    OrgSlug,
    Support,
    SupportContext,
    _support_for,
    audit_entry,
    get_repo,
)
from app.auth import CurrentUser, get_current_user
from app.platform_db import get_db_pool

GERAL = "GERAL"  # a "unidade" do dashboard da organização na auditoria (e 'geral' na URL)


@dataclass(frozen=True)
class OrgDashboardUnit:
    code: str
    name: str
    timezone: str
    visible: bool  # a pessoa vê o dashboard nesta unidade (app_private.dashboard_scope)


@dataclass(frozen=True)
class ResolvedOrgDashboard:
    org_id: str
    title: str
    source: str
    units: list[OrgDashboardUnit]


@dataclass(frozen=True)
class OrgDashboardAccess:
    user: CurrentUser
    org_slug: str
    org_id: str
    dashboard_key: str
    title: str
    source: str
    units: list[OrgDashboardUnit]  # todas visíveis
    timezone: str
    support: SupportContext | None = None


class OrgDashboardRepo(Protocol):
    async def resolve(
        self, user_id: str, org_slug: str, dashboard_key: str
    ) -> ResolvedOrgDashboard | None: ...


# Uma linha por unidade ativa em que o dashboard 'org' está ligado; nenhuma = não existe (para a pessoa).
_RESOLVE_SQL = """
select o.id::text as org_id, d.name as title, d.source,
       u.code, u.name, u.timezone,
       app_private.dashboard_scope($1::uuid, u.id, d.key) is not null as visible
  from app.organizations o
  join app.dashboard_catalog d on d.key = $3 and d.active and d.status = 'available' and d.scope = 'org'
  join app.org_dashboards od   on od.org_id = o.id and od.dashboard_key = d.key and od.enabled
  join app.units u             on u.id = od.unit_id and u.active
 where o.slug = $2 and o.active
 order by u.code
"""


class PgOrgDashboardRepo:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def resolve(self, user_id, org_slug, dashboard_key):
        rows = await self._pool.fetch(_RESOLVE_SQL, user_id, org_slug, dashboard_key)
        if not rows:
            return None
        first = rows[0]
        return ResolvedOrgDashboard(
            org_id=first["org_id"],
            title=first["title"],
            source=first["source"],
            units=[
                OrgDashboardUnit(
                    code=r["code"], name=r["name"], timezone=r["timezone"], visible=r["visible"]
                )
                for r in rows
            ],
        )


def get_org_dashboard_repo(pool: Annotated[asyncpg.Pool, Depends(get_db_pool)]) -> OrgDashboardRepo:
    return PgOrgDashboardRepo(pool)


async def require_org_dashboard(
    request: Request,
    org_slug: OrgSlug,
    dashboard_key: DashboardKey,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    repo: Annotated[OrgDashboardRepo, Depends(get_org_dashboard_repo)],
    audit: Annotated[AccessRepo, Depends(get_repo)],
    support: Support,
    now: Now,
) -> OrgDashboardAccess:
    """Dependency das rotas /orgs/{org}/geral/dashboards/{key}: 401 sem login, 403 sem acesso (auditado).

    Em modo suporte, o acesso é o do membro da sessão, e a negação não é auditada em nome dele."""
    ctx = await _support_for(request, user, org_slug, audit, support, now)
    if ctx is not None:
        user = ctx.member
    resolved = await repo.resolve(user.user_id, org_slug, dashboard_key)
    if resolved is None or not all(u.visible for u in resolved.units):
        if ctx is None:
            await audit.insert_audit(
                audit_entry(
                    request,
                    user,
                    "dashboard.access_denied",
                    org_id=resolved.org_id if resolved else None,
                    target_type="dashboard",
                    target_id=dashboard_key,
                    metadata={"org": org_slug, "unit": GERAL},
                )
            )
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Sem acesso")
    return OrgDashboardAccess(
        user=user,
        org_slug=org_slug,
        org_id=resolved.org_id,
        dashboard_key=dashboard_key,
        title=resolved.title,
        source=resolved.source,
        units=resolved.units,
        # Período "de hoje" no fuso da 1ª unidade (NG, LA e RJ usam o mesmo hoje; Manaus é o padrão).
        timezone=resolved.units[0].timezone,
        support=ctx,
    )
