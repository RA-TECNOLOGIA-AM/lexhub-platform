"""Bancos de origem (NG, LAADV, LEXFLOW, LEXPRE): conexões, estado e reconexão.

Regras:
  * A API não espera nenhum banco de origem para subir. `start()` abre cada banco numa tarefa de
    fundo; banco que não responde fica 'down' e é tentado de novo sozinho (1 s, 2 s, 4 s... até
    1 min entre as tentativas). Assim um banco fora do ar afeta só os dashboards dele.
  * Banco que cai depois de conectado: a consulta que não consegue conexão marca o banco como
    'down' (`report_failure`) e uma tarefa de fundo confere até ele voltar. Enquanto isso, as
    consultas desse banco falham na hora com SourceUnavailable (503, ou o último dado bom do
    cache), sem cada uma esperar o tempo limite de conexão.
  * Banco sem variáveis fica 'off' e nunca é tentado.
  * Sessões só leitura ('lexhub-v2-api') e limite de consultas simultâneas por banco.

Mesmos nomes de variáveis e padrões de pool da v1 (api_dashboards). Diferença: na v1, banco
obrigatório fora do ar impedia a subida; aqui nenhum banco de origem impede.
"""

import asyncio
import logging
import random
import socket
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any, Literal

import asyncpg
from fastapi import Request

from app.config import SOURCE_DATABASES, Settings
from app.logs import seconds

logger = logging.getLogger(__name__)

# connecting = primeira tentativa em andamento; down = sem conexão (tentando de novo); off = sem variáveis.
Status = Literal["connecting", "up", "down", "off"]

APPLICATION_NAME = "lexhub-v2-api"

# Tentativas de uma consulta em falha transitória (igual à v1).
MAX_DB_CONNECTION_RETRIES = 5
# Teto da espera entre tentativas de reconexão de um banco fora do ar.
RECONNECT_MAX_DELAY = 60.0
# Tempo para fechar um pool no desligamento antes de derrubar as conexões (o uvicorn espera 25 s).
CLOSE_TIMEOUT = 10.0

# Sem conexão com o banco: rede, servidor desligado ou conexão que caiu. TimeoutError é um OSError.
CONNECTION_ERRORS: tuple[type[Exception], ...] = (OSError, asyncpg.PostgresConnectionError)
# Vale tentar de novo na mesma consulta: conexão que caiu no meio ou cache de statements velho.
_RETRYABLE_DB_ERRORS: tuple[type[Exception], ...] = (
    OSError,
    asyncpg.PostgresConnectionError,
    asyncpg.InvalidCachedStatementError,
    asyncpg.OutdatedSchemaCacheError,
)


class SourceUnavailable(Exception):
    """Banco de origem (ou planilha) desligado, fora do ar ou sem resposta no momento."""


class ConnectionLost(Exception):
    """A conexão caiu no meio da consulta, e o asyncpg avisou com um InterfaceError
    ("the underlying connection is closed") no lugar do erro original."""


def connect_hint(exc: BaseException) -> str:
    """Tipo do erro + uma dica do que costuma ser (sem a mensagem, que pode trazer host/usuário)."""
    name = type(exc).__name__
    if isinstance(exc, asyncpg.InvalidPasswordError):
        return f"{name} (usuário ou senha errados)"
    if isinstance(exc, asyncpg.InvalidCatalogNameError):
        return f"{name} (banco não existe: confira DB_*_NAME)"
    if isinstance(exc, ConnectionRefusedError):
        return f"{name} (porta fechada ou servidor desligado)"
    if isinstance(exc, TimeoutError):
        return f"{name} (sem resposta: rede/VPN ou IP não liberado no banco)"
    if isinstance(exc, socket.gaierror):
        return f"{name} (host não encontrado: confira DB_*_HOST)"
    return name


def reconnect_delay(attempt: int) -> float:
    """Espera antes da próxima reconexão: 1 s, 2 s, 4 s... até 1 min, com variação de ±20%
    para réplicas diferentes não baterem no banco ao mesmo tempo."""
    return min(RECONNECT_MAX_DELAY, 2.0 ** (attempt - 1)) * random.uniform(0.8, 1.2)


def _backoff(attempt: int) -> float:
    """Espera entre tentativas de uma consulta: 0,4 s, 0,8 s, 1,6 s... com teto de 2 s (igual à v1)."""
    return min(2.0, 0.4 * (2 ** (attempt - 1)))


async def _read_only(conn: asyncpg.Connection) -> None:
    """Cada conexão nova fica só leitura. Vai num SET depois de conectar (e não na abertura)
    porque bancos com PgBouncer na frente, como o LAADV, recusam esse parâmetro na abertura.
    Camada extra: atrás de PgBouncer em modo transação esse SET pode se perder; quem garante
    é fetch_read_only."""
    await conn.execute("SET default_transaction_read_only = on")


