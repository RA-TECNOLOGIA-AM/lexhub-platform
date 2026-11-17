"""Meta anual (Financeiro) — a página "Meta Anual" da v1 (rotas /meta_anual_NG e /meta_anual_LA), sem mudar o
cálculo.

Fonte: a planilha do financeiro de cada unidade no Google Sheets (aba REPASSES CLIENTES; app/sheets.py), a
mesma da v1: NG em `sheets_financeiro_ng`, LA em `sheets_financeiro_la` (a unidade lê a planilha a que está
ligada: app.unit_source_refs). O cálculo é o da v1, copiado sem mudança em app/analyses/sheets/financeiro_NG.py
e financeiro_LA.py (get_financeiro_*_faturamento_trimestral_meta): a mesma lógica, cada um com as suas metas.
Faturamento (honorários + sucumbência, pela DATA DO TED) por trimestre e acumulado no ano, contra as metas
Triste, Base, Avançada e Super (anuais e por trimestre), e a análise preditiva. Só a entrada muda:

    v1                                  aqui
    year (padrão 2026)              ->  o ano do fim do período (ctx.period.end)
    as_of (padrão hoje)             ->  o fim do período (padrão: hoje, no fuso da unidade)
    compare_year (padrão year - 1)  ->  igual (year - 1)

Como as rotas da v1, a zona projetada "ABAIXO_TRISTE" vira "ENTRADA" (_normalize_meta_anual_*_payload).
"""

from typing import Any

from app import sheets
from app.analyses.sheets.financeiro_LA import get_financeiro_LA_faturamento_trimestral_meta
from app.analyses.sheets.financeiro_NG import get_financeiro_NG_faturamento_trimestral_meta
from app.dashboards.base import AltSource, DashboardContext, DashboardModule

ABA = "REPASSES CLIENTES"
ROTULO = "Planilha do financeiro"

# Planilha (fonte) -> o cálculo da v1 daquela unidade.
CALCULO = {
    "sheets_financeiro_ng": get_financeiro_NG_faturamento_trimestral_meta,
    "sheets_financeiro_la": get_financeiro_LA_faturamento_trimestral_meta,
}


def _normalizar(payload: dict[str, Any]) -> dict[str, Any]:
    """v1 (_normalize_meta_anual_ng_payload / _la_payload): abaixo da Triste a projeção é "ENTRADA"."""
    projecao = (payload.get("predicao") or {}).get("projecao_fim_ano")
    if isinstance(projecao, dict) and projecao.get("zona_projetada") == "ABAIXO_TRISTE":
        projecao["zona_projetada"] = "ENTRADA"
    return payload


async def build(ctx: DashboardContext) -> dict:
    calcular = CALCULO.get(ctx.source_db, get_financeiro_NG_faturamento_trimestral_meta)
    token = sheets.usar_fonte(ctx.source)
    try:
        data = await calcular(year=ctx.period.end.year, as_of=ctx.period.end)
    finally:
        sheets.soltar_fonte(token)
    return {"data": _normalizar(data)}


MODULE = DashboardModule(
    key="meta-anual",
    source_db="sheets_financeiro_ng",
    source_label=ROTULO,
    build=build,
    queries=(ABA,),
    alt_sources={"sheets_financeiro_la": AltSource(ROTULO, (ABA,))},
)
