"""Validação do login (JWT do Supabase Auth) feita localmente, sem chamada HTTP por requisição.

O token é verificado com as chaves públicas do projeto (JWKS), que ficam em cache.
Um `kid` desconhecido força uma nova busca (rotação de chave), limitada a uma por
intervalo para que tokens forjados não virem um laço de requisições ao Supabase.
"""

import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Annotated, Any

import httpx
import jwt
from fastapi import Depends, HTTPException, Request, status

from app.config import Settings, get_settings

JwksLoader = Callable[[], Awaitable[dict[str, Any]]]

_ASYMMETRIC_ALGS = ["ES256", "RS256", "EdDSA"]
_REFRESH_MIN_INTERVAL_S = 60.0


class InvalidToken(Exception):
    """Token ausente, malformado, expirado ou de outro projeto."""


@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    email: str | None
    claims: dict[str, Any]


def http_jwks_loader(settings: Settings) -> JwksLoader:
    async def load() -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=5) as http:
            r = await http.get(settings.jwks_url)
            r.raise_for_status()
            return r.json()

    return load


class TokenVerifier:
    def __init__(self, settings: Settings, jwks_loader: JwksLoader | None = None):
        self._settings = settings
        self._load = jwks_loader or http_jwks_loader(settings)
        self._keys: dict[str, jwt.PyJWK] = {}
        self._loaded = False
        self._last_forced = 0.0
        self._lock = asyncio.Lock()

    async def _refresh(self, force: bool) -> None:
        async with self._lock:
            now = time.monotonic()
            if force:
                # kid desconhecido: no máximo uma rebusca por intervalo.
                if self._last_forced and now - self._last_forced < _REFRESH_MIN_INTERVAL_S:
                    return
                self._last_forced = now
            elif self._loaded:
                return
            self._loaded = True
            try:
                data = await self._load()
            except (httpx.HTTPError, ValueError):
                return  # mantém as chaves que já tinha; o token cai como inválido
            keys = {}
            for jwk in data.get("keys", []):
                try:
                    keys[jwk["kid"]] = jwt.PyJWK(jwk)
                except (KeyError, jwt.PyJWKError):
                    continue
            self._keys = keys

    async def _key_for(self, kid: str | None) -> jwt.PyJWK | None:
        if not self._loaded:
            await self._refresh(force=False)
        if kid and kid not in self._keys:
            await self._refresh(force=True)
        return self._keys.get(kid) if kid else None

    async def verify(self, token: str) -> CurrentUser:
        try:
            header = jwt.get_unverified_header(token)
        except jwt.PyJWTError as e:
            raise InvalidToken from e

        alg = header.get("alg")
        if alg in _ASYMMETRIC_ALGS:
            jwk = await self._key_for(header.get("kid"))
            if jwk is None:
                raise InvalidToken
            key, algorithms = jwk.key, [alg]
        elif alg == "HS256" and self._settings.SUPABASE_JWT_SECRET:
            key, algorithms = self._settings.SUPABASE_JWT_SECRET, ["HS256"]
        else:
            raise InvalidToken  # inclui alg=none e HS256 sem segredo configurado

        try:
            claims = jwt.decode(
                token,
                key=key,
                algorithms=algorithms,
                audience=self._settings.JWT_AUDIENCE,
                issuer=self._settings.jwt_issuer,
                options={"require": ["sub", "exp", "aud", "iss"]},
                leeway=30,
            )
        except jwt.PyJWTError as e:
            raise InvalidToken from e

        return CurrentUser(user_id=claims["sub"], email=claims.get("email"), claims=claims)


def get_verifier(request: Request) -> TokenVerifier:
    return request.app.state.token_verifier


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não autenticado",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    request: Request,
    verifier: Annotated[TokenVerifier, Depends(get_verifier)],
) -> CurrentUser:
    scheme, _, token = (request.headers.get("Authorization") or "").partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise _unauthorized()
    try:
        return await verifier.verify(token.strip())
    except InvalidToken:
        raise _unauthorized() from None


def build_verifier(settings: Settings | None = None) -> TokenVerifier:
    return TokenVerifier(settings or get_settings())
