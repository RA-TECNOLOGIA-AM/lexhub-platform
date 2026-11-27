"""Conectar fonte (banco próprio e planilha) e gerenciar a fonte: o banco da plataforma.

As regras ficam nas funções do banco (migrations 20261117180000_conectar_banco_planilha.sql,
20261118100000_fontes_liga_desliga.sql e 20261127110000_fonte_facebook_ads.sql): só a TI da
LexGroup (app_private.is_source_admin), auditoria, key gerada. Aqui só chamamos e traduzimos o erro:
  42501 -> NotAllowed (403); P0001 -> RuleBroken (409, a mensagem vai para a tela).
"""

import json
from dataclasses import dataclass
from typing import Annotated, Any, Protocol

import asyncpg
from fastapi import Depends

from app.access import get_db_pool


class NotAllowed(Exception):
    """Quem chamou não é TI da LexGroup."""


class RuleBroken(Exception):
    """Regra do banco quebrada (fonte não encontrada, não gerenciada pela tela...). A mensagem é da tela."""


@dataclass(frozen=True)
class ManagedSource:
    id: str
    key: str
    org_id: str
    unit_id: str | None
    connector: str
    name: str
    config: dict[str, Any]
    secret_ciphertext: str | None


class SourceAdminRepo(Protocol):
    async def is_source_admin(self, user_id: str) -> bool: ...

    async def unit_id(self, org_slug: str, unit_code: str) -> str | None: ...

    async def source(self, org_slug: str, key: str) -> ManagedSource | None: ...

    async def connect(
        self,
        user_id: str,
        unit_id: str,
        connector: str,
        name: str,
        detail: str,
        config: dict[str, Any],
        ciphertext: str,
        writer_ack: bool,
        schema_cache: dict | None,
    ) -> dict[str, Any]: ...

    async def set_secret(
        self,
        user_id: str,
        source_id: str,
        ciphertext: str,
        writer_ack: bool,
        schema_cache: dict | None,
    ) -> dict[str, Any]: ...

    async def disconnect(self, user_id: str, source_id: str) -> None: ...

    async def set_enabled(self, user_id: str, source_id: str, enabled: bool) -> dict[str, Any]: ...

    async def record_run(
        self, source_id: str, kind: str, ok: bool, checks: list[dict], ms: int, error: str | None
    ) -> None: ...

    async def set_config(
        self, user_id: str, source_id: str, config: dict[str, Any], detail: str
    ) -> dict[str, Any]: ...

    async def recompute_results(self, source_id: str, conversions: list[str]) -> None: ...

    async def ad_accounts_in_use(self) -> dict[str, str]: ...


_UNIT_SQL = """
select u.id::text from app.units u
  join app.organizations o on o.id = u.org_id and o.active
 where o.slug = $1 and u.code = $2 and u.active
"""

# Contas de anúncios já ligadas a uma fonte (em qualquer organização): conta -> 'Organização · UNIDADE'.
_AD_ACCOUNTS_SQL = """
select ds.config ->> 'ad_account_id' as account, o.name || ' · ' || coalesce(u.code, '?') as place
  from app.data_sources ds
  join app.organizations o on o.id = ds.org_id
  left join app.units u on u.id = ds.owner_unit_id
 where ds.connector = 'facebook_ads' and ds.active
"""

_SOURCE_SQL = """
select ds.id::text, ds.key, ds.org_id::text, ds.owner_unit_id::text as unit_id, ds.connector, ds.name,
       ds.config::text, ds.secret_ciphertext
  from app.data_sources ds
  join app.organizations o on o.id = ds.org_id and o.active
 where o.slug = $1 and ds.key = $2 and ds.active
"""


async def _call(pool: asyncpg.Pool, sql: str, *args: Any) -> Any:
    try:
        return await pool.fetchval(sql, *args)
    except asyncpg.InsufficientPrivilegeError as exc:
        raise NotAllowed(str(exc)) from exc
    except (asyncpg.RaiseError, asyncpg.CheckViolationError) as exc:
        raise RuleBroken(str(exc)) from exc


