"""Teste de conexão de um banco próprio da operação (Postgres ou MySQL): o "Testar e salvar" da tela.

Quatro checagens, nesta ordem; a primeira que falha para o resto (as seguintes voltam `skipped`):
  network   o host resolve para endereço público e a porta abre (app/net_guard.py);
  login     usuário e senha entram no banco, com ou sem SSL; o endereço conectado é conferido de novo;
  read      lista as tabelas e lê uma linha (vira o `schema_cache` da fonte, para o analista);
  readOnly  o usuário NÃO pode escrever. Se puder, é aviso (warn): a tela pede "Salvar mesmo assim".
As mensagens vão para a tela: genéricas, sem repassar o erro do driver (não ajudam quem tenta mapear portas).
Os conectores (como abrir, consultar e fechar em cada banco) ficam atrás de `DbDriver`: banco novo = um driver.
"""

import asyncio
import contextlib
import re
import ssl
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

import aiomysql
import asyncpg
import pymysql

from app.net_guard import BlockedHost, HostNotFound, check_peer, resolve_public

Connector = Literal["postgres", "mysql"]

# Até quantas tabelas e colunas o schema_cache guarda (um banco grande não estoura a linha da fonte).
MAX_TABLES = 300
MAX_COLUMNS = 6000


@dataclass(frozen=True)
class DbTarget:
    connector: Connector
    host: str
    port: int
    database: str
    user: str
    password: str
    ssl: bool

    def config(self) -> dict[str, Any]:
        """O que vai para app.data_sources.config (sem a senha)."""
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "user": self.user,
            "ssl": self.ssl,
        }


@dataclass
class Check:
    # account: só o Facebook Ads (a conta de anúncios está ativa? app/facebook_ads.py)
    key: Literal["network", "login", "read", "readOnly", "account"]
    ok: bool
    message: str
    ms: int = 0
    severity: Literal["error", "warn"] = "error"
    skipped: bool = False


@dataclass
class CheckResult:
    checks: list[Check]
    can_write: bool = False
    schema_cache: dict[str, list[list[str]]] | None = None
    ms: int = 0

    @property
    def ok(self) -> bool:
        """Passou rede, login e leitura (escrita liberada é só aviso)."""
        return all(c.ok or c.severity == "warn" for c in self.checks if not c.skipped)

    @property
    def error(self) -> str | None:
        failed = next((c for c in self.checks if not c.ok and c.severity == "error"), None)
        return failed.message if failed else None


# --- Drivers ----------------------------------------------------------------------------------------


class DbDriver(Protocol):
    async def connect(self, target: DbTarget, timeout: float) -> Any: ...

    def peername(self, conn: Any) -> object: ...

    async def tables(self, conn: Any) -> list[tuple[str, str, str]]: ...  # (tabela, coluna, tipo)

    async def sample(self, conn: Any, table: str) -> None: ...

    async def can_write(self, conn: Any) -> bool: ...

    async def close(self, conn: Any) -> None: ...


