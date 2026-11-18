"""Julgados Sentenças (LexFlow) — dashboards da v1 /julgados_NG, _LA e _RJ, sem mudança.

O cálculo é a cópia da v1 em app/analyses/v1_dashboard_julgados_sentenca.py, gerada por
`scripts/copiar_v1/gerar_generico.py --banco lexflow julgados_NG julgados_LA julgados_RJ`, mais os módulos
app/analyses/{NG,LA,RJ}/julgados_sentenca*.py (os mesmos que os Julgados Acórdãos já usam). A query
`julgados` é uma só para os três escritórios (NG = 20, LA = 21, RJ = 27): o recorte é feito em Python.

Como na página da v1, que buscava o dashboard duas vezes (com e sem período):
  * os gráficos "mês a mês" (procedentes, improcedentes e extintos) vêm do histórico todo;
  * as opções do filtro de matéria juntam o gráfico por matéria do período com o do histórico, que chega
    como `historico_julgados_por_materia_<unidade>`.

A exportação é a das rotas /julgados_*/export da v1 (campos, filtros e período da página).
"""

from dataclasses import replace
from typing import Any

from app.analyses import v1_dashboard_julgados_sentenca as copia
from app.analyses import v1_julgados_export as v1_export
from app.analyses.LA import julgados_sentenca_LA as la
from app.analyses.NG import julgados_sentenca as ng
from app.analyses.RJ import julgados_sentenca_RJ as rj
from app.analyses.situacao_processo import _situacoes_processo_ctx, parse_situacoes_processo
from app.dashboards import generico_v1
from app.dashboards.base import DashboardContext, DashboardInputError, ExportSpec, NotReady

_FALTA = "Julgados Sentenças não existe na v1 para esta unidade (só NG, LA e RJ)"
UNIDADES = ("NG", "LA", "RJ")

# Unidade -> (busca da v1, recorte do escritório, parser dos filtros, filtros interativos, status resultante
# dos embargos). Na v1 o RJ busca pela fetch_julgados_LA: é a mesma query `julgados`.
_POR_UNIDADE: dict[str, tuple[Any, Any, Any, Any, Any]] = {
    "NG": (
        copia.fetch_julgados_NG,
        ng._base_julgados_NG,
        copia._parse_julgados_sentenca_filtros,
        ng.filtrar_sentencas_julgados_NG,
        ng._get_resultado_embargos_sentenca,
    ),
    "LA": (
        copia.fetch_julgados_LA,
        la._base_julgados_LA,
        copia._parse_julgados_sentenca_filtros_la,
        la.filtrar_sentencas_julgados_LA,
        la._get_resultado_embargos_sentenca,
    ),
    "RJ": (
        copia.fetch_julgados_LA,
        rj._base_julgados_RJ,
        copia._parse_julgados_sentenca_filtros_rj,
        rj.filtrar_sentencas_julgados_RJ,
        rj._get_resultado_embargos_sentenca,
    ),
}

# Parâmetros dos filtros interativos, na ordem de _parse_julgados_sentenca_filtros da v1.
_FILTROS = (
    "materia_julgados",
    "juiz_julgados",
    "comarca_julgados",
    "competencia_julgados",
    "categoria_julgados",
    "uf_julgados",
    "motivo_extincao_julgados",
    "ano_ajuizamento_julgados",
    "resultado_embargos_julgados",
)


async def export_rows(ctx: DashboardContext) -> list[dict[str, Any]]:
    """As linhas de /julgados_<unidade>/export da v1, com os filtros e o período da página."""
    if ctx.unit_ref not in _POR_UNIDADE:
        raise NotReady(_FALTA)
    buscar, base, parse, filtrar, resultado_embargos = _POR_UNIDADE[ctx.unit_ref]
    try:
        situacao = parse_situacoes_processo(ctx.filters.get(generico_v1.FILTRO_SITUACAO, []))
    except ValueError as exc:
        raise DashboardInputError(str(exc)) from None

    token_fonte = copia.usar_fonte(ctx.source)
    token_situacao = _situacoes_processo_ctx.set(situacao)
    try:
        processos = await buscar()
    finally:
        _situacoes_processo_ctx.reset(token_situacao)
        copia._fonte_ctx.reset(token_fonte)

    filtros = parse(*(ctx.filters.get(n) or None for n in _FILTROS))
    rows = filtrar(base(processos), filtros)
    rows = v1_export._filtrar_rows_julgados_por_data(
        rows, "DATA_SENTENCA", ctx.period.start, ctx.period.end
    )
    rows = v1_export._anotar_resultado_embargos_export(rows, resultado_embargos)
    # Valor em reais como no CSV da v1 ("R$ 1.234,56"); o resto sai pelo formato padrão da V2.
    return [
        {
            **row,
            "VALOR_SENTENCA": v1_export._formatar_moeda_brl(
                v1_export._valor_moeda_julgados(row.get("VALOR_SENTENCA"))
            ),
        }
        for row in rows
    ]


MODULE = replace(
    generico_v1.modulo(
        key="julgados-sentencas",
        v1_por_unidade={u: f"julgados_{u}" for u in UNIDADES},
        descricao_falta=_FALTA,
        copia=copia,
        historico=(
            *(
                f"julgados_sentenca_{c}_por_mes_{u}"
                for u in UNIDADES
                for c in ("procedentes", "improcedentes", "extintos")
            ),
            # "destino=origem": a matéria do histórico com outro nome (a do período continua no campo da v1)
            *(f"historico_julgados_por_materia_{u}=julgados_por_materia_{u}" for u in UNIDADES),
        ),
    ),
    export=ExportSpec(
        fields=v1_export._CAMPOS_EXPORT_JULGADOS_SENTENCA_NG,
        labels=v1_export._LABELS_EXPORT_JULGADOS_SENTENCA_NG,
        sheet_name="Julgados Sentenças",
        rows=export_rows,
    ),
)
