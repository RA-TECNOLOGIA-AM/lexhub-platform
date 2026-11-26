"""Peticionamento (banco legado) — dashboards da v1 /peticionamento (NG), /peticionamento_RJ e
/peticionamento_LA, sem mudança.

NG e RJ saem do banco ng (generico_ng.py, cópia em app/analyses/v1_dashboard_generico_ng.py, query
setor_confeccao); a LA, do banco laadv (cópia da rota _LA em app/analyses/v1_dashboard_generico_la.py, query
setor_confeccao_LA). A resposta é a da v1 de cada rota (a da LA tem os nomes com _LA); o front lê as duas.
Os gráficos "mês a mês" e os não peticionados por matéria vêm do histórico todo, com os mesmos filtros, e o
"Revisão" é a fila de agora: na v1 a página os buscava numa segunda chamada, sem data.
"""

from dataclasses import replace

from app.analyses import v1_dashboard_generico_la as copia_la
from app.dashboards import generico_ng, legado_export

MODULE = generico_ng.modulo(
    key="peticionamento",
    v1_por_unidade={"NG": "peticionamento", "RJ": "peticionamento_RJ", "LA": "peticionamento_LA"},
    descricao_falta="Peticionamento (banco legado) não existe na v1 para esta unidade",
    alternativas={"laadv": (copia_la, "LA")},
    historico=(
        "peticionados_por_mes",
        "nao_peticionados_por_mes",
        "nao_peticionados_por_materia",
        "stats.processos_em_revisao",  # a fila de revisão de agora, como a v1 (sem data)
        "confeccionados_por_mes_LA",
        "nao_confeccionados_por_mes_LA",
        "nao_confeccionados_por_materia_LA",
        "stats.nao_confeccionados_LA",  # os represados de agora, como a v1 (sem data)
    ),
    commission_fields=(
        "comissionamento_peticionamento_por_funcionario",
        "comissionamento_peticionamento_LA_por_funcionario",
    ),
)

# A exportação da v1 (/x/export, /x_RJ/export e /x_LA/export): app/dashboards/legado_export.py.
MODULE = replace(MODULE, export=legado_export.PETICIONAMENTO)
