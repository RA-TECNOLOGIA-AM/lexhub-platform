"""Pendências Intermediárias (LexFlow) — as páginas da v1 NG/PendenciasIntermediarias_NG.tsx e
LA/PendenciasIntermediarias_LA.tsx (setor PENDÊNCIA(S) no LexFlow, área Jurídico).

v1: GET /pendencias_intermediarias_NG e /pendencias_intermediarias_LA, copiadas sem mudança em
app/analyses/v1_dashboard_intermediarias.py (scripts/copiar_v1/gerar_generico.py --banco lexflow
pendencias_intermediarias_NG pendencias_intermediarias_LA), com app/analyses/{NG,LA}/pendencias_intermediarias_*.py.

Como a página da v1, duas chamadas da mesma rota:
  * a do período, com os filtros da página (funcionário e atividade): cards, dilação, distribuições e a lista;
  * a sem datas e sem esses filtros: os gráficos "mês a mês" das concluídas e a média por funcionário
    (o filtro de funcionário nesses gráficos é aplicado no navegador, somando as séries de cada um, como na v1).
Só os campos que a página usa, sempre com os nomes da NG (os do LA seguem generico_v1.nome_na_unidade), e sem as
chaves nulas dos itens das listas (os pontos da v1 trazem uma dúzia de campos sempre vazios).

Na v1 os filtros do NG têm sufixo (funcionario_intermediarias_ng) e os do LA não; aqui os dois usam o mesmo nome
(funcionario_intermediarias, atividade_intermediarias), mapeado para o parâmetro da rota de cada unidade.

RJ (V2, 19/11/2026): a v1 não tem a página no RJ. O RJ usa a rota do NG sem mudança (o mesmo cálculo, o mesmo setor
PENDÊNCIA e a mesma atividade de dilação, "MANIFESTAÇÃO - ELABORAR DILAÇÃO"), lendo as queries do RJ
(escritório 27, em source_queries.py): a fonte troca agendamentos_*_intermediarias_NG pelas _RJ.
"""

from dataclasses import replace
from datetime import date
from typing import Any

from app.analyses import v1_dashboard_intermediarias as v1
from app.dashboards import generico_v1
from app.dashboards.base import (
    DashboardContext,
    DashboardModule,
    ExportOption,
    ExportSpec,
    NotReady,
)

UNIDADES = ("NG", "LA", "RJ")

# A rota da v1 de cada unidade: o RJ não tem a dele e usa a do NG.
ROTA = {"NG": "NG", "LA": "LA", "RJ": "NG"}

# As queries do NG que a rota busca -> as do RJ (mesmo SQL, escritório 27).
QUERIES_RJ = {
    "agendamentos_setor_intermediarias_NG": "agendamentos_setor_intermediarias_RJ",
    "agendamentos_dilacao_prazo_intermediarias_NG": "agendamentos_dilacao_prazo_intermediarias_RJ",
}
assert set(QUERIES_RJ) == set(v1.QUERIES_POR_DASHBOARD["pendencias_intermediarias_NG"])


class _FonteRJ:
    """A fonte do pedido, devolvendo as linhas das queries do RJ quando a rota do NG pede as dela (`mapa`: query
    do NG -> a do RJ; padrão, as das Pendências Intermediárias)."""

    def __init__(self, fonte: Any, mapa: dict[str, str] | None = None) -> None:
        self._fonte = fonte
        self._mapa = QUERIES_RJ if mapa is None else mapa

    async def fetch(self, query_name: str) -> list[dict[str, Any]]:
        return await self._fonte.fetch(self._mapa.get(query_name, query_name))

    def synced_at(self) -> float | None:
        return self._fonte.synced_at()


