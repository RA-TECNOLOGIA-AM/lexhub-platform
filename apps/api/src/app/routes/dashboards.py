from typing import Annotated

from fastapi import APIRouter, Depends

from app.access import DashboardAccess, require_dashboard

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