def ssl_context(enabled: bool) -> ssl.SSLContext | None:
    """SSL ligado = criptografa sem validar o certificado (banco pequeno costuma ter autoassinado)."""
    if not enabled:
        return None
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _quote_pg(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


_PG_TABLES = f"""
select c.table_schema || '.' || c.table_name, c.column_name, c.data_type
  from information_schema.columns c
  join information_schema.tables t
    on t.table_schema = c.table_schema and t.table_name = c.table_name
 where c.table_schema not in ('pg_catalog', 'information_schema')
   and c.table_schema not like 'pg_toast%'
 order by c.table_schema, c.table_name, c.ordinal_position
 limit {MAX_COLUMNS}
"""

# Superusuário/cria papel ou banco, ou INSERT/UPDATE/DELETE/TRUNCATE em alguma tabela visível.
_PG_CAN_WRITE = """
select r.rolsuper or r.rolcreaterole or r.rolcreatedb
       or exists (select 1 from information_schema.table_privileges p
                   where p.privilege_type in ('INSERT', 'UPDATE', 'DELETE', 'TRUNCATE'))
  from pg_roles r
 where r.rolname = current_user
"""


class PostgresDriver:
    async def connect(self, target: DbTarget, timeout: float) -> asyncpg.Connection:
        return await asyncpg.connect(
            host=target.host,
            port=target.port,
            user=target.user,
            password=target.password,
            database=target.database,
            ssl=ssl_context(target.ssl) or False,
            timeout=timeout,
            statement_cache_size=0,  # pode haver PgBouncer na frente
            server_settings={"application_name": "lexhub-v2-api"},
        )

    def peername(self, conn: asyncpg.Connection) -> object:
        return conn._transport.get_extra_info("peername")

    async def tables(self, conn: asyncpg.Connection) -> list[tuple[str, str, str]]:
        async with conn.transaction(readonly=True):
            return [tuple(r) for r in await conn.fetch(_PG_TABLES)]

    async def sample(self, conn: asyncpg.Connection, table: str) -> None:
        schema, name = table.split(".", 1)
        async with conn.transaction(readonly=True):
            await conn.fetch(f"select * from {_quote_pg(schema)}.{_quote_pg(name)} limit 1")

    async def can_write(self, conn: asyncpg.Connection) -> bool:
        async with conn.transaction(readonly=True):
            return bool(await conn.fetchval(_PG_CAN_WRITE))

    async def close(self, conn: asyncpg.Connection) -> None:
        await conn.close(timeout=2)


_MY_TABLES = f"""
select concat(table_schema, '.', table_name), column_name, data_type
  from information_schema.columns
 where table_schema = database()
 order by table_name, ordinal_position
 limit {MAX_COLUMNS}
"""

# GRANT com qualquer privilégio que escreve ou muda o banco.
_MY_WRITE_GRANT = re.compile(
    r"\b(ALL PRIVILEGES|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|INDEX|EXECUTE|SUPER)\b",
    re.IGNORECASE,
)


class MySqlDriver:
    async def connect(self, target: DbTarget, timeout: float) -> aiomysql.Connection:
        return await aiomysql.connect(
            host=target.host,
            port=target.port,
            user=target.user,
            password=target.password,
            db=target.database,
            ssl=ssl_context(target.ssl),
            connect_timeout=timeout,
            autocommit=True,
            init_command="SET SESSION TRANSACTION READ ONLY",
        )

    def peername(self, conn: aiomysql.Connection) -> object:
        return conn._writer.get_extra_info("peername")

    async def _query(self, conn: aiomysql.Connection, sql: str) -> list[tuple]:
        async with conn.cursor() as cur:
            await cur.execute(sql)
            return list(await cur.fetchall())

    async def tables(self, conn: aiomysql.Connection) -> list[tuple[str, str, str]]:
        return [tuple(r) for r in await self._query(conn, _MY_TABLES)]

    async def sample(self, conn: aiomysql.Connection, table: str) -> None:
        name = table.split(".", 1)[1].replace("`", "``")
        await self._query(conn, f"select * from `{name}` limit 1")

    async def can_write(self, conn: aiomysql.Connection) -> bool:
        grants = await self._query(conn, "SHOW GRANTS FOR CURRENT_USER()")
        return any(_MY_WRITE_GRANT.search(str(row[0]).split(" ON ", 1)[0]) for row in grants)

    async def close(self, conn: aiomysql.Connection) -> None:
        conn.close()


DRIVERS: dict[str, DbDriver] = {"postgres": PostgresDriver(), "mysql": MySqlDriver()}


# --- Mensagens ----------------------------------------------------------------------------------


def _login_message(exc: BaseException, target: DbTarget) -> str:
    if isinstance(
        exc, asyncpg.InvalidPasswordError | asyncpg.InvalidAuthorizationSpecificationError
    ):
        return "Usuário ou senha recusados pelo banco. Confira e teste de novo."
    if isinstance(exc, asyncpg.InvalidCatalogNameError):
        return f"O banco {target.database} não existe nesse servidor."
    if isinstance(exc, pymysql.err.OperationalError) and exc.args:
        code = exc.args[0]
        if code == 1045:
            return "Usuário ou senha recusados pelo banco. Confira e teste de novo."
        if code in (1044, 1049):
            return f"O banco {target.database} não existe ou o usuário não tem acesso a ele."
    if isinstance(exc, ssl.SSLError) or "SSL" in str(exc):
        return "O servidor recusou a conexão com SSL. Teste com o SSL desligado ou ligue o SSL no banco."
    if isinstance(exc, TimeoutError):
        return "O banco não respondeu ao login a tempo."
    return "Não foi possível entrar no banco com esses dados."


# --- O teste ------------------------------------------------------------------------------------


@dataclass
class _Clock:
    started: float = field(default_factory=time.perf_counter)

    def ms(self) -> int:
        return int((time.perf_counter() - self.started) * 1000)


async def _open_port(host: str, port: int, timeout: float) -> None:
    _, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout)
    writer.close()
    try:
        await writer.wait_closed()
    except OSError:
        pass


Checker = Callable[[DbTarget], Awaitable[CheckResult]]


