"""Protocolo (banco NG) — dashboards da v1 /protocolo (NG) e /protocolo_RJ, sem mudança.

Ver generico_ng.py (entrada) e app/analyses/v1_dashboard_generico_ng.py (cálculo copiado da v1).
"""

from app.dashboards import generico_ng

MODULE = generico_ng.modulo(
    key="protocolo",
    v1_por_unidade={"NG": "protocolo", "RJ": "protocolo_RJ"},
    descricao_falta="Protocolo (banco NG) não existe na v1 para esta unidade",
)
