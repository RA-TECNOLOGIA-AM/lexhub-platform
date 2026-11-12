"""Pré-protocolo (LexPre) — a visão geral dos 4 setores antes do protocolo, como na v1.

Na v1 a página "Dashboard Geral Pré Protocolo (LexPre)" (PreProtocoloGeralLexpre.tsx) não tem rota
própria: chama os 4 dashboards LexPre do setor (Pendência, Org. Documentos, Peticionamento e Protocolo)
só com o período, sem filtros, e mostra resolvidos, represados e tempo médio de cada um.

Na V2: o mesmo, no servidor, com os 4 módulos LexPre já iguais à v1 (sem mudar o cálculo). Assim quem
tem acesso ao card Pré-protocolo não precisa de acesso aos 4 dashboards. A resposta traz o `stats` de
cada setor (o que a página usa); as buscas no LexPre são as mesmas e passam pelo mesmo cache.
"""

import asyncio
from dataclasses import replace

from app.dashboards import (
    org_documentos_lexpre,
    pendencias_lexpre,
    peticionamento_lexpre,
    protocolo_lexpre,
)
from app.dashboards.base import DashboardContext, DashboardModule

# Setor na resposta -> módulo LexPre da V2 (mesma ordem da página da v1).
SETORES: dict[str, DashboardModule] = {
    "pendencias": pendencias_lexpre.MODULE,
    "org_documentos": org_documentos_lexpre.MODULE,
    "peticionamento": peticionamento_lexpre.MODULE,
    "protocolo": protocolo_lexpre.MODULE,
}


async def build(ctx: DashboardContext) -> dict:
    # v1: cada setor só com from/to (sem filtros); aqui, cada módulo com os seus filtros vazios.
    respostas = await asyncio.gather(
        *(m.build(replace(ctx, filters={f: [] for f in m.filters})) for m in SETORES.values())
    )
    return {setor: {"stats": r.get("stats")} for setor, r in zip(SETORES, respostas, strict=True)}


MODULE = DashboardModule(
    key="pre-protocolo",
    source_db="lexpre",
    source_label="LexPre",
    build=build,
    queries=tuple(dict.fromkeys(q for m in SETORES.values() for q in m.queries)),
)
