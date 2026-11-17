"""Financeiro Estratégico (Financeiro) — a página da v1 (FinanceiroEstrategicoNG.tsx), sem mudar o cálculo.

Na v1, quatro rotas (/financeiro_estrategico_<NG|LA>, /conversao, /previsao e /clientes_pendentes); aqui, um
dashboard só, com as quatro partes na mesma resposta:

    reflexo_financeiro   seções "Reflexo Financeiro", "Reflexo de Ajuizamento" e "Evolução" (período e filtros
                         da página) + o valor protocolado do LexFlow e o "% Julgados Procedentes"
    conversao            seção "Conversão" (os seletores de ano dela: conv_ano_ajuizamento e conv_ano_financeiro,
                         + origem e matéria da página)
    previsao             seção "Previsão" (a base inteira, sem filtros)
    clientes_pendentes   o modal do card "Clientes Pendentes" (ano e mês do TED: pend_ano e pend_mes, + os
                         filtros da página)

Fontes: a planilha do financeiro da unidade (aba REPASSES CLIENTES; app/sheets.py) e o valor de causa ajuizado
no LexFlow (query valor_causa_ajuizado_lexflow_<NG|LA>; DashboardModule.extra_queries). O cálculo da planilha é o
da v1, copiado sem mudança em app/analyses/sheets/financeiro_NG.py (o mesmo para NG e LA: muda a planilha e as
regras de FINANCEIRO_ESTRATEGICO_CONFIG); o do LexFlow é o das rotas da v1 (dashboard_routes.py), copiado abaixo.
"""

import asyncio
from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Any

from app import sheets
from app.analyses.sheets.financeiro_NG import (
    _normalizar_materia as _normalizar_materia_financeiro,
)
from app.analyses.sheets.financeiro_NG import (
    _receita_por_materia_pizza as _pizza_por_materia_financeiro,
)
from app.analyses.sheets.financeiro_NG import (
    _variacao_vs_mes_anterior as _variacao_vs_mes_anterior_financeiro,
)
from app.analyses.sheets.financeiro_NG import (
    get_financeiro_NG_clientes_pendentes,
    get_financeiro_NG_conversao,
    get_financeiro_NG_previsao,
    get_financeiro_NG_reflexo_financeiro,
)
from app.dashboards.base import AltSource, DashboardContext, DashboardModule
from app.utils import parse_date_from_db, resolver_periodo_comparativo

ABA = "REPASSES CLIENTES"
ROTULO = "Planilha do financeiro + LexFlow"
LEXFLOW = "lexflow"
QUERY_AJUIZADO = {"NG": "valor_causa_ajuizado_lexflow_NG", "LA": "valor_causa_ajuizado_lexflow_LA"}
ANO_SEM_DATA_AJUIZAMENTO = "(Em branco)"  # v1: dashboard_routes.ANO_SEM_DATA_AJUIZAMENTO

Ajuizado = list[tuple[date | None, int, float, str]]


def _escritorio(ctx: DashboardContext) -> str:
    """NG lê a planilha da NG; a LA (sem ela), a da LA (alt_sources)."""
    return "LA" if ctx.source_db == "sheets_financeiro_la" else "NG"


# --- Camada das rotas da v1 (dashboard_routes.py), copiada: só a busca vem do ctx ------------------------


async def _valor_causa_ajuizado_lexflow(ctx: DashboardContext, escritorio: str) -> Ajuizado:
    """v1 _valor_causa_ajuizado_lexflow: `(data de ajuizamento, quantidade, valor de causa, matéria)` por dia e
    matéria — lexflow, escritório do dashboard (NG = 20, LA = 21) sem RJ, ANP = dano moral. Data `None` =
    processo sem distribuição; matéria com o mesmo rótulo normalizado das pizzas da planilha."""
    fonte = ctx.extra_sources.get(LEXFLOW)
    if fonte is None:  # unidade sem o LexFlow ligado: como banco fora do ar
        from app.sources import SourceUnavailable

        raise SourceUnavailable(LEXFLOW)
    rows = await fonte.fetch(QUERY_AJUIZADO[escritorio])
    return [
        (
            parse_date_from_db(r["DATA_AJUIZAMENTO"]) if r.get("DATA_AJUIZAMENTO") else None,
            int(r.get("QUANTIDADE") or 0),
            float(r.get("VALOR_CAUSA") or 0),
            _normalizar_materia_financeiro(r.get("MATERIA")),
        )
        for r in rows
    ]


