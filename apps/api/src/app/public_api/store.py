"""Chaves da API pública no banco da plataforma (tabelas app.api_* da migration 20261126230000).

O alcance da chave fica no banco (`app_private.api_key_scope`, coberta por supabase/tests/api_publica_test.sql).
`ApiKeyRepo` é a interface das rotas; os testes trocam por tests/public_api_fakes.py.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Annotated, Protocol

import asyncpg
from fastapi import Depends

from app.platform_db import get_db_pool


@dataclass(frozen=True)
class ApiKey:
    id: str
    org_id: str
    org_slug: str
    user_id: str
    status: str  # pending | active | rejected | revoked
    tokens_valid_since: datetime | None


@dataclass(frozen=True)
class RefreshRow:
    id: str
    key_id: str
    token_hash: str
    expires_at: datetime
    used_at: datetime | None
    revoked_at: datetime | None


@dataclass(frozen=True)
class KeyAccess:
    """Unidade resolvida pela URL e o que a chave alcança nela (scope None = sem acesso)."""

    org_id: str
    unit_id: str
    scope: str | None
    timezone: str = "America/Manaus"
    can_see_commission: bool = False
    source_refs: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Reachable:
    org_slug: str
    unit_code: str
    unit_id: str
    dashboard_key: str


class ApiKeyRepo(Protocol):
    async def get_key(self, key_id: str) -> ApiKey | None: ...

    async def get_active_key_for(self, user_id: str, org_slug: str) -> ApiKey | None: ...

    async def get_refresh(self, token_hash: str) -> RefreshRow | None: ...

    async def consume_refresh(self, refresh_id: str, now: datetime) -> bool: ...

    async def insert_refresh(self, key_id: str, token_hash: str, expires_at: datetime) -> str: ...

    async def mark_replaced(self, refresh_id: str, new_id: str) -> None: ...

    async def revoke_all(self, key_id: str, now: datetime) -> None: ...

    async def touch_last_used(self, key_id: str, now: datetime) -> None: ...

    async def resolve(
        self, key_id: str, org_slug: str, unit_code: str, dashboard_key: str
    ) -> KeyAccess | None: ...

    async def reachable(self, key_id: str) -> list[Reachable]: ...


_KEY_COLS = """
select k.id::text, k.org_id::text, o.slug as org_slug, k.user_id::text, k.status, k.tokens_valid_since
  from app.api_keys k
  join app.organizations o on o.id = k.org_id
"""
_GET_KEY_SQL = _KEY_COLS + " where k.id = $1::uuid"
_ACTIVE_KEY_SQL = _KEY_COLS + " where k.user_id = $1::uuid and o.slug = $2 and k.status = 'active'"

_GET_REFRESH_SQL = """
select id::text, key_id::text, token_hash, expires_at, used_at, revoked_at
  from app.api_refresh_tokens where token_hash = $1
"""
# Condicional no próprio UPDATE: de duas trocas simultâneas do mesmo token, só uma recebe a linha.
_CONSUME_SQL = """
update app.api_refresh_tokens set used_at = $2
 where id = $1::uuid and used_at is null and revoked_at is null
returning id
"""
_INSERT_REFRESH_SQL = """
insert into app.api_refresh_tokens (key_id, token_hash, expires_at)
values ($1::uuid, $2, $3) returning id::text
"""
_REPLACED_SQL = "update app.api_refresh_tokens set replaced_by = $2::uuid where id = $1::uuid"
_REVOKE_REFRESH_SQL = """
update app.api_refresh_tokens set revoked_at = $2 where key_id = $1::uuid and revoked_at is null
"""
_TOKENS_SINCE_SQL = "update app.api_keys set tokens_valid_since = $2 where id = $1::uuid"
_TOUCH_SQL = "update app.api_keys set last_used_at = $2 where id = $1::uuid"

_RESOLVE_SQL = """
select o.id::text as org_id,
       u.id::text as unit_id,
       u.timezone,
       app_private.api_key_scope(k.id, u.id, $4) as scope,
       (app_private.has_unit_permission(k.user_id, u.id, 'org.dashboards.all')
        or app_private.has_unit_permission(k.user_id, u.id, 'unit.dashboards.all')) as can_see_commission,
       coalesce((select jsonb_object_agg(r.source, r.ref) from app.unit_source_refs r
                  where r.unit_id = u.id), '{}'::jsonb)::text as source_refs
  from app.api_keys k
  join app.organizations o on o.id = k.org_id and o.slug = $2 and o.active
  join app.units u on u.org_id = o.id and u.code = $3 and u.active
 where k.id = $1::uuid
"""

_REACHABLE_SQL = """
select o.slug as org_slug, u.code as unit_code, u.id::text as unit_id, od.dashboard_key
  from app.api_keys k
  join app.organizations o on o.id = k.org_id and o.active
  join app.units u on u.org_id = o.id and u.active
  join app.org_dashboards od on od.unit_id = u.id and od.enabled
 where k.id = $1::uuid and k.status = 'active'
   and app_private.api_key_scope(k.id, u.id, od.dashboard_key) is not null
 order by u.code, od.dashboard_key
"""


def _key(row) -> ApiKey | None:
    return ApiKey(**dict(row)) if row else None


class PgApiKeyRepo:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def get_key(self, key_id):
        return _key(await self._pool.fetchrow(_GET_KEY_SQL, key_id))

    async def get_active_key_for(self, user_id, org_slug):
        return _key(await self._pool.fetchrow(_ACTIVE_KEY_SQL, user_id, org_slug))

    async def get_refresh(self, token_hash):
        row = await self._pool.fetchrow(_GET_REFRESH_SQL, token_hash)
        return RefreshRow(**dict(row)) if row else None

    async def consume_refresh(self, refresh_id, now):
        return await self._pool.fetchval(_CONSUME_SQL, refresh_id, now) is not None

    async def insert_refresh(self, key_id, token_hash, expires_at):
        return await self._pool.fetchval(_INSERT_REFRESH_SQL, key_id, token_hash, expires_at)

    async def mark_replaced(self, refresh_id, new_id):
        await self._pool.execute(_REPLACED_SQL, refresh_id, new_id)

    async def revoke_all(self, key_id, now):
        async with self._pool.acquire() as con, con.transaction():
            await con.execute(_REVOKE_REFRESH_SQL, key_id, now)
            await con.execute(_TOKENS_SINCE_SQL, key_id, now)

    async def touch_last_used(self, key_id, now):
        await self._pool.execute(_TOUCH_SQL, key_id, now)

    async def resolve(self, key_id, org_slug, unit_code, dashboard_key):
        row = await self._pool.fetchrow(_RESOLVE_SQL, key_id, org_slug, unit_code, dashboard_key)
        if row is None:
            return None
        return KeyAccess(
            org_id=row["org_id"],
            unit_id=row["unit_id"],
            scope=row["scope"],
            timezone=row["timezone"],
            can_see_commission=row["can_see_commission"],
            source_refs=json.loads(row["source_refs"]),
        )

    async def reachable(self, key_id):
        return [Reachable(**dict(r)) for r in await self._pool.fetch(_REACHABLE_SQL, key_id)]


def get_api_key_repo(pool: Annotated[asyncpg.Pool, Depends(get_db_pool)]) -> ApiKeyRepo:
    return PgApiKeyRepo(pool)
