import asyncio
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import build_verifier
from app.cache_warmer import warm_loop, warm_targets
from app.config import get_settings
from app.dashboards import DASHBOARDS
from app.database import DatabaseManager
from app.routes import catalog, dashboards, health, hub, me
from app.source_cache import MemoryStore, SourceCache
from app.sources import PgSourceFetcher
from app.supabase_client import create_supabase


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


def create_app() -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.supabase = await create_supabase(settings)
        app.state.token_verifier = build_verifier(settings)
        app.state.db_pool = (
            await asyncpg.create_pool(
                settings.DATABASE_URL,
                min_size=1,
                max_size=10,
                command_timeout=60,
                # O pooler do Supabase (modo transaction) não suporta prepared statements.
                statement_cache_size=0,
            )
            if settings.DATABASE_URL
            else None
        )
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
            if settings.SOURCE_CACHE_WARM_ENABLED:
                warmer = asyncio.create_task(_start_warmer(app, settings))
            yield
        finally:
            if warmer is not None:
                warmer.cancel()
            await app.state.databases.close()
            if app.state.db_pool is not None:
                await app.state.db_pool.close()

    app = FastAPI(title="API Dashboard V2", version="0.1.0", lifespan=lifespan)

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
            allow_headers=["Authorization", "Content-Type"],
        )

    app.include_router(health.router)
    app.include_router(me.router)
    app.include_router(catalog.router)
    app.include_router(hub.router)
    app.include_router(dashboards.router)
    return app


app = create_app()
