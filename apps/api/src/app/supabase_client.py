from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from supabase import AsyncClient, acreate_client
from supabase_auth import AsyncGoTrueClient

from app.config import Settings, get_settings


async def create_supabase(settings: Settings) -> AsyncClient:
    """Cria o cliente. Usa a chave secreta se configurada; senão, a publishable (respeita RLS)."""
    key = settings.supabase_secret_key or settings.SUPABASE_PUBLISHABLE_KEY
    return await acreate_client(settings.SUPABASE_URL, key)


def get_supabase(request: Request) -> AsyncClient:
    """Dependency FastAPI: `sb: AsyncClient = Depends(get_supabase)`."""
    return request.app.state.supabase


def get_supabase_admin(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> AsyncClient:
    """Cliente administrativo: operações privilegiadas nunca usam a chave pública."""
    if not settings.supabase_secret_key:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Login por dispositivo não configurado no servidor.",
        )
    return request.app.state.supabase


async def get_supabase_auth(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AsyncIterator[AsyncGoTrueClient]:
    """Cliente Auth isolado para a verificação, que salva a sessão emitida em seu próprio estado."""
    if not settings.SUPABASE_PUBLISHABLE_KEY:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase Auth não configurado no servidor.",
        )
    auth = AsyncGoTrueClient(
        url=f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1",
        headers={
            "apiKey": settings.SUPABASE_PUBLISHABLE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_PUBLISHABLE_KEY}",
        },
        auto_refresh_token=False,
        persist_session=False,
    )
    try:
        yield auth
    finally:
        await auth.close()
