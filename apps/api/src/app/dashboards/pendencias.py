"""Pendências (banco legado) — dashboards da v1 /pendencias (NG), /pendencias_RJ e /pendencia_LA, sem mudança.

NG e RJ saem do banco ng (generico_ng.py, cópia em app/analyses/v1_dashboard_generico_ng.py, query
setor_pendencias); a LA, do banco laadv (cópia da rota _LA em app/analyses/v1_dashboard_generico_la.py, query
setor_pendencia_LA). A resposta é a da v1 de cada rota (a da LA tem os nomes com _LA); o front lê as duas.
Como na página da v1 da NG, o que é da fila de agora (não resolvidas, as com mais de 5 dias e a origem delas)
e o "mês a mês" vêm do histórico todo, com os mesmos filtros: a v1 os buscava numa chamada sem data.
"""

from dataclasses import replace

from app.analyses import v1_dashboard_generico_la as copia_la
from app.dashboards import generico_ng, legado_export

MODULE = generico_ng.modulo(
    key="pendencias",
    v1_por_unidade={"NG": "pendencias", "RJ": "pendencias_RJ", "LA": "pendencia_LA"},
    descricao_falta="Pendências (banco legado) não existe na v1 para esta unidade",
    alternativas={"laadv": (copia_la, "LA")},
    historico=(
        "pendencias_resolvidas_por_mes",
        "pendencias_nao_resolvidas_por_origem",
        "stats.pendencias_nao_resolvidas",
        "stats.pendencias_nao_resolvidas_com_atraso",
        "pendencias_resolvidas_por_mes_LA",
        "pendencias_nao_resolvidas_por_origem_LA",
        # Na v1 a página da LA lia estes dois do período; aqui, a fila de agora, como na NG (a tela diz "não
        # depende do período"). Em 16/11/2026 deu o mesmo (8 e 8).
        "stats.pendencias_nao_resolvidas_LA",
        "stats.pendencias_nao_resolvidas_com_atraso_LA",
    ),
    commission_fields=(
        "comissionamento_pendencias_por_funcionario",
        "comissionamento_pendencias_LA_por_funcionario",
    ),
)

# A exportação da v1 (/x/export, /x_RJ/export e /x_LA/export): app/dashboards/legado_export.py.
MODULE = replace(MODULE, export=legado_export.PENDENCIAS)