def _na_rota(ctx: DashboardContext) -> tuple[DashboardContext, str]:
    """O contexto e a rota da v1 da unidade (no RJ, a do NG com a fonte das queries do RJ)."""
    rota = ROTA.get(ctx.unit_ref)
    if rota is None:
        raise NotReady("Pendências Intermediárias existe na NG, no LA e no RJ")
    if ctx.unit_ref == "RJ":
        ctx = replace(ctx, source=_FonteRJ(ctx.source))
    return ctx, rota


# Os filtros da página (nome na V2) e o parâmetro da rota da v1 em cada unidade.
FILTROS = ("funcionario_intermediarias", "atividade_intermediarias")


def _parametro(filtro: str, unidade: str) -> str:
    return f"{filtro}_ng" if unidade == "NG" else filtro


CAMPOS_PERIODO_STATS = (
    "total_atividades_intermediarias_NG",
    "atividades_intermediarias_em_andamento_NG",
    "atividades_intermediarias_vencidas_NG",
    "atividades_intermediarias_vencem_hoje_NG",
    "atividades_intermediarias_concluidas_NG",
    "total_por_prazo_intermediarias_NG",
    "por_prazo_em_andamento_intermediarias_NG",
    "por_prazo_vencidas_intermediarias_NG",
    "por_prazo_vencem_hoje_intermediarias_NG",
    "por_prazo_concluidas_intermediarias_NG",
    "dilacoes_intermediarias_total_encerrados_NG",
    "dilacoes_intermediarias_count_NG",
    "dilacoes_intermediarias_taxa_NG",
    "dilacoes_intermediarias_faixa_NG",
)
CAMPOS_PERIODO_LISTAS = (
    "intermediarias_processos_por_atividade_NG",
    "intermediarias_processos_por_atividade_por_prazo_NG",
    "intermediarias_demandas_por_funcionario_NG",
    "intermediarias_demandas_por_funcionario_por_prazo_NG",
    "intermediarias_atividades_lista_NG",
    "intermediarias_por_prazo_lista_NG",
    "intermediarias_atividades_lista_filtros_opcoes_NG",
    "intermediarias_por_prazo_lista_filtros_opcoes_NG",
    "dilacoes_intermediarias_por_funcionario_NG",
)
CAMPOS_HISTORICO = (
    "intermediarias_concluidas_por_mes_NG",
    "intermediarias_concluidas_por_dia_NG",
    "intermediarias_concluidas_por_dia_por_funcionario_NG",
    "intermediarias_concluidas_por_prazo_por_mes_NG",
    "intermediarias_concluidas_por_prazo_por_dia_NG",
    "intermediarias_concluidas_por_prazo_por_dia_por_funcionario_NG",
    "media_intermediarias_concluidas_por_funcionario_NG",
    "media_intermediarias_concluidas_por_prazo_por_funcionario_NG",
)


def _sem_nulos(valor: Any) -> Any:
    """Listas e dicionários de listas sem as chaves nulas de cada item."""
    if isinstance(valor, list):
        return [
            {k: x for k, x in item.items() if x is not None} if isinstance(item, dict) else item
            for item in valor
        ]
    if isinstance(valor, dict) and all(isinstance(x, list) for x in valor.values()):
        return {k: _sem_nulos(x) for k, x in valor.items()}
    return valor


def _campo(resposta: dict[str, Any], nome_ng: str, unidade: str) -> Any:
    nome = generico_v1.nome_na_unidade(nome_ng, unidade)
    if resposta.get(nome) is not None:
        return resposta[nome]
    return (resposta.get("stats") or {}).get(nome)


def filtros_da_rota(ctx: DashboardContext) -> dict[str, list[str] | None]:
    """Os filtros da página nos parâmetros da rota da v1 da unidade (lista ou None)."""
    saida: dict[str, list[str] | None] = {}
    rota = ROTA.get(ctx.unit_ref, ctx.unit_ref)
    for filtro in FILTROS:
        valores = [str(v).strip() for v in ctx.filters.get(filtro) or [] if str(v).strip()]
        saida[_parametro(filtro, rota)] = valores or None
    return saida


