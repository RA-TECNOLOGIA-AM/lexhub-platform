"""Pendências (banco NG) — dashboards da v1 /pendencias (NG) e /pendencias_RJ, sem mudança.

Ver generico_ng.py (entrada) e app/analyses/v1_dashboard_generico_ng.py (cálculo copiado da v1).
"""

from app.dashboards import generico_ng

MODULE = generico_ng.modulo(
    key="pendencias",
    v1_por_unidade={"NG": "pendencias", "RJ": "pendencias_RJ"},
    descricao_falta="Pendências (banco NG) não existe na v1 para esta unidade",
)
