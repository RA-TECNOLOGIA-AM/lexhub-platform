"""Publicações (LexFlow, NG/LA/RJ) — as páginas da v1 NG/PublicacoesNG.tsx, LA/PublicacoesLA.tsx e RJ/PublicacoesRJ.tsx.

A v1 chamava /publicacoes_<u> três vezes: no período com os filtros (quase tudo da página), sem período e sem filtros
(só os nomes dos leitores, para as opções do filtro) e sem período com os filtros (dois números de um texto de ajuda,
que já vêm iguais na chamada do período). Aqui a API faz as duas primeiras (a rota copiada sem mudança em
app/analyses/v1_dashboard_generico.py) e devolve só os campos usados, sempre com os nomes da NG
(generico_v1.nome_na_unidade), para o front ser um só.

Filtros: os da v1 com o sufixo _publicacoes (leitor e matéria com vários valores; documento, tribunal, órgão e os do
agendamento com um só, como os cliques nos gráficos da v1) e a situação do processo.
"""

from typing import Any

from app.analyses import v1_dashboard_generico as v1
from app.dashboards import generico_v1
from app.dashboards.base import DashboardContext, DashboardModule, NotReady

UNIDADES = ("NG", "LA", "RJ")

# Filtro da v1 -> se aceita vários valores.
FILTROS = {
    "leitor": True,
    "materia": True,
    "documento": False,
    "tribunal": False,
    "orgao": False,
    "atividade_agendamento": False,
    "setor_agendamento": False,
    "status_agendamento": False,
}

STATS = (
    "publicacoes_recebidas_periodo_NG",
    "publicacoes_recebidas_hoje_NG",
    "publicacoes_tratadas_periodo_NG",
    "publicacoes_pendentes_NG",
    "media_tempo_tratamento_publicacoes_NG",
    "publicacoes_pendentes_zeradas_no_periodo_NG",
    "dia_referencia_publicacoes_NG",
    "publicacoes_tratadas_ultimo_dia_NG",
    "publicacoes_recebidas_dia_referencia_NG",
    "publicacoes_cumpridas_mesmo_dia_dia_referencia_NG",
    "pct_tratadas_mesmo_dia_publicacoes_NG",
    "publicacoes_com_agendamento_apos_finalizacao_NG",
    "publicacoes_sem_agendamento_apos_finalizacao_NG",
    "publicacoes_com_data_disponibilizacao_NG",
    "publicacoes_cumpridas_mesmo_dia_chegada_NG",
)
LISTAS = (
    "publicacoes_por_materia_NG",
    "publicacoes_por_tipo_documento_NG",
    "publicacoes_por_tribunal_NG",
    "publicacoes_por_orgao_NG",
    "publicacoes_agendamento_apos_finalizacao_por_atividade_NG",
    "publicacoes_agendamento_apos_finalizacao_por_setor_NG",
    "publicacoes_cumprido_por_leitor_NG",
    "publicacoes_pendentes_por_leitor_NG",
    "publicacoes_recebidas_por_dia_NG",
    "publicacoes_tratadas_por_dia_NG",
    "publicacoes_visualizadas_por_dia_NG",
    "publicacoes_pendentes_por_dias_atraso_NG",
    "publicacoes_lista_NG",
)
COMISSAO = "comissionamento_publicacoes_NG_por_funcionario"


def _nome(c: str, u: str) -> str:
    # A comissão tem a unidade no meio (comissionamento_publicacoes_LA_por_funcionario).
    if c == COMISSAO:
        return f"comissionamento_publicacoes_{u}_por_funcionario"
    return generico_v1.nome_na_unidade(c, u)


def _sem_vazios(lista: Any) -> Any:
    """Linhas sem os campos null (o modelo de ponto da v1 manda uma dúzia sempre vazios; a lista é grande)."""
    if not isinstance(lista, list):
        return lista
    return [
        {k: x for k, x in i.items() if x is not None} if isinstance(i, dict) else i for i in lista
    ]


def filtros_v1(ctx: DashboardContext) -> dict[str, Any]:
    """Os filtros do pedido nos parâmetros da rota da v1 (lista ou um valor)."""
    saida: dict[str, Any] = {}
    for nome, varios in FILTROS.items():
        valores = [
            str(v).strip() for v in ctx.filters.get(f"{nome}_publicacoes") or [] if str(v).strip()
        ]
        saida[nome] = (valores or None) if varios else next(iter(valores), None)
    return saida


async def build(ctx: DashboardContext) -> dict:
    u = ctx.unit_ref
    if u not in UNIDADES:
        raise NotReady("Publicações existe na NG, no LA e no RJ (como na v1)")
    rota = v1.HANDLERS[f"publicacoes_{u}"]

    async def chamar(de, ate, **filtros: Any) -> dict[str, Any]:
        todos = dict.fromkeys(generico_v1._parametros(rota))
        todos.update(filtros)
        resposta = await generico_v1.chamar_v1(ctx, v1, rota, from_date=de, to_date=ate, **todos)
        return resposta.model_dump()

    periodo = await chamar(ctx.period.start, ctx.period.end, **filtros_v1(ctx))
    stats = periodo.get("stats") or {}
    corpo: dict[str, Any] = {
        "stats": {c: stats.get(_nome(c, u)) for c in STATS},
        **{c: _sem_vazios(periodo.get(_nome(c, u))) for c in LISTAS},
    }
    # Os leitores de todo o histórico, sem filtro (as opções do filtro Leitor da v1).
    catalogo = await chamar(None, None)
    leitores = {
        str(p.get("name") or "").strip()
        for c in ("publicacoes_cumprido_por_leitor_NG", "publicacoes_pendentes_por_leitor_NG")
        for p in catalogo.get(_nome(c, u)) or []
        if isinstance(p, dict)
    }
    corpo["leitores"] = sorted(n for n in leitores if n)
    # Comissão (R$ 0,20 por certa, R$ 0,50 por errada): só para quem vê a comissão de todos.
    corpo["comissao"] = (
        _sem_vazios(periodo.get(_nome(COMISSAO, u))) if ctx.can_see_commission else None
    )
    corpo["unidade"] = u
    return corpo


MODULE = DashboardModule(
    key="publicacoes",
    source_db="lexflow",
    source_label="LexFlow",
    build=build,
    filters={**{f"{n}_publicacoes": str for n in FILTROS}, "situacao_processo": str},
    queries=tuple(
        dict.fromkeys(q for u in UNIDADES for q in v1.QUERIES_POR_DASHBOARD[f"publicacoes_{u}"])
    ),
)
