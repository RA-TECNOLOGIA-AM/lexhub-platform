from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from app.access import AccessRepo, deny_org, get_repo
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
        await deny_org(request, user, audit, org)
    return build_me(orgs, current, membership, platform_staff=is_platform_staff(user))
