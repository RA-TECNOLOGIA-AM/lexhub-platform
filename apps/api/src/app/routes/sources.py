from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth import CurrentUser, get_current_user
from app.database import SourceUnavailable
from app.source_cache import SourceCache
from app.source_health import MonitoredRepo, failing_by_org, get_monitored_repo
from app.source_offices import (
    OfficeFetch,
    OfficesOut,
    OfficesRepo,
    Product,
    build_offices,
    get_office_reader,
    get_offices_repo,
)
from app.sources import get_source_cache

# Fora de /orgs/{org}: a lista é do banco do produto inteiro e só a TI da LexGroup vê.
router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("/{product}/offices", response_model=OfficesOut)
async def list_offices(
    product: Product,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    repo: Annotated[OfficesRepo, Depends(get_offices_repo)],
    reader: Annotated[OfficeFetch, Depends(get_office_reader)],
) -> OfficesOut:
    """Conectar fonte: os escritórios do LexPre/LexFlow e a unidade a que cada um já está ligado."""
    if not await repo.is_source_admin(user.user_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Só a TI da LexGroup conecta fontes")
    try:
        rows = await reader(product)
    except SourceUnavailable as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Banco do {product} indisponível"
        ) from exc
    return build_offices(product, rows, await repo.linked(product))


class FailingOut(BaseModel):
    orgs: dict[str, list[str]]  # slug -> chaves das fontes com falha ([] = nenhuma)


@router.get("/failing", response_model=FailingOut)
async def failing_sources(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    repo: Annotated[MonitoredRepo, Depends(get_monitored_repo)],
    cache: Annotated[SourceCache, Depends(get_source_cache)],
) -> FailingOut:
    """Tela Clientes: fontes com falha de cada organização (app/source_health.py). Só a TI da
    LexGroup. Lê o banco da plataforma (quais fontes contam) e o registro de leituras; nada vai aos
    bancos de origem."""
    if not await repo.is_source_admin(user.user_id):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="Só a TI da LexGroup vê as fontes dos clientes"
        )
    return FailingOut(orgs=await failing_by_org(cache.reads, await repo.monitored()))
