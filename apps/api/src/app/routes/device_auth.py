import logging
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from postgrest.exceptions import APIError
from pydantic import BaseModel, Field
from supabase import AsyncClient
from supabase_auth import AsyncGoTrueClient
from supabase_auth.errors import AuthApiError

from app.config import Settings, get_settings
from app.device_auth import (
    DeviceAuthRepository,
    DeviceAuthUnavailable,
    SupabaseDeviceAuthRepository,
    digest_device_value,
)
from app.me import MeRepo, get_me_repo
from app.supabase_client import get_supabase_admin, get_supabase_auth

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth/device", tags=["device auth"])

_USER_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
_USER_CODE_LENGTH = 8
_POLL_INTERVAL = 5
_SESSION_LIFETIME = timedelta(minutes=10)


class DeviceCodeOut(BaseModel):
    device_code: str
    user_code: str
    verification_uri: str
    interval: int
    expires_in: int


class DeviceAuthorizeIn(BaseModel):
    user_code: str = Field(min_length=1, max_length=32)


class DeviceSessionOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class DeviceAuthError(BaseModel):
    error: str
    error_description: str


def get_device_auth_repository(
    client: Annotated[AsyncClient, Depends(get_supabase_admin)],
) -> DeviceAuthRepository:
    return SupabaseDeviceAuthRepository(client)


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _rate_limit_key(secret: str, action: str, request: Request) -> str:
    return digest_device_value(secret, "rate-limit", f"{action}:{_client_ip(request)}")


async def _enforce_rate_limit(
    repository: DeviceAuthRepository,
    settings: Settings,
    request: Request,
    action: str,
    limit: int,
) -> None:
    if not await repository.allow_request(
        _rate_limit_key(settings.supabase_secret_key, action, request),
        limit,
        60,
    ):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas tentativas. Aguarde um minuto e tente novamente.",
            headers={"Retry-After": "60"},
        )


def _oauth_error(error: str, description: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=DeviceAuthError(error=error, error_description=description).model_dump(),
        headers={"Cache-Control": "no-store", "Pragma": "no-cache"},
    )


def _new_user_code() -> str:
    code = "".join(secrets.choice(_USER_CODE_ALPHABET) for _ in range(_USER_CODE_LENGTH))
    return f"{code[:4]}-{code[4:]}"


def _normalize_user_code(value: str) -> str | None:
    normalized = value.strip().upper()
    letters = normalized.replace("-", "")
    if (
        len(normalized) != 9
        or normalized[4] != "-"
        or len(letters) != _USER_CODE_LENGTH
        or any(char not in _USER_CODE_ALPHABET for char in letters)
    ):
        return None
    return f"{letters[:4]}-{letters[4:]}"


def _bearer_token(request: Request) -> str:
    scheme, separator, token = (request.headers.get("Authorization") or "").partition(" ")
    if scheme.lower() != "bearer" or not separator or not token.strip():
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Não autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token.strip()


@router.post("/code", response_model=DeviceCodeOut)
async def create_device_code(
    request: Request,
    repository: Annotated[DeviceAuthRepository, Depends(get_device_auth_repository)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> DeviceCodeOut:
    if not settings.WEB_BASE_URL:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Login por dispositivo não configurado",
        )
    try:
        await _enforce_rate_limit(repository, settings, request, "create", 10)
        now = datetime.now(UTC)
        await repository.cleanup_expired(now)
        for _ in range(5):
            device_code = secrets.token_urlsafe(32)
            user_code = _new_user_code()
            created = await repository.create_session(
                digest_device_value(settings.supabase_secret_key, "device", device_code),
                digest_device_value(settings.supabase_secret_key, "user", user_code),
                now + _SESSION_LIFETIME,
            )
            if created:
                verification_uri = (
                    f"{settings.WEB_BASE_URL.rstrip('/')}/ativar?"
                    f"{urlencode({'code': user_code})}"
                )
                return DeviceCodeOut(
                    device_code=device_code,
                    user_code=user_code,
                    verification_uri=verification_uri,
                    interval=_POLL_INTERVAL,
                    expires_in=int(_SESSION_LIFETIME.total_seconds()),
                )
    except (APIError, httpx.HTTPError) as exc:
        logger.warning("Falha ao criar login por dispositivo (%s)", type(exc).__name__)
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível iniciar o login por dispositivo.",
        ) from None
    raise HTTPException(
        status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Não foi possível reservar um código de ativação. Tente novamente.",
    )


