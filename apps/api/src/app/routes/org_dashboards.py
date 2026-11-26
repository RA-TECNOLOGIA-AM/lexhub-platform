"""Rotas dos dashboards da organização (scope 'org', ex.: Estratégico Geral): /orgs/{org}/geral/dashboards.

Esqueleto: confere o acesso (app/org_dashboard.py) e devolve o `meta` (o mesmo formato dos dashboards de
unidade, com unit 'geral') e as unidades que o dashboard reúne, cada uma com o bloco vazio onde as análises
vão entrar. Sem cálculo, sem fonte lida e sem exportar ainda.
"""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dashboards.base import DashboardInputError, resolve_period
from app.org_dashboard import OrgDashboardAccess, require_org_dashboard
from app.routes.dashboards import Today, get_today

router = APIRouter(prefix="/orgs/{org_slug}/geral/dashboards", tags=["dashboards"])

UNIT = "geral"  # o mesmo segmento da URL do front (/:org/geral/dashboards/:key)


@router.get("/{dashboard_key}/access")
async def org_dashboard_access(
    access: Annotated[OrgDashboardAccess, Depends(require_org_dashboard)],
):
    """Confere se o usuário logado pode ver o dashboard da organização e quais unidades ele reúne."""
    return {
        "org": access.org_slug,
        "unit": UNIT,
        "dashboard": access.dashboard_key,
        "units": [u.code for u in access.units],
    }


@router.get("/{dashboard_key}")
async def org_dashboard_data(
    access: Annotated[OrgDashboardAccess, Depends(require_org_dashboard)],
    today: Annotated[Today, Depends(get_today)],
    start: Annotated[date | None, Query(alias="from")] = None,
    end: Annotated[date | None, Query(alias="to")] = None,
):
    """`meta` + as unidades do dashboard da organização. As análises entram em `units[].data`."""
    try:
        period = resolve_period(start, end, today(access.timezone))
    except DashboardInputError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e)) from None
    return {
        "meta": {
            "unit": UNIT,
            "from": period.start.isoformat(),
            "to": period.end.isoformat(),
            "source": access.source,
            "synced_at": None,  # sem fonte lida ainda
            "timezone": access.timezone,
        },
        "units": [{"code": u.code, "name": u.name, "data": {}} for u in access.units],
    }
