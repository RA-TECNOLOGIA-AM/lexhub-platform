"""Organização de Documentos (banco legado) — dashboards da v1 /org-documentos (NG), /org_doc_RJ e
/org_doc_LA, sem mudança.

NG e RJ saem do banco ng (generico_ng.py, cópia em app/analyses/v1_dashboard_generico_ng.py, query
setor_org_doc); a LA, do banco laadv (cópia da rota _LA em app/analyses/v1_dashboard_generico_la.py, query
setor_org_documentos_LA). A resposta é a da v1 de cada rota (a da LA tem os nomes com _LA); o front lê as
duas. Como na v1, a fila de agora (represados, retornos, os não resolvidos por matéria, funcionário e mês) e
o "mês a mês" vêm do histórico todo, com os mesmos filtros: na v1 a página os buscava numa segunda chamada,
sem data.
"""

from dataclasses import replace

from app.analyses import v1_dashboard_generico_la as copia_la
from app.dashboards import generico_ng, legado_export

MODULE = generico_ng.modulo(
    key="org-documentos",
    v1_por_unidade={"NG": "org-documentos", "RJ": "org_doc_RJ", "LA": "org_doc_LA"},
    descricao_falta="Organização de Documentos (banco legado) não existe na v1 para esta unidade",
    alternativas={"laadv": (copia_la, "LA")},
    historico=(
        "resolvidos_total_por_mes",
        "nao_resolvidos_total_por_mes",
        "nao_organizados_total_por_materia",
        "nao_organizados_por_funcionario",
        "stats.nao_organizados",
        "stats.retorno_pet",
        "stats.retorno_pendencia",
        "resolvidos_total_por_mes_LA",
        "nao_organizados_total_por_mes_LA",
        "nao_organizados_total_por_materia_LA",
        "nao_organizados_por_funcionario_LA",
        "stats.nao_organizados_LA",
        "stats.retorno_pendencia_LA",
    ),
    commission_fields=(
        "comissionamento_por_funcionario",
        "comissionamento_org_doc_LA_por_funcionario",
    ),
)

# A exportação da v1 (/x/export, /x_RJ/export e /x_LA/export): app/dashboards/legado_export.py.
MODULE = replace(MODULE, export=legado_export.ORG_DOC)