@router.post("/authorize", response_model=dict[str, str])
async def authorize_device(
    request: Request,
    body: Annotated[DeviceAuthorizeIn, Body()],
    client: Annotated[AsyncClient, Depends(get_supabase_admin)],
    repository: Annotated[DeviceAuthRepository, Depends(get_device_auth_repository)],
    me_repo: Annotated[MeRepo, Depends(get_me_repo)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, str] | JSONResponse:
    try:
        await _enforce_rate_limit(repository, settings, request, "authorize", 10)
    except (APIError, httpx.HTTPError) as exc:
        logger.warning("Falha no limite de tentativas de ativação (%s)", type(exc).__name__)
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível validar a ativação agora.",
        ) from None

    token = _bearer_token(request)
    try:
        user_response = await client.auth.get_user(token)
    except AuthApiError:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Não autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except httpx.HTTPError as exc:
        logger.warning("Falha ao validar sessão de ativação (%s)", type(exc).__name__)
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível validar sua sessão agora.",
        ) from None

    if user_response is None or user_response.user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Não autenticado")

    # Só quem já tem acesso ao LexHub (membro ativo de alguma organização) liga uma TV.
    # Qualquer conta Google entra no login (é assim que se pede acesso); sem esta checagem,
    # ela aprovaria uma TV que ficaria parada na tela "sem acesso" com uma sessão dela.
    if not await me_repo.list_memberships(user_response.user.id):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Sua conta ainda não tem acesso ao LexHub. Peça acesso antes de conectar uma TV.",
        )

    user_code = _normalize_user_code(body.user_code)
    if user_code is None:
        return _oauth_error("invalid_grant", "Código inválido ou expirado.")

    try:
        result = await repository.approve(
            digest_device_value(settings.supabase_secret_key, "user", user_code),
            user_response.user.id,
        )
    except (APIError, httpx.HTTPError) as exc:
        logger.warning("Falha ao aprovar login por dispositivo (%s)", type(exc).__name__)
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível aprovar o dispositivo agora.",
        ) from None
    if result != "approved":
        return _oauth_error("invalid_grant", "Código inválido ou expirado.")
    return {"status": "approved"}


@router.get("/token", response_model=DeviceSessionOut)
async def poll_device_token(
    request: Request,
    device_code: Annotated[str, Query(min_length=40, max_length=128)],
    client: Annotated[AsyncClient, Depends(get_supabase_admin)],
    auth: Annotated[AsyncGoTrueClient, Depends(get_supabase_auth)],
    repository: Annotated[DeviceAuthRepository, Depends(get_device_auth_repository)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> DeviceSessionOut | JSONResponse:
    try:
        await _enforce_rate_limit(repository, settings, request, "poll", 60)
        claim_id = str(uuid.uuid4())
        device_hash = digest_device_value(settings.supabase_secret_key, "device", device_code)
        claim = await repository.claim(device_hash, claim_id)
    except (APIError, httpx.HTTPError) as exc:
        logger.warning("Falha ao consultar login por dispositivo (%s)", type(exc).__name__)
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível consultar o login agora.",
        ) from None

    result = str(claim.get("result")) if claim else "invalid"
    if result == "authorization_pending":
        return _oauth_error("authorization_pending", "Aguardando aprovação.")
    if result == "slow_down":
        return _oauth_error("slow_down", "Aguarde antes de consultar novamente.")
    if result == "expired":
        return _oauth_error("expired_token", "O código de ativação expirou.")
    if result != "approved" or not claim or not claim.get("user_id"):
        return _oauth_error("invalid_grant", "Código de dispositivo inválido.")

    user_id = str(claim["user_id"])
    try:
        user_response = await client.auth.admin.get_user_by_id(user_id)
        user = user_response.user
        if user is None or not user.email:
            raise DeviceAuthUnavailable("O usuário não tem e-mail para emitir uma sessão.")
        link = await client.auth.admin.generate_link({"type": "magiclink", "email": user.email})
        auth_response = await auth.verify_otp(
            {"token_hash": link.properties.hashed_token, "type": "magiclink"}
        )
        session = auth_response.session
        if session is None:
            raise DeviceAuthUnavailable("O Supabase Auth não emitiu uma sessão.")
    except (AuthApiError, httpx.HTTPError, DeviceAuthUnavailable) as exc:
        try:
            await repository.finish(device_hash, claim_id, consume=False)
        except (APIError, httpx.HTTPError) as release_error:
            logger.error(
                "Não foi possível liberar a sessão reivindicada (%s)",
                type(release_error).__name__,
            )
        logger.error("Falha ao emitir sessão Supabase para TV (%s)", type(exc).__name__)
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível emitir a sessão da TV agora. Tente novamente.",
        ) from None

    try:
        consumed = await repository.finish(device_hash, claim_id, consume=True)
    except (APIError, httpx.HTTPError) as exc:
        logger.error("Não foi possível consumir sessão de dispositivo (%s)", type(exc).__name__)
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível concluir o login por dispositivo.",
        ) from None
    if not consumed:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="O login da TV já foi consumido. Gere um novo código.",
        )

    response = DeviceSessionOut(
        access_token=session.access_token,
        refresh_token=session.refresh_token,
        token_type="bearer",
        expires_in=session.expires_in,
    )
    return JSONResponse(
        content=response.model_dump(),
        headers={"Cache-Control": "no-store", "Pragma": "no-cache"},
    )
