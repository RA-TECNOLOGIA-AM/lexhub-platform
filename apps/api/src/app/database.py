"""Bancos de origem (NG, LAADV, LEXFLOW, LEXPRE), no padrão do database.py da v1.

Igual à v1: mesmos nomes, padrões de pool e tentativas; banco obrigatório que falha
derruba a subida (só o LEXPRE é opcional).
Diferente: banco sem variáveis fica 'off'; sessões só leitura ('lexhub-v2-api');
limite de consultas por banco aqui dentro; gerenciador entregue por get_databases.
"""

import asyncio
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Literal

import asyncpg
from fastapi import Request

from app.config import SOURCE_DATABASES, Settings

logger = logging.getLogger(__name__)

Status = Literal["up", "down", "off"]

APPLICATION_NAME = "lexhub-v2-api"

# Igual à v1: tentativas em falhas transitórias e bancos que podem faltar na subida.
MAX_DB_CONNECTION_RETRIES = 5
OPTIONAL_DATABASES = frozenset({"lexpre"})

# Erros transitórios: reconectar / expirar o pool e tentar de novo (igual à v1).
_RETRYABLE_DB_ERRORS: tuple[type[Exception], ...] = (
    asyncpg.PostgresConnectionError,
    asyncpg.InvalidCachedStatementError,
    asyncpg.OutdatedSchemaCacheError,
)
# Falhas de conexão na subida (igual à v1).
_CONNECT_ERRORS: tuple[type[Exception], ...] = (
    asyncpg.PostgresConnectionError,
    ConnectionResetError,
    OSError,
)


def _backoff(attempt: int) -> float:
    """Espera entre tentativas: 0,4 s, 0,8 s, 1,6 s... com teto de 2 s (igual à v1)."""
    return min(2.0, 0.4 * (2 ** (attempt - 1)))


async def _read_only(conn: asyncpg.Connection) -> None:
    """Cada conexão nova fica só leitura. Vai num SET depois de conectar (e não na abertura)
    porque bancos com PgBouncer na frente, como o LAADV, recusam esse parâmetro na abertura."""
    await conn.execute("SET default_transaction_read_only = on")


class DatabaseManager:
    """Gerenciador de conexões com os bancos de origem."""

    def __init__(self, settings: Settings):
        self._settings = settings
        self._pools: dict[str, asyncpg.Pool] = {}
        self._limits: dict[str, asyncio.Semaphore] = {}
        self._status: dict[str, Status] = {name: "off" for name in SOURCE_DATABASES}

    def _pool_kwargs(self) -> dict:
        s = self._settings
        return {
            "min_size": s.DB_POOL_MIN_SIZE,
            "max_size": s.DB_POOL_MAX_SIZE,
            "max_inactive_connection_lifetime": s.DB_POOL_MAX_INACTIVE_CONNECTION_LIFETIME,
            "max_queries": s.DB_POOL_MAX_QUERIES,
            "command_timeout": s.DB_POOL_COMMAND_TIMEOUT,
            "timeout": s.DB_POOL_ACQUIRE_TIMEOUT,
            "server_settings": {"application_name": APPLICATION_NAME},
            "init": _read_only,
        }

    async def initialize(self) -> None:
        """Abre os pools de todos os bancos configurados. Obrigatório que falha = erro (igual à v1).

        Os bancos abrem ao mesmo tempo (cada um num servidor diferente): a subida leva o tempo do
        mais lento, não a soma. Cada banco recebe as mesmas conexões de antes, só não espera os outros.
        """
        pending = []
        for name in SOURCE_DATABASES:
            target = self._settings.source_dsn(name)
            if target is None:
                continue  # sem variáveis no .env: desligado
            self._limits[name] = asyncio.Semaphore(self._settings.source_concurrency(name))
            pending.append(self._open_pool(name, target))
        # Espera todos terminarem (sucesso ou falha) e só então repassa o erro de um obrigatório.
        results = await asyncio.gather(*pending, return_exceptions=True)
        errors = [r for r in results if isinstance(r, BaseException)]
        if errors:
            raise errors[0]

    async def _open_pool(self, name: str, target: dict) -> None:
        optional = name in OPTIONAL_DATABASES
        for attempt in range(1, MAX_DB_CONNECTION_RETRIES + 1):
            try:
                self._pools[name] = await asyncpg.create_pool(**target, **self._pool_kwargs())
                self._status[name] = "up"
                logger.info("Conexão com banco '%s' estabelecida", name)
                return
            except _CONNECT_ERRORS as exc:
                # Só o tipo do erro: a mensagem pode trazer host ou usuário do .env.
                logger.warning(
                    "Falha ao conectar ao banco '%s' (tentativa %d/%d): %s",
                    name,
                    attempt,
                    MAX_DB_CONNECTION_RETRIES,
                    type(exc).__name__,
                )
                if attempt < MAX_DB_CONNECTION_RETRIES:
                    await asyncio.sleep(_backoff(attempt))
        self._status[name] = "down"
        if not optional:
            raise RuntimeError(
                f"Banco obrigatório '{name}' indisponível na subida (ver DB_{name.upper()}_*)"
            )
        logger.warning("Banco opcional '%s' indisponível: a API sobe sem esse pool", name)

    async def close(self) -> None:
        """Fecha todos os pools."""
        for name, pool in self._pools.items():
            await pool.close()
            logger.info("Conexão com banco '%s' fechada", name)
        self._pools.clear()

    def status(self) -> dict[str, Status]:
        """Estado de cada banco: up, down ou off (sem variáveis)."""
        return dict(self._status)

    def get_pool(self, db_name: str) -> asyncpg.Pool:
        """Pool de um banco ('ng', 'laadv', 'lexflow' ou 'lexpre'). Erro se não estiver aberto."""
        if db_name not in self._pools:
            raise ValueError(
                f"Banco '{db_name}' não está inicializado ({self._status.get(db_name, 'off')})"
            )
        return self._pools[db_name]

    @asynccontextmanager
    async def get_connection(self, db_name: str) -> AsyncIterator[asyncpg.Connection]:
        """`async with databases.get_connection('ng') as conn:` — respeita DB_QUERY_CONCURRENCY_*."""
        pool = self.get_pool(db_name)
        async with self._limits[db_name], pool.acquire() as connection:
            yield connection


async def run_with_connection_retry[T](
    manager: DatabaseManager,
    db_name: str,
    operation: Callable[[asyncpg.Connection], Awaitable[T]],
    *,
    operation_name: str = "query",
    max_retries: int = MAX_DB_CONNECTION_RETRIES,
) -> T:
    """Executa `operation(conn)` e, em falha transitória, expira o pool e tenta de novo (igual à v1)."""
    for attempt in range(1, max_retries + 1):
        try:
            async with manager.get_connection(db_name) as conn:
                return await operation(conn)
        except TimeoutError:
            raise
        except _RETRYABLE_DB_ERRORS as exc:
            logger.warning(
                "Falha transitória ao executar '%s' em '%s' (tentativa %d/%d): %s",
                operation_name,
                db_name,
                attempt,
                max_retries,
                type(exc).__name__,
            )
            if attempt >= max_retries:
                raise
            await manager.get_pool(db_name).expire_connections()
            await asyncio.sleep(_backoff(attempt))
    raise AssertionError("inalcançável")  # o laço sempre retorna ou levanta


def get_databases(request: Request) -> DatabaseManager:
    """Dependency FastAPI: `databases: DatabaseManager = Depends(get_databases)`."""
    return request.app.state.databases
