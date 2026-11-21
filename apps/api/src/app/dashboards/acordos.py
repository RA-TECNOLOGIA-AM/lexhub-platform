"""Execução Acordos (LexFlow) — dashboards da v1 /execucao_acordos_NG, _LA e _RJ, sem mudança.

Ver generico_v1.py (entrada) e app/analyses/v1_dashboard_generico.py (cálculo copiado da v1).

`historico`: o que as páginas da v1 (NG/ExecucaoAcordos.tsx, LA/ExecucaoAcordosLA.tsx, RJ/ExecucaoAcordosRJ.tsx)
liam da segunda chamada, sem data: o estoque de
agora (total e valor em execução, processos sem valor de alçada), as distribuições (fechamento, matéria,
subfase, sentença, tipo de ação, comarca) e os gráficos "mês a mês". Nomes da NG; os de LA e RJ pela regra
da v1 (generico_v1.nome_na_unidade).
"""

from dataclasses import replace

from app.dashboards import execucao_export, generico_v1
from app.unit_scope import com_recorte

_MODULO = generico_v1.modulo(
    key="acordos",
    v1_por_unidade={
        "NG": "execucao_acordos_NG",
        "LA": "execucao_acordos_LA",
        "RJ": "execucao_acordos_RJ",
    },
    descricao_falta="Acordos não existe na v1 para esta unidade",
    historico=generico_v1.historico_por_unidade(
        (
            "stats.total_em_execucao_acordos_NG",
            "stats.valor_total_em_execucao_acordos_NG",
            "stats.total_valor_alcada_final_vazio_acordos_NG",
            "stats.total_valor_alcada_final_vazio_acordos_NG_detalhe",
            "fechamento_acordo_por_subfase_NG",
            "valor_fechamento_acordo_por_subfase_NG",
            "execucao_acordos_por_materia_NG",
            "execucao_acordos_por_subfase_NG",
            "valor_execucao_acordos_por_subfase_NG",
            "execucao_acordos_por_sentenca_NG",
            "execucao_acordos_por_tipo_acao_NG",
            "execucao_acordos_por_comarca_total_NG",
            "execucao_acordos_valor_por_comarca_total_NG",
            "quantidade_entrada_execucao_acordos_por_mes_NG",
            "quantidade_saida_execucao_acordos_por_mes_NG",
            "valor_entrada_execucao_acordos_por_mes_NG",
            "valor_saida_execucao_acordos_por_mes_NG",
            "execucao_acordos_resolvidos_por_dia_NG",
            "execucao_acordos_resolvidos_por_dia_por_prazo_NG",
        ),
        ("NG", "LA", "RJ"),
    ),
)

# A exportação da v1 (execucao_export.py).
MODULE = replace(
    _MODULO,
    export=execucao_export.ACORDOS,
    export_reports={"atividades": execucao_export.ATIVIDADES_ACORDOS},
)

# Só as linhas da unidade da tela nas queries que trazem todos os escritórios (app/unit_scope.py).
MODULE = replace(MODULE, unit_scoped=com_recorte(MODULE.queries))
