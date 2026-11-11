"""Acordos (LexFlow) — dashboards da v1 /execucao_acordos_NG, _LA e _RJ, sem mudança.

Ver generico_v1.py (entrada) e app/analyses/v1_dashboard_generico.py (cálculo copiado da v1).
"""

from app.dashboards import generico_v1

MODULE = generico_v1.modulo(
    key="acordos",
    v1_por_unidade={
        "NG": "execucao_acordos_NG",
        "LA": "execucao_acordos_LA",
        "RJ": "execucao_acordos_RJ",
    },
    descricao_falta="Acordos não existe na v1 para esta unidade",
)
