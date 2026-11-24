"""Banco da plataforma (DATABASE_URL, pooler do Supabase): pool, conexões quentes e erros.

O pooler fica em São Paulo, atrás de um balanceador TCP da AWS, e abrir uma conexão (TCP + TLS +
autenticação, saindo de outra região) leva de 1 a 10 s. Com o padrão anterior (1 conexão mínima,
fechada depois de 5 min parada, e tempo limite de 10 s), quase toda requisição depois de uma pausa
abria conexão nova; quando passava de 10 s, o usuário recebia 500. Agora:

  * o pool abre PLATFORM_DB_POOL_MIN_SIZE conexões na subida, e `keep_warm` roda um `select 1`
    nelas a cada PLATFORM_DB_KEEPALIVE_INTERVAL s: elas nunca ficam paradas o bastante para o
    pool fechá-las (MAX_INACTIVE_CONNECTION_LIFETIME) nem para o balanceador cortá-las (o NLB da
    AWS corta conexão TCP ociosa em 350 s). Conexão que morreu é trocada aqui, em segundo plano,
    e não na requisição do usuário;
  * abrir conexão tem tempo limite próprio (PLATFORM_DB_CONNECT_TIMEOUT, 30 s), maior que o dos
    bancos de origem;
  * sem conexão com o banco, qualquer rota responde 503 ("banco indisponível"), não 500
    (`install_error_handlers`).

Diferente dos bancos de origem, este impede a subida: sem ele nenhuma rota de usuário funciona, e
falhar na subida faz o Swarm voltar à versão anterior num deploy com DATABASE_URL errada.
"""

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any
from urllib.parse import urlparse

import asyncpg
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import Settings
from app.database import connect_hint
from app.logs import seconds

logger = logging.getLogger(__name__)

# Tentativas de abrir o pool na subida (cada conexão limitada por PLATFORM_DB_CONNECT_TIMEOUT).
PLATFORM_DB_ATTEMPTS = 3
# Conexão parada além disto o pool fecha (abaixo dos 350 s do balanceador). As mínimas nunca
# chegam a isso: keep_warm as usa a cada PLATFORM_DB_KEEPALIVE_INTERVAL.
MAX_INACTIVE_CONNECTION_LIFETIME = 300.0
# Sem conexão com o banco: rede, tempo limite (TimeoutError é OSError) ou conexão que caiu.
UNAVAILABLE_ERRORS: tuple[type[Exception], ...] = (OSError, asyncpg.PostgresConnectionError)

PoolFactory = Callable[..., Awaitable[Any]]


def url_modo_transacao(url: str) -> str:
    """A 5432 do pooler do Supabase é modo sessão: cada cliente ocupa uma vaga e o teto é 15
    (`EMAXCONNSESSION`). O pool daqui já desliga prepared statements para o modo transação, então
    a mesma URL na 6543 não estoura esse teto."""
    host = urlparse(url).hostname or ""
    porta_sessao = f"@{host}:5432"
    if host.endswith("pooler.supabase.com") and porta_sessao in url:
        logger.warning(
            "Banco da plataforma: URL na porta 5432 (modo sessão, teto de 15 clientes); "
            "conectando na 6543 (modo transação)"
        )
        return url.replace(porta_sessao, f"@{host}:6543", 1)
    return url


