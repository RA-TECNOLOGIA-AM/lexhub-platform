"""Emissão, rotação e checagem dos tokens da API pública (regras da v1).

- `issue_pair`: "Gerar tokens" na tela. Revoga os tokens anteriores da chave antes de emitir o par novo.
- `rotate`: POST /v1/auth/token. O refresh enviado deixa de valer; reusar um já trocado (inclusive em duas
  trocas simultâneas) revoga todos os tokens da chave.
- `authenticate`: access token -> chave ativa. A chave vem do banco com cache curto (60 s), então revogar
  vale sem esperar o token vencer.
"""

import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.public_api.store import ApiKey, ApiKeyRepo
from app.public_api.tokens import (
    InvalidAccessToken,
    hash_refresh_token,
    issue_access_token,
    new_refresh_token,
    verify_access_token,
)


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    access_expires_at: datetime
    refresh_token: str
    refresh_expires_at: datetime


class RefreshRejected(Exception):
    """reason: invalido | vencido | reuso | chave_inativa."""

    def __init__(self, reason: str, key_id: str | None = None):
        super().__init__(reason)
        self.reason = reason
        self.key_id = key_id  # chave do refresh, quando conhecida (auditoria do reuso)


class KeyCache:
    def __init__(self, ttl_s: float = 60.0, monotonic: Callable[[], float] = time.monotonic):
        self._ttl = ttl_s
        self._now = monotonic
        self._items: dict[str, tuple[float, ApiKey | None]] = {}

    async def get(self, repo: ApiKeyRepo, key_id: str) -> ApiKey | None:
        hit = self._items.get(key_id)
        if hit and self._now() - hit[0] < self._ttl:
            return hit[1]
        key = await repo.get_key(key_id)
        self._items[key_id] = (self._now(), key)
        return key

    def forget(self, key_id: str) -> None:
        self._items.pop(key_id, None)


KEY_CACHE = KeyCache()


def _secret(settings) -> str:
    if not settings.PUBLIC_API_JWT_SECRET:
        raise RuntimeError("PUBLIC_API_JWT_SECRET não configurado")
    return settings.PUBLIC_API_JWT_SECRET


async def _new_pair(
    repo: ApiKeyRepo, key_id: str, settings, now: datetime
) -> tuple[TokenPair, str]:
    access, access_exp = issue_access_token(
        key_id, _secret(settings), settings.PUBLIC_API_ACCESS_TOKEN_TTL_SECONDS, now
    )
    refresh = new_refresh_token()
    refresh_exp = now + timedelta(days=settings.PUBLIC_API_REFRESH_TOKEN_TTL_DAYS)
    refresh_id = await repo.insert_refresh(key_id, hash_refresh_token(refresh), refresh_exp)
    return TokenPair(access, access_exp, refresh, refresh_exp), refresh_id


async def issue_pair(repo: ApiKeyRepo, key: ApiKey, settings, now: datetime) -> TokenPair:
    _secret(settings)
    await repo.revoke_all(key.id, now)
    KEY_CACHE.forget(key.id)
    pair, _ = await _new_pair(repo, key.id, settings, now)
    return pair


async def rotate(repo: ApiKeyRepo, refresh_token: str, settings, now: datetime) -> TokenPair:
    _secret(settings)
    row = await repo.get_refresh(hash_refresh_token(refresh_token))
    if row is None or row.revoked_at is not None:
        raise RefreshRejected("invalido")
    if row.used_at is not None:
        await repo.revoke_all(row.key_id, now)
        KEY_CACHE.forget(row.key_id)
        raise RefreshRejected("reuso", row.key_id)
    if now >= row.expires_at:
        raise RefreshRejected("vencido", row.key_id)
    key = await repo.get_key(row.key_id)
    if key is None or key.status != "active":
        raise RefreshRejected("chave_inativa", row.key_id)
    if not await repo.consume_refresh(row.id, now):
        await repo.revoke_all(row.key_id, now)
        KEY_CACHE.forget(row.key_id)
        raise RefreshRejected("reuso", row.key_id)
    pair, new_id = await _new_pair(repo, key.id, settings, now)
    await repo.mark_replaced(row.id, new_id)
    return pair


async def authenticate(
    repo: ApiKeyRepo, access_token: str, settings, now: datetime, cache: KeyCache = KEY_CACHE
) -> ApiKey:
    claims = verify_access_token(access_token, _secret(settings), now)
    key = await cache.get(repo, claims.key_id)
    if key is None or key.status != "active":
        raise InvalidAccessToken("chave inativa")
    # O iat do JWT tem precisão de segundos: compara com tokens_valid_since truncado.
    since = key.tokens_valid_since
    if since is not None and claims.issued_at < since.replace(microsecond=0):
        raise InvalidAccessToken("token revogado")
    return key
