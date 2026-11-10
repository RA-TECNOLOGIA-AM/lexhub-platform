from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response, status
from pydantic import StringConstraints

from app.access import (
    AccessRepo,
    DashboardKey,
    OrgAccess,
    audit_entry,
    get_repo,
    require_org,
)
from app.hub_prefs import MAX_ORDER, HubPrefsRepo, clean_order, get_hub_prefs_repo

router = APIRouter(prefix="/orgs/{org_slug}", tags=["hub"])

Org = Annotated[OrgAccess, Depends(require_org)]
Prefs = Annotated[HubPrefsRepo, Depends(get_hub_prefs_repo)]
KeyItem = Annotated[str, StringConstraints(pattern=r"^[a-z0-9][a-z0-9_-]{1,62}$")]
OrderBody = Annotated[list[KeyItem], Body(max_length=MAX_ORDER)]

NO_CONTENT = Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/favorites")
async def list_favorites(access: Org, prefs: Prefs) -> list[str]:
    """Keys dos dashboards favoritos da pessoa nesta organização."""
    return await prefs.list_favorites(access.user.user_id, access.org_id)


@router.post("/favorites/{dashboard_key}", status_code=204)
async def add_favorite(
    request: Request,
    dashboard_key: DashboardKey,
    access: Org,
    prefs: Prefs,
    audit: Annotated[AccessRepo, Depends(get_repo)],
) -> Response:
    """Favorita. Repetir não é erro; dashboard que a pessoa não pode abrir = 403 (auditado)."""
    if not await prefs.add_favorite(access.user.user_id, access.org_id, dashboard_key):
        await audit.insert_audit(
            audit_entry(
                request,
                access.user,
                "dashboard.access_denied",
                org_id=access.org_id,
                target_type="dashboard",
                target_id=dashboard_key,
                metadata={"org": access.org_slug, "action": "favorite"},
            )
        )
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Sem acesso")
    return NO_CONTENT


@router.delete("/favorites/{dashboard_key}", status_code=204)
async def remove_favorite(dashboard_key: DashboardKey, access: Org, prefs: Prefs) -> Response:
    """Desfavorita. Tirar o que não estava lá não é erro."""
    await prefs.remove_favorite(access.user.user_id, access.org_id, dashboard_key)
    return NO_CONTENT


@router.get("/hub-order")
async def get_hub_order(access: Org, prefs: Prefs) -> list[str]:
    """Ordem dos cards que a pessoa arrastou ([] = ordem do catálogo)."""
    return await prefs.get_order(access.user.user_id, access.org_id)


@router.put("/hub-order", status_code=204)
async def set_hub_order(keys: OrderBody, access: Org, prefs: Prefs) -> Response:
    """Salva a ordem inteira (a lista que está na tela). Key repetida conta só a primeira vez."""
    await prefs.set_order(access.user.user_id, access.org_id, clean_order(keys))
    return NO_CONTENT