def _build_financeiro_valor_protocolado(
    dias: Ajuizado, from_date: date, to_date: date
) -> dict[str, Any]:
    """v1 _build_financeiro_valor_protocolado: valor de causa ajuizado no período, pela data de distribuição
    do lexflow, e o mesmo recorte do mês anterior (`resolver_periodo_comparativo`)."""
    inicio, fim, inicio_ant, fim_ant = resolver_periodo_comparativo(from_date, to_date)

    def _soma(a: date, b: date) -> tuple[float, int]:
        sel = [(q, v) for d, q, v, _ in dias if d is not None and a <= d <= b]
        return round(sum(v for _, v in sel), 2), sum(q for q, _ in sel)

    valor, quantidade = _soma(inicio, fim)
    valor_anterior, quantidade_anterior = _soma(inicio_ant, fim_ant)

    por_materia: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"quantidade": 0, "valor": Decimal(0)}
    )
    for d, q, v, materia in dias:
        if d is not None and inicio <= d <= fim:
            por_materia[materia]["quantidade"] += q
            por_materia[materia]["valor"] += Decimal(str(v))
    return {
        "valor": valor,
        "valor_anterior": valor_anterior,
        "comparativo": _variacao_vs_mes_anterior_financeiro(valor, valor_anterior),
        "quantidade": quantidade,
        "quantidade_anterior": quantidade_anterior,
        "por_materia": _pizza_por_materia_financeiro(dict(por_materia)),
    }


def _valor_causa_ajuizado_por_ano(dias: Ajuizado) -> dict[str, tuple[float, int]]:
    """v1 _valor_causa_ajuizado_por_ano: `{ano: (valor de causa, quantidade)}` ajuizado no histórico inteiro,
    pelo ano da distribuição no lexflow ("(Em branco)" = sem distribuição)."""
    por_ano: dict[str, list[float]] = defaultdict(lambda: [0.0, 0])
    for d, q, v, _ in dias:
        acc = por_ano[str(d.year) if d else ANO_SEM_DATA_AJUIZAMENTO]
        acc[0] += v
        acc[1] += q
    return {ano: (round(v, 2), int(q)) for ano, (v, q) in por_ano.items()}


def _soma_anos(por_ano: dict[str, tuple[float, int]], anos: list[str] | None) -> tuple[float, int]:
    """v1 _soma_anos: soma valor e quantidade dos anos selecionados (lista vazia/None = todos)."""
    alvo = {str(a).strip() for a in (anos or []) if str(a).strip()}
    sel = [vq for ano, vq in por_ano.items() if not alvo or ano in alvo]
    return round(sum(v for v, _ in sel), 2), sum(q for _, q in sel)


async def _reflexo(ctx: DashboardContext, escritorio: str, dias: Ajuizado) -> dict[str, Any]:
    """v1 _financeiro_estrategico_dashboard: o reflexo da planilha + o valor protocolado do LexFlow e o
    "% Julgados Procedentes" (entradas do Reflexo de Ajuizamento ÷ processos protocolados)."""
    f = ctx.filters
    inicio_atual, fim_atual, _, _ = resolver_periodo_comparativo(ctx.period.start, ctx.period.end)
    reflexo = await get_financeiro_NG_reflexo_financeiro(
        from_date=inicio_atual,
        to_date=fim_atual,
        origens=f.get("origem") or None,
        materias=f.get("materia") or None,
        anos_ajuizamento=f.get("ano_ajuizamento") or None,
        escritorio=escritorio,
    )
    valor_protocolado = _build_financeiro_valor_protocolado(dias, inicio_atual, fim_atual)
    reflexo["valor_protocolado"] = valor_protocolado
    ajuiz = reflexo["reflexo_ajuizamento"]

    def _pct(entradas: int, protocolados: int) -> float:
        return round(entradas / protocolados * 100, 2) if protocolados else 0.0

    pct_atual = _pct(ajuiz["total_entradas"]["valor"], valor_protocolado["quantidade"])
    pct_anterior = _pct(
        ajuiz["total_entradas"]["valor_anterior"], valor_protocolado["quantidade_anterior"]
    )
    ajuiz["percentual_procedentes"] = {
        "valor": pct_atual,
        "valor_anterior": pct_anterior,
        "comparativo": _variacao_vs_mes_anterior_financeiro(pct_atual, pct_anterior),
    }
    return reflexo


