"""Emendas e Manifestações (LexFlow) — as páginas da v1 NG/EmendasManifestacoes_NG.tsx e
LA/EmendasManifestacoes_LA.tsx (área Jurídico). NG: setor MANIFESTAÇÃO (com UF); LA: setor INTERMEDIÁRIAS.

v1: GET /emendas_manifestacoes_NG e /emendas_manifestacoes_LA, copiadas sem mudança em
app/analyses/v1_dashboard_emendas.py (scripts/copiar_v1/gerar_generico.py --banco lexflow emendas_manifestacoes_NG
emendas_manifestacoes_LA), com app/analyses/{NG,LA}/emendas_manifestacoes_*.py.

Como a página da v1 (e como as Pendências Intermediárias), duas chamadas da mesma rota:
  * a do período, com os filtros da página (funcionário, atividade e, no NG, UF): cards, comissão (agenda cumprida,
    peças e valores por funcionário), distribuições, médias por funcionário e a lista;
  * a sem datas e sem esses filtros: só os gráficos "mês a mês" das concluídas (o filtro de funcionário nesses
    gráficos é aplicado no navegador, somando as séries de cada um, como na v1).
Só os campos que a página usa, sempre com os nomes da NG, e sem as chaves nulas dos itens das listas.

RJ (V2, 19/11/2026): a v1 não tem a página no RJ. O RJ usa a rota do NG sem mudança (o mesmo cálculo, o mesmo
setor MANIFESTAÇÃO com UF, a mesma regra de comissão: R$ 1,00 por manifestação e R$ 0,50 por dilação), lendo a
query do RJ (escritório 27, em source_queries.py), como as Pendências Intermediárias no RJ. Única diferença
(decisão de 19/11/2026): no RJ, "MANIFESTAR DILAÇÃO DE PRAZO" também conta como dilação (DILACAO_EXTRA_RJ).
"""

from dataclasses import replace
from datetime import date
from typing import Any

from app.analyses import v1_dashboard_emendas as v1
from app.analyses.NG import emendas_manifestacoes_NG as emendas_ng
from app.dashboards import generico_v1
from app.dashboards.base import (
    DashboardContext,
    DashboardModule,
    ExportOption,
    ExportSpec,
    NotReady,
)
from app.dashboards.pendencias_intermediarias import _campo, _FonteRJ, _sem_nulos

UNIDADES = ("NG", "LA", "RJ")

# A rota da v1 de cada unidade: o RJ não tem a dele e usa a do NG.
ROTA = {"NG": "NG", "LA": "LA", "RJ": "NG"}

# A query do NG que a rota busca -> a do RJ (mesmo SQL, escritório 27).
QUERIES_RJ = {
    "agendamentos_setor_emendas_manifestacoes_NG": "agendamentos_setor_emendas_manifestacoes_RJ"
}
assert set(QUERIES_RJ) == set(v1.QUERIES_POR_DASHBOARD["emendas_manifestacoes_NG"])

# No RJ a dilação também é pedida como "MANIFESTAR DILAÇÃO DE PRAZO" (no NG só existe ELABORAR DILAÇÃO).
DILACAO_EXTRA_RJ = frozenset({"MANIFESTAR DILAÇÃO DE PRAZO"})

# Os filtros da página: o mesmo nome da rota da v1 nas duas unidades; a UF só existe no NG.
FILTROS = (
    "funcionario_emendas_manifestacoes",
    "atividade_emendas_manifestacoes",
    "uf_emendas_manifestacoes",
)

CAMPOS_PERIODO_STATS = (
    "total_atividades_emendas_manifestacoes_NG",
    "atividades_emendas_manifestacoes_em_andamento_NG",
    "atividades_emendas_manifestacoes_vencidas_NG",
    "atividades_emendas_manifestacoes_vencem_hoje_NG",
    "atividades_emendas_manifestacoes_concluidas_NG",
    "total_por_prazo_emendas_manifestacoes_NG",
    "por_prazo_em_andamento_emendas_manifestacoes_NG",
    "por_prazo_vencidas_emendas_manifestacoes_NG",
    "por_prazo_vencem_hoje_emendas_manifestacoes_NG",
    "por_prazo_concluidas_emendas_manifestacoes_NG",
    # só NG
    "comparativo_qtd_manifestacoes_emendas_manifestacoes_NG",
    "comparativo_qtd_dilacoes_emendas_manifestacoes_NG",
    "emendas_manifestacoes_uf_opcoes_NG",
)
CAMPOS_PERIODO_LISTAS = (
    "emendas_manifestacoes_processos_por_atividade_NG",
    "emendas_manifestacoes_processos_por_atividade_por_prazo_NG",
    "emendas_manifestacoes_demandas_por_funcionario_NG",
    "emendas_manifestacoes_demandas_por_funcionario_por_prazo_NG",
    "emendas_manifestacoes_atividades_lista_NG",
    "emendas_manifestacoes_por_prazo_lista_NG",
    "emendas_manifestacoes_atividades_lista_filtros_opcoes_NG",
    "emendas_manifestacoes_por_prazo_lista_filtros_opcoes_NG",
    "media_emendas_manifestacoes_concluidas_por_funcionario_NG",
    "media_emendas_manifestacoes_concluidas_por_prazo_por_funcionario_NG",
    "emendas_manifestacoes_comissionamento_por_funcionario_NG",
)
CAMPOS_HISTORICO = (
    "emendas_manifestacoes_concluidas_por_mes_NG",
    "emendas_manifestacoes_concluidas_por_dia_NG",
    "emendas_manifestacoes_concluidas_por_dia_por_funcionario_NG",
    "emendas_manifestacoes_concluidas_por_prazo_por_mes_NG",
    "emendas_manifestacoes_concluidas_por_prazo_por_dia_NG",
    "emendas_manifestacoes_concluidas_por_prazo_por_dia_por_funcionario_NG",
)


