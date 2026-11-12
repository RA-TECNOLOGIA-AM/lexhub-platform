"""Peticionamento (banco NG) — dashboards da v1 /peticionamento (NG) e /peticionamento_RJ, sem mudança.

Ver generico_ng.py (entrada) e app/analyses/v1_dashboard_generico_ng.py (cálculo copiado da v1).
"""

from app.dashboards import generico_ng

MODULE = generico_ng.modulo(
    key="peticionamento",
    v1_por_unidade={"NG": "peticionamento", "RJ": "peticionamento_RJ"},
    descricao_falta="Peticionamento (banco NG) não existe na v1 para esta unidade",
)
