"""Exportação da Execução Condenação e da Execução Acordos (NG), como na v1.

v1: GET /execucao/export, /execucao_acordos_NG/export e /execucao_acordos_NG/atividades/export
(dashboard_routes.py). Campos, rótulos, recortes e as linhas vêm da cópia sem mudança em
app/analyses/v1_dashboard_generico.py (gerar_generico.py --extra). Aqui só a ligação com a V2: os filtros da
página e as escolhas da janela (ctx.export_options) entram nos mesmos parâmetros das rotas da v1.
"""

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

assert (
    tuple(RECORTE.choices)
    == v1._CRITERIOS_EXPORT_EXECUCAO_NG
    == v1._CRITERIOS_EXPORT_EXECUCAO_ACORDOS_NG
)
assert tuple(VISAO_ATIVIDADES.choices) == v1._VIEWS_EXPORT_EXECUCAO_ACORDOS_ATIVIDADES_NG


def _so_ng(ctx: DashboardContext, nome: str) -> None:
    # A v1 tem exportações próprias para LA e RJ (outras rotas e nomes); por enquanto a V2 só porta a da NG.
    if ctx.unit_ref != "NG":
        raise NotReady(f"A exportação de {nome} desta unidade ainda não foi migrada (só a da NG)")


def _lista(ctx: DashboardContext, chave: str) -> list[Any] | None:
    return list(ctx.filters.get(chave) or []) or None


def _um(ctx: DashboardContext, chave: str) -> Any:
    return next(iter(ctx.filters.get(chave) or []), None)


async def _linhas_execucao(ctx: DashboardContext) -> list[dict[str, Any]]:
    """= export_execucao da v1 (os mesmos filtros e o recorte)."""
    _so_ng(ctx, "Execução Condenação")
    return await generico_v1.chamar_v1(
        ctx,
        v1,
        v1._rows_execucao_filtradas,
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
    """= export_execucao_acordos_ng da v1 (os mesmos filtros e o recorte)."""
    _so_ng(ctx, "Execução Acordos")
    return await generico_v1.chamar_v1(
        ctx,
        v1,
        v1._rows_execucao_acordos_filtradas,
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
    """= export_execucao_acordos_ng_atividades da v1 (os filtros da seção Atividades e a visão)."""
    _so_ng(ctx, "Atividades da Execução Acordos")
    return await generico_v1.chamar_v1(
        ctx,
        v1,
        v1._rows_execucao_acordos_atividades_filtradas,
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
