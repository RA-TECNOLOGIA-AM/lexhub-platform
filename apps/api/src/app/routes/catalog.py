import asyncio
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.access import DashboardKey, OrgAccess, UnitCode, require_org
from app.catalog import (
    CatalogRepo,
    DashboardCatalogOut,
    DashboardMissing,
    ToggleNotAllowed,
    build_catalog,
    get_catalog_repo,
)
from app.dashboards import DASHBOARDS
from app.database import SourceUnavailable
from app.source_cache import SourceCache
from app.sources import get_source_cache, get_source_switch
from app.unit_scope import ESCRITORIO_POR_UNIDADE, UNIT_COLUMN, scoped_name

router = APIRouter(prefix="/orgs/{org_slug}", tags=["catalog"])


@router.get("/dashboards", response_model=DashboardCatalogOut)
async def list_dashboards(
    access: Annotated[OrgAccess, Depends(require_org)],
    repo: Annotated[CatalogRepo, Depends(get_catalog_repo)],
    cache: Annotated[SourceCache, Depends(get_source_cache)],
    switch: Annotated[Any, Depends(get_source_switch)],
) -> DashboardCatalogOut:
    """Hub: os dashboards que a pessoa pode abrir nesta organização e em quais unidades."""
    # As duas consultas não dependem uma da outra: vão juntas (cada ida ao banco custa caro).
    rows, upcoming = await asyncio.gather(
        repo.list_available(access.user.user_id, access.org_id), repo.list_upcoming()
    )
    keys = {r.key for r in rows}
    return build_catalog(
        rows, upcoming, await synced_from_cache(cache, keys), await disabled_sources(switch, keys)
    )


class EnabledIn(BaseModel):
    enabled: bool


class EnabledOut(BaseModel):
    unit: str
    dashboard: str
    enabled: bool


@router.put("/units/{unit_code}/dashboards/{dashboard_key}/enabled", response_model=EnabledOut)
async def set_dashboard_enabled(
    unit_code: UnitCode,
    dashboard_key: DashboardKey,
    body: EnabledIn,
    access: Annotated[OrgAccess, Depends(require_org)],
    repo: Annotated[CatalogRepo, Depends(get_catalog_repo)],
) -> EnabledOut:
    """Liga/desliga o dashboard numa unidade (só o Desenvolvedor). Desligado some do hub e da API para todos;
    o Desenvolvedor continua vendo. O banco confere a permissão e grava na auditoria."""
    try:
        enabled = await repo.set_enabled(
            access.user.user_id, access.org_slug, unit_code, dashboard_key, body.enabled
        )
    except ToggleNotAllowed as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(exc)) from None
    except DashboardMissing as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from None
    return EnabledOut(unit=unit_code, dashboard=dashboard_key, enabled=enabled)


async def disabled_sources(switch: Any, keys: set[str]) -> set[str]:
    """Cards cuja fonte principal está desligada (app/source_switch.py: a lista guardada por 30 s).

    Sem o banco da plataforma (switch None) ou sem conseguir ler a lista: nenhum. O hub nunca cai por
    isso; ao abrir, o dashboard confere de novo e responde 423 se a fonte estiver desligada.
    """
    if switch is None:
        return set()
    out: set[str] = set()
    for key in keys:
        module = DASHBOARDS.get(key)
        if module is None:
            continue
        try:
            if await switch.is_disabled(module.source_db):
                out.add(key)
        except SourceUnavailable:
            return set()
    return out


async def synced_from_cache(cache: SourceCache, keys: set[str]) -> dict[str, datetime]:
    """Card -> quando veio do banco o dado MAIS ANTIGO que ele tem no cache. Nenhuma query no cache: fica de
    fora (null, "Atualiza ao abrir").

    A hora vem da memória ou, depois de um deploy/reload, do registro no Redis (app/read_log.py).
    Só as queries que estão no cache contam: sem o aquecedor no LexFlow e no LexPre, e com as queries de todas
    as unidades em `module.queries` (o Recursal tem 12), exigir todas deixava o card quase sempre sem hora.
    """
    out: dict[str, datetime] = {}
    for key in keys:
        module = DASHBOARDS.get(key)
        if module is None or not module.queries:
            continue
        found = [await _query_fetched_at(cache, module.source_db, q) for q in module.queries]
        times = [t for t in found if t is not None]
        if times:
            out[key] = datetime.fromtimestamp(min(times), UTC)
    return out


async def _query_fetched_at(cache: SourceCache, db: str, query: str) -> float | None:
    """Quando a query veio do banco: a inteira ou, se for o caso, o recorte mais novo de alguma unidade
    (app/unit_scope.py). O card é do dashboard, não de uma unidade: mostra a sincronização mais recente."""
    names = [query]
    if db == "lexflow" and query in UNIT_COLUMN:
        names += [scoped_name(query, e) for e in ESCRITORIO_POR_UNIDADE.values()]
    found = [await cache.last_read(f"{db}:{n}") for n in names]
    times = [t for t in found if t is not None]
    return max(times, default=None)
