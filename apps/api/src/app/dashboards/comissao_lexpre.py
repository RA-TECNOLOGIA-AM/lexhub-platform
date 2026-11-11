"""Comissão Comercial (LexPre) — mesmo cálculo da v1 do Comercial (LexPre), com escopo próprio.

Na v1 a página Comissão Comercial não tem endpoint próprio: chama GET /comercial-lexpre com
escopo_proprio=true (lib/api.ts, getComercialLexpreNG({ escopoProprio: true })). Quem não é
Gestor/Desenvolvedor vê a página INTEIRA só com os próprios dados (todo KPI, gráfico e pool de
comissão), pelo atendente vinculado; sem vínculo, a página zera.

Na V2: o mesmo `build` do comercial_lexpre.py com escopo_proprio=True; "Gestor/Desenvolvedor" =
quem gere a unidade (ctx.can_see_commission) e o atendente vinculado = app.member_source_refs
(ctx.own_ref, preenchido pela casca porque o módulo declara own_rows_only).
"""

from app.dashboards import comercial_lexpre
from app.dashboards.base import DashboardContext, DashboardModule


async def build(ctx: DashboardContext) -> dict:
    return await comercial_lexpre.build(ctx, escopo_proprio=True)


MODULE = DashboardModule(
    key="comissao-lexpre",
    source_db="lexpre",
    source_label="LexPre",
    build=build,
    queries=comercial_lexpre.QUERIES,
    filters=comercial_lexpre.MODULE.filters,
    own_rows_only=True,
)
