"""Comercial (banco NG) — dashboards da v1 /comercial (NG) e /comercial_RJ, sem mudança.

Na v1 a resposta do /comercial traz também os números da LA (fontes do banco LAADV e do LexFlow). Um
módulo da V2 lê um banco só: essas fontes chegam vazias, como na v1 quando elas estão fora do ar. Os
campos do NG (os que a página Comercial NG usa) não mudam.

Ver generico_ng.py (entrada) e app/analyses/v1_dashboard_generico_ng.py (cálculo copiado da v1).
"""

from app.dashboards import generico_ng

MODULE = generico_ng.modulo(
    key="comercial",
    v1_por_unidade={"NG": "comercial", "RJ": "comercial_RJ"},
    descricao_falta="Comercial (banco NG) não existe na v1 para esta unidade",
)
