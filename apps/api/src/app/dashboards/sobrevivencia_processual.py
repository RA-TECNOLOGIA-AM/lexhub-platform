"""Sobrevivência Processual (TCC, LexFlow) — a página da v1 GERAL/TccSobrevivenciaProcessual.tsx.

v1: GET /tcc_sobrevivencia_processual. A API só monta a coorte (um processo por linha: distribuição como t = 0,
sentença, acórdão de mérito, acordo e pagamento) em colunas + dicionários de categorias, com o cálculo copiado sem
mudança em app/analyses/GERAL/tcc_sobrevivencia_processual.py; o Kaplan-Meier e o log-rank rodam no navegador a cada
filtro, como na v1 (web: pages/dashboards/sobrevivencia-processual/kaplanMeier.ts).

A coorte é a do estudo (NG e LA/AM; o RJ ficou fora) e não depende do período do calendário. Na V2 cada unidade vê só
o próprio escritório (regra de negócio de 18/11/2026: a NG vê a NG e o LA vê o LA), então a coorte já vem recortada
aqui e a página não tem mais o filtro de escritório da v1.
"""

from app.analyses.GERAL.tcc_sobrevivencia_processual import (
    ESCRITORIO_POR_ID,
    montar_payload_tcc_sobrevivencia,
)
from app.dashboards.base import DashboardContext, DashboardModule, NotReady

QUERY = "tcc_sobrevivencia_processual"

# A unidade (ref no LexFlow) -> o escritório assinante na coorte (v1: ESCRITORIO_POR_ID, 20 = NG e 21 = LA/AM).
ESCRITORIO_DA_UNIDADE = {ref: id_ for id_, ref in ESCRITORIO_POR_ID.items()}


async def build(ctx: DashboardContext) -> dict:
    escritorio = ESCRITORIO_DA_UNIDADE.get(ctx.unit_ref)
    if escritorio is None:
        raise NotReady("A Sobrevivência Processual (estudo do TCC) existe só para a NG e o LA/AM")
    linhas = [
        r for r in await ctx.source.fetch(QUERY) if r.get("id_escritorio_assinante") == escritorio
    ]
    return montar_payload_tcc_sobrevivencia(linhas)


MODULE = DashboardModule(
    key="sobrevivencia-processual",
    source_db="lexflow",
    source_label="LexFlow",
    build=build,
    queries=(QUERY,),
)
