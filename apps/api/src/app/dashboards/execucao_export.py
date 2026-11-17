"""Exportação da Execução Condenação e da Execução Acordos (NG, LA e RJ), como na v1.

v1: GET /execucao/export (NG), /execucao_LA/export, /execucao_RJ/export, /execucao_acordos_{NG,LA,RJ}/export e
/execucao_acordos_{NG,LA,RJ}/atividades/export (dashboard_routes.py). Campos, rótulos, recortes e as linhas vêm
da cópia sem mudança em app/analyses/v1_dashboard_generico.py (gerar_generico.py --extra); os campos e rótulos
são os mesmos nas três unidades. Aqui só a ligação com a V2: a função de linhas da unidade, os filtros da página
e as escolhas da janela (ctx.export_options) nos mesmos parâmetros das rotas da v1.
"""

from collections.abc import Callable
from typing import Any

from app.analyses import v1_dashboard_generico as v1
from app.dashboards import generico_v1
from app.dashboards.base import DashboardContext, ExportOption, ExportSpec, NotReady

# O recorte da v1 (?criterio=): o mesmo dos cards de Indicadores e da lista "Execuções de Acordo".
RECORTE = ExportOption(
    key="criterio",
    label="Recorte",
    choices={
        "entrada": "Entradas no período",
        "saida": "Saídas no período",
        "total": "Total em execução agora",
    },
)
# A visão da seção Atividades (?view=), como o botão Concluídas / Por prazo.
VISAO_ATIVIDADES = ExportOption(
    key="view",
    label="Visão das atividades",
    choices={"concluidas": "Concluídas", "por_prazo": "Por prazo"},
)

# As funções de linhas da v1 por unidade (ref da unidade no LexFlow).
LINHAS_EXECUCAO = {
    "NG": v1._rows_execucao_filtradas,
    "LA": v1._rows_execucao_la_filtradas,
    "RJ": v1._rows_execucao_RJ_filtradas,
}
LINHAS_ACORDOS = {
    "NG": v1._rows_execucao_acordos_filtradas,
    "LA": v1._rows_execucao_acordos_LA_filtradas,
    "RJ": v1._rows_execucao_acordos_RJ_filtradas,
}
LINHAS_ATIVIDADES_ACORDOS = {
    "NG": v1._rows_execucao_acordos_atividades_filtradas,
    "LA": v1._rows_execucao_acordos_la_atividades_filtradas,
    "RJ": v1._rows_execucao_acordos_rj_atividades_filtradas,
}

for u in ("NG", "LA", "RJ"):
    assert tuple(RECORTE.choices) == getattr(v1, f"_CRITERIOS_EXPORT_EXECUCAO_{u}")
    assert tuple(RECORTE.choices) == getattr(v1, f"_CRITERIOS_EXPORT_EXECUCAO_ACORDOS_{u}")
    assert tuple(VISAO_ATIVIDADES.choices) == getattr(
        v1, f"_VIEWS_EXPORT_EXECUCAO_ACORDOS_ATIVIDADES_{u}"
    )
    for base in ("EXECUCAO", "EXECUCAO_ACORDOS", "EXECUCAO_ACORDOS_ATIVIDADES"):
        assert getattr(v1, f"_CAMPOS_EXPORT_{base}_{u}") == getattr(v1, f"_CAMPOS_EXPORT_{base}_NG")
        assert getattr(v1, f"_LABELS_EXPORT_{base}_{u}") == getattr(v1, f"_LABELS_EXPORT_{base}_NG")


def _da_unidade(
    ctx: DashboardContext, linhas: dict[str, Callable[..., Any]], nome: str
) -> Callable[..., Any]:
    fn = linhas.get(ctx.unit_ref)
    if fn is None:
        raise NotReady(f"A v1 não tem exportação de {nome} para esta unidade")
    return fn


def _lista(ctx: DashboardContext, chave: str) -> list[Any] | None:
    return list(ctx.filters.get(chave) or []) or None


def _um(ctx: DashboardContext, chave: str) -> Any:
    return next(iter(ctx.filters.get(chave) or []), None)


async def _linhas_execucao(ctx: DashboardContext) -> list[dict[str, Any]]:
    """= export_execucao / export_execucao_LA / export_execucao_rj da v1 (os mesmos filtros e o recorte)."""
    return await generico_v1.chamar_v1(
        ctx,
        v1,
        _da_unidade(ctx, LINHAS_EXECUCAO, "Execução Condenação"),
        ctx.period.start,
        ctx.period.end,
        _lista(ctx, "materia"),
        _lista(ctx, "subfase"),
        _um(ctx, "ano_ajuizamento_execucao"),
        criterio=ctx.export_options.get("criterio", "entrada"),
        uf=_lista(ctx, "uf"),
        comarca=_lista(ctx, "comarca"),
    )


async def _linhas_acordos(ctx: DashboardContext) -> list[dict[str, Any]]:
    """= export_execucao_acordos_{ng,la,rj} da v1 (os mesmos filtros e o recorte)."""
    return await generico_v1.chamar_v1(
        ctx,
        v1,
        _da_unidade(ctx, LINHAS_ACORDOS, "Execução Acordos"),
        ctx.period.start,
        ctx.period.end,
        _lista(ctx, "materia"),
        _lista(ctx, "subfase"),
        _um(ctx, "tipo_acao_execucao_acordos"),
        _lista(ctx, "uf"),
        criterio=ctx.export_options.get("criterio", "entrada"),
        comarca=_lista(ctx, "comarca"),
        ano_ajuizamento_execucao_acordos=_um(ctx, "ano_ajuizamento_execucao_acordos"),
    )


async def _linhas_atividades_acordos(ctx: DashboardContext) -> list[dict[str, Any]]:
    """= export_execucao_acordos_{ng,la,rj}_atividades da v1 (os filtros da seção Atividades e a visão)."""
    return await generico_v1.chamar_v1(
        ctx,
        v1,
        _da_unidade(ctx, LINHAS_ATIVIDADES_ACORDOS, "Atividades da Execução Acordos"),
        ctx.period.start,
        ctx.period.end,
        _lista(ctx, "funcionario_execucao_acordos"),
        _lista(ctx, "atividade_execucao_acordos"),
        _lista(ctx, "status_execucao_acordos"),
        _lista(ctx, "situacao_execucao_acordos"),
        ctx.export_options.get("view", "concluidas"),
    )


EXECUCAO = ExportSpec(
    fields=v1._CAMPOS_EXPORT_EXECUCAO_NG,
    labels=v1._LABELS_EXPORT_EXECUCAO_NG,
    sheet_name="Execução",
    sheet_name_por_unidade={"LA": "Execução LA"},
    rows=_linhas_execucao,
    options=(RECORTE,),
    title="Processos",
)

ACORDOS = ExportSpec(
    fields=v1._CAMPOS_EXPORT_EXECUCAO_ACORDOS_NG,
    labels=v1._LABELS_EXPORT_EXECUCAO_ACORDOS_NG,
    sheet_name="Execução Acordos",
    rows=_linhas_acordos,
    options=(RECORTE,),
    title="Processos",
)

ATIVIDADES_ACORDOS = ExportSpec(
    fields=v1._CAMPOS_EXPORT_EXECUCAO_ACORDOS_ATIVIDADES_NG,
    labels=v1._LABELS_EXPORT_EXECUCAO_ACORDOS_ATIVIDADES_NG,
    sheet_name="Atividades",
    rows=_linhas_atividades_acordos,
    options=(VISAO_ATIVIDADES,),
    title="Atividades",
)
