"""Execução (LexFlow) — dashboards da v1 /execucao (NG), /execucao_LA e /execucao_RJ, sem mudança.

Ver generico_v1.py (entrada) e app/analyses/v1_dashboard_generico.py (cálculo copiado da v1).
"""

from app.dashboards import generico_v1

MODULE = generico_v1.modulo(
    key="execucao",
    v1_por_unidade={"NG": "execucao", "LA": "execucao_LA", "RJ": "execucao_RJ"},
    descricao_falta="Execução não existe na v1 para esta unidade",
)
