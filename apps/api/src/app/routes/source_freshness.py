"""Unidades e fontes: quando cada fonte foi lida, no mesmo modelo do card do hub.

A hora vem do cache da API (app/source_cache.py), e não do log de sincronização no Supabase (que só o
worker, ainda inexistente, escreveria). A rota só lê a memória do processo: não consulta banco nenhum,
não aquece e não renova nada. Quem pede passa as chaves (as fontes que `api.list_sources` já mostrou).
"""

import re
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.access import OrgAccess, require_org
from app.source_cache import SourceCache
from app.sources import get_source_cache

router = APIRouter(prefix="/orgs/{org_slug}", tags=["sources"])

_KEY = re.compile(r"^[a-z][a-z0-9_]{1,31}$")  # o mesmo formato de app.data_sources.key
MAX_KEYS = 50


class SourceFreshnessOut(BaseModel):
    # null = ninguém abriu um dashboard dessa fonte desde que a API subiu
    fetched_at: datetime | None
    ttl_min: int  # quanto tempo a leitura vale no cache
    error: str | None  # tipo do erro (nunca a mensagem) se a busca falhou depois da última leitura
    error_at: datetime | None


class SourcesFreshnessOut(BaseModel):
    sources: dict[str, SourceFreshnessOut]


def _when(epoch: float | None) -> datetime | None:
    return datetime.fromtimestamp(epoch, UTC) if epoch is not None else None


def parse_keys(raw: str) -> list[str]:
    """'lexflow,ng,ng' -> ['lexflow', 'ng'] (na ordem); chave fora do formato ou demais = 422."""
    keys = list(dict.fromkeys(k.strip() for k in raw.split(",") if k.strip()))
    if len(keys) > MAX_KEYS or any(not _KEY.match(k) for k in keys):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Chaves de fonte inválidas"
        )
    return keys


@router.get("/sources/freshness", response_model=SourcesFreshnessOut)
async def sources_freshness(
    access: Annotated[OrgAccess, Depends(require_org)],
    cache: Annotated[SourceCache, Depends(get_source_cache)],
    keys: Annotated[str, Query(max_length=2000)] = "",
) -> SourcesFreshnessOut:
    out: dict[str, SourceFreshnessOut] = {}
    for key in parse_keys(keys):
        reads = (await cache.reads.of_db(key)).values()
        ok_at = max((r.ok_at for r in reads if r.ok_at is not None), default=None)
        fail = max(((r.fail_at, r.error) for r in reads if r.fail_at is not None), default=None)
        if fail is not None and ok_at is not None and fail[0] <= ok_at:
            fail = None  # houve leitura boa depois da última falha
        out[key] = SourceFreshnessOut(
            fetched_at=_when(ok_at),
            ttl_min=max(1, round(cache.ttl_of(f"{key}:") / 60)),
            error=fail[1] if fail else None,
            error_at=_when(fail[0]) if fail else None,
        )
    return SourcesFreshnessOut(sources=out)