async def check_database(
    target: DbTarget,
    *,
    timeout: float = 8.0,
    allow_private: bool = False,
    driver: DbDriver | None = None,
    open_port: Callable[[str, int, float], Awaitable[None]] = _open_port,
) -> CheckResult:
    """Roda as 4 checagens. Nunca levanta: o resultado diz o que passou e o que falhou."""
    drv = driver or DRIVERS[target.connector]
    total = _Clock()
    checks: list[Check] = []
    where = f"{target.host}:{target.port}"

    def stop(failed: Check) -> CheckResult:
        checks.append(failed)
        for key, msg in (
            ("network", "Rede"),
            ("login", "Login"),
            ("read", "Leitura"),
            ("readOnly", "Só leitura"),
        ):
            if not any(c.key == key for c in checks):
                checks.append(Check(key, False, f"{msg}: não testado", skipped=True))
        return CheckResult(checks, ms=total.ms())

    # 1. Rede
    step = _Clock()
    try:
        await resolve_public(target.host, target.port, allow_private=allow_private)
        await open_port(target.host, target.port, timeout)
    except BlockedHost:
        return stop(
            Check(
                "network",
                False,
                "Este endereço é de rede interna ou usa porta de sistema. "
                "Use o endereço público do banco (porta 1024 ou maior).",
                step.ms(),
            )
        )
    except HostNotFound:
        return stop(Check("network", False, f"O host {target.host} não foi encontrado.", step.ms()))
    except (OSError, TimeoutError):
        return stop(
            Check(
                "network",
                False,
                f"A API não alcançou {where}. Confira o endereço e se o IP do LexHub está "
                "liberado no firewall do banco.",
                step.ms(),
            )
        )
    checks.append(Check("network", True, f"A API alcançou {where}", step.ms()))

    # 2. Login (+ o endereço de fato conectado)
    step = _Clock()
    try:
        conn = await asyncio.wait_for(drv.connect(target, timeout), timeout + 1)
    except Exception as exc:  # noqa: BLE001 (cada driver tem os seus erros; a mensagem é genérica)
        return stop(Check("login", False, _login_message(exc, target), step.ms()))
    try:
        try:
            check_peer(drv.peername(conn), allow_private=allow_private)
        except BlockedHost:
            return stop(
                Check("login", False, "O endereço conectado é de rede interna. Conexão recusada.")
            )
        ssl_text = "com SSL" if target.ssl else "sem SSL"
        checks.append(
            Check("login", True, f"Entrou no banco {target.database} {ssl_text}", step.ms())
        )

        # 3. Leitura
        step = _Clock()
        try:
            rows = await asyncio.wait_for(drv.tables(conn), timeout)
            schema = _schema_cache(rows)
            if not schema:
                return stop(
                    Check(
                        "read",
                        False,
                        "O usuário não enxerga nenhuma tabela. Confira o GRANT SELECT do passo 1.",
                        step.ms(),
                    )
                )
            await asyncio.wait_for(drv.sample(conn, next(iter(schema))), timeout)
        except Exception:  # noqa: BLE001
            return stop(
                Check("read", False, "Entrou, mas não conseguiu ler as tabelas.", step.ms())
            )
        checks.append(Check("read", True, f"{len(schema)} tabelas encontradas", step.ms()))

        # 4. Só leitura
        step = _Clock()
        try:
            can_write = await asyncio.wait_for(drv.can_write(conn), timeout)
        except Exception:  # noqa: BLE001
            can_write = True  # sem saber, trata como pode escrever (pede confirmação)
        if can_write:
            checks.append(
                Check(
                    "readOnly",
                    False,
                    f"O usuário {target.user} pode alterar dados. Recomendamos um usuário só de "
                    "leitura (passo 1).",
                    step.ms(),
                    severity="warn",
                )
            )
        else:
            checks.append(
                Check("readOnly", True, "O usuário não tem permissão de escrita", step.ms())
            )
        return CheckResult(checks, can_write=can_write, schema_cache=schema, ms=total.ms())
    finally:
        with contextlib.suppress(Exception):  # fechar não muda o resultado do teste
            await drv.close(conn)


def _schema_cache(rows: list[tuple[str, str, str]]) -> dict[str, list[list[str]]]:
    """[(tabela, coluna, tipo)] -> {tabela: [[coluna, tipo], ...]}, até MAX_TABLES tabelas."""
    out: dict[str, list[list[str]]] = {}
    for table, column, dtype in rows:
        if table not in out and len(out) >= MAX_TABLES:
            break
        out.setdefault(str(table), []).append([str(column), str(dtype)])
    return out
