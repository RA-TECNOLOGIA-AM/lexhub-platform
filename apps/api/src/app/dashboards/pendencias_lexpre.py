"""Pendências (LexPre) — ponto de encaixe para o código da v1.

>>> PARA O DEV DE DADOS <<<
Mesmo molde do Protocolo (ver o cabeçalho de protocolo_lexpre.py). Cole:
  * em `build`, o corpo de `_build_pendencia_lexpre_response` (dashboard_routes.py da v1);
  * em `export_rows`, o corpo de `_rows_pendencia_lexpre_export`.
Trocas: `await fetch_log_setor_demanda_lexpre_ng()` -> `await ctx.source.fetch("log_setor_demanda_lexpre_NG")`
(e `fetch_setor_func_lexpre()` -> `ctx.source.fetch("setor_func_lexpre_NG")`), escritorio_id -> int(ctx.unit_ref),
período -> ctx.period, funcionario/area_atuacao_id/uf -> ctx.filters[...].
Devolva o dict de PendenciaLexpreNGResponse (v1). Comissão (comissionamento_pendencias_por_funcionario): devolva a
lista completa; a casca mostra a de todos para quem gere a unidade e só a própria para os demais.
"""

from app.dashboards.base import DashboardContext, DashboardModule, ExportSpec, NotReady

NOT_READY = "Os números de Pendências ainda não foram ligados (aguardando a cópia da v1)"


async def build(ctx: DashboardContext) -> dict:
    raise NotReady(NOT_READY)


async def export_rows(ctx: DashboardContext) -> list[dict]:
    raise NotReady(NOT_READY)


# Copiados da v1 sem mudança (_CAMPOS_EXPORT_ e _LABELS_EXPORT_PENDENCIA_LEXPRE_NG).
CAMPOS_EXPORT = {
    "id_demanda": "ID_DEMANDA",
    "numero_processo": "NUMERO_PROCESSO",
    "cliente_nome": "CLIENTE_NOME",
    "materia": "MATERIA",
    "funcionario": "FUNCIONARIO",
    "situacao": "SITUACAO",
    "status_demanda": "STATUS_DEMANDA",
    "setor_atual": "SETOR_ATUAL_NOME",
    "origem": "ORIGEM",
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
    "origem": "Origem",
    "data_entrada": "Data de Entrada",
    "data_saida": "Data de Saída",
    "valor_causa": "Valor de Causa (R$)",
    "dano_moral": "Dano Moral (R$)",
    "area_atuacao": "Área de Atuação",
}

MODULE = DashboardModule(
    key="pendencias-lexpre",
    source_db="lexpre",
    source_label="LexPre",
    build=build,
    # Mesmos parâmetros da v1 (GET /pendencia-lexpre): sem matéria.
    filters={"funcionario": str, "area_atuacao_id": int, "uf": str},
    commission_fields=("comissionamento_pendencias_por_funcionario",),
    export=ExportSpec(
        fields=CAMPOS_EXPORT,
        labels=LABELS_EXPORT,
        sheet_name="Pendências (LexPre)",
        rows=export_rows,
    ),
)
