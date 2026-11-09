from fastapi import Request
from supabase import AsyncClient, acreate_client

from app.config import Settings


async def create_supabase(settings: Settings) -> AsyncClient:
    """Cria o cliente. Usa a chave secreta se configurada; senão, a publishable (respeita RLS)."""
    key = settings.supabase_secret_key or settings.SUPABASE_PUBLISHABLE_KEY
    return await acreate_client(settings.SUPABASE_URL, key)


def get_supabase(request: Request) -> AsyncClient:
    """Dependency FastAPI: `sb: AsyncClient = Depends(get_supabase)`."""
    return request.app.state.supabase
