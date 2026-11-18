"""Execução Condenação (LexFlow) — dashboards da v1 /execucao (NG), /execucao_LA e /execucao_RJ, sem mudança.

Ver generico_v1.py (entrada) e app/analyses/v1_dashboard_generico.py (cálculo copiado da v1).

`historico`: o que as páginas da v1 (NG/Execucao.tsx, LA/Execucao_LA.tsx, RJ/ExecucaoRJ.tsx) liam da segunda
chamada, sem data: o estoque de agora
(total e valores em execução, processos sem valor), as distribuições (matéria, subfase, comarca) e os gráficos
"mês a mês". `total_em_execucao` com período é a entrada no período; sem período, o total em execução: vem
como `total_em_execucao_historico`. Os nomes são os da NG; os de LA e RJ saem pela regra das rotas da v1
(generico_v1.nome_na_unidade: _NG -> _LA/_RJ).
"""

from dataclasses import replace

from app.dashboards import execucao_campos, execucao_export, generico_v1
from app.dashboards.base import DashboardContext

_MODULO = generico_v1.modulo(
    key="execucao",
    v1_por_unidade={"NG": "execucao", "LA": "execucao_LA", "RJ": "execucao_RJ"},
    descricao_falta="Execução não existe na v1 para esta unidade",
    historico=generico_v1.historico_por_unidade(
        (
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
        ("NG", "LA", "RJ"),
    ),
)


async def build(ctx: DashboardContext) -> dict:
    """O cálculo da v1 + os processos em execução com campo em branco (V2: a faixa "Atenção" dos Julgados)."""
    body = await _MODULO.build(ctx)
    body[execucao_campos.CHAVE] = await execucao_campos.lista(ctx)
    return body


# A exportação da v1 (execucao_export.py) e, na V2, o relatório dos campos em branco (uma aba por campo).
MODULE = replace(
    _MODULO,
    build=build,
    export=execucao_export.EXECUCAO,
    export_reports={
        **_MODULO.export_reports,
        execucao_campos.RELATORIO: execucao_campos.RELATORIO_SPEC,
    },
)
