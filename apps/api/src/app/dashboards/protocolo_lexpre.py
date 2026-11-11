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

Exportação: cole em `export_rows` o corpo de `_rows_protocolo_lexpre_export` (mesmas trocas acima).
Os mapas de campos e rótulos abaixo já são os da v1 (_CAMPOS_EXPORT_ e _LABELS_EXPORT_PROTOCOLO_LEXPRE_NG).
A casca valida format/campos, confere can_export, gera CSV/XLSX como na v1 e registra na auditoria.
"""

from app.dashboards.base import DashboardContext, DashboardModule, ExportSpec, NotReady

NOT_READY = "Os números do Protocolo ainda não foram ligados (aguardando a cópia da v1)"


async def build(ctx: DashboardContext) -> dict:
    raise NotReady(NOT_READY)


async def export_rows(ctx: DashboardContext) -> list[dict]:
    raise NotReady(NOT_READY)


# Copiados da v1 sem mudança (api_dashboards/src/app/dashboard_routes.py).
CAMPOS_EXPORT = {
    "id_demanda": "ID_DEMANDA",
    "numero_processo": "NUMERO_PROCESSO",
    "cliente_nome": "CLIENTE_NOME",
    "materia": "MATERIA",
    "funcionario": "FUNCIONARIO",
    "situacao": "SITUACAO",
    "status_demanda": "STATUS_DEMANDA",
    "setor_atual": "SETOR_ATUAL_NOME",
    "data_entrada": "DATA_ENTRADA",
    "data_saida": "DATA_SAIDA",
    "valor_causa": "VALOR_CAUSA",
    "dano_moral": "DANO_MORAL",
    "area_atuacao": "AREA_ATUACAO",
}
LABELS_EXPORT = {
    "id_demanda": "ID da Demanda",
    "numero_processo": "Número do Processo",
    "cliente_nome": "Nome do Cliente",
    "materia": "Matéria",
    "funcionario": "Funcionário Responsável",
    "situacao": "Situação",
    "status_demanda": "Status da Demanda",
    "setor_atual": "Setor Atual",
    "data_entrada": "Data de Entrada",
    "data_saida": "Data de Saída",
    "valor_causa": "Valor de Causa (R$)",
    "dano_moral": "Dano Moral (R$)",
    "area_atuacao": "Área de Atuação",
}

MODULE = DashboardModule(
    key="protocolo-lexpre",
    source_db="lexpre",
    source_label="LexPre",
    build=build,
    # Mesmos parâmetros da v1 (GET /protocolo-lexpre).
    filters={"materia": str, "funcionario": str, "area_atuacao_id": int, "uf": str},
    commission_fields=("comissionamento_por_funcionario",),
    v2_only_fields=("protocolados_no_prazo", "metas", "pendencias_mais_antigas"),
    export=ExportSpec(
        fields=CAMPOS_EXPORT,
        labels=LABELS_EXPORT,
        sheet_name="Protocolo (LexPre)",
        rows=export_rows,
    ),
)
