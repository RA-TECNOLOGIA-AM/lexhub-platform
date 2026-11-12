"""Organização de Documentos (banco NG) — dashboards da v1 /org-documentos (NG) e /org_doc_RJ, sem mudança.

Ver generico_ng.py (entrada) e app/analyses/v1_dashboard_generico_ng.py (cálculo copiado da v1).
"""

from app.dashboards import generico_ng

MODULE = generico_ng.modulo(
    key="org-documentos",
    v1_por_unidade={"NG": "org-documentos", "RJ": "org_doc_RJ"},
    descricao_falta="Organização de Documentos (banco NG) não existe na v1 para esta unidade",
)
