import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends

from app.access import OrgAccess, require_org
from app.catalog import CatalogRepo, DashboardCatalogOut, build_catalog, get_catalog_repo

router = APIRouter(prefix="/orgs/{org_slug}", tags=["catalog"])


@router.get("/dashboards", response_model=DashboardCatalogOut)
async def list_dashboards(
    access: Annotated[OrgAccess, Depends(require_org)],
    repo: Annotated[CatalogRepo, Depends(get_catalog_repo)],
) -> DashboardCatalogOut:
    """Hub: os dashboards que a pessoa pode abrir nesta organização e em quais unidades."""
    # As duas consultas não dependem uma da outra: vão juntas (cada ida ao banco custa caro).
    rows, upcoming = await asyncio.gather(
        repo.list_available(access.user.user_id, access.org_id), repo.list_upcoming()
    )
    return build_catalog(rows, upcoming)
