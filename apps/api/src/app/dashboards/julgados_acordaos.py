"""Julgados Acórdãos (LexFlow) — dashboards da v1 /julgados_acordaos_NG, _LA e _RJ, sem mudança.

O cálculo é a cópia da v1 em app/analyses/v1_dashboard_julgados.py, gerada por
`scripts/copiar_v1/gerar_generico.py --banco lexflow julgados_acordaos_NG julgados_acordaos_LA
julgados_acordaos_RJ`, mais os módulos app/analyses/{NG,LA,RJ}/julgados_acordao*.py. A query `julgados`
é uma só para os três escritórios (NG = 20, LA = 21, RJ = 27): o recorte é feito em Python, como na v1.

Como na página da v1, que buscava o dashboard duas vezes (com e sem período):
  * os gráficos "mês a mês" (procedentes, improcedentes e extintos) vêm do histórico todo;
  * as opções do filtro de matéria juntam o gráfico por matéria do período com o do histórico, que chega
    como `historico_julgados_acordao_por_materia_<unidade>`.

A exportação é a das rotas /julgados_acordaos_*/export da v1 (campos, filtros e período da página).
"""

from dataclasses import replace
from typing import Any

from app.analyses import v1_dashboard_julgados as copia
from app.analyses import v1_julgados_export as v1_export
from app.analyses.LA import julgados_acordao_LA as la
from app.analyses.NG import julgados_acordao as ng
from app.analyses.RJ import julgados_acordao_RJ as rj
from app.analyses.situacao_processo import _situacoes_processo_ctx, parse_situacoes_processo
from app.dashboards import dados_faltando, generico_v1
from app.dashboards.base import DashboardContext, DashboardInputError, ExportSpec, NotReady
from app.unit_scope import com_recorte

_FALTA = "Julgados Acórdãos não existe na v1 para esta unidade (só NG, LA e RJ)"
UNIDADES = ("NG", "LA", "RJ")

# Unidade -> (busca da v1, recorte do escritório, filtros interativos, status resultante dos embargos).
# Na v1 o RJ busca pela fetch_julgados_LA: é a mesma query `julgados`.
_POR_UNIDADE: dict[str, tuple[Any, Any, Any, Any]] = {
    "NG": (
        copia.fetch_julgados_NG,
        ng._base_julgados_NG,
        ng.filtrar_acordaos_julgados_NG,
        ng._get_resultado_embargos_acordao,
    ),
    "LA": (
        copia.fetch_julgados_LA,
        la._base_julgados_LA,
        la.filtrar_acordaos_julgados_LA,
        la._get_resultado_embargos_acordao,
    ),
    "RJ": (
        copia.fetch_julgados_LA,
        rj._base_julgados_RJ,
        rj.filtrar_acordaos_julgados_RJ,
        rj._get_resultado_embargos_acordao,
    ),
}

# Parâmetros dos filtros interativos, na ordem de _parse_julgados_acordao_filtros da v1.
_FILTROS = (
    "materia_julgados",
    "relator_julgados",
    "comarca_julgados",
    "competencia_julgados",
    "categoria_julgados",
    "uf_julgados",
    "motivo_extincao_julgados",
    "ano_ajuizamento_julgados",
    "resultado_embargos_julgados",
)


async def _processos(ctx: DashboardContext) -> list[dict[str, Any]]:
    """A query `julgados` da unidade, com o recorte de situação do processo dos filtros (como a v1)."""
    if ctx.unit_ref not in _POR_UNIDADE:
        raise NotReady(_FALTA)
    buscar = _POR_UNIDADE[ctx.unit_ref][0]
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

    return processos


def _filtros(ctx: DashboardContext) -> Any:
    """Os filtros interativos da página no formato da v1."""
    return copia._parse_julgados_acordao_filtros(*(ctx.filters.get(n) or None for n in _FILTROS))


async def export_rows(ctx: DashboardContext) -> list[dict[str, Any]]:
    """As linhas de /julgados_acordaos_<unidade>/export da v1, com os filtros e o período da página."""
    processos = await _processos(ctx)
    _, base, filtrar, resultado_embargos = _POR_UNIDADE[ctx.unit_ref]
    filtros = _filtros(ctx)
    rows = filtrar(base(processos), filtros)
    rows = v1_export._filtrar_rows_julgados_por_data(
        rows, "DATA_ACORDAO", ctx.period.start, ctx.period.end
    )
    rows = v1_export._anotar_resultado_embargos_export(rows, resultado_embargos)
    # Valor em reais como no CSV da v1 ("R$ 1.234,56"); o resto sai pelo formato padrão da V2.
    return [
        {
            **row,
            "VALOR_ACORDAO": v1_export._formatar_moeda_brl(
                v1_export._valor_moeda_julgados(row.get("VALOR_ACORDAO"))
            ),
        }
        for row in rows
    ]


# A faixa "Atenção" da v1 por unidade (histórico todo: a v1 passa from_date=None e to_date=None).
_DADOS_FALTANDO = {
    "NG": ng.get_julgados_acordao_dados_faltando_NG,
    "LA": la.get_julgados_acordao_dados_faltando_LA,
    "RJ": rj.get_julgados_acordao_dados_faltando_RJ,
}


async def campos_faltando_rows(ctx: DashboardContext) -> list[dict[str, Any]]:
    """V2: o relatório da faixa "Atenção" (uma aba por campo): os mesmos itens do modal, como a v1 os monta
    (filtros interativos da página, sem o período), com matéria, comarca e UF do processo."""
    processos = await _processos(ctx)
    filtrar = _POR_UNIDADE[ctx.unit_ref][2]
    filtrados = filtrar(processos, _filtros(ctx))
    itens = _DADOS_FALTANDO[ctx.unit_ref](filtrados, from_date=None, to_date=None)
    return dados_faltando.enriquecer(itens, filtrados)


MODULE = replace(
    generico_v1.modulo(
        key="julgados-acordaos",
        v1_por_unidade={u: f"julgados_acordaos_{u}" for u in UNIDADES},
        descricao_falta=_FALTA,
        copia=copia,
        historico=(
            *(
                f"julgados_acordao_{c}_por_mes_{u}"
                for u in UNIDADES
                for c in ("procedentes", "improcedentes", "extintos")
            ),
            # "destino=origem": a matéria do histórico com outro nome (a do período continua no campo da v1)
            *(
                f"historico_julgados_acordao_por_materia_{u}=julgados_acordao_por_materia_{u}"
                for u in UNIDADES
            ),
        ),
    ),
    export=ExportSpec(
        fields=v1_export._CAMPOS_EXPORT_JULGADOS_ACORDAO_NG,
        labels=v1_export._LABELS_EXPORT_JULGADOS_ACORDAO_NG,
        sheet_name="Julgados Acórdãos",
        rows=export_rows,
    ),
    export_reports={
        dados_faltando.RELATORIO: dados_faltando.relatorio(
            (
                "Relator",
                "Matéria",
                "Comarca",
                "Competência",
                "UF",
                "Valor do acórdão",
                "Data do acórdão (mérito lançado)",
                "Mérito do acórdão (data lançada)",
            ),
            campos_faltando_rows,
        ),
    },
)

# Só as linhas da unidade da tela nas queries que trazem todos os escritórios (app/unit_scope.py).
MODULE = replace(MODULE, unit_scoped=com_recorte(MODULE.queries))
