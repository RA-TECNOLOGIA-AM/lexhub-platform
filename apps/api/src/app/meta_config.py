"""A configuração da Meta (Facebook Ads) em uso: a da tela tem prioridade sobre a do .env.

A TI da LexGroup configura em Unidades e fontes > Integração Meta (app/routes/integrations_routes.py):
o ID e a chave secreta do app, a versão da Graph API e a pausa da coleta. Fica em app.platform_integrations
(migration 20261127120000_integracao_meta.sql), com a chave secreta cifrada pela SOURCE_SECRET_KEY.

O que vale, campo a campo:
  tela      o que está salvo no banco;
  servidor  o .env da API (FACEBOOK_APP_ID, FACEBOOK_APP_SECRET, FACEBOOK_GRAPH_VERSION), quando a tela não definiu;
  padrão    a versão v26.0 e a coleta sem pausa.
A leitura do banco fica guardada por TTL segundos (as rotas e a coleta pedem `refresh()` antes de usar);
salvar pela tela chama `invalidate()`. Banco fora (ou a migration ainda não aplicada): vale o último lido ou o
.env, e a API segue funcionando.
"""

import json
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Annotated, Any, Protocol

import asyncpg
from fastapi import Depends, Request

from app.access import get_db_pool
from app.config import Settings, get_settings
from app.connection_check import Check, CheckResult
from app.secret_box import SecretBox, SecretKeyMissing, SecretUnreadable

logger = logging.getLogger(__name__)

KEY = "meta"
DEFAULT_GRAPH_VERSION = "v26.0"
# As versões oferecidas na tela (a Meta mantém cada uma por uns 2 anos; v26.0 é de 29/07/2026).
GRAPH_VERSIONS = ("v24.0", "v25.0", "v26.0")


@dataclass(frozen=True)
class MetaSettings:
    app_id: str = ""
    app_secret: str = ""
    graph_version: str = DEFAULT_GRAPH_VERSION
    sync_paused: bool = False
    # De onde veio cada campo: 'tela', 'servidor', 'padrão' ou 'nenhum'.
    origin: dict[str, str] = field(default_factory=dict)
    updated_at: datetime | None = None
    updated_by: str | None = None
    secret_unreadable: bool = False  # a chave salva não abre com a SOURCE_SECRET_KEY atual

    @property
    def app_token(self) -> str | None:
        """O token do app ('id|chave'), para o /debug_token e o teste do app. Sem os dois: None."""
        return f"{self.app_id}|{self.app_secret}" if self.app_id and self.app_secret else None


@dataclass(frozen=True)
class StoredIntegration:
    config: dict[str, Any]
    secret_ciphertext: str | None
    updated_at: datetime | None
    updated_by: str | None  # nome de quem salvou (membro da LexGroup)


class IntegrationRepo(Protocol):
    async def load(self, key: str) -> StoredIntegration | None: ...

    async def save(
        self,
        user_id: str,
        key: str,
        config: dict[str, Any],
        ciphertext: str | None,
        secret_action: str,
    ) -> None: ...


def resolve(
    stored: StoredIntegration | None, settings: Settings, box: SecretBox | None
) -> MetaSettings:
    """Junta a tela (stored) e o .env, campo a campo. Puro: testado sem banco."""
    config = stored.config if stored else {}
    origin: dict[str, str] = {}

    app_id = str(config.get("app_id") or "").strip()
    origin["appId"] = "tela" if app_id else "nenhum"
    if not app_id and settings.FACEBOOK_APP_ID.strip():
        app_id, origin["appId"] = settings.FACEBOOK_APP_ID.strip(), "servidor"

    secret, unreadable = "", False
    if stored and stored.secret_ciphertext:
        try:
            if box is None:
                raise SecretUnreadable("sem SOURCE_SECRET_KEY")
            secret, origin["appSecret"] = box.decrypt(stored.secret_ciphertext), "tela"
        except SecretUnreadable:
            unreadable = True
    if not secret and settings.FACEBOOK_APP_SECRET.strip():
        secret, origin["appSecret"] = settings.FACEBOOK_APP_SECRET.strip(), "servidor"
    origin.setdefault("appSecret", "nenhum")

    version = str(config.get("graph_version") or "").strip()
    origin["graphVersion"] = "tela" if version else "padrão"
    if not version and settings.FACEBOOK_GRAPH_VERSION.strip() != DEFAULT_GRAPH_VERSION:
        version, origin["graphVersion"] = settings.FACEBOOK_GRAPH_VERSION.strip(), "servidor"

    return MetaSettings(
        app_id=app_id,
        app_secret=secret,
        graph_version=version or DEFAULT_GRAPH_VERSION,
        sync_paused=bool(config.get("sync_paused", False)),
        origin=origin,
        updated_at=stored.updated_at if stored else None,
        updated_by=stored.updated_by if stored else None,
        secret_unreadable=unreadable,
    )


