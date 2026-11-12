"""NPS (banco NG) — dashboard da v1 /nps_NG, sem mudança. Na V2 só para a NG.

Na v1 o NPS da LA (/nps_LA) lê o banco LAADV: fica fora deste módulo, como os outros do banco NG.
Ver generico_ng.py (entrada) e app/analyses/v1_dashboard_generico_ng.py (cálculo copiado da v1).
"""

from app.dashboards import generico_ng

MODULE = generico_ng.modulo(
    key="nps",
    v1_por_unidade={"NG": "nps_NG"},
    descricao_falta="NPS (banco NG) só existe na v1 para a NG",
)