async def _conversao(ctx: DashboardContext, escritorio: str, dias: Ajuizado) -> dict[str, Any]:
    """v1 _financeiro_estrategico_conversao (medida RECEITA_CONVERSAO do Power BI): receita da planilha nos
    anos marcados; Valor de Causa Ajuizado do lexflow nos anos de Data Ajuizamento marcados."""
    f = ctx.filters
    anos_ajuiz = f.get("conv_ano_ajuizamento") or None
    payload = await get_financeiro_NG_conversao(
        anos_ajuizamento=anos_ajuiz,
        anos_financeiro=f.get("conv_ano_financeiro") or None,
        origens=f.get("origem") or None,
        materias=f.get("materia") or None,
        escritorio=escritorio,
    )
    valor_ajuizado, quantidade_ajuizada = _soma_anos(
        _valor_causa_ajuizado_por_ano(dias), anos_ajuiz
    )
    percentual = round(payload["receita"] / valor_ajuizado * 100, 2) if valor_ajuizado > 0 else 0.0
    return {
        **payload,
        "valor_causa_ajuizado": {"valor": valor_ajuizado, "quantidade": quantidade_ajuizada},
        "percentual_conversao": percentual,
    }


async def _previsao(escritorio: str, dias: Ajuizado) -> dict[str, Any]:
    """v1 _financeiro_estrategico_previsao: 4 cenários de receita do próximo ano, com a base inteira."""
    ajuizado_por_ano = {
        int(ano): valor
        for ano, (valor, _) in _valor_causa_ajuizado_por_ano(dias).items()
        if ano.isdigit()
    }
    return await get_financeiro_NG_previsao(
        ajuizado_por_ano=ajuizado_por_ano, escritorio=escritorio
    )


async def _clientes_pendentes(ctx: DashboardContext, escritorio: str) -> dict[str, Any]:
    """v1 _financeiro_estrategico_clientes_pendentes: o modal do card (réplica do "Controle de Clientes")."""
    f = ctx.filters
    return await get_financeiro_NG_clientes_pendentes(
        anos=f.get("pend_ano") or None,
        meses=f.get("pend_mes") or None,
        origens=f.get("origem") or None,
        materias=f.get("materia") or None,
        anos_ajuizamento=f.get("ano_ajuizamento") or None,
        escritorio=escritorio,
    )


async def build(ctx: DashboardContext) -> dict:
    escritorio = _escritorio(ctx)
    token = sheets.usar_fonte(ctx.source)
    try:
        dias = await _valor_causa_ajuizado_lexflow(ctx, escritorio)
        reflexo, conversao, previsao, pendentes = await asyncio.gather(
            _reflexo(ctx, escritorio, dias),
            _conversao(ctx, escritorio, dias),
            _previsao(escritorio, dias),
            _clientes_pendentes(ctx, escritorio),
        )
    finally:
        sheets.soltar_fonte(token)
    return {
        "escritorio": escritorio,
        "reflexo_financeiro": reflexo,
        "conversao": conversao,
        "previsao": previsao,
        "clientes_pendentes": pendentes,
    }


MODULE = DashboardModule(
    key="financeiro-estrategico",
    source_db="sheets_financeiro_ng",
    source_label=ROTULO,
    build=build,
    # Os filtros da página (os da v1) e os seletores próprios da Conversão e do modal de Clientes Pendentes.
    filters={
        "origem": str,
        "materia": str,
        "ano_ajuizamento": str,
        "conv_ano_ajuizamento": str,
        "conv_ano_financeiro": str,
        "pend_ano": str,
        "pend_mes": int,
    },
    queries=(ABA,),
    alt_sources={"sheets_financeiro_la": AltSource(ROTULO, (ABA,))},
    extra_queries={LEXFLOW: tuple(QUERY_AJUIZADO.values())},
)
