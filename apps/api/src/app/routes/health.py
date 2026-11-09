from typing import Annotated

import httpx
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.config import Settings, get_settings
from app.database import DatabaseManager, get_databases

router = APIRouter(prefix="/health", tags=["health"])


async def check_supabase(
    settings: Settings, transport: httpx.AsyncBaseTransport | None = None
) -> tuple[bool, str | None]:
    url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/health"
    try:
        async with httpx.AsyncClient(timeout=5, transport=transport) as http:
            r = await http.get(url, headers={"apikey": settings.SUPABASE_PUBLISHABLE_KEY})
        if r.status_code == 200:
            return True, None
        return False, f"HTTP {r.status_code}"
    except httpx.HTTPError as e:
        return False, str(e) or type(e).__name__


@router.get("")
async def health():
    return {"status": "ok"}


@router.get("/supabase")
async def health_supabase(settings: Annotated[Settings, Depends(get_settings)]):
    ok, err = await check_supabase(settings)
    if ok:
        return {"status": "ok", "supabase": "up"}
    return JSONResponse(
        status_code=503, content={"status": "error", "supabase": "down", "detail": err}
    )


@router.get("/sources")
async def health_sources(manager: Annotated[DatabaseManager, Depends(get_databases)]):
    """Estado de cada banco de origem: up, down ou off (sem variáveis). 503 se algum configurado caiu.

    Só nomes e estados: nunca host, usuário ou mensagem de erro (é uma rota pública).
    """
    databases = manager.status()
    ok = "down" not in databases.values()
    body = {"status": "ok" if ok else "error", "databases": databases}
    return body if ok else JSONResponse(status_code=503, content=body)
