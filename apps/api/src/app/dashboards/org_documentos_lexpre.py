"""Organização de Documentos (LexPre) — cálculo da v1 ligado à casca da V2.

Corpo de `_build_org_doc_lexpre_response` e `_rows_org_doc_lexpre_export` (api_dashboards/src/app/
dashboard_routes.py) copiado SEM mudar a lógica, com os mesmos nomes da v1. Só a entrada mudou
(mesmas trocas do protocolo_lexpre.py): fetch_* -> ctx.source.fetch(<query>), escritorio_id ->
int(ctx.unit_ref), from_date/to_date -> ctx.period, filtros -> ctx.filters[...] ([] = sem filtro).
Novo na V2: `opcoes_filtro` (antes dos filtros).
"""

from datetime import date
from typing import Any

from app.analyses.NG.org_doc_lexpre import (
    _entradas_org_doc as entradas_org_doc_lexpre,
)
from app.analyses.NG.org_doc_lexpre import (
    _entradas_org_doc_por_demanda as entradas_org_doc_lexpre_por_demanda,
)
from app.analyses.NG.org_doc_lexpre import (
    _filter_saidas_by_date_range as filter_saidas_org_doc_lexpre_by_date_range,
)
from app.analyses.NG.org_doc_lexpre import (
    _filter_saidas_by_protocolo_date_range as filter_saidas_org_doc_lexpre_by_protocolo_date_range,
)
from app.analyses.NG.org_doc_lexpre import (
    _filtrar_resolvidos_reais as filtrar_resolvidos_reais_org_doc_lexpre,
)
from app.analyses.NG.org_doc_lexpre import (
    _indexar_movimentacoes as indexar_movimentacoes_org_doc_lexpre,
)
from app.analyses.NG.org_doc_lexpre import (
    _normalizar_materia,
    filter_org_doc_lexpre_por_area_atuacao,
    filter_org_doc_lexpre_por_escritorio,
    filter_org_doc_lexpre_por_funcionarios,
    filter_org_doc_lexpre_por_materia,
    filter_org_doc_lexpre_por_uf,
    list_funcionarios_org_doc_lexpre,
)
from app.analyses.NG.org_doc_lexpre import (
    _saidas_org_doc as saidas_org_doc_lexpre,
)
from app.analyses.NG.org_doc_lexpre import (
    get_cancelados as get_cancelados_org_doc_lexpre,
)
from app.analyses.NG.org_doc_lexpre import (
    get_comissionamento_por_funcionario as get_comissionamento_por_funcionario_org_doc_lexpre,
)
from app.analyses.NG.org_doc_lexpre import (
    get_comparativo_cancelados as get_comparativo_cancelados_org_doc_lexpre,
)
from app.analyses.NG.org_doc_lexpre import (
    get_comparativo_devolvido_pendencia as get_comparativo_devolvido_pendencia_org_doc_lexpre,
)
from app.analyses.NG.org_doc_lexpre import (
    get_comparativo_mediana_tempo_resolvidos as get_comparativo_mediana_tempo_resolvidos_org_doc_lexpre,
)
from app.analyses.NG.org_doc_lexpre import (
    get_comparativo_organizados_automaticamente as get_comparativo_organizados_automaticamente_org_doc_lexpre,
)
from app.analyses.NG.org_doc_lexpre import (
    get_comparativo_organizados_manualmente as get_comparativo_organizados_manualmente_org_doc_lexpre,
)
from app.analyses.NG.org_doc_lexpre import (
    get_comparativo_protocolados_total as get_comparativo_protocolados_total_org_doc_lexpre,
)
from app.analyses.NG.org_doc_lexpre import (
    get_comparativo_resolvidos_total as get_comparativo_resolvidos_total_org_doc_lexpre,
)
from app.analyses.NG.org_doc_lexpre import (
    get_comparativo_tempo_medio_resolvidos as get_comparativo_tempo_medio_resolvidos_org_doc_lexpre,
)
from app.analyses.NG.org_doc_lexpre import (
    get_devolvido_pendencia as get_devolvido_pendencia_org_doc_lexpre,
)
from app.analyses.NG.org_doc_lexpre import (
    get_media_resolvidos_por_funcionario as get_media_resolvidos_por_funcionario_org_doc_lexpre,
)
from app.analyses.NG.org_doc_lexpre import (
    get_media_tempo_resolvidos as get_media_tempo_resolvidos_org_doc_lexpre,
)
from app.analyses.NG.org_doc_lexpre import (
    get_mediana_tempo_resolvidos as get_mediana_tempo_resolvidos_org_doc_lexpre,
)
from app.analyses.NG.org_doc_lexpre import (
    get_organizados_e_peticionados_automaticamente as get_organizados_e_peticionados_automaticamente_org_doc_lexpre,
)
from app.analyses.NG.org_doc_lexpre import (
    get_organizados_manualmente as get_organizados_manualmente_org_doc_lexpre,
)
from app.analyses.NG.org_doc_lexpre import (
    get_protocolados_por_funcionario as get_protocolados_por_funcionario_org_doc_lexpre,
)
from app.analyses.NG.org_doc_lexpre import (
    get_protocolados_total as get_protocolados_total_org_doc_lexpre,
)
from app.analyses.NG.org_doc_lexpre import (
    get_represados as get_represados_org_doc_lexpre,
)
from app.analyses.NG.org_doc_lexpre import (
    get_resolvidos_por_dia_por_funcionario as get_resolvidos_por_dia_por_funcionario_org_doc_lexpre,
)
from app.analyses.NG.org_doc_lexpre import (
    get_resolvidos_total as get_resolvidos_total_org_doc_lexpre,
)
from app.analyses.NG.org_doc_lexpre import (
    get_retorno_pendencia as get_retorno_pendencia_org_doc_lexpre,
)
from app.analyses.NG.org_doc_lexpre import (
    get_retorno_pet as get_retorno_pet_org_doc_lexpre,
)
from app.analyses.NG.org_doc_lexpre import (
    get_valor_causa_por_funcionario as get_valor_causa_por_funcionario_org_doc_lexpre,
)
from app.analyses.NG.org_doc_lexpre import (
    get_valor_causa_protocolado_por_funcionario as get_valor_causa_protocolado_por_funcionario_org_doc_lexpre,
)
from app.analyses.NG.org_doc_lexpre import (
    group_nao_organizados_por_funcionario as group_nao_organizados_por_funcionario_org_doc_lexpre,
)
from app.analyses.NG.org_doc_lexpre import (
    group_nao_organizados_total_por_materia as group_nao_organizados_total_por_materia_org_doc_lexpre,
)
from app.analyses.NG.org_doc_lexpre import (
    group_nao_resolvidos_total_por_mes as group_nao_resolvidos_total_por_mes_org_doc_lexpre,
)
from app.analyses.NG.org_doc_lexpre import (
    group_protocolados_total_por_materia as group_protocolados_total_por_materia_org_doc_lexpre,
)
from app.analyses.NG.org_doc_lexpre import (
    group_resolvidos_por_dia as group_resolvidos_por_dia_org_doc_lexpre,
)
from app.analyses.NG.org_doc_lexpre import (
    group_resolvidos_por_funcionario as group_resolvidos_por_funcionario_org_doc_lexpre,
)
from app.analyses.NG.org_doc_lexpre import (
    group_resolvidos_total_por_materia as group_resolvidos_total_por_materia_org_doc_lexpre,
)
from app.analyses.NG.org_doc_lexpre import (
    group_resolvidos_total_por_mes as group_resolvidos_total_por_mes_org_doc_lexpre,
)
from app.analyses.NG.org_doc_lexpre import (
    list_export_rows as list_export_rows_org_doc_lexpre,
)
from app.analyses.v1_routes import (
    ChartDataPoint,
    OrgDocLexpreComissionamentoRow,
    OrgDocLexpreNGResponse,
    OrgDocLexpreNGStats,
    OrgDocLexpreStat,
    _restringir_por_funcionarios_selecionados,
)
from app.dashboards.base import DashboardContext, DashboardModule, ExportSpec
from app.dashboards.opcoes_lexpre import opcoes_filtro_setor

