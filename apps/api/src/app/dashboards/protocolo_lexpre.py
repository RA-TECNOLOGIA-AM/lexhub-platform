"""Protocolo (LexPre) — ponto de encaixe para o código da v1.

>>> PARA O DEV DE DADOS <<<
Cole em `build` o corpo de `_build_protocolo_lexpre_response` (api_dashboards/src/app/dashboard_routes.py),
SEM mudar a lógica, trocando só a entrada:

    v1                                              aqui
    await fetch_log_setor_demanda_lexpre_ng()  ->  await ctx.source.fetch("log_setor_demanda_lexpre_NG")
    escritorio_id (ESCRITORIO_NGAM etc.)        ->  int(ctx.unit_ref)
    from_date / to_date (+ padrão do mês)       ->  ctx.period.start / ctx.period.end (padrão já aplicado)
    materia, funcionario, area_atuacao_id, uf   ->  ctx.filters["materia"], ... (listas; [] = sem filtro)

As funções de análise (filter_*, get_*, group_*) vêm copiadas da v1 para app/analyses/ e a query
"log_setor_demanda_lexpre_NG" para app/source_queries.py (mesmo texto).

Devolva um dict com os campos de ProtocoloLexpreNGResponse (v1), em snake_case, mais:
  * "opcoes_filtro": {"materias": [...], "funcionarios": [...], "ufs": [...], "areas": [{"id", "nome"}]}
    calculadas nas linhas da unidade e do período ANTES dos filtros.
Não precisa tratar `meta`, acesso, comissão nem os campos novos da V2: a casca faz.
"""

from app.dashboards.base import DashboardContext, DashboardModule, NotReady


async def build(ctx: DashboardContext) -> dict:
    raise NotReady("Os números do Protocolo ainda não foram ligados (aguardando a cópia da v1)")


MODULE = DashboardModule(
    key="protocolo-lexpre",
    source_db="lexpre",
    source_label="LexPre",
    build=build,
    # Mesmos parâmetros da v1 (GET /protocolo-lexpre).
    filters={"materia": str, "funcionario": str, "area_atuacao_id": int, "uf": str},
    commission_fields=("comissionamento_por_funcionario",),
    v2_only_fields=("protocolados_no_prazo", "metas", "pendencias_mais_antigas"),
)
