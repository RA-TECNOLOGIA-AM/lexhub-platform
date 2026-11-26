"""Tokens da API pública (/v1), no modelo da v1.

- Access token: JWT HS256 com `PUBLIC_API_JWT_SECRET`, validade `PUBLIC_API_ACCESS_TOKEN_TTL_SECONDS`
  (1 semana). Só carrega a chave (`sub`); o alcance vem do banco a cada chamada.
- Refresh token: texto aleatório `lxr_...`. Só o SHA-256 fica no banco; o valor aparece uma vez.
"""

import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt

REFRESH_PREFIX = "lxr_"
_TYP = "lxh_access"
_ALG = "HS256"


class InvalidAccessToken(Exception):
    """Assinatura, formato, tipo ou validade do access token não conferem."""


@dataclass(frozen=True)
class AccessClaims:
    key_id: str
    issued_at: datetime
    expires_at: datetime


def issue_access_token(key_id: str, secret: str, ttl_s: int, now: datetime) -> tuple[str, datetime]:
    expires_at = now + timedelta(seconds=ttl_s)
    claims = {"sub": key_id, "iat": now, "exp": expires_at, "typ": _TYP, "jti": uuid.uuid4().hex}
    return jwt.encode(claims, secret, algorithm=_ALG), expires_at


def verify_access_token(token: str, secret: str, now: datetime) -> AccessClaims:
    try:
        claims = jwt.decode(
            token,
            secret,
            algorithms=[_ALG],
            options={
                "require": ["sub", "iat", "exp", "typ"],
                "verify_exp": False,
                "verify_iat": False,
            },
        )
    except jwt.PyJWTError as exc:
        raise InvalidAccessToken(str(exc)) from None
    if claims.get("typ") != _TYP:
        raise InvalidAccessToken("tipo de token inválido")
    issued_at = datetime.fromtimestamp(claims["iat"], UTC)
    expires_at = datetime.fromtimestamp(claims["exp"], UTC)
    if now >= expires_at:
        raise InvalidAccessToken("token expirado")
    return AccessClaims(key_id=str(claims["sub"]), issued_at=issued_at, expires_at=expires_at)


def new_refresh_token() -> str:
    return REFRESH_PREFIX + secrets.token_urlsafe(32)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
