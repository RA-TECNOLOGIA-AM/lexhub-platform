"""Fontes com o segredo cifrado no banco: banco próprio da operação e planilha publicada.

Os bancos do `.env` (LexPre, LexFlow, NG, LAADV) seguem no DatabaseManager. As fontes conectadas pela
tela e as planilhas antigas (sheets_financeiro_*, cujo link saiu do .env no PR 3) vivem em
app.data_sources (connector postgres/mysql/sheets, segredo cifrado) e chegam aqui pela key
(o "nome do banco" das queries, ex.: 'pg_mco_3fa9c1'):

  * RegisteredRepo        lê a linha da fonte no banco da plataforma;
  * RegisteredSources     decifra o segredo (app/secret_box.py) e guarda por `ttl` (5 min): trocar a senha
                          ou desconectar invalida na hora nesta réplica; nas outras, vale em até 5 min
                          (config_version muda e o pool é refeito). Abre pools pequenos (0 a 2 conexões)
                          só quando alguém usa, conferindo o endereço conectado (app/net_guard.py).
                          É também o ConnectionProvider (app/database.py) das fontes Postgres;
  * RegisteredSourceFetcher  o SourceFetcher de uma fonte conectada: banco (consulta registrada em
                          app/source_queries.py), planilha (a aba) ou conta de anúncios da Meta (a query
                          `facebook_ads`, com o que a coleta guardou no próprio LexHub: app/facebook_ads_sync.py).
O roteamento (banco do .env x fonte da tela) fica em app/sources.py (source_fetcher).
"""

import asyncio
import json
import logging
import time
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Protocol

import aiomysql
import asyncpg

from app.config import Settings
from app.connection_check import ssl_context
from app.database import (
    APPLICATION_NAME,
    CONNECTION_ERRORS,
    SourceDisabled,
    SourceUnavailable,
    fetch_read_only,
    run_with_connection_retry,
)
from app.net_guard import BlockedHost, HostNotFound, check_peer, resolve_public
from app.secret_box import SecretBox, SecretKeyMissing, SecretUnreadable
from app.source_queries import QUERIES

logger = logging.getLogger(__name__)

CONNECTED = ("postgres", "mysql", "sheets", "facebook_ads")

# A única query de uma conta de anúncios da Meta: as linhas da coleta nas colunas de metrics_ads.facebook_ads
# (banco ng), as que o Marketing lê.
ADS_QUERY = "facebook_ads"


@dataclass(frozen=True)
class RegisteredRow:
    id: str
    key: str
    connector: str
    config: dict[str, Any]
    secret_ciphertext: str
    config_version: int
    enabled: bool = True


@dataclass(frozen=True)
class RegisteredSource:
    row: RegisteredRow
    secret: str  # senha do banco ou link da planilha (decifrado; nunca sai da API)
    loaded_at: float


class RegisteredRepo(Protocol):
    async def load(self, key: str) -> RegisteredRow | None: ...

    async def ads_rows(self, source_id: str) -> list[dict[str, Any]]: ...


_LOAD_SQL = """
select id::text, key, connector, config::text, secret_ciphertext, config_version, enabled
  from app.data_sources
 where key = $1 and active and connector = any($2::text[]) and secret_ciphertext is not null
"""


# O que a coleta guardou (app.facebook_ads_daily), nas colunas de metrics_ads.facebook_ads (banco ng), para o
# cálculo da v1 ler igual: id_conta sem o "act_", nome_conta = o nome da conta na Meta. `cadastros` sai das
# ações (cadastro concluído), já que a coleta não tem coluna para ele; sem a ação no dia, null, como no ng.
_ADS_ROWS_SQL = """
select f.day as "date",
       f.campaign_id, f.campaign_name as campaign,
       f.adset_id, f.adset_name as adset,
       f.ad_id, f.ad_name as ad,
       f.reach as alcance, f.impressions as impressoes, f.spend as valor_gasto,
       f.link_clicks as cliques_no_link, f.landing_page_views as landing_page_view, f.leads,
       (select sum((a ->> 'value')::numeric)::bigint
          from jsonb_array_elements(f.actions) a
         where a ->> 'action_type' = 'complete_registration') as cadastros,
       regexp_replace(f.account_id, '^act_', '') as id_conta,
       coalesce(ds.config ->> 'account_name', ds.name) as nome_conta
  from app.facebook_ads_daily f
  join app.data_sources ds on ds.id = f.source_id
 where f.source_id = $1::uuid
 order by f.day, f.ad_id
"""


