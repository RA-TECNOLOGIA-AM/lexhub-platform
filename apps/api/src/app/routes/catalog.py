import asyncio
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends

from app.access import OrgAccess, require_org
from app.catalog import CatalogRepo, DashboardCatalogOut, build_catalog, get_catalog_repo
from app.dashboards import DASHBOARDS
from app.source_cache import SourceCache
from app.sources import get_source_cache

router = APIRouter(prefix="/orgs/{org_slug}", tags=["catalog"])


@router.get("/dashboards", response_model=DashboardCatalogOut)
async def list_dashboards(
    access: Annotated[OrgAccess, Depends(require_org)],
    repo: Annotated[CatalogRepo, Depends(get_catalog_repo)],
    cache: Annotated[SourceCache, Depends(get_source_cache)],
) -> DashboardCatalogOut:
    """Hub: os dashboards que a pessoa pode abrir nesta organização e em quais unidades."""
    # As duas consultas não dependem uma da outra: vão juntas (cada ida ao banco custa caro).
    rows, upcoming = await asyncio.gather(
        repo.list_available(access.user.user_id, access.org_id), repo.list_upcoming()
    )
    return build_catalog(rows, upcoming, synced_from_cache(cache, {r.key for r in rows}))


def synced_from_cache(cache: SourceCache, keys: set[str]) -> dict[str, datetime]:
    """Card -> quando o dado MAIS ANTIGO que ele usa veio do banco. Sem tudo no cache: fica de fora (null)."""
    out: dict[str, datetime] = {}
    for key in keys:
        module = DASHBOARDS.get(key)
        if module is None or not module.queries:
            continue
        times = [cache.fetched_at(f"{module.source_db}:{q}") for q in module.queries]
        if all(t is not None for t in times):
            out[key] = datetime.fromtimestamp(min(times), UTC)
    return out