def _rota(ctx: DashboardContext) -> Any:
    rota = ROTA.get(ctx.unit_ref)
    if rota is None:
        raise NotReady("Emendas e Manifestações existe na NG, no LA e no RJ")
    return v1.HANDLERS[f"emendas_manifestacoes_{rota}"]


def _na_rota(ctx: DashboardContext) -> DashboardContext:
    """No RJ, o contexto com a fonte que troca a query do NG pela do RJ."""
    if ctx.unit_ref == "RJ":
        return replace(ctx, source=_FonteRJ(ctx.source, QUERIES_RJ))
    return ctx


def filtros_da_rota(ctx: DashboardContext) -> dict[str, list[str] | None]:
    """Os filtros da página que a rota da unidade aceita (lista ou None); a UF é só do NG."""
    params = generico_v1._parametros(_rota(ctx))
    saida: dict[str, list[str] | None] = {}
    for filtro in FILTROS:
        if filtro in params:
            valores = [str(v).strip() for v in ctx.filters.get(filtro) or [] if str(v).strip()]
            saida[filtro] = valores or None
    return saida


async def _chamar(
    ctx: DashboardContext, de: date | None, ate: date | None, filtros: dict[str, Any]
) -> Any:
    fn = _rota(ctx)
    todos = dict.fromkeys(generico_v1._parametros(fn))
    todos.update(filtros)
    extra = DILACAO_EXTRA_RJ if ctx.unit_ref == "RJ" else frozenset()
    token = emendas_ng._dilacao_extra_ctx.set(extra)
    try:
        return await generico_v1.chamar_v1(
            _na_rota(ctx), v1, fn, from_date=de, to_date=ate, **todos
        )
    finally:
        emendas_ng._dilacao_extra_ctx.reset(token)


async def build(ctx: DashboardContext) -> dict:
    u = ROTA.get(ctx.unit_ref, ctx.unit_ref)  # de que rota da v1 os nomes vêm (o RJ lê os do NG)
    periodo = (
        await _chamar(ctx, ctx.period.start, ctx.period.end, filtros_da_rota(ctx))
    ).model_dump()
    historico = (await _chamar(ctx, None, None, {})).model_dump()
    return {
        "unidade": ctx.unit_ref,
        "stats": {c: _campo(periodo, c, u) for c in CAMPOS_PERIODO_STATS},
        **{c: _sem_nulos(_campo(periodo, c, u)) for c in CAMPOS_PERIODO_LISTAS},
        **{c: _sem_nulos(_campo(historico, c, u)) for c in CAMPOS_HISTORICO},
    }


# ---------- Exportação: v1 GET /emendas_manifestacoes_{NG,LA}/export ----------

VISAO = ExportOption(
    key="visao",
    label="Lista",
    choices={"por_prazo": "Por prazo", "concluidas": "Concluídas"},
)

# Uma coluna por cabeçalho da v1 (_HEADERS_EXPORT_EMENDAS_MANIFESTACOES), na mesma ordem (as mesmas das Pendências).
COLUNAS = (
    ("id", "ID"),
    ("numero_processo", "Nº Processo"),
    ("descricao", "Descrição"),
    ("operacao", "Operação"),
    ("status", "Status"),
    ("responsavel", "Responsável"),
    ("encerrado_pelo_responsavel", "Encerrado pelo responsável"),
    ("setor_atividade", "Setor / Atividade"),
    ("atividade", "Atividade"),
    ("criado_em", "Criado em"),
    ("prazo", "Prazo"),
    ("em_andamento", "Em andamento"),
    ("vencida", "Vencida"),
    ("vence_hoje", "Vence hoje"),
    ("concluida", "Concluída"),
)
assert [label for _, label in COLUNAS] == v1._HEADERS_EXPORT_EMENDAS_MANIFESTACOES


async def export_rows(ctx: DashboardContext) -> list[dict[str, Any]]:
    """= export_emendas_manifestacoes_{NG,LA} da v1: a lista da visão escolhida, com os filtros e o período da
    página, nas colunas e valores de _linhas_export_emendas_manifestacoes (o RJ, pela rota do NG)."""
    u = ROTA.get(ctx.unit_ref, ctx.unit_ref)
    resposta = await _chamar(ctx, ctx.period.start, ctx.period.end, filtros_da_rota(ctx))
    visao = ctx.export_options.get("visao", "por_prazo")
    lista = getattr(
        resposta,
        f"emendas_manifestacoes_por_prazo_lista_{u}"
        if visao == "por_prazo"
        else f"emendas_manifestacoes_atividades_lista_{u}",
    )
    linhas = v1._linhas_export_emendas_manifestacoes(lista or [])
    return [dict(zip((slug for slug, _ in COLUNAS), linha, strict=True)) for linha in linhas]


EXPORT = ExportSpec(
    fields={slug: slug for slug, _ in COLUNAS},
    labels=dict(COLUNAS),
    sheet_name="Emendas e Manifestações",
    rows=export_rows,
    options=(VISAO,),
)


MODULE = DashboardModule(
    key="emendas-manifestacoes",
    source_db="lexflow",
    source_label="LexFlow",
    build=build,
    filters={**{f: str for f in FILTROS}, generico_v1.FILTRO_SITUACAO: str},
    export=EXPORT,
    queries=(
        *dict.fromkeys(
            q for u in ("NG", "LA") for q in v1.QUERIES_POR_DASHBOARD[f"emendas_manifestacoes_{u}"]
        ),
        *QUERIES_RJ.values(),
    ),
)
