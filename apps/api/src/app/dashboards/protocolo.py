"""Protocolo (banco legado) — dashboards da v1 /protocolo (NG), /protocolo_RJ e /protocolo_LA, sem mudança.

NG e RJ saem do banco ng (generico_ng.py, cópia em app/analyses/v1_dashboard_generico_ng.py); a LA, do
banco laadv (cópia da rota _LA em app/analyses/v1_dashboard_generico_la.py, gerada por
scripts/copiar_v1/gerar_generico.py --banco laadv protocolo_LA). A resposta é a da v1 de cada rota (a da LA
tem os nomes com _LA); o front lê as duas. Os gráficos "mês a mês" vêm do histórico todo, com os mesmos
filtros: na v1 a página os buscava numa segunda chamada, sem data.
"""

from app.analyses import v1_dashboard_generico_la as copia_la
from app.dashboards import generico_ng

MODULE = generico_ng.modulo(
    key="protocolo",
    v1_por_unidade={"NG": "protocolo", "RJ": "protocolo_RJ", "LA": "protocolo_LA"},
    descricao_falta="Protocolo (banco legado) não existe na v1 para esta unidade",
    alternativas={"laadv": (copia_la, "LA")},
    historico=(
        "protocolados_por_mes",
        "nao_protocolados_por_mes",
        "protocolados_por_mes_LA",
        "represados_por_mes_LA",
    ),
    commission_fields=(
        "comissionamento_protocolo_por_funcionario",
        "comissionamento_protocolo_LA_por_funcionario",
    ),
)