class PgRegisteredRepo:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def load(self, key: str) -> RegisteredRow | None:
        r = await self._pool.fetchrow(_LOAD_SQL, key, list(CONNECTED))
        if r is None:
            return None
        return RegisteredRow(
            id=r["id"],
            key=r["key"],
            connector=r["connector"],
            config=json.loads(r["config"]),
            secret_ciphertext=r["secret_ciphertext"],
            config_version=r["config_version"],
            enabled=r["enabled"],
        )

    async def ads_rows(self, source_id: str) -> list[dict[str, Any]]:
        return [dict(r) for r in await self._pool.fetch(_ADS_ROWS_SQL, source_id)]


async def _guarded(conn: asyncpg.Connection, allow_private: bool) -> None:
    """`init` de cada conexão nova de uma fonte da tela: endereço conectado público + sessão só leitura."""
    check_peer(conn._transport.get_extra_info("peername"), allow_private=allow_private)
    await conn.execute("SET default_transaction_read_only = on")


class RegisteredSources:
    def __init__(
        self,
        repo: RegisteredRepo,
        settings: Settings,
        *,
        ttl: float = 300,
        clock: Callable[[], float] = time.monotonic,
    ):
        self._repo = repo
        self._settings = settings
        self._ttl = ttl
        self._clock = clock
        self._cache: dict[str, RegisteredSource] = {}
        self._pg: dict[str, tuple[int, asyncpg.Pool]] = {}
        self._my: dict[str, tuple[int, aiomysql.Pool]] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    def _box(self) -> SecretBox:
        return SecretBox.from_setting(self._settings.SOURCE_SECRET_KEY)

    async def get(self, key: str) -> RegisteredSource:
        """A fonte com o segredo decifrado. Não existe, chave faltando ou segredo ilegível = SourceUnavailable;
        desligada na tela = SourceDisabled."""
        hit = self._cache.get(key)
        if hit is not None and self._clock() - hit.loaded_at < self._ttl:
            return hit
        row = await self._repo.load(key)
        if row is None:
            self._cache.pop(key, None)
            raise SourceUnavailable(key)
        if not row.enabled:
            await self.invalidate(key)
            raise SourceDisabled(key)
        try:
            secret = self._box().decrypt(row.secret_ciphertext)
        except (SecretKeyMissing, SecretUnreadable, ValueError) as exc:
            logger.error(
                "%s: segredo não abre (%s); confira SOURCE_SECRET_KEY", key, type(exc).__name__
            )
            raise SourceUnavailable(key) from exc
        source = RegisteredSource(row=row, secret=secret, loaded_at=self._clock())
        self._cache[key] = source
        return source

    async def ads_rows(self, key: str) -> list[dict[str, Any]]:
        """As linhas guardadas de uma conta de anúncios da Meta (desligada = SourceDisabled, como as outras)."""
        source = await self.get(key)
        if source.row.connector != "facebook_ads":
            raise SourceUnavailable(key)
        try:
            return await self._repo.ads_rows(source.row.id)
        except (*CONNECTION_ERRORS, asyncpg.PostgresError) as exc:
            raise SourceUnavailable(key) from exc

    async def invalidate(self, key: str) -> None:
        """Senha trocada, fonte desligada ou desconectada: esquece a fonte e fecha os pools dela nesta réplica."""
        self._cache.pop(key, None)
        for pools in (self._pg, self._my):
            entry = pools.pop(key, None)
            if entry is not None:
                await _close(entry[1])

    async def _target(self, key: str, connector: str) -> RegisteredSource:
        source = await self.get(key)
        if source.row.connector != connector:
            raise SourceUnavailable(key)
        cfg = source.row.config
        try:
            await resolve_public(
                cfg["host"],
                int(cfg["port"]),
                allow_private=self._settings.SOURCE_ALLOW_PRIVATE_HOSTS,
            )
        except (BlockedHost, HostNotFound, OSError) as exc:
            raise SourceUnavailable(key) from exc
        return source

    async def pg_pool(self, key: str) -> asyncpg.Pool:
        async with self._locks.setdefault(key, asyncio.Lock()):
            source = await self._target(key, "postgres")
            entry = self._pg.get(key)
            if entry is not None and entry[0] == source.row.config_version:
                return entry[1]
            if entry is not None:
                await _close(entry[1])
            cfg = source.row.config
            allow = self._settings.SOURCE_ALLOW_PRIVATE_HOSTS
            try:
                pool = await asyncpg.create_pool(
                    host=cfg["host"],
                    port=int(cfg["port"]),
                    user=cfg["user"],
                    password=source.secret,
                    database=cfg["database"],
                    ssl=ssl_context(bool(cfg.get("ssl"))) or False,
                    min_size=0,
                    max_size=2,
                    max_inactive_connection_lifetime=60,
                    statement_cache_size=0,
                    timeout=self._settings.DB_CONNECT_TIMEOUT,
                    command_timeout=self._settings.DB_POOL_COMMAND_TIMEOUT,
                    server_settings={"application_name": APPLICATION_NAME},
                    init=lambda conn: _guarded(conn, allow),
                )
            except (*CONNECTION_ERRORS, asyncpg.PostgresError) as exc:
                raise SourceUnavailable(key) from exc
            self._pg[key] = (source.row.config_version, pool)
            return pool

    async def my_pool(self, key: str) -> aiomysql.Pool:
        async with self._locks.setdefault(key, asyncio.Lock()):
            source = await self._target(key, "mysql")
            entry = self._my.get(key)
            if entry is not None and entry[0] == source.row.config_version:
                return entry[1]
            if entry is not None:
                await _close(entry[1])
            cfg = source.row.config
            try:
                pool = await aiomysql.create_pool(
                    minsize=0,
                    maxsize=2,
                    pool_recycle=60,
                    host=cfg["host"],
                    port=int(cfg["port"]),
                    user=cfg["user"],
                    password=source.secret,
                    db=cfg["database"],
                    ssl=ssl_context(bool(cfg.get("ssl"))),
                    connect_timeout=self._settings.DB_CONNECT_TIMEOUT,
                    autocommit=True,
                    init_command="SET SESSION TRANSACTION READ ONLY",
                )
            except Exception as exc:
                raise SourceUnavailable(key) from exc
            self._my[key] = (source.row.config_version, pool)
            return pool

    # --- ConnectionProvider (Postgres) ---

    @asynccontextmanager
    async def get_connection(self, key: str) -> AsyncIterator[asyncpg.Connection]:
        pool = await self.pg_pool(key)
        try:
            conn = await pool.acquire(timeout=self._settings.DB_POOL_ACQUIRE_TIMEOUT)
        except (*CONNECTION_ERRORS, BlockedHost) as exc:
            raise SourceUnavailable(key) from exc
        try:
            yield conn
        finally:
            await pool.release(conn)

    async def expire_connections(self, key: str) -> None:
        entry = self._pg.get(key)
        if entry is not None:
            await entry[1].expire_connections()

    def report_failure(self, key: str, exc: BaseException) -> None:
        logger.warning("%s: sem conexão com a fonte conectada (%s)", key, type(exc).__name__)

    async def close(self) -> None:
        for key in list(self._pg) + list(self._my):
            await self.invalidate(key)


