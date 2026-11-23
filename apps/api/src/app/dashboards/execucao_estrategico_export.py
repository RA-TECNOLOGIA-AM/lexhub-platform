"""Relatório do Execução Estratégico Geral (NG, LA e RJ), como o "Relatório" da página da v1.

v1: ExecucaoRelatorioPersonalizadoDialog (ExecucaoEstrategicoGeral{,LA,RJ}.tsx), que chamava as rotas
/execucao{,_LA,_RJ}/export (Condenação), /execucao_acordos_{NG,LA,RJ}/export (Acordos) ou
/execucao_geral{,_la,_rj}/export ("Os dois juntos": XLSX com uma aba de cada, CSV num .zip com um CSV de cada).
As linhas, campos e rótulos são os mesmos da Execução Condenação e da Execução Acordos (execucao_export.py, cópia
sem mudança da v1); aqui só o que a página do Estratégico tinha de próprio:

  * a origem: "Filtros ativos na Página" (matéria, subfase, ano de ajuizamento, UF e comarca da página) ou
    "Relatório personalizado" (do zero: só o período e o recorte);
  * o escopo: Condenação (o relatório principal), Acordos (?relatorio=acordos) ou os dois (?relatorio=ambos);
  * o recorte (entrada, saída ou total), o mesmo nas duas origens.
"""

from typing import Any

from app.analyses import v1_dashboard_generico as v1
from app.dashboards import export, generico_v1
from app.dashboards.base import DashboardContext, ExportOption, ExportPart, ExportSpec
from app.dashboards.execucao_export import LINHAS_ACORDOS, LINHAS_EXECUCAO, RECORTE, _da_unidade

ORIGEM = ExportOption(
    key="origem",
    label="Origem",
    choices={
        "pagina": "Filtros ativos na página",
        "personalizado": "Relatório personalizado",
    },
)
OPCOES = (ORIGEM, RECORTE)


def _filtros(ctx: DashboardContext) -> dict[str, list[Any]]:
    """Os filtros da página, ou nenhum no relatório personalizado (a v1 mandava null em todos)."""
    return {} if ctx.export_options.get("origem") == "personalizado" else ctx.filters


def _lista(filtros: dict[str, list[Any]], chave: str) -> list[Any] | None:
    return list(filtros.get(chave) or []) or None


def _um(filtros: dict[str, list[Any]], chave: str) -> Any:
    return next(iter(filtros.get(chave) or []), None)


async def _linhas_condenacao(ctx: DashboardContext) -> list[dict[str, Any]]:
    """= export_execucao{,_LA,_rj} da v1, com os filtros da página do Estratégico (ou nenhum)."""
    f = _filtros(ctx)
    return await generico_v1.chamar_v1(
        ctx,
        v1,
        _da_unidade(ctx, LINHAS_EXECUCAO, "Execução Condenação"),
        ctx.period.start,
        ctx.period.end,
        _lista(f, "materia"),
        _lista(f, "subfase"),
        _um(f, "ano_ajuizamento"),
        criterio=ctx.export_options.get("criterio", "entrada"),
        uf=_lista(f, "uf"),
        comarca=_lista(f, "comarca"),
    )


async def _linhas_acordos(ctx: DashboardContext) -> list[dict[str, Any]]:
    """= export_execucao_acordos_{ng,la,rj} da v1, com os filtros da página do Estratégico (ou nenhum).

    Sem o tipo de ação: a página do Estratégico não tem esse filtro (a v1 mandava None)."""
    f = _filtros(ctx)
    return await generico_v1.chamar_v1(
        ctx,
        v1,
        _da_unidade(ctx, LINHAS_ACORDOS, "Execução Acordos"),
        ctx.period.start,
        ctx.period.end,
        _lista(f, "materia"),
        _lista(f, "subfase"),
        None,
        _lista(f, "uf"),
        criterio=ctx.export_options.get("criterio", "entrada"),
        comarca=_lista(f, "comarca"),
        ano_ajuizamento_execucao_acordos=_um(f, "ano_ajuizamento"),
    )


CONDENACAO = ExportSpec(
    fields=v1._CAMPOS_EXPORT_EXECUCAO_NG,
    labels=v1._LABELS_EXPORT_EXECUCAO_NG,
    sheet_name="Execução Condenação",
    rows=_linhas_condenacao,
    options=OPCOES,
    title="Condenação",
)

ACORDOS = ExportSpec(
    fields=v1._CAMPOS_EXPORT_EXECUCAO_ACORDOS_NG,
    labels=v1._LABELS_EXPORT_EXECUCAO_ACORDOS_NG,
    sheet_name="Execução Acordos",
    rows=_linhas_acordos,
    options=OPCOES,
    title="Acordos",
)

# "Os dois juntos" (v1: /execucao_geral/export): as abas e os CSVs com os nomes da v1.
AMBOS = export.combined(
    (
        ExportPart("condenacao", "Execução Condenação", "execucao_condenacao.csv", CONDENACAO),
        ExportPart("acordos", "Execução Acordos", "execucao_acordos.csv", ACORDOS),
    ),
    sheet_name="Execução Geral",
    options=OPCOES,
    title="Condenação e Acordos",
)
