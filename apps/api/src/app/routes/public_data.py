"""Dados da API pública /v1: os mesmos do "Exportar" de cada dashboard, em JSON e paginados.

A chave vale como o dono dela (Owner, Gestor ou Controller), mas o alcance é o dos setores da chave
(`app_private.api_key_scope`), não o do cargo. A rota monta um DashboardAccess com esse alcance e usa as
mesmas peças da exportação (routes/dashboards.py), então API e arquivo exportado sempre batem.
"""

import math
from dataclasses import replace
from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.encoders import jsonable_encoder

from app.access import (
    AccessRepo,
    DashboardAccess,
    DashboardKey,
    OrgSlug,
    UnitCode,
    audit_entry,
    get_repo,
)
from app.analyses.common import memo
from app.auth import CurrentUser
from app.clock import get_now
from app.dashboards import DASHBOARDS, export
from app.public_api.rate_limit import RateLimiter
from app.public_api.store import ApiKey, ApiKeyRepo, get_api_key_repo
from app.routes.dashboards import Today, _prepare, _run, get_today, get_unit_scope
from app.routes.public_auth import require_api_key
from app.sources import SourceFactory, SourceRefsRepo, get_source_factory, get_source_refs_repo

router = APIRouter(prefix="/v1", tags=["api pública"])

MAX_DAYS = 366
_LIMITER = RateLimiter(limit=60, window_s=60)


def get_rate_limiter() -> RateLimiter:
    return _LIMITER


def _owner(key: ApiKey) -> CurrentUser:
    return CurrentUser(user_id=key.user_id, email=None, claims={})


def _split(campos: list[str] | None) -> list[str]:
    """`campos` por vírgula, repetido ou os dois juntos."""
    return [c.strip() for v in campos or [] for c in v.split(",") if c.strip()]


@router.get("/catalogo")
async def catalog(
    key: Annotated[ApiKey, Depends(require_api_key)],
    keys: Annotated[ApiKeyRepo, Depends(get_api_key_repo)],
) -> dict:
    """O que a chave alcança agora: unidade, dashboard e relatórios (com os campos) de cada um."""
    acesso = []
    for item in await keys.reachable(key.id):
        module = DASHBOARDS.get(item.dashboard_key)
        if module is None:
            continue
        reports = ([("", module.export)] if module.export else []) + list(
            module.export_reports.items()
        )
        if not reports:
            continue
        acesso.append(
            {
                "org": item.org_slug,
                "unidade": item.unit_code,
                "dashboard": item.dashboard_key,
                "relatorios": [
                    {"chave": chave, "titulo": spec.title, "campos": list(spec.fields)}
                    for chave, spec in reports
                ],
            }
        )
    return {"acesso": acesso}


@router.get("/orgs/{org_slug}/units/{unit_code}/dashboards/{dashboard_key}")
async def dashboard_data(
    request: Request,
    org_slug: OrgSlug,
    unit_code: UnitCode,
    dashboard_key: DashboardKey,
    key: Annotated[ApiKey, Depends(require_api_key)],
    keys: Annotated[ApiKeyRepo, Depends(get_api_key_repo)],
    limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
    refs: Annotated[SourceRefsRepo, Depends(get_source_refs_repo)],
    sources: Annotated[SourceFactory, Depends(get_source_factory)],
    audit: Annotated[AccessRepo, Depends(get_repo)],
    today: Annotated[Today, Depends(get_today)],
    unit_scope: Annotated[bool, Depends(get_unit_scope)],
    now: Annotated[datetime, Depends(get_now)],
    start: Annotated[date, Query(alias="from")],
    end: Annotated[date, Query(alias="to")],
    campos: Annotated[list[str] | None, Query()] = None,
    relatorio: Annotated[str | None, Query()] = None,
    pagina: Annotated[int, Query(ge=1)] = 1,
    tamanho_pagina: Annotated[int, Query(ge=1, le=5000)] = 1000,
) -> dict:
    if not limiter.hit(key.id):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Limite de {limiter.limit} chamadas por minuto",
            headers={"Retry-After": "60"},
        )
    if end < start:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail="'to' é anterior a 'from'."
        )
    if (end - start).days > MAX_DAYS:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Máximo de {MAX_DAYS} dias entre 'from' e 'to'.",
        )

    owner = _owner(key)
    resolved = await keys.resolve(key.id, org_slug, unit_code, dashboard_key)
    if resolved is None or resolved.scope is None:
        await audit.insert_audit(
            audit_entry(
                request,
                owner,
                "api.access_denied",
                org_id=key.org_id,
                target_type="dashboard",
                target_id=dashboard_key,
                metadata={"key_id": key.id, "org": org_slug, "unit": unit_code},
            )
        )
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="Sem acesso a este dashboard pela chave"
        )

    access = DashboardAccess(
        user=owner,
        org_slug=org_slug,
        unit_code=unit_code,
        dashboard_key=dashboard_key,
        org_id=resolved.org_id,
        unit_id=resolved.unit_id,
        scope=resolved.scope,
        timezone=resolved.timezone,
        can_see_commission=resolved.can_see_commission,
        can_export=True,
        source_refs=resolved.source_refs,
    )
    module, ctx = await _prepare(
        request, access, refs, sources, audit, today, start, end, unit_scope
    )
    try:
        spec = export.pick_report(module, relatorio, ctx.unit_ref)
    except export.ExportError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from None
    if spec is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Este dashboard não tem exportação")
    if spec.parts:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Este relatório junta outros: use o parâmetro relatorio com um destes: "
            + ", ".join(module.export_reports),
        )
    try:
        slugs = export.pick_fields(spec, _split(campos))
        opcoes = export.pick_options(spec, dict(request.query_params))
    except export.ExportError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from None
    ctx = replace(ctx, export_options=opcoes)

    rows = await _run(module, memo.no_pedido(spec.rows(ctx)))
    total = len(rows)
    inicio = (pagina - 1) * tamanho_pagina
    fatia = [
        {s: row.get(spec.fields[s]) for s in slugs}
        for row in rows[inicio : inicio + tamanho_pagina]
    ]

    await keys.touch_last_used(key.id, now)
    await audit.insert_audit(
        audit_entry(
            request,
            owner,
            "api.read",
            org_id=resolved.org_id,
            target_type="dashboard",
            target_id=dashboard_key,
            metadata={
                "key_id": key.id,
                "org": org_slug,
                "unit": unit_code,
                "relatorio": relatorio or "",
                "from": start.isoformat(),
                "to": end.isoformat(),
                "pagina": pagina,
                "total": total,
            },
        )
    )
    return jsonable_encoder(
        {
            "org": org_slug,
            "unidade": unit_code,
            "dashboard": dashboard_key,
            "relatorio": relatorio or "",
            "periodo": {"from": start, "to": end},
            "campos": slugs,
            "paginacao": {
                "pagina": pagina,
                "tamanho_pagina": tamanho_pagina,
                "total": total,
                "total_paginas": math.ceil(total / tamanho_pagina) if total else 0,
            },
            "dados": fatia,
        }
    )
