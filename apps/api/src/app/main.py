import asyncio
import logging
import time
from contextlib import asynccontextmanager
from urllib.parse import urlsplit

import asyncpg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import build_verifier
from app.cache import CacheService, build_cache, safe_redis_target
from app.cache_warmer import warm_loop, warm_targets
from app.config import Settings, get_settings
from app.dashboards import DASHBOARDS
from app.database import DatabaseManager, connect_hint
from app.logs import configure_logging, seconds
from app.request_log import RequestLogMiddleware
from app.routes import catalog, dashboards, device_auth, health, hub, me, sources
from app.source_cache import MemoryStore, SourceCache, ttl_by_query
from app.sources import source_fetcher
from app.supabase_client import create_supabase

VERSION = "0.1.0"

# Tentativas de conectar no banco da plataforma na subida (cada uma limitada por DB_CONNECT_TIMEOUT).
PLATFORM_DB_ATTEMPTS = 3

logger = logging.getLogger("app.startup")


async def _start_warmer(app: FastAPI, settings) -> None:
    """Mantém quentes as queries dos dashboards (só dos bancos que estão no ar)."""
    databases: DatabaseManager = app.state.databases
    await warm_loop(
        app.state.source_cache,
        lambda db: source_fetcher(databases, db),
        warm_targets(DASHBOARDS.values()),
        databases.is_up,
        interval=settings.SOURCE_CACHE_WARM_INTERVAL,
    )


async def _log_cache(cache: CacheService, settings: Settings) -> None:
    """Estado do Redis na subida (o RedisCache já avisa sozinho se não conectar)."""
    state = await cache.status()
    if state == "off":
        logger.info("Redis desligado (CACHE_ENABLED=false): cache só em memória, por réplica")
    elif state == "up":
        logger.info(
            "Redis ligado em %s (prefixo '%s'; TTL %s, pesadas %s)",
            safe_redis_target(settings.REDIS_URL),
            settings.CACHE_KEY_PREFIX,
            seconds(settings.CACHE_TTL_DEFAULT),
            seconds(settings.CACHE_TTL_HEAVY),
        )


def _log_auth(settings: Settings) -> None:
    """De onde vem o login e com que chave a API fala com o Supabase (nunca a chave em si)."""
    host = urlsplit(settings.SUPABASE_URL).hostname or settings.SUPABASE_URL
    key = "chave secreta" if settings.supabase_secret_key else "chave publishable (respeita RLS)"
    logger.info("Supabase: %s, com %s", host, key)
    legacy = " + segredo HS256 legado" if settings.SUPABASE_JWT_SECRET else ""
    logger.info("Login: tokens do Supabase Auth conferidos localmente (JWKS%s)", legacy)


async def _open_platform_db(settings: Settings) -> asyncpg.Pool | None:
    """Banco da plataforma (login, acesso, catálogo, auditoria). Sem DATABASE_URL, as rotas dão 503.

    Diferente dos bancos de origem, este impede a subida: sem ele nenhuma rota de usuário funciona,
    e falhar na subida faz o Swarm voltar à versão anterior num deploy com DATABASE_URL errada.
    As tentativas têm tempo limite, então a falha aparece no log em segundos.
    """
    if not settings.DATABASE_URL:
        logger.warning(
            "Banco da plataforma: DATABASE_URL vazio; rotas protegidas vão responder 503"
        )
        return None
    logger.info("Banco da plataforma: conectando...")
    started = time.perf_counter()
    for attempt in range(1, PLATFORM_DB_ATTEMPTS + 1):
        try:
            pool = await asyncpg.create_pool(
                settings.DATABASE_URL,
                min_size=1,
                max_size=10,
                command_timeout=60,
                timeout=settings.DB_CONNECT_TIMEOUT,
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
            await asyncio.sleep(2 * attempt)
        else:
            logger.info(
                "Banco da plataforma conectado em %s", seconds(time.perf_counter() - started)
            )
            return pool
    raise AssertionError("inalcançável")  # o laço sempre retorna ou levanta


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.LOG_LEVEL)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        started = time.perf_counter()
        logger.info("Subindo LexHub API v%s (log %s)", VERSION, settings.LOG_LEVEL.upper())
        _log_auth(settings)
        app.state.supabase = await create_supabase(settings)
        app.state.token_verifier = build_verifier(settings)
        app.state.db_pool = await _open_platform_db(settings)
        # Bancos de origem da v1 (NG, LAADV, LEXFLOW, LEXPRE): conectam em segundo plano e se
        # reconectam sozinhos; fora do ar, só os dashboards daquele banco ficam indisponíveis.
        # Sem variáveis no .env, o banco fica desligado.
        app.state.databases = DatabaseManager(settings)
        # Redis (L2): igual à v1, opcional; fora do ar = só memória, sem impedir a subida.
        app.state.cache = build_cache(settings)
        app.state.source_cache = SourceCache(
            MemoryStore(settings.SOURCE_CACHE_MAX_ENTRIES),
            ttl=settings.SOURCE_CACHE_TTL,
            stale_max_age=settings.SOURCE_CACHE_STALE_MAX_AGE,
            shared=app.state.cache,
            shared_ttl=ttl_by_query(settings.CACHE_TTL_HEAVY, settings.CACHE_TTL_DEFAULT),
        )
        warmer = None
        try:
            await _log_cache(app.state.cache, settings)
            app.state.databases.start()  # não espera: cada banco conecta numa tarefa de fundo
            logger.info(
                "Cache: dados valem %s; se o banco cair, serve o último dado bom por até %s",
                seconds(settings.SOURCE_CACHE_TTL),
                seconds(settings.SOURCE_CACHE_STALE_MAX_AGE),
            )
            if settings.SOURCE_CACHE_WARM_ENABLED:
                warmer = asyncio.create_task(_start_warmer(app, settings))
            else:
                logger.info("Aquecedor do cache desligado (SOURCE_CACHE_WARM_ENABLED=false)")
            logger.info(
                "API pronta em %s: %d dashboards registrados",
                seconds(time.perf_counter() - started),
                len(DASHBOARDS),
            )
            yield
        finally:
            logger.info("Desligando a API...")
            if warmer is not None:
                warmer.cancel()
                await asyncio.gather(warmer, return_exceptions=True)
            await app.state.databases.close()
            await app.state.cache.close()
            if app.state.db_pool is not None:
                await app.state.db_pool.close()
            logger.info("API desligada")

    app = FastAPI(title="API Dashboard V2", version=VERSION, lifespan=lifespan)

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
            allow_headers=["Authorization", "Content-Type"],
        )
    # Por último = mais externo: mede a requisição inteira, inclusive o CORS.
    app.add_middleware(RequestLogMiddleware)

    app.include_router(health.router)
    app.include_router(me.router)
    app.include_router(catalog.router)
    app.include_router(hub.router)
    app.include_router(dashboards.router)
    app.include_router(device_auth.router)
    app.include_router(sources.router)
    return app


app = create_app()