QUERIES = ("log_setor_demanda_lexpre_NG",)


def opcoes_filtro(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Novo na V2: valores possíveis dos filtros, nas linhas da unidade ANTES dos filtros."""
    return opcoes_filtro_setor(
        rows,
        _normalizar_materia,
        list_funcionarios_org_doc_lexpre,
        ("materias", "funcionarios", "ufs", "areas"),
    )


async def build(ctx: DashboardContext) -> dict:
    # --- entrada (V2) ---
    escritorio_id = int(ctx.unit_ref)
    from_date = ctx.period.start
    to_date = ctx.period.end
    materia = ctx.filters["materia"]
    funcionario = ctx.filters["funcionario"]
    area_atuacao_id = ctx.filters["area_atuacao_id"]
    uf = ctx.filters["uf"]

    # --- v1: _build_org_doc_lexpre_response (sem mudança daqui para baixo) ---
    rows = filter_org_doc_lexpre_por_escritorio(
        await ctx.source.fetch("log_setor_demanda_lexpre_NG"), escritorio_id=escritorio_id
    )
    opcoes = opcoes_filtro(rows)  # V2: antes dos filtros
    rows = filter_org_doc_lexpre_por_materia(rows, materia)
    rows = filter_org_doc_lexpre_por_area_atuacao(rows, area_atuacao_id)
    rows = filter_org_doc_lexpre_por_uf(rows, uf)
    rows = filter_org_doc_lexpre_por_funcionarios(rows, funcionario)

    hoje = date.today()
    inicio, fim = (
        (from_date, to_date) if (from_date and to_date) else (date(hoje.year, hoje.month, 1), hoje)
    )

    # No sistema, uma demanda pode sair da Organização de Documentos para
    # QUALQUER setor — só a saída com destino Peticionamento (manual) ou
    # Protocolo (automático) é uma resolução de fato; saída para Pendências é
    # devolução (ver get_devolvido_pendencia). Cancelamento não tem destino
    # pareado, então "Cancelados" usa `saidas_todas` (sem esse filtro).
    idx = indexar_movimentacoes_org_doc_lexpre(rows)
    saidas_todas = saidas_org_doc_lexpre(rows)
    saidas = filtrar_resolvidos_reais_org_doc_lexpre(saidas_todas, idx)
    entradas_por_demanda = entradas_org_doc_lexpre_por_demanda(entradas_org_doc_lexpre(rows))
    saidas_todas_periodo = filter_saidas_org_doc_lexpre_by_date_range(saidas_todas, inicio, fim)
    saidas_periodo = filter_saidas_org_doc_lexpre_by_date_range(saidas, inicio, fim)
    # "Protocolados" (quantidade e valor) ancorado em DATA_PROTOCOLO, não em DATA
    # de saída do setor — ver docstring de
    # `get_protocolados_total`/`_filter_saidas_by_protocolo_date_range` (ajuste
    # de 07/10/2026, pedido do usuário).
    saidas_protocoladas_periodo = filter_saidas_org_doc_lexpre_by_protocolo_date_range(
        saidas, inicio, fim
    )

    resolvidos_por_dia_por_func = get_resolvidos_por_dia_por_funcionario_org_doc_lexpre(
        saidas_periodo, entradas_por_demanda
    )

    response = OrgDocLexpreNGResponse(
        stats=OrgDocLexpreNGStats(
            resolvidos_total=OrgDocLexpreStat(
                total=get_resolvidos_total_org_doc_lexpre(saidas_periodo),
                comparativo=get_comparativo_resolvidos_total_org_doc_lexpre(rows, inicio, fim),
            ),
            organizados_manualmente=OrgDocLexpreStat(
                total=get_organizados_manualmente_org_doc_lexpre(saidas_periodo),
                comparativo=get_comparativo_organizados_manualmente_org_doc_lexpre(
                    rows, inicio, fim
                ),
            ),
            organizados_e_peticionados_automaticamente=OrgDocLexpreStat(
                total=get_organizados_e_peticionados_automaticamente_org_doc_lexpre(saidas_periodo),
                comparativo=get_comparativo_organizados_automaticamente_org_doc_lexpre(
                    rows, inicio, fim
                ),
            ),
            cancelados=OrgDocLexpreStat(
                total=get_cancelados_org_doc_lexpre(saidas_todas_periodo),
                comparativo=get_comparativo_cancelados_org_doc_lexpre(rows, inicio, fim),
            ),
            protocolados_total=OrgDocLexpreStat(
                total=get_protocolados_total_org_doc_lexpre(saidas_protocoladas_periodo),
                comparativo=get_comparativo_protocolados_total_org_doc_lexpre(rows, inicio, fim),
            ),
            media_tempo_resolvidos=get_media_tempo_resolvidos_org_doc_lexpre(
                saidas_periodo, entradas_por_demanda
            ),
            mediana_tempo_resolvidos=get_mediana_tempo_resolvidos_org_doc_lexpre(
                saidas_periodo, entradas_por_demanda
            ),
            comparativo_tempo_medio_resolvidos=get_comparativo_tempo_medio_resolvidos_org_doc_lexpre(
                rows, inicio, fim
            ),
            comparativo_mediana_tempo_resolvidos=get_comparativo_mediana_tempo_resolvidos_org_doc_lexpre(
                rows, inicio, fim
            ),
            represados=get_represados_org_doc_lexpre(rows),
            devolvido_pendencia=get_devolvido_pendencia_org_doc_lexpre(rows),
            comparativo_devolvido_pendencia=get_comparativo_devolvido_pendencia_org_doc_lexpre(
                rows, inicio, fim
            ),
            retorno_pendencia=get_retorno_pendencia_org_doc_lexpre(rows),
            retorno_pet=get_retorno_pet_org_doc_lexpre(rows),
        ),
        resolvidos_total_por_materia=[
            ChartDataPoint(**x)
            for x in group_resolvidos_total_por_materia_org_doc_lexpre(saidas_periodo)
        ],
        protocolados_total_por_materia=[
            ChartDataPoint(**x)
            for x in group_protocolados_total_por_materia_org_doc_lexpre(
                saidas_protocoladas_periodo
            )
        ],
        nao_organizados_total_por_materia=[
            ChartDataPoint(**x)
            for x in group_nao_organizados_total_por_materia_org_doc_lexpre(rows)
        ],
        # Evolução mês a mês usa o histórico completo (sem recorte de período) — mesmo
        # critério do dashboard antigo (banco `ng`), que usa "all_org_doc" nesse gráfico.
        resolvidos_total_por_mes=[
            ChartDataPoint(**x) for x in group_resolvidos_total_por_mes_org_doc_lexpre(saidas)
        ],
        nao_resolvidos_total_por_mes=[
            ChartDataPoint(**x) for x in group_nao_resolvidos_total_por_mes_org_doc_lexpre(rows)
        ],
        resolvidos_por_dia_org=[
            ChartDataPoint(**x) for x in group_resolvidos_por_dia_org_doc_lexpre(saidas_periodo)
        ],
        resolvidos_por_dia_por_funcionario_org={
            k: [ChartDataPoint(**i) for i in v]
            for k, v in resolvidos_por_dia_por_func["por_funcionario"].items()
            if not funcionario or k in set(funcionario)
        },
        nao_organizados_por_funcionario=[
            ChartDataPoint(**x)
            for x in _restringir_por_funcionarios_selecionados(
                group_nao_organizados_por_funcionario_org_doc_lexpre(rows), funcionario
            )
        ],
        resolvidos_por_funcionario=[
            ChartDataPoint(**x)
            for x in _restringir_por_funcionarios_selecionados(
                group_resolvidos_por_funcionario_org_doc_lexpre(
                    saidas_periodo, entradas_por_demanda
                ),
                funcionario,
            )
        ],
        protocolados_por_funcionario=[
            ChartDataPoint(**x)
            for x in _restringir_por_funcionarios_selecionados(
                get_protocolados_por_funcionario_org_doc_lexpre(
                    saidas_protocoladas_periodo, entradas_por_demanda
                ),
                funcionario,
            )
        ],
        media_resolvidos_por_funcionario=[
            ChartDataPoint(**x)
            for x in _restringir_por_funcionarios_selecionados(
                get_media_resolvidos_por_funcionario_org_doc_lexpre(
                    saidas_periodo, entradas_por_demanda, inicio, fim
                ),
                funcionario,
            )
        ],
        valor_causa_por_funcionario=[
            ChartDataPoint(**x)
            for x in _restringir_por_funcionarios_selecionados(
                get_valor_causa_por_funcionario_org_doc_lexpre(
                    saidas_periodo, entradas_por_demanda
                ),
                funcionario,
            )
        ],
        valor_causa_protocolado_por_funcionario=[
            ChartDataPoint(**x)
            for x in _restringir_por_funcionarios_selecionados(
                get_valor_causa_protocolado_por_funcionario_org_doc_lexpre(
                    saidas_protocoladas_periodo, entradas_por_demanda
                ),
                funcionario,
            )
        ],
        comissionamento_por_funcionario=[
            OrgDocLexpreComissionamentoRow(**x)
            for x in _restringir_por_funcionarios_selecionados(
                get_comissionamento_por_funcionario_org_doc_lexpre(
                    saidas_protocoladas_periodo, entradas_por_demanda
                ),
                funcionario,
                key="funcionario",
            )
        ],
        funcionarios_org_doc=list_funcionarios_org_doc_lexpre(rows),
    )
    # --- saída (V2): o JSON da v1 + opcoes_filtro ---
    return {**response.model_dump(), "opcoes_filtro": opcoes}


async def export_rows(ctx: DashboardContext) -> list[dict]:
    # --- entrada (V2) ---
    escritorio_id = int(ctx.unit_ref)
    from_date = ctx.period.start
    to_date = ctx.period.end
    materia = ctx.filters["materia"]
    funcionario = ctx.filters["funcionario"]
    area_atuacao_id = ctx.filters["area_atuacao_id"]
    uf = ctx.filters["uf"]

    # --- v1: _rows_org_doc_lexpre_export (sem mudança) ---
    rows = filter_org_doc_lexpre_por_escritorio(
        await ctx.source.fetch("log_setor_demanda_lexpre_NG"), escritorio_id=escritorio_id
    )
    rows = filter_org_doc_lexpre_por_materia(rows, materia)
    rows = filter_org_doc_lexpre_por_area_atuacao(rows, area_atuacao_id)
    rows = filter_org_doc_lexpre_por_uf(rows, uf)
    rows = filter_org_doc_lexpre_por_funcionarios(rows, funcionario)

    hoje = date.today()
    inicio, fim = (
        (from_date, to_date) if (from_date and to_date) else (date(hoje.year, hoje.month, 1), hoje)
    )
    return list_export_rows_org_doc_lexpre(rows, inicio, fim)


# Copiados da v1 sem mudança (_CAMPOS_EXPORT_ORG_DOC_LEXPRE_NG, _LABELS_EXPORT_ORG_DOC_LEXPRE_NG).
CAMPOS_EXPORT = {
    "id_demanda": "ID_DEMANDA",
    "numero_processo": "NUMERO_PROCESSO",
    "cliente_nome": "CLIENTE_NOME",
    "materia": "MATERIA",
    "funcionario": "FUNCIONARIO",
    "situacao": "SITUACAO",
    "status_demanda": "STATUS_DEMANDA",
    "setor_atual": "SETOR_ATUAL_NOME",
    "destino": "DESTINO",
    "data_entrada": "DATA_ENTRADA",
    "data_saida": "DATA_SAIDA",
    "data_protocolo": "DATA_PROTOCOLO",
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
    "destino": "Destino",
    "data_entrada": "Data de Entrada",
    "data_saida": "Data de Saída",
    "data_protocolo": "Data de Protocolo",
    "valor_causa": "Valor de Causa (R$)",
    "dano_moral": "Dano Moral (R$)",
    "area_atuacao": "Área de Atuação",
}


MODULE = DashboardModule(
    key="org-documentos-lexpre",
    source_db="lexpre",
    source_label="LexPre",
    build=build,
    queries=QUERIES,
    # Mesmos parâmetros da v1 (GET /org-documentos-lexpre).
    filters={"materia": str, "funcionario": str, "area_atuacao_id": int, "uf": str},
    commission_fields=("comissionamento_por_funcionario",),
    export=ExportSpec(
        fields=CAMPOS_EXPORT,
        labels=LABELS_EXPORT,
        sheet_name="Organização de Documentos (LexPre)",
        rows=export_rows,
    ),
)
