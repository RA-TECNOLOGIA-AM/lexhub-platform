"""Reajuizamentos do LexPre (demandas.reajuizamento = true) em cards separados nos setores.

A query principal dos setores (log_setor_demanda_lexpre_NG) exclui os reajuizamentos: eles não entram em
nenhum total nem comissão. Para mostrá-los, cada setor roda o PRÓPRIO cálculo uma segunda vez trocando o log
pelo log só dos reajuizamentos (log_setor_demanda_lexpre_reajuizamento_NG) e copia alguns números dessa
rodada para campos `*_reajuizamento` da resposta. A regra é a mesma do setor; comissão, listas e gráficos da
segunda rodada são descartados. A segunda rodada não lê o banco legado (extra_sources vazio): o reajuizamento
do legado, quando há, vem pelo caminho do legado de cada setor.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import replace
from typing import Any

from app.dashboards.base import DashboardContext

QUERY_LOG = "log_setor_demanda_lexpre_NG"
QUERY_REAJUIZAMENTO = "log_setor_demanda_lexpre_reajuizamento_NG"


class _SoReajuizamento:
    """Fonte que entrega o log dos reajuizamentos no lugar do log dos setores; o resto passa direto."""

    def __init__(self, inner: Any):
        self._inner = inner

    async def fetch(self, query_name: str) -> list[dict[str, Any]]:
        return await self._inner.fetch(QUERY_REAJUIZAMENTO if query_name == QUERY_LOG else query_name)

    def synced_at(self) -> float | None:
        return self._inner.synced_at()


def rodada_de_reajuizamento(ctx: DashboardContext) -> bool:
    """Esta chamada já é a segunda rodada (evita rodar de novo dentro dela)."""
    return isinstance(ctx.source, _SoReajuizamento)


async def calcular_reajuizamento(
    build: Callable[[DashboardContext], Awaitable[dict]], ctx: DashboardContext
) -> dict[str, Any]:
    """`stats` do cálculo do setor só com os reajuizamentos (mesmo período e filtros, sem legado)."""
    sub = replace(ctx, source=_SoReajuizamento(ctx.source), extra_sources={}, extra_refs={})
    return (await build(sub)).get("stats") or {}


def total(stats: dict[str, Any], campo: str) -> int:
    """Número de um card: `{"total": n}` ou `n`."""
    v = stats.get(campo)
    if isinstance(v, dict):
        v = v.get("total")
    return int(v or 0)


async def acrescentar_reajuizamento(
    build: Callable[[DashboardContext], Awaitable[dict]],
    ctx: DashboardContext,
    corpo: dict[str, Any],
    campos: dict[str, str],
) -> None:
    """Põe em `corpo["stats"]` os cards de reajuizamento: `campos` = {campo na resposta: card do setor}.

    Soma ao que já estiver no campo (o reajuizamento do legado NG/RJ, quando a página o mistura).
    Na segunda rodada não faz nada.
    """
    if rodada_de_reajuizamento(ctx):
        return
    reaj = await calcular_reajuizamento(build, ctx)
    stats = corpo.setdefault("stats", {})
    for campo, card in campos.items():
        stats[campo] = int(stats.get(campo) or 0) + total(reaj, card)
