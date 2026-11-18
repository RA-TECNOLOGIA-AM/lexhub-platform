import asyncio
import logging
import time
from contextlib import asynccontextmanager
from urllib.parse import urlsplit

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import build_verifier
from app.cache import CacheService, build_cache, safe_redis_target
from app.cache_warmer import warm_loop, warm_targets
from app.config import Settings, get_settings
from app.dashboards import DASHBOARDS
from app.database import DatabaseManager
from app.logs import configure_logging, seconds
from app.platform_db import install_error_handlers, keep_warm, open_platform_pool
from app.registered_sources import PgRegisteredRepo, RegisteredSources
from app.request_log import RequestLogMiddleware
from app.routes import (
    catalog,
    dashboards,
    device_auth,
    health,
    hub,
    me,
    source_connections,
    sources,
)
from app.source_cache import MemoryStore, SourceCache, ttl_by_query
from app.source_switch import PgDisabledRepo, SourceSwitch
from app.sources import source_fetcher
from app.supabase_client import create_supabase

VERSION = "0.1.0"

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
        # Banco da plataforma: impede a subida e fica com conexões quentes (app/platform_db.py).
        app.state.db_pool = await open_platform_pool(settings)
        # Bancos de origem da v1 (NG, LAADV, LEXFLOW, LEXPRE): conectam em segundo plano e se
        # reconectam sozinhos; fora do ar, só os dashboards daquele banco ficam indisponíveis.
        # Sem variáveis no .env, o banco fica desligado.
        app.state.databases = DatabaseManager(settings)
        # Fontes conectadas pela tela (banco próprio e planilha): lidas do banco da plataforma quando
        # alguém usa, com o segredo decifrado pela SOURCE_SECRET_KEY (app/registered_sources.py).
        app.state.registered_sources = (
            RegisteredSources(PgRegisteredRepo(app.state.db_pool), settings)
            if app.state.db_pool is not None
            else None
        )
        # Liga/desliga das fontes da tela, checado antes do cache (app/source_switch.py).
        app.state.source_switch = (
            SourceSwitch(PgDisabledRepo(app.state.db_pool))
            if app.state.db_pool is not None
            else None
        )
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
        keeper = None
        try:
            if app.state.db_pool is not None:
                keeper = asyncio.create_task(
                    keep_warm(
                        app.state.db_pool,
                        settings.PLATFORM_DB_POOL_MIN_SIZE,
                        settings.PLATFORM_DB_KEEPALIVE_INTERVAL,
                        settings.PLATFORM_DB_CONNECT_TIMEOUT,
                    )
                )
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
            tasks = [t for t in (warmer, keeper) if t is not None]
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            await app.state.databases.close()
            if app.state.registered_sources is not None:
                await app.state.registered_sources.close()
            await app.state.cache.close()
            if app.state.db_pool is not None:
                await app.state.db_pool.close()
            logger.info("API desligada")

    app = FastAPI(title="API Dashboard V2", version=VERSION, lifespan=lifespan)
    # Sem conexão com o banco: 503 com mensagem clara, não 500 (app/platform_db.py).
    install_error_handlers(app)

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
    app.include_router(source_connections.platform)
    app.include_router(source_connections.org)
    return app


app = create_app()
