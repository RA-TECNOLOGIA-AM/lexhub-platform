"""Tokens da API pública.

- POST /orgs/{org}/api-key/tokens (login do LexHub): o dono de uma chave ativa gera o par de tokens.
  Gerar de novo invalida os anteriores. Os tokens aparecem só nesta resposta.
- POST /v1/auth/token: troca o refresh token por um par novo (rotação, regras em app/public_api/service.py).
- `require_api_key`: dependency das rotas de dados /v1 (Authorization: Bearer <access token>).
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.access import AccessRepo, OrgSlug, audit_entry, get_repo
from app.auth import CurrentUser, get_current_user
from app.clock import get_now
from app.config import Settings, get_settings
from app.public_api.service import (
    KEY_CACHE,
    KeyCache,
    RefreshRejected,
    TokenPair,
    authenticate,
    issue_pair,
    rotate,
)
from app.public_api.store import ApiKey, ApiKeyRepo, get_api_key_repo
from app.public_api.tokens import InvalidAccessToken

org = APIRouter(prefix="/orgs/{org_slug}/api-key", tags=["api pública"])
v1 = APIRouter(prefix="/v1", tags=["api pública"])

_OFF = "API pública desligada (PUBLIC_API_JWT_SECRET não configurado)."
_REJECTED = {
    "invalido": "Refresh token inválido.",
    "vencido": "Refresh token vencido: gere novos tokens no LexHub.",
    "reuso": (
        "Refresh token já usado: por segurança, todos os tokens desta chave foram revogados. "
        "Gere novos tokens no LexHub."
    ),
    "chave_inativa": "Chave de API inativa.",
}


class TokenOut(BaseModel):
    access_token: str
    access_expires_at: datetime
    refresh_token: str
    refresh_expires_at: datetime
    token_type: str = "Bearer"


class RefreshIn(BaseModel):
    refresh_token: str = Field(min_length=1, max_length=200)


def get_key_cache() -> KeyCache:
    return KEY_CACHE


def _out(pair: TokenPair) -> TokenOut:
    return TokenOut(**vars(pair))


def _require_secret(settings: Settings) -> None:
    if not settings.PUBLIC_API_JWT_SECRET:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=_OFF)


@org.post("/tokens", response_model=TokenOut)
async def issue_tokens(
    request: Request,
    org_slug: OrgSlug,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    keys: Annotated[ApiKeyRepo, Depends(get_api_key_repo)],
    audit: Annotated[AccessRepo, Depends(get_repo)],
    settings: Annotated[Settings, Depends(get_settings)],
    now: Annotated[datetime, Depends(get_now)],
) -> TokenOut:
    _require_secret(settings)
    key = await keys.get_active_key_for(user.user_id, org_slug)
    if key is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="Você não tem chave de API ativa nesta organização."
        )
    pair = await issue_pair(keys, key, settings, now)
    await audit.insert_audit(
        audit_entry(
            request,
            user,
            "api_key.tokens_issued",
            org_id=key.org_id,
            target_type="api_key",
            target_id=key.id,
        )
    )
    return _out(pair)


@v1.post("/auth/token", response_model=TokenOut)
async def renew_token(
    request: Request,
    body: RefreshIn,
    keys: Annotated[ApiKeyRepo, Depends(get_api_key_repo)],
    audit: Annotated[AccessRepo, Depends(get_repo)],
    settings: Annotated[Settings, Depends(get_settings)],
    now: Annotated[datetime, Depends(get_now)],
) -> TokenOut:
    _require_secret(settings)
    try:
        return _out(await rotate(keys, body.refresh_token, settings, now))
    except RefreshRejected as exc:
        if exc.reason == "reuso" and exc.key_id:
            key = await keys.get_key(exc.key_id)
            if key is not None:
                owner = CurrentUser(user_id=key.user_id, email=None, claims={})
                await audit.insert_audit(
                    audit_entry(
                        request,
                        owner,
                        "api_key.refresh_reuse",
                        org_id=key.org_id,
                        target_type="api_key",
                        target_id=key.id,
                    )
                )
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=_REJECTED[exc.reason]) from None


async def require_api_key(
    request: Request,
    keys: Annotated[ApiKeyRepo, Depends(get_api_key_repo)],
    settings: Annotated[Settings, Depends(get_settings)],
    now: Annotated[datetime, Depends(get_now)],
    cache: Annotated[KeyCache, Depends(get_key_cache)],
) -> ApiKey:
    _require_secret(settings)
    scheme, _, token = (request.headers.get("Authorization") or "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Envie o access token em Authorization: Bearer <token>.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return await authenticate(keys, token.strip(), settings, now, cache)
    except InvalidAccessToken as exc:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail=f"Access token inválido: {exc}.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
