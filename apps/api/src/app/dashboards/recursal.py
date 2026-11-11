"""Recursal (LexFlow) — dashboards da v1 /recursal_NG e /recursal_LA, sem mudança (a v1 não tem RJ).

Ver generico_v1.py (entrada) e app/analyses/v1_dashboard_generico.py (cálculo copiado da v1).
"""

from app.dashboards import generico_v1

MODULE = generico_v1.modulo(
    key="recursal",
    v1_por_unidade={"NG": "recursal_NG", "LA": "recursal_LA"},
    descricao_falta="Recursal não existe na v1 para esta unidade (só NG e LA)",
)