class MetaConfig:
    def __init__(
        self,
        repo: IntegrationRepo | None,
        settings: Settings,
        box: SecretBox | None,
        *,
        ttl: float = 60.0,
        clock: Callable[[], float] = time.monotonic,
    ):
        self._repo, self._settings, self._box = repo, settings, box
        self._ttl, self._clock = ttl, clock
        self._current = resolve(None, settings, box)
        self._loaded_at: float | None = None

    @property
    def current(self) -> MetaSettings:
        return self._current

    def invalidate(self) -> None:
        self._loaded_at = None

    async def refresh(self, *, force: bool = False) -> MetaSettings:
        if self._repo is None:
            return self._current
        fresh = self._loaded_at is not None and self._clock() - self._loaded_at < self._ttl
        if fresh and not force:
            return self._current
        try:
            stored = await self._repo.load(KEY)
        except (asyncpg.PostgresError, asyncpg.InterfaceError, OSError, TimeoutError) as exc:
            # Banco fora ou migration ainda não aplicada: fica o que já tinha.
            logger.warning(
                "Integração Meta: não leu a configuração da tela (%s)", type(exc).__name__
            )
            self._loaded_at = self._clock()
            return self._current
        self._current = resolve(stored, self._settings, self._box)
        self._loaded_at = self._clock()
        return self._current


def view(meta: MetaSettings, settings: Settings) -> dict[str, Any]:
    """O que a tela recebe: nunca a chave secreta, só se ela existe e de onde vem."""
    versions = list(GRAPH_VERSIONS)
    if meta.graph_version not in versions:
        versions.append(meta.graph_version)
    return {
        "appId": meta.app_id or None,
        "hasAppSecret": bool(meta.app_secret),
        "secretUnreadable": meta.secret_unreadable,
        "graphVersion": meta.graph_version,
        "versions": versions,
        "syncPaused": meta.sync_paused,
        # A trava da máquina (FACEBOOK_ADS_SYNC_ENABLED): sem ela, a pausa da tela não muda nada.
        "syncAvailable": settings.FACEBOOK_ADS_SYNC_ENABLED,
        "origin": meta.origin,
        "updatedAt": meta.updated_at.isoformat() if meta.updated_at else None,
        "updatedBy": meta.updated_by,
    }


# --- Teste do app na Meta ------------------------------------------------------------------------------

AppChecker = Callable[[str, str, str], Awaitable[tuple[CheckResult, str | None]]]


async def check_app(app_id: str, app_secret: str, version: str) -> tuple[CheckResult, str | None]:
    """O ID e a chave do app abrem /{app_id} na Graph API? Devolve as checagens e o nome do app."""
    from app.facebook_ads import (  # aqui: evita import circular
        GraphClient,
        GraphError,
        GraphUnavailable,
    )

    started = time.perf_counter()

    def ms() -> int:
        return int((time.perf_counter() - started) * 1000)

    async with GraphClient(f"{app_id}|{app_secret}", version=version) as graph:
        try:
            app = await graph.get(f"/{app_id}", {"fields": "id,name"})
        except GraphUnavailable:
            msg = "A API não alcançou graph.facebook.com."
            return CheckResult([Check("network", False, msg, ms())]), None
        except GraphError as exc:
            msg = (
                f"A Meta recusou o ID e a chave do app na versão {version} "
                f"(código {exc.code or exc.status}). Confira em developers.facebook.com > seu app > "
                "Configurações do app > Básico."
            )
            checks = [
                Check("network", True, "A API alcançou graph.facebook.com", ms()),
                Check("login", False, msg, ms()),
            ]
            return CheckResult(checks), None
    name = str(app.get("name") or app_id)
    checks = [
        Check("network", True, "A API alcançou graph.facebook.com", ms()),
        Check("login", True, f"App {name} ({app_id}) aceito pela Meta na versão {version}", ms()),
    ]
    return CheckResult(checks, ms=ms()), name


# --- Banco da plataforma ------------------------------------------------------------------------------

_LOAD_SQL = """
select i.config::text, i.secret_ciphertext, i.updated_at,
       (select m.full_name from app.memberships m
          join app.organizations o on o.id = m.org_id and o.slug = 'lexgroup'
         where m.user_id = i.updated_by limit 1) as updated_by
  from app.platform_integrations i
 where i.key = $1
"""


class PgIntegrationRepo:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def load(self, key: str) -> StoredIntegration | None:
        r = await self._pool.fetchrow(_LOAD_SQL, key)
        if r is None:
            return None
        return StoredIntegration(
            config=json.loads(r["config"]),
            secret_ciphertext=r["secret_ciphertext"],
            updated_at=r["updated_at"],
            updated_by=r["updated_by"],
        )

    async def save(self, user_id, key, config, ciphertext, secret_action) -> None:
        from app.source_admin import _call  # o mesmo tradutor de erro (42501 -> 403, P0001 -> 409)

        await _call(
            self._pool,
            "select app_private.set_platform_integration($1::uuid, $2, $3::jsonb, $4, $5)",
            user_id,
            key,
            json.dumps(config),
            ciphertext,
            secret_action,
        )


def build_meta_config(pool: asyncpg.Pool | None, settings: Settings) -> MetaConfig:
    try:
        box: SecretBox | None = SecretBox.from_setting(settings.SOURCE_SECRET_KEY)
    except (SecretKeyMissing, ValueError):
        box = None
    return MetaConfig(PgIntegrationRepo(pool) if pool is not None else None, settings, box)


async def get_meta_config(
    request: Request, settings: Annotated[Settings, Depends(get_settings)]
) -> MetaConfig:
    """A configuração da Meta atualizada (app.state.meta_config; sem ela, só o .env)."""
    meta = getattr(request.app.state, "meta_config", None)
    if meta is None:
        meta = MetaConfig(None, settings, None)
        request.app.state.meta_config = meta
    await meta.refresh()
    return meta


def get_integration_repo(pool: Annotated[asyncpg.Pool, Depends(get_db_pool)]) -> IntegrationRepo:
    return PgIntegrationRepo(pool)