async def _close(pool: Any) -> None:
    try:
        if isinstance(pool, asyncpg.Pool):
            await asyncio.wait_for(pool.close(), 5)
        else:
            pool.close()
            await asyncio.wait_for(pool.wait_closed(), 5)
    except Exception:  # noqa: BLE001
        if isinstance(pool, asyncpg.Pool):
            pool.terminate()


class RegisteredSourceFetcher:
    """SourceFetcher de uma fonte conectada pela tela. Banco: `fetch(nome da query)` com a query de
    app/source_queries.py cujo "database" é a key da fonte. Planilha: `fetch(aba)`. Conta de anúncios da
    Meta: `fetch("facebook_ads")`."""

    def __init__(
        self,
        registered: RegisteredSources,
        key: str,
        queries: dict[str, dict] = QUERIES,
    ):
        self._registered = registered
        self._key = key
        self._queries = queries
        self._fetched: list[float] = []

    async def fetch(self, query_name: str) -> list[dict[str, Any]]:
        source = await self._registered.get(self._key)
        connector = source.row.connector
        if connector == "sheets":
            from app.sheets import SheetSourceFetcher  # aqui: evita import circular

            async def link() -> str:
                return (await self._registered.get(self._key)).secret

            rows = await SheetSourceFetcher(self._key, link).fetch(query_name)
        elif connector == "facebook_ads":
            if query_name != ADS_QUERY:
                raise ValueError(f"Conta de anúncios {self._key} só responde {ADS_QUERY}")
            rows = await self._registered.ads_rows(self._key)
        else:
            spec = self._queries[query_name]
            if spec["database"] != self._key:
                raise ValueError(
                    f"Query {query_name} é do banco {spec['database']}, não de {self._key}"
                )
            if connector == "postgres":
                rows = [
                    dict(r)
                    for r in await run_with_connection_retry(
                        self._registered,
                        self._key,
                        lambda conn: fetch_read_only(conn, spec["query"]),
                        operation_name=query_name,
                    )
                ]
            else:
                rows = await self._mysql(spec["query"])
        self._fetched.append(time.time())
        return rows

    async def _mysql(self, query: str) -> list[dict[str, Any]]:
        pool = await self._registered.my_pool(self._key)
        try:
            async with pool.acquire() as conn, conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("START TRANSACTION READ ONLY")
                try:
                    await cur.execute(query)
                    return list(await cur.fetchall())
                finally:
                    await cur.execute("ROLLBACK")
        except (OSError, TimeoutError, aiomysql.OperationalError) as exc:
            raise SourceUnavailable(self._key) from exc

    def synced_at(self) -> float | None:
        return min(self._fetched) if self._fetched else None
