from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from pydantic import BaseModel

from app.access import AccessRepo, OrgAccess, audit_entry, get_repo, require_org
from app.me import UnitOut
from app.support import (
    SupportMemberOut,
    SupportRepo,
    SupportSessionOut,
    SupportStartIn,
    get_support_repo,
)

router = APIRouter(prefix="/orgs/{org_slug}", tags=["support"])


@router.post(
    "/support/sessions", response_model=SupportSessionOut, status_code=status.HTTP_201_CREATED
)
async def start_session(
    request: Request,
    body: SupportStartIn,
    access: Annotated[OrgAccess, Depends(require_org)],
    support: Annotated[SupportRepo, Depends(get_support_repo)],
    repo: Annotated[AccessRepo, Depends(get_repo)],
) -> SupportSessionOut:
    """Modo suporte: começa a navegar como um membro, por até 1 hora. Só Owner/Dev.

    Se a pessoa já tinha uma sessão aberta, ela é encerrada. Tudo vai para a auditoria
    (support.started / support.ended), com o motivo.
    """
    user = access.user
    if not await support.can_support(user.user_id, access.org_id):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="Só Owner e Desenvolvedor usam o modo suporte."
        )
    member = await support.member(access.org_id, str(body.membership_id))
    # Outra organização, inativo e a própria pessoa: a mesma resposta, sem revelar qual.
    if member is None or member["user_id"] == user.user_id:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="Membro não encontrado nesta organização."
        )
    session = await support.start(access.org_id, user.user_id, member, body.reason)
    previous = session.replaced
    if previous is not None:
        await repo.insert_audit(
            audit_entry(
                request,
                user,
                "support.ended",
                org_id=previous.org_id,
                target_type="membership",
                target_id=previous.target_membership_id,
                metadata={"session": previous.id, "end_reason": previous.end_reason},
            )
        )
    await repo.insert_audit(
        audit_entry(
            request,
            user,
            "support.started",
            org_id=access.org_id,
            target_type="membership",
            target_id=member["membership_id"],
            metadata={"session": session.id, "reason": body.reason},
        )
    )
    return SupportSessionOut(
        session_id=session.id,
        expires_at=session.expires_at,
        member=SupportMemberOut(
            membership_id=member["membership_id"],
            name=member["name"],
            avatar_path=member["avatar_path"],
            role_label=member["role_label"],
            units=[UnitOut(code=u["code"], name=u["name"]) for u in member["units"]],
        ),
    )


@router.delete("/support/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def end_session(
    request: Request,
    session_id: UUID,
    access: Annotated[OrgAccess, Depends(require_org)],
    support: Annotated[SupportRepo, Depends(get_support_repo)],
    repo: Annotated[AccessRepo, Depends(get_repo)],
) -> Response:
    """Sai do modo suporte. Só o dono da sessão; repetir não muda nada (204 de novo).

    O front manda X-Support-Session aqui também: aí access.user é o membro, e quem sai é o actor."""
    actor = access.support.actor if access.support is not None else access.user
    session = await support.get(str(session_id))
    if session is None or session.actor_user_id != actor.user_id or session.org_id != access.org_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Sessão de suporte não encontrada.")
    # Só audita quem de fato encerrou: a segunda chamada (ou o vencimento) já fechou antes.
    applied = await support.end(session.id, "exit")
    if applied is not None:
        await repo.insert_audit(
            audit_entry(
                request,
                actor,
                "support.ended",
                org_id=session.org_id,
                target_type="membership",
                target_id=session.target_membership_id,
                metadata={"session": session.id, "end_reason": applied},
            )
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


class HiddenOut(BaseModel):
    key: str
    title: str
    area: str
    reason: str


@router.get("/support/sessions/{session_id}/hidden", response_model=list[HiddenOut])
async def hidden_dashboards(
    session_id: UUID,
    unit: Annotated[str, Query(pattern=r"^[A-Z0-9_]{2,16}$")],
    access: Annotated[OrgAccess, Depends(require_org)],
    support: Annotated[SupportRepo, Depends(get_support_repo)],
) -> list[HiddenOut]:
    """Modo suporte: os dashboards da unidade que o membro não vê, com o motivo. Só leitura.

    Só dentro da própria sessão: o cabeçalho X-Support-Session já validado (require_org) e o mesmo id
    no caminho. A lista é sempre do membro da sessão, nunca de quem pede."""
    if access.support is None or access.support.session_id != str(session_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Sessão de suporte não encontrada.")
    rows = await support.hidden(access.org_id, unit, access.support.target_user_id)
    return [HiddenOut(key=r.key, title=r.title, area=r.area, reason=r.reason) for r in rows]
