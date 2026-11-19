"""Réplicas (LexFlow) — as páginas da v1 NG/Replicas_NG.tsx e LA/Replicas_LA.tsx (área Jurídico; setor RÉPLICA no
NG e RÉPLICAS no LA).

v1: GET /replicas_NG e /replicas_LA, copiadas sem mudança em app/analyses/v1_dashboard_replicas.py
(scripts/copiar_v1/gerar_generico.py --banco lexflow replicas_NG replicas_LA), com
app/analyses/{NG,LA}/replicas_*.py. Única troca na cópia: o nome da função da rota do NG (na v1 era o mesmo da do
LA; ver a nota "V2:" em v1_dashboard_replicas.py).

Como a página da v1 (e como as Pendências Intermediárias), duas chamadas da mesma rota:
  * a do período, com os filtros da página (funcionário e atividade): cards, taxa de procedência (1G) dos processos
    com réplica, distribuições e a lista;
  * a sem datas e sem esses filtros: os gráficos "mês a mês" das concluídas e a média por funcionário.
Só os campos que a página usa, sempre com os nomes da NG, e sem as chaves nulas dos itens das listas. A v1 não tem
exportação de Réplicas; a comissão (só LA, R$ 1,50 por réplica concluída) sai das demandas por funcionário, no front.

Na v1 os filtros do NG têm sufixo (funcionario_replicas_ng) e os do LA não; aqui os dois usam o mesmo nome
(funcionario_replicas, atividade_replicas), mapeado para o parâmetro da rota de cada unidade.

RJ (V2, 19/11/2026): a v1 não tem a página no RJ. O RJ usa a rota do NG sem mudança (o mesmo cálculo, o mesmo setor
RÉPLICA, a taxa de procedência pela atividade ELABORAR RÉPLICA e sem comissão), lendo as queries do RJ (escritório
27, em source_queries.py), como as Pendências Intermediárias e as Emendas e Manifestações no RJ.
"""

from dataclasses import replace
from datetime import date
from typing import Any

from app.analyses import v1_dashboard_replicas as v1
from app.dashboards import generico_v1
from app.dashboards.base import DashboardContext, DashboardModule, NotReady
from app.dashboards.pendencias_intermediarias import _campo, _FonteRJ, _sem_nulos

UNIDADES = ("NG", "LA", "RJ")

# A rota da v1 de cada unidade: o RJ não tem a dele e usa a do NG.
ROTA = {"NG": "NG", "LA": "LA", "RJ": "NG"}

# As queries do NG que a rota busca -> as do RJ (mesmo SQL, escritório 27).
QUERIES_RJ = {
    "agendamentos_setor_replicas_NG": "agendamentos_setor_replicas_RJ",
    "processos_status_1g_replicas_NG": "processos_status_1g_replicas_RJ",
}
assert set(QUERIES_RJ) == set(v1.QUERIES_POR_DASHBOARD["replicas_NG"])

FILTROS = ("funcionario_replicas", "atividade_replicas")


def _parametro(filtro: str, unidade: str) -> str:
    return f"{filtro}_ng" if unidade == "NG" else filtro


CAMPOS_PERIODO_STATS = (
    "total_atividades_replicas_NG",
    "atividades_replicas_em_andamento_NG",
    "atividades_replicas_vencidas_NG",
    "atividades_replicas_vencem_hoje_NG",
    "atividades_replicas_concluidas_NG",
    "total_por_prazo_replicas_NG",
    "por_prazo_em_andamento_replicas_NG",
    "por_prazo_vencidas_replicas_NG",
    "por_prazo_vencem_hoje_replicas_NG",
    "por_prazo_concluidas_replicas_NG",
    "replicas_procedencia_total_processos_NG",
    "replicas_procedencia_total_decididos_NG",
    "replicas_procedencia_procedentes_NG",
    "replicas_procedencia_pendentes_NG",
    "replicas_taxa_procedencia_NG",
)
CAMPOS_PERIODO_LISTAS = (
    "replicas_processos_por_atividade_NG",
    "replicas_processos_por_atividade_por_prazo_NG",
    "replicas_demandas_por_funcionario_NG",
    "replicas_demandas_por_funcionario_por_prazo_NG",
    "replicas_atividades_lista_NG",
    "replicas_por_prazo_lista_NG",
    "replicas_atividades_lista_filtros_opcoes_NG",
    "replicas_por_prazo_lista_filtros_opcoes_NG",
)
CAMPOS_HISTORICO = (
    "replicas_concluidas_por_mes_NG",
    "replicas_concluidas_por_dia_NG",
    "replicas_concluidas_por_dia_por_funcionario_NG",
    "replicas_concluidas_por_prazo_por_mes_NG",
    "replicas_concluidas_por_prazo_por_dia_NG",
    "replicas_concluidas_por_prazo_por_dia_por_funcionario_NG",
    "media_replicas_concluidas_por_funcionario_NG",
    "media_replicas_concluidas_por_prazo_por_funcionario_NG",
)


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
    rota = ROTA.get(ctx.unit_ref)
    if rota is None:
        raise NotReady("Réplicas existe na NG, no LA e no RJ")
    if ctx.unit_ref == "RJ":
        ctx = replace(ctx, source=_FonteRJ(ctx.source, QUERIES_RJ))
    fn = v1.HANDLERS[f"replicas_{rota}"]
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


MODULE = DashboardModule(
    key="replicas",
    source_db="lexflow",
    source_label="LexFlow",
    build=build,
    filters={**{f: str for f in FILTROS}, generico_v1.FILTRO_SITUACAO: str},
    queries=(
        *dict.fromkeys(q for u in ("NG", "LA") for q in v1.QUERIES_POR_DASHBOARD[f"replicas_{u}"]),
        *QUERIES_RJ.values(),
    ),
)