async def open_platform_pool(
    settings: Settings,
    *,
    create_pool: PoolFactory = asyncpg.create_pool,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> asyncpg.Pool | None:
    """Abre o pool na subida. Sem DATABASE_URL, None (as rotas protegidas dão 503)."""
    if not settings.DATABASE_URL:
        logger.warning(
            "Banco da plataforma: DATABASE_URL vazio; rotas protegidas vão responder 503"
        )
        return None
    logger.info("Banco da plataforma: conectando...")
    started = time.perf_counter()
    for attempt in range(1, PLATFORM_DB_ATTEMPTS + 1):
        try:
            pool = await create_pool(
                url_modo_transacao(settings.DATABASE_URL),
                min_size=settings.PLATFORM_DB_POOL_MIN_SIZE,
                max_size=settings.PLATFORM_DB_POOL_MAX_SIZE,
                max_inactive_connection_lifetime=MAX_INACTIVE_CONNECTION_LIFETIME,
                command_timeout=60,
                timeout=settings.PLATFORM_DB_CONNECT_TIMEOUT,
                # O pooler do Supabase (modo transaction) não suporta prepared statements.
                statement_cache_size=0,
            )
        except (OSError, asyncpg.PostgresError, asyncpg.InterfaceError) as exc:
            # Só o tipo e a dica: a mensagem pode trazer host ou usuário da DATABASE_URL.
            logger.error(
                "Banco da plataforma: falha ao conectar (tentativa %d/%d): %s",
                attempt,
                PLATFORM_DB_ATTEMPTS,
                connect_hint(exc),
            )
            if attempt == PLATFORM_DB_ATTEMPTS:
                raise RuntimeError(
                    "Banco da plataforma (DATABASE_URL) indisponível: a API não sobe sem ele"
                ) from None
            await sleep(2 * attempt)
        else:
            logger.info(
                "Banco da plataforma conectado em %s (pool %d-%d, conexões testadas a cada %s)",
                seconds(time.perf_counter() - started),
                settings.PLATFORM_DB_POOL_MIN_SIZE,
                settings.PLATFORM_DB_POOL_MAX_SIZE,
                seconds(settings.PLATFORM_DB_KEEPALIVE_INTERVAL),
            )
            return pool
    raise AssertionError("inalcançável")  # o laço sempre retorna ou levanta


async def _ping(pool: asyncpg.Pool, timeout: float) -> None:
    async with pool.acquire(timeout=timeout) as conn:
        await conn.fetchval("select 1", timeout=timeout)


async def ping_connections(pool: asyncpg.Pool, size: int, timeout: float) -> int:
    """Um `select 1` em `size` conexões ao mesmo tempo (cada acquire pega uma diferente).

    Mantém essas conexões em uso e reabre as que faltarem ou tiverem morrido (o pool descarta a
    conexão que falhou). Devolve quantas responderam.
    """
    results = await asyncio.gather(
        *(_ping(pool, timeout) for _ in range(size)), return_exceptions=True
    )
    failed = [r for r in results if isinstance(r, BaseException)]
    if failed:
        logger.warning(
            "Banco da plataforma: %d de %d conexões não responderam ao teste (%s); serão reabertas",
            len(failed),
            size,
            connect_hint(failed[0]),
        )
    return size - len(failed)


async def keep_warm(
    pool: asyncpg.Pool,
    size: int,
    interval: float,
    timeout: float,
    *,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> None:
    """Tarefa de fundo: a cada `interval` s, testa as `size` conexões mínimas (ver o módulo)."""
    while True:
        await sleep(interval)
        try:
            await ping_connections(pool, size, timeout)
        except Exception as exc:  # noqa: BLE001 — a tarefa nunca pode morrer
            logger.warning("Banco da plataforma: teste das conexões falhou (%s)", connect_hint(exc))


async def database_unavailable(request: Request, exc: Exception) -> JSONResponse:
    """Sem conexão com o banco: 503 com uma mensagem clara, em vez de 500 com traceback."""
    logger.warning(
        "%s %s: sem conexão com o banco (%s)", request.method, request.url.path, connect_hint(exc)
    )
    return JSONResponse(
        status_code=503,
        content={"detail": "Banco de dados indisponível no momento. Tente de novo em instantes."},
        headers={"Retry-After": "5"},
    )


def install_error_handlers(app: FastAPI) -> None:
    for exc_type in UNAVAILABLE_ERRORS:
        app.add_exception_handler(exc_type, database_unavailable)
