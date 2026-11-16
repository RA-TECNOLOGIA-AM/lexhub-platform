import asyncio
import logging
import time
from contextlib import asynccontextmanager
from urllib.parse import urlsplit

import asyncpg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import build_verifier
from app.cache_warmer import warm_loop, warm_targets
from app.config import Settings, get_settings
from app.dashboards import DASHBOARDS
from app.database import DatabaseManager
from app.logs import configure_logging, seconds
from app.request_log import RequestLogMiddleware
from app.routes import catalog, dashboards, device_auth, health, hub, me
from app.source_cache import MemoryStore, SourceCache
from app.sources import PgSourceFetcher
from app.supabase_client import create_supabase

VERSION = "0.1.0"

logger = logging.getLogger("app.startup")


async def _start_warmer(app: FastAPI, settings) -> None:
    """Mantém quentes as queries dos dashboards (só dos bancos que estão no ar)."""
    databases = app.state.databases
    await warm_loop(
        app.state.source_cache,
        lambda db: PgSourceFetcher(databases, db),
        warm_targets(DASHBOARDS.values()),
        lambda db: databases.status().get(db) == "up",
        interval=settings.SOURCE_CACHE_WARM_INTERVAL,
    )


def _log_auth(settings: Settings) -> None:
    """De onde vem o login e com que chave a API fala com o Supabase (nunca a chave em si)."""
    host = urlsplit(settings.SUPABASE_URL).hostname or settings.SUPABASE_URL
    key = "chave secreta" if settings.supabase_secret_key else "chave publishable (respeita RLS)"
    logger.info("Supabase: %s, com %s", host, key)
    legacy = " + segredo HS256 legado" if settings.SUPABASE_JWT_SECRET else ""
    logger.info("Login: tokens do Supabase Auth conferidos localmente (JWKS%s)", legacy)


async def _open_platform_db(settings: Settings) -> asyncpg.Pool | None:
    """Banco da plataforma (acesso, catálogo, auditoria). Sem DATABASE_URL, as rotas dão 503."""
    if not settings.DATABASE_URL:
        logger.warning(
            "Banco da plataforma: DATABASE_URL vazio; rotas protegidas vão responder 503"
        )
        return None
    logger.info("Banco da plataforma: conectando...")
    started = time.perf_counter()
    try:
        pool = await asyncpg.create_pool(
            settings.DATABASE_URL,
            min_size=1,
            max_size=10,
            command_timeout=60,
            # O pooler do Supabase (modo transaction) não suporta prepared statements.
            statement_cache_size=0,
        )
    except Exception as exc:
        # Só o tipo: a mensagem pode trazer host ou usuário da DATABASE_URL.
        logger.error("Banco da plataforma: falha ao conectar (%s)", type(exc).__name__)
        raise
    logger.info("Banco da plataforma conectado em %s", seconds(time.perf_counter() - started))
    return pool


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
        # Bancos de origem da v1 (NG, LAADV, LEXFLOW, LEXPRE). Igual à v1: obrigatório fora do ar
        # impede a subida; o LEXPRE é opcional. Sem variáveis no .env, o banco fica desligado.
        app.state.databases = DatabaseManager(settings)
        app.state.source_cache = SourceCache(
            MemoryStore(settings.SOURCE_CACHE_MAX_ENTRIES),
            ttl=settings.SOURCE_CACHE_TTL,
            stale_max_age=settings.SOURCE_CACHE_STALE_MAX_AGE,
        )
        warmer = None
        try:
            await app.state.databases.initialize()
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
            await app.state.databases.close()
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
    return app


app = create_app()
