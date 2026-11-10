from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.access import AccessRepo, audit_entry, get_repo
from app.auth import CurrentUser, get_current_user, is_platform_staff
from app.me import MeOut, MeRepo, build_me, get_me_repo, pick_org

router = APIRouter(tags=["me"])

OrgQuery = Annotated[str | None, Query(pattern=r"^[a-z0-9][a-z0-9-]{1,62}$")]


@router.get("/me", response_model=MeOut)
async def get_me(
    request: Request,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    repo: Annotated[MeRepo, Depends(get_me_repo)],
    audit: Annotated[AccessRepo, Depends(get_repo)],
    org: OrgQuery = None,
) -> MeOut:
    """Quem está logado, na organização pedida (?org=slug) ou na padrão (a última usada)."""
    orgs = await repo.list_orgs(user.user_id)
    current = pick_org(orgs, org)
    membership = await repo.membership(user.user_id, current.id) if current else None
    if current is None or membership is None:
        # Mesma resposta para organização inexistente, sem acesso ou pessoa sem organização.
        await audit.insert_audit(
            audit_entry(
                request,
                user,
                "org.access_denied",
                target_type="org",
                target_id=org,
                metadata={"org": org},
            )
        )
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Sem acesso")
    return build_me(orgs, current, membership, platform_staff=is_platform_staff(user))
