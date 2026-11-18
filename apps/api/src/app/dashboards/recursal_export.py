"""Exportação e comissão do Recursal (NG, LA e RJ), como na v1.

Relatório Personalizado — v1: GET /recursal_{NG,LA,RJ}/export (dashboard_routes.py). Campos, rótulos, linhas e
valores vêm da cópia sem mudança em app/analyses/v1_dashboard_generico.py (gerar_generico.py --extra
export_recursal_*). Como na janela da v1, vão os filtros da página, menos "Extintos 2º grau" e, da seção Atividades,
o funcionário e a situação (a v1 só mandava atividade e status); sem período (a v1 só recortava pelas datas
escolhidas campo a campo, que a janela da V2 ainda não tem).

Comissão do setor Recursos — v1: GET /recursal_NG/comissao/export (só NG). Mesmo cálculo
(get_comissao_recursos_NG_por_funcionario: quantidade de Análise e Confecção, bônus da meta de qualidade e de zero
retrabalho, descontos por erro, com o detalhamento dos descontos); o PDF é montado no navegador, como as outras
comissões da V2.
"""

from typing import Any

from app.analyses import v1_dashboard_generico as v1
from app.analyses.NG import recurso_NG
from app.dashboards import generico_v1
from app.dashboards.base import DashboardContext, ExportSpec, NotReady

UNIDADES = ("NG", "LA", "RJ")

for _u in UNIDADES:
    assert getattr(v1, f"_CAMPOS_EXPORT_RECURSAL_{_u}") == v1._CAMPOS_EXPORT_RECURSAL_NG
    assert getattr(v1, f"_LABELS_EXPORT_RECURSAL_{_u}") == v1._LABELS_EXPORT_RECURSAL_NG


def _lista(ctx: DashboardContext, chave: str) -> list[Any] | None:
    valores = [str(v).strip() for v in ctx.filters.get(chave) or [] if str(v).strip()]
    return valores or None


def _ids(ctx: DashboardContext, chave: str) -> list[int] | None:
    valores = _lista(ctx, chave)
    return [int(v) for v in valores] if valores else None


async def _linhas(ctx: DashboardContext) -> list[dict[str, Any]]:
    """= export_recursal_{NG,LA,RJ} da v1 até as linhas, com cada campo já no valor do arquivo (slug -> valor)."""
    u = ctx.unit_ref
    if u not in UNIDADES:
        raise NotReady("A v1 não tem exportação do Recursal para esta unidade")
    sufixo = u.lower()
    filtros, filtros_atividades = v1._parse_recursal_la_filtros_completos(
        id_1g=_ids(ctx, "id_1g_recursal"),
        id_2g=_ids(ctx, "id_2g_recursal"),
        juiz=_lista(ctx, "juiz_recursal"),
        relator=_lista(ctx, "relator_recursal"),
        decisao=_lista(ctx, "decisao_recursal"),
        materia=_lista(ctx, "materia_recursal"),
        competencia=_lista(ctx, "competencia_recursal"),
        vara=_lista(ctx, "vara_recursal"),
        subfase=_lista(ctx, "subfase_recursal"),
        atividade_recursos=_lista(ctx, "atividade_recursos"),
        status_recursos=_lista(ctx, "status_recursos"),
    )

    async def calcular() -> list[dict[str, Any]]:
        linhas = await getattr(v1, f"_rows_recursal_{sufixo}_filtradas")(
            await getattr(v1, f"fetch_recursal_{u}")(), filtros, filtros_atividades, None, None
        )
        linhas = getattr(v1, f"_enriquecer_numero_processo_export_{sufixo}")(linhas)
        valor = getattr(v1, f"_valor_campo_export_recursal_{sufixo}")
        return [{s: valor(linha, s) for s in v1._CAMPOS_EXPORT_RECURSAL_NG} for linha in linhas]

    return await generico_v1.chamar_v1(ctx, v1, calcular)


PROCESSOS = ExportSpec(
    # As linhas já trazem o valor de cada campo (a v1 calculava alguns, como a decisão): slug -> slug.
    fields={s: s for s in v1._CAMPOS_EXPORT_RECURSAL_NG},
    labels=v1._LABELS_EXPORT_RECURSAL_NG,
    sheet_name="Relatório",
    rows=_linhas,
    title="Processos",
)


async def comissao(ctx: DashboardContext) -> dict[str, Any] | None:
    """A comissão do setor Recursos do período (só NG, como a v1), com o filtro de funcionário da página."""
    if ctx.unit_ref != "NG":
        return None

    async def calcular() -> dict[str, Any]:
        agendamentos = await v1.fetch_agendamentos_setor_recursos_NG()
        processos = await v1.fetch_recursal_NG()
        ini, fim = ctx.period.start, ctx.period.end
        qtd = recurso_NG.get_total_provimento_mensal_NG(processos, from_date=ini, to_date=fim)
        meta_atingida = qtd >= recurso_NG.META_PROVIMENTO_MENSAL_NG
        nomes = _lista(ctx, "funcionario_recursos")
        linhas, detalhes = recurso_NG.get_comissao_recursos_NG_por_funcionario(
            agendamentos,
            meta_atingida,
            from_date=ini,
            to_date=fim,
            funcionarios=frozenset(nomes) if nomes else None,
        )
        return {
            "linhas": linhas,
            "detalhes": detalhes,
            "meta_atingida": meta_atingida,
            "qtd_provimento": qtd,
            "meta": recurso_NG.META_PROVIMENTO_MENSAL_NG,
        }

    return await generico_v1.chamar_v1(ctx, v1, calcular)
