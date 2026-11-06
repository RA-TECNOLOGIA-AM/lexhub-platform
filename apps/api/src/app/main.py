from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import build_verifier
from app.config import get_settings
from app.routes import dashboards, health
from app.supabase_client import create_supabase


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
        try:
            yield
        finally:
            if app.state.db_pool is not None:
                await app.state.db_pool.close()

    app = FastAPI(title="API Dashboard V2", version="0.1.0", lifespan=lifespan)

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PATCH", "DELETE"],
            allow_headers=["Authorization", "Content-Type"],
        )

    app.include_router(health.router)
    app.include_router(dashboards.router)
    return app


app = create_app()
