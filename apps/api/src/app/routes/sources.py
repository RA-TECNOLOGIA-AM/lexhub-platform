from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import CurrentUser, get_current_user
from app.source_offices import (
    OfficeFetch,
    OfficesOut,
    OfficesRepo,
    Product,
    build_offices,
    get_office_reader,
    get_offices_repo,
)
from app.sources import SourceUnavailable

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