class PgSourceAdminRepo:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def is_source_admin(self, user_id: str) -> bool:
        return bool(
            await self._pool.fetchval("select app_private.is_source_admin($1::uuid)", user_id)
        )

    async def unit_id(self, org_slug: str, unit_code: str) -> str | None:
        return await self._pool.fetchval(_UNIT_SQL, org_slug, unit_code)

    async def source(self, org_slug: str, key: str) -> ManagedSource | None:
        r = await self._pool.fetchrow(_SOURCE_SQL, org_slug, key)
        if r is None:
            return None
        return ManagedSource(
            id=r["id"],
            key=r["key"],
            org_id=r["org_id"],
            unit_id=r["unit_id"],
            connector=r["connector"],
            name=r["name"],
            config=json.loads(r["config"]),
            secret_ciphertext=r["secret_ciphertext"],
        )

    async def connect(
        self,
        user_id,
        unit_id,
        connector,
        name,
        detail,
        config,
        ciphertext,
        writer_ack,
        schema_cache,
    ):
        out = await _call(
            self._pool,
            "select app_private.connect_source($1::uuid, $2::uuid, $3, $4, $5, $6::jsonb, $7, $8,"
            " $9::jsonb)::text",
            user_id,
            unit_id,
            connector,
            name,
            detail,
            json.dumps(config),
            ciphertext,
            writer_ack,
            json.dumps(schema_cache) if schema_cache is not None else None,
        )
        return json.loads(out)

    async def set_secret(self, user_id, source_id, ciphertext, writer_ack, schema_cache):
        out = await _call(
            self._pool,
            "select app_private.set_source_secret($1::uuid, $2::uuid, $3, $4, $5::jsonb)::text",
            user_id,
            source_id,
            ciphertext,
            writer_ack,
            json.dumps(schema_cache) if schema_cache is not None else None,
        )
        return json.loads(out)

    async def disconnect(self, user_id: str, source_id: str) -> None:
        await _call(
            self._pool,
            "select app_private.disconnect_source($1::uuid, $2::uuid)",
            user_id,
            source_id,
        )

    async def set_enabled(self, user_id: str, source_id: str, enabled: bool) -> dict[str, Any]:
        out = await _call(
            self._pool,
            "select app_private.set_source_enabled($1::uuid, $2::uuid, $3)::text",
            user_id,
            source_id,
            enabled,
        )
        return json.loads(out)

    async def set_config(self, user_id, source_id, config, detail):
        """Personalização do Facebook Ads (20261127110000_fonte_facebook_ads.sql)."""
        out = await _call(
            self._pool,
            "select app_private.set_source_config($1::uuid, $2::uuid, $3::jsonb, $4)::text",
            user_id,
            source_id,
            json.dumps(config),
            detail,
        )
        return json.loads(out)

    async def recompute_results(self, source_id, conversions):
        """Conversões trocadas: "resultados" de novo, a partir das ações já guardadas."""
        await self._pool.execute(
            "select app_private.facebook_ads_recompute_results($1::uuid, $2::text[])",
            source_id,
            conversions,
        )

    async def ad_accounts_in_use(self) -> dict[str, str]:
        return {r["account"]: r["place"] for r in await self._pool.fetch(_AD_ACCOUNTS_SQL)}

    async def record_run(self, source_id, kind, ok, checks, ms, error):
        await self._pool.execute(
            "select app_private.record_source_run($1::uuid, $2, $3, $4::jsonb, $5, $6)",
            source_id,
            kind,
            ok,
            json.dumps(checks),
            ms,
            error,
        )


def get_source_admin_repo(pool: Annotated[asyncpg.Pool, Depends(get_db_pool)]) -> SourceAdminRepo:
    return PgSourceAdminRepo(pool)
