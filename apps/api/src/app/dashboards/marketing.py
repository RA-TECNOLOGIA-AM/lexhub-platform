"""Marketing (banco NG) — dashboard da v1 /marketing_NG, sem mudança. Só existe para a NG na v1.

Ver generico_ng.py (entrada) e app/analyses/v1_dashboard_generico_ng.py (cálculo copiado da v1).
"""

from app.dashboards import generico_ng

MODULE = generico_ng.modulo(
    key="marketing",
    v1_por_unidade={"NG": "marketing_NG"},
    descricao_falta="Marketing (banco NG) só existe na v1 para a NG",
)
