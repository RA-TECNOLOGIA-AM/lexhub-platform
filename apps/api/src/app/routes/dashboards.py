from collections.abc import Awaitable, Callable, Hashable
from dataclasses import replace
from datetime import UTC, date, datetime
from typing import Annotated, Any
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from app.access import AccessRepo, DashboardAccess, audit_entry, get_repo, require_dashboard
from app.dashboards import DASHBOARDS, export
from app.dashboards.base import (
    DashboardContext,
    DashboardInputError,
    DashboardModule,
    NotReady,
    Remember,
    parse_filters,
    resolve_period,
    shape_response,
)
from app.database import SourceDisabled
from app.result_memo import Compute, ResultMemo, filters_key, run_now
from app.sources import (
    SourceFactory,
    SourceRefsRepo,
    SourceUnavailable,
    get_source_factory,
    get_source_refs_repo,
)

router = APIRouter(prefix="/orgs/{org_slug}/units/{unit_code}/dashboards", tags=["dashboards"])

# Status do nginx para "o cliente fechou a conexão antes da resposta": só aparece no log da API.
CLIENT_CLOSED_REQUEST = 499


@router.get("/{dashboard_key}/access")
async def dashboard_access(access: Annotated[DashboardAccess, Depends(require_dashboard)]):
    """Confere se o usuário logado pode ver o dashboard nesta unidade e com qual escopo."""
    return {
        "org": access.org_slug,
        "unit": access.unit_code,
        "dashboard": access.dashboard_key,
        "scope": access.scope,
    }


Today = Callable[[str], date]


def today_in(timezone: str) -> date:
    """Hoje no fuso da unidade (o 'mês atual' do período padrão depende disso)."""
    return datetime.now(ZoneInfo(timezone)).date()


def _iso(epoch: float | None) -> str | None:
    return datetime.fromtimestamp(epoch, UTC).isoformat() if epoch is not None else None


def get_today() -> Today:
    """Dependency: o relógio (trocável nos testes)."""
    return today_in


async def _deny(
    request: Request, audit: AccessRepo, access: DashboardAccess, reason: str, detail: str
):
    """403 auditado, com o motivo (ex.: 'own_sem_vinculo', 'sem_permissao_exportar')."""
    await audit.insert_audit(
        audit_entry(
            request,
            access.user,
            "dashboard.access_denied",
            org_id=access.org_id,
            target_type="dashboard",
            target_id=access.dashboard_key,
            metadata={"org": access.org_slug, "unit": access.unit_code, "reason": reason},
        )
    )
    raise HTTPException(status.HTTP_403_FORBIDDEN, detail=detail)


async def _prepare(
    request: Request,
    access: DashboardAccess,
    refs: SourceRefsRepo,
    sources: SourceFactory,
    audit: AccessRepo,
    today: Today,
    start: date | None,
    end: date | None,
) -> tuple[DashboardModule, DashboardContext]:
    """O que dados e exportação têm em comum: módulo, escopo, período, filtros e unidade -> fonte."""
    module = DASHBOARDS.get(access.dashboard_key)
    if module is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="Este dashboard ainda não tem dados na V2"
        )

    # 'own' precisa saber qual funcionário da fonte é a pessoa; sem esse vínculo, nega (nunca mostra dos outros).
    if access.scope != "all":
        await _deny(request, audit, access, "own_sem_vinculo", "Sem acesso")

    day = today(access.timezone)
    try:
        period = resolve_period(start, end, day)
        query = request.query_params
        filters = parse_filters(module.filters, {k: query.getlist(k) for k in module.filters})
    except DashboardInputError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from None

    picked = module.pick_source(access.source_refs)
    if picked is None:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"A unidade {access.unit_code} ainda não está ligada à fonte {module.source_label}",
        )
    source_db, unit_ref = picked

    own_ref = None
    if module.own_rows_only and not access.can_see_commission:
        own_ref = await refs.member_ref(access.user.user_id, access.org_id, source_db)

    extra_refs = {
        db: ref for db in module.extra_queries if (ref := access.source_refs.get(db)) is not None
    }
    source = sources(source_db)
    extra_sources = {db: sources(db) for db in extra_refs}
    ctx = DashboardContext(
        source=source,
        source_db=source_db,
        unit_ref=unit_ref,
        period=period,
        filters=filters,
        can_see_commission=access.can_see_commission,
        own_ref=own_ref,
        extra_sources=extra_sources,
        extra_refs=extra_refs,
        remember=_remember(
            get_result_memo(request),
            # Tudo que muda o cálculo além do que o módulo põe na chave (período, filtros...). O dia
            # entra porque a cópia da v1 usa "hoje" (vencidas, vencem hoje).
            base=(
                module.key,
                source_db,
                unit_ref,
                tuple(sorted(extra_refs.items())),
                access.can_see_commission,
                own_ref,
                day,
            ),
            fetchers={source_db: source, **extra_sources},
        ),
    )
    return module, ctx


def get_result_memo(request: Request) -> ResultMemo | None:
    """A memória dos cálculos criada no lifespan (None = a app subiu sem ela, como nos testes)."""
    return getattr(request.app.state, "result_memo", None)


def _remember(memo: ResultMemo | None, base: tuple, fetchers: dict) -> Remember:
    """ctx.remember deste pedido: a chave do módulo + `base`, lendo as versões nas fontes do pedido."""
    if memo is None:
        return run_now

    async def remember(key: Hashable, compute: Compute) -> Any:
        return await memo.get_or_compute((base, key), fetchers, compute)

    return remember