async def _chamar(
    ctx: DashboardContext, de: date | None, ate: date | None, filtros: dict[str, Any]
) -> dict[str, Any]:
    ctx, rota = _na_rota(ctx)
    fn = v1.HANDLERS[f"pendencias_intermediarias_{rota}"]
    todos = dict.fromkeys(generico_v1._parametros(fn))
    todos.update(filtros)
    resposta = await generico_v1.chamar_v1(ctx, v1, fn, from_date=de, to_date=ate, **todos)
    return resposta.model_dump()


async def build(ctx: DashboardContext) -> dict:
    u = ROTA.get(ctx.unit_ref, ctx.unit_ref)  # de que rota da v1 os nomes vêm (o RJ lê os do NG)
    periodo = await _chamar(ctx, ctx.period.start, ctx.period.end, filtros_da_rota(ctx))
    historico = await _chamar(ctx, None, None, {})
    return {
        "unidade": ctx.unit_ref,
        "stats": {c: _campo(periodo, c, u) for c in CAMPOS_PERIODO_STATS},
        **{c: _sem_nulos(_campo(periodo, c, u)) for c in CAMPOS_PERIODO_LISTAS},
        **{c: _sem_nulos(_campo(historico, c, u)) for c in CAMPOS_HISTORICO},
    }


# ---------- Exportação: v1 GET /pendencias_intermediarias_{NG,LA}/export (o RJ, pela do NG) ----------

# A visão da lista exportada (?visao= da v1), a mesma que está ativa na página.
VISAO = ExportOption(
    key="visao",
    label="Lista",
    choices={"por_prazo": "Por prazo", "concluidas": "Concluídas"},
)

# Uma coluna por cabeçalho da v1 (_HEADERS_EXPORT_INTERMEDIARIAS), na mesma ordem.
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
assert [label for _, label in COLUNAS] == v1._HEADERS_EXPORT_INTERMEDIARIAS


async def export_rows(ctx: DashboardContext) -> list[dict[str, Any]]:
    """= export_pendencias_intermediarias_{NG,LA} da v1: a lista da visão escolhida, com os filtros e o período
    da página, nas colunas e valores de _linhas_export_intermediarias."""
    filtros = filtros_da_rota(ctx)
    ctx, u = _na_rota(ctx)
    fn = v1.HANDLERS[f"pendencias_intermediarias_{u}"]
    todos = dict.fromkeys(generico_v1._parametros(fn))
    todos.update(filtros)
    resposta = await generico_v1.chamar_v1(
        ctx, v1, fn, from_date=ctx.period.start, to_date=ctx.period.end, **todos
    )
    visao = ctx.export_options.get("visao", "por_prazo")
    lista = getattr(
        resposta,
        f"intermediarias_por_prazo_lista_{u}"
        if visao == "por_prazo"
        else f"intermediarias_atividades_lista_{u}",
    )
    linhas = v1._linhas_export_intermediarias(lista or [])
    return [dict(zip((slug for slug, _ in COLUNAS), linha, strict=True)) for linha in linhas]


EXPORT = ExportSpec(
    fields={slug: slug for slug, _ in COLUNAS},
    labels=dict(COLUNAS),
    sheet_name="Pendências Intermediárias",
    rows=export_rows,
    options=(VISAO,),
)


MODULE = DashboardModule(
    key="pendencias-intermediarias",
    source_db="lexflow",
    source_label="LexFlow",
    build=build,
    filters={**{f: str for f in FILTROS}, generico_v1.FILTRO_SITUACAO: str},
    export=EXPORT,
    queries=(
        *dict.fromkeys(
            q
            for u in ("NG", "LA")
            for q in v1.QUERIES_POR_DASHBOARD[f"pendencias_intermediarias_{u}"]
        ),
        *QUERIES_RJ.values(),
    ),
)
