"""Execução Condenação (LexFlow) — dashboards da v1 /execucao (NG), /execucao_LA e /execucao_RJ, sem mudança.

Ver generico_v1.py (entrada) e app/analyses/v1_dashboard_generico.py (cálculo copiado da v1).

`historico`: o que a página NG da v1 (NG/Execucao.tsx) lia da segunda chamada, sem data: o estoque de agora
(total e valores em execução, processos sem valor), as distribuições (matéria, subfase, comarca) e os gráficos
"mês a mês". `total_em_execucao` com período é a entrada no período; sem período, o total em execução: vem
como `total_em_execucao_historico`.
"""

from app.dashboards import generico_v1

MODULE = generico_v1.modulo(
    key="execucao",
    v1_por_unidade={"NG": "execucao", "LA": "execucao_LA", "RJ": "execucao_RJ"},
    descricao_falta="Execução não existe na v1 para esta unidade",
    historico=(
        "stats.total_em_execucao_historico=stats.total_em_execucao",
        "stats.valor_total_em_execucao",
        "stats.valor_remanescente_em_execucao",
        "stats.total_valor_execucao_vazio",
        "stats.total_valor_execucao_vazio_detalhe",
        "execucao_por_materia",
        "execucao_por_subfase",
        "valor_execucao_por_subfase",
        "execucao_por_comarca_total",
        "execucao_valor_por_comarca_total",
        "valor_remanescente_por_mes",
        "valor_execucao_saida_periodo_por_mes",
        "quantidade_entrada_execucao_por_mes",
        "valor_entrada_execucao_por_mes",
        "execucao_resolvidos_por_dia_NG",
        "execucao_resolvidos_por_dia_por_prazo_NG",
    ),
)