async def _run[T](module: DashboardModule, work: Awaitable[T]) -> T:
    """Roda o cálculo do módulo: 501 se ainda não ligado, 423 se a fonte foi desligada na tela,
    503 se a fonte estiver fora do ar."""
    try:
        return await work
    except NotReady as exc:
        raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, detail=str(exc)) from None
    except DashboardInputError as exc:  # filtro que só o cálculo valida (ex.: situacao_processo)
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from None
    except SourceDisabled:
        # Não é falha de integração: a TI da LexGroup desligou a fonte (a tela mostra "Fonte desligada").
        raise HTTPException(
            status.HTTP_423_LOCKED,
            detail=f"A fonte {module.source_label} está desligada",
        ) from None
    except SourceUnavailable:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"A fonte {module.source_label} está indisponível no momento",
        ) from None


@router.get("/{dashboard_key}")
async def dashboard_data(
    request: Request,
    access: Annotated[DashboardAccess, Depends(require_dashboard)],
    refs: Annotated[SourceRefsRepo, Depends(get_source_refs_repo)],
    sources: Annotated[SourceFactory, Depends(get_source_factory)],
    audit: Annotated[AccessRepo, Depends(get_repo)],
    today: Annotated[Today, Depends(get_today)],
    start: Annotated[date | None, Query(alias="from")] = None,
    end: Annotated[date | None, Query(alias="to")] = None,
):
    """Dados de um dashboard numa unidade: período, filtros da v1, `meta` e o que o módulo calcula."""
    module, ctx = await _prepare(request, access, refs, sources, audit, today, start, end)
    # O cálculo prende o único worker. Se a pessoa já desistiu (trocou o filtro de novo e o front
    # cancelou esta busca), não calcula: a requisição que vale não fica esperando na fila.
    if await request.is_disconnected():
        return Response(status_code=CLIENT_CLOSED_REQUEST)
    # Mesmo período e filtros sobre os mesmos dados (ex.: voltar a um filtro, outra pessoa na mesma tela):
    # o resultado guardado, sem calcular de novo (app/result_memo.py).
    data = await _run(
        module,
        ctx.remember(("resposta", ctx.period, filters_key(ctx.filters)), lambda: module.build(ctx)),
    )

    meta = {
        "unit": access.unit_code,
        "from": ctx.period.start.isoformat(),
        "to": ctx.period.end.isoformat(),
        "source": module.label_of(ctx.source_db),
        "synced_at": _iso(ctx.source.synced_at()),  # quando o dado veio do banco (cache)
        "timezone": access.timezone,
    }
    # Quem não gere a unidade vê só a própria comissão: precisa saber quem a pessoa é na fonte.
    own_ref = None
    if module.commission_fields and not access.can_see_commission:
        own_ref = await refs.member_ref(access.user.user_id, access.org_id, ctx.source_db)
    return shape_response(module, data, meta, access.can_see_commission, own_ref)


@router.get("/{dashboard_key}/export")
async def dashboard_export(
    request: Request,
    access: Annotated[DashboardAccess, Depends(require_dashboard)],
    refs: Annotated[SourceRefsRepo, Depends(get_source_refs_repo)],
    sources: Annotated[SourceFactory, Depends(get_source_factory)],
    audit: Annotated[AccessRepo, Depends(get_repo)],
    today: Annotated[Today, Depends(get_today)],
    start: Annotated[date | None, Query(alias="from")] = None,
    end: Annotated[date | None, Query(alias="to")] = None,
    format: Annotated[str | None, Query()] = None,
    campos: Annotated[list[str] | None, Query()] = None,
    relatorio: Annotated[str | None, Query()] = None,
) -> Response:
    """Relatório do dashboard (CSV ou XLSX), como na v1, com o período e os filtros pedidos. Sempre auditado.

    `relatorio` escolhe um dos outros relatórios do dashboard (ex.: as Atividades dos Acordos); as opções dele
    (ex.: ?criterio=saida) vêm na URL e chegam ao cálculo em ctx.export_options."""
    module, ctx = await _prepare(request, access, refs, sources, audit, today, start, end)
    try:
        spec = export.pick_report(module, relatorio)
    except export.ExportError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from None
    if spec is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Este dashboard não tem exportação")
    if not access.can_export:
        await _deny(request, audit, access, "sem_permissao_exportar", "Sem permissão para exportar")
    try:
        fmt = export.pick_format(format)
        slugs = export.pick_fields(spec, campos or [])
        opcoes = export.pick_options(spec, dict(request.query_params))
    except export.ExportError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from None
    ctx = replace(ctx, export_options=opcoes)

    rows = await _run(module, spec.rows(ctx))
    headers, data = export.table(spec, slugs, rows)
    if fmt == "xlsx":
        aba = spec.sheet_name_por_unidade.get(ctx.unit_ref, spec.sheet_name)
        body = (
            export.to_xlsx_por_aba(spec, slugs, rows, aba)
            if spec.sheet_by
            else export.to_xlsx(headers, data, aba)
        )
    else:
        body = export.to_csv(headers, data)

    await audit.insert_audit(
        audit_entry(
            request,
            access.user,
            "dashboard.export",
            org_id=access.org_id,
            target_type="dashboard",
            target_id=access.dashboard_key,
            metadata={
                "org": access.org_slug,
                "unit": access.unit_code,
                "from": ctx.period.start.isoformat(),
                "to": ctx.period.end.isoformat(),
                "filters": {k: v for k, v in ctx.filters.items() if v},
                "campos": slugs,
                "format": fmt,
                **({"relatorio": relatorio} if relatorio else {}),
                **({"opcoes": opcoes} if opcoes else {}),
                "rows": len(rows),
            },
        )
    )
    name = export.filename(
        access.dashboard_key, access.unit_code, fmt, [relatorio or "", *opcoes.values()]
    )
    return Response(
        content=body,
        media_type=export.FORMATS[fmt],
        headers={"Content-Disposition": f'attachment; filename="{name}"'},
    )