async def fetch_read_only(conn: asyncpg.Connection, query: str) -> list[asyncpg.Record]:
    """Roda a consulta dentro de BEGIN READ ONLY ... COMMIT. Vale mesmo atrás de PgBouncer em
    modo transação, onde o SET de sessão de _read_only pode cair numa conexão diferente."""
    async with conn.transaction(readonly=True):
        return await conn.fetch(query)


PoolFactory = Callable[..., Awaitable[Any]]


class DatabaseManager:
    """Conexões com os bancos de origem: abre em segundo plano, acompanha o estado e reconecta."""

    def __init__(
        self,
        settings: Settings,
        *,
        create_pool: PoolFactory = asyncpg.create_pool,
        delay: Callable[[int], float] = reconnect_delay,
    ):
        self._settings = settings
        self._create_pool = create_pool
        self._delay = delay
        self._targets = {
            name: target
            for name in SOURCE_DATABASES
            if (target := settings.source_dsn(name)) is not None
        }
        self._status: dict[str, Status] = {
            name: "connecting" if name in self._targets else "off" for name in SOURCE_DATABASES
        }
        self._limits = {
            name: asyncio.Semaphore(settings.source_concurrency(name)) for name in self._targets
        }
        self._pools: dict[str, asyncpg.Pool] = {}
        self._tasks: dict[str, asyncio.Task] = {}

    def _pool_kwargs(self) -> dict:
        s = self._settings
        return {
            "min_size": s.DB_POOL_MIN_SIZE,
            "max_size": s.DB_POOL_MAX_SIZE,
            "max_inactive_connection_lifetime": s.DB_POOL_MAX_INACTIVE_CONNECTION_LIFETIME,
            "max_queries": s.DB_POOL_MAX_QUERIES,
            "command_timeout": s.DB_POOL_COMMAND_TIMEOUT,
            # Tempo limite de cada conexão nova (o asyncpg chama de `timeout`).
            "timeout": s.DB_CONNECT_TIMEOUT,
            "server_settings": {"application_name": APPLICATION_NAME},
            "init": _read_only,
        }

    def start(self) -> None:
        """Abre os bancos configurados em segundo plano e volta na hora."""
        for name in SOURCE_DATABASES:
            if name in self._targets:
                self._supervise(name)
            else:
                logger.info("%s desligado (sem DB_%s_*)", name, name.upper())

    def _supervise(self, name: str) -> None:
        """Garante uma (e só uma) tarefa conectando ou conferindo o banco."""
        task = self._tasks.get(name)
        if task is None or task.done():
            self._tasks[name] = asyncio.create_task(self._connect_loop(name), name=f"db-{name}")

    async def _connect_loop(self, name: str) -> None:
        returning = name in self._pools
        logger.info("%s: %s...", name, "conferindo se voltou" if returning else "conectando")
        started = time.perf_counter()
        attempt = 0
        while True:
            attempt += 1
            try:
                await self._connect_once(name)
            # Qualquer erro: a tarefa de reconexão nunca pode morrer, senão o banco fica 'down'
            # para sempre. O log mostra o tipo e a dica; a próxima tentativa vem depois.
            except Exception as exc:  # noqa: BLE001
                self._status[name] = "down"
                delay = self._delay(attempt)
                logger.warning(
                    "%s: sem conexão (tentativa %d): %s; nova tentativa em %s",
                    name,
                    attempt,
                    connect_hint(exc),
                    seconds(delay),
                )
                await asyncio.sleep(delay)
                continue
            self._status[name] = "up"
            s = self._settings
            logger.info(
                "%s %s em %s (pool %d-%d, até %d consultas simultâneas, só leitura)",
                name,
                "voltou" if returning else "conectado",
                seconds(time.perf_counter() - started),
                s.DB_POOL_MIN_SIZE,
                s.DB_POOL_MAX_SIZE,
                s.source_concurrency(name),
            )
            return

    async def _connect_once(self, name: str) -> None:
        pool = self._pools.get(name)
        if pool is None:
            self._pools[name] = await self._create_pool(
                **self._targets[name], **self._pool_kwargs()
            )
            return
        # Já havia pool (o banco caiu depois de conectado): troca as conexões antigas e confere
        # se uma nova responde.
        timeout = self._settings.DB_CONNECT_TIMEOUT
        await pool.expire_connections()
        async with pool.acquire(timeout=timeout) as conn:
            await conn.fetchval("select 1", timeout=timeout)

    def report_failure(self, name: str, exc: BaseException) -> None:
        """Uma consulta não conseguiu falar com o banco: marca 'down' e confere em segundo plano."""
        if self._status.get(name) != "up":
            return
        self._status[name] = "down"
        logger.warning(
            "%s: caiu (%s); as consultas dele ficam indisponíveis até voltar",
            name,
            connect_hint(exc),
        )
        self._supervise(name)

    async def expire_connections(self, name: str) -> None:
        """Descarta as conexões abertas do banco (as próximas consultas abrem conexões novas)."""
        pool = self._pools.get(name)
        if pool is not None:
            await pool.expire_connections()

    async def close(self) -> None:
        """Para as reconexões e fecha os pools (à força se passar de CLOSE_TIMEOUT)."""
        tasks = list(self._tasks.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        self._tasks.clear()
        names = list(self._pools)
        for pool in self._pools.values():
            try:
                await asyncio.wait_for(pool.close(), CLOSE_TIMEOUT)
            except TimeoutError:
                pool.terminate()
        self._pools.clear()
        if names:
            logger.info("Conexões fechadas: %s", ", ".join(names))

    def status(self) -> dict[str, Status]:
        """Estado de cada banco: connecting, up, down ou off (sem variáveis)."""
        return dict(self._status)

    def is_up(self, name: str) -> bool:
        return self._status.get(name) == "up"

    def get_pool(self, name: str) -> asyncpg.Pool:
        """Pool de um banco no ar. Desligado, conectando ou fora = SourceUnavailable (na hora)."""
        if not self.is_up(name):
            raise SourceUnavailable(name)
        return self._pools[name]

    @asynccontextmanager
    async def get_connection(self, name: str) -> AsyncIterator[asyncpg.Connection]:
        """`async with databases.get_connection('ng') as conn:` — respeita DB_QUERY_CONCURRENCY_*.

        Sem conseguir conexão, marca o banco como 'down' e levanta SourceUnavailable.
        """
        pool = self.get_pool(name)
        async with self._limits[name]:
            try:
                conn = await pool.acquire(timeout=self._settings.DB_POOL_ACQUIRE_TIMEOUT)
            except CONNECTION_ERRORS as exc:
                self.report_failure(name, exc)
                raise SourceUnavailable(name) from exc
            try:
                yield conn
            finally:
                await pool.release(conn)


async def run_with_connection_retry[T](
    manager: DatabaseManager,
    db_name: str,
    operation: Callable[[asyncpg.Connection], Awaitable[T]],
    *,
    operation_name: str = "query",
    max_retries: int = MAX_DB_CONNECTION_RETRIES,
) -> T:
    """Executa `operation(conn)`; em falha transitória, renova as conexões e tenta de novo (igual à v1).

    Vira SourceUnavailable (503, ou o último dado bom do cache):
      * banco desligado, fora do ar ou sem conexão: o banco fica 'down' até voltar;
      * consulta que passou do DB_POOL_COMMAND_TIMEOUT, ou que o próprio banco cancelou
        (statement_timeout do servidor): o banco segue 'up' (lentidão não é queda).
    """
    for attempt in range(1, max_retries + 1):
        try:
            async with manager.get_connection(db_name) as conn:
                try:
                    return await operation(conn)
                except asyncpg.InterfaceError as exc:
                    # Quando a conexão cai no meio de uma transação, o asyncpg esconde o erro
                    # original (ConnectionDoesNotExistError) atrás de "the underlying connection
                    # is closed", ao fechar a transação. A pergunta tem de ser feita aqui dentro:
                    # depois que a conexão volta ao pool, o proxy recusa qualquer chamada.
                    # Com a conexão aberta, InterfaceError é bug: sobe na hora, sem repetir.
                    if not conn.is_closed():
                        raise
                    raise ConnectionLost(db_name) from exc
        except SourceUnavailable:
            raise
        except TimeoutError as exc:  # antes dos transitórios: TimeoutError também é um OSError
            logger.warning(
                "'%s' em '%s' passou do tempo limite (DB_POOL_COMMAND_TIMEOUT)",
                operation_name,
                db_name,
            )
            raise SourceUnavailable(db_name) from exc
        except asyncpg.QueryCanceledError as exc:
            # O próprio banco cancelou a consulta (statement_timeout do servidor). Repetir só
            # esperaria o mesmo limite de novo.
            logger.warning(
                "'%s' em '%s' foi cancelada pelo próprio banco (statement_timeout do servidor)",
                operation_name,
                db_name,
            )
            raise SourceUnavailable(db_name) from exc
        except (*_RETRYABLE_DB_ERRORS, ConnectionLost) as exc:
            failure: Exception = exc
        logger.warning(
            "Falha transitória ao executar '%s' em '%s' (tentativa %d/%d): %s",
            operation_name,
            db_name,
            attempt,
            max_retries,
            type(failure).__name__,
        )
        if attempt >= max_retries:
            if isinstance(failure, (*CONNECTION_ERRORS, ConnectionLost)):
                manager.report_failure(db_name, failure)
                raise SourceUnavailable(db_name) from failure
            raise failure
        await manager.expire_connections(db_name)
        await asyncio.sleep(_backoff(attempt))
    raise AssertionError("inalcançável")  # o laço sempre retorna ou levanta


def get_databases(request: Request) -> DatabaseManager:
    """Dependency FastAPI: `databases: DatabaseManager = Depends(get_databases)`."""
    return request.app.state.databases
