from collections.abc import Callable
from datetime import date, datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.access import AccessRepo, DashboardAccess, audit_entry, get_repo, require_dashboard
from app.dashboards import DASHBOARDS
from app.dashboards.base import (
    DashboardContext,
    DashboardInputError,
    NotReady,
    parse_filters,
    resolve_period,
    shape_response,
)
from app.sources import (
    SourceFactory,
    SourceRefsRepo,
    SourceUnavailable,
    get_source_factory,
    get_source_refs_repo,
)

router = APIRouter(prefix="/orgs/{org_slug}/units/{unit_code}/dashboards", tags=["dashboards"])


@router.get("/{dashboard_key}/access")
async def dashboard_access(access: Annotated[DashboardAccess, Depends(require_dashboard)]):
    """Confere se o usuário logado pode ver o dashboard nesta unidade e com qual escopo."""
    return {
        "org": access.org_slug,
        "unit": access.unit_code,
        "dashboard": access.dashboard_key,
        "scope": access.scope,
    }


Today = Callable[[str], date]


def today_in(timezone: str) -> date:
    """Hoje no fuso da unidade (o 'mês atual' do período padrão depende disso)."""
    return datetime.now(ZoneInfo(timezone)).date()


def get_today() -> Today:
    """Dependency: o relógio (trocável nos testes)."""
    return today_in


@router.get("/{dashboard_key}")
async def dashboard_data(
    request: Request,
    access: Annotated[DashboardAccess, Depends(require_dashboard)],
    refs: Annotated[SourceRefsRepo, Depends(get_source_refs_repo)],
    sources: Annotated[SourceFactory, Depends(get_source_factory)],
    audit: Annotated[AccessRepo, Depends(get_repo)],
    today: Annotated[Today, Depends(get_today)],
    start: Annotated[date | None, Query(alias="from")] = None,
    end: Annotated[date | None, Query(alias="to")] = None,
):
    """Dados de um dashboard numa unidade: período, filtros da v1, `meta` e o que o módulo calcula."""
    module = DASHBOARDS.get(access.dashboard_key)
    if module is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="Este dashboard ainda não tem dados na V2"
        )

    # 'own' precisa saber qual funcionário da fonte é a pessoa; sem esse vínculo, nega (nunca mostra dos outros).
    if access.scope != "all":
        await audit.insert_audit(
            audit_entry(
                request,
                access.user,
                "dashboard.access_denied",
                org_id=access.org_id,
                target_type="dashboard",
                target_id=access.dashboard_key,
                metadata={
                    "org": access.org_slug,
                    "unit": access.unit_code,
                    "reason": "own_sem_vinculo",
                },
            )
        )
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Sem acesso")

    try:
        period = resolve_period(start, end, today(access.timezone))
        query = request.query_params
        filters = parse_filters(module.filters, {k: query.getlist(k) for k in module.filters})
    except DashboardInputError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from None

    unit_ref = await refs.unit_ref(access.unit_id, module.source_db)
    if unit_ref is None:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"A unidade {access.unit_code} ainda não está ligada à fonte {module.source_label}",
        )

    ctx = DashboardContext(
        source=sources(module.source_db),
        unit_ref=unit_ref,
        period=period,
        filters=filters,
        can_see_commission=access.can_see_commission,
    )
    try:
        data = await module.build(ctx)
    except NotReady as exc:
        raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, detail=str(exc)) from None
    except SourceUnavailable:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"A fonte {module.source_label} está indisponível no momento",
        ) from None

    meta = {
        "unit": access.unit_code,
        "from": period.start.isoformat(),
        "to": period.end.isoformat(),
        "source": module.source_label,
        "synced_at": None,  # vem do cache de 5 min quando ele existir
        "timezone": access.timezone,
    }
    # Quem não gere a unidade vê só a própria comissão: precisa saber quem a pessoa é na fonte.
    own_ref = None
    if module.commission_fields and not access.can_see_commission:
        own_ref = await refs.member_ref(access.user.user_id, access.org_id, module.source_db)
    return shape_response(module, data, meta, access.can_see_commission, own_ref)
