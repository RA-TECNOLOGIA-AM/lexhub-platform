"""Peticionamento (LexPre) — cálculo da v1 ligado à casca da V2.

Corpo de `_build_peticionamento_lexpre_response` e `_rows_peticionamento_lexpre_export`
(api_dashboards/src/app/dashboard_routes.py) copiado SEM mudar a lógica, com os mesmos nomes da v1.
Só a entrada mudou (mesmas trocas do protocolo_lexpre.py). Novo na V2: `opcoes_filtro`.
"""

from datetime import date
from typing import Any

from app.analyses.NG.peticionamento_lexpre import (
    SETOR_PETICIONAMENTO_IDS as SETOR_PETICIONAMENTO_IDS_LEXPRE,
)
from app.analyses.NG.peticionamento_lexpre import (
    _entradas_por_demanda as entradas_por_demanda_peticionamento_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    _entradas_setor as entradas_setor_peticionamento_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    _filter_saidas_by_date_range as filter_saidas_peticionamento_lexpre_by_date_range,
)
from app.analyses.NG.peticionamento_lexpre import (
    _filter_saidas_by_protocolo_date_range as filter_saidas_peticionamento_lexpre_by_protocolo_date_range,
)
from app.analyses.NG.peticionamento_lexpre import (
    _filtrar_peticionados_reais as filtrar_peticionados_reais_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    _indexar_movimentacoes as indexar_movimentacoes_peticionamento_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    _normalizar_materia,
    filter_peticionamento_lexpre_por_area_atuacao,
    filter_peticionamento_lexpre_por_escritorio,
    filter_peticionamento_lexpre_por_funcionarios,
    filter_peticionamento_lexpre_por_materia,
    filter_peticionamento_lexpre_por_uf,
    list_funcionarios_peticionamento_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    _saidas_setor as saidas_setor_peticionamento_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    get_cancelados as get_cancelados_peticionamento_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    get_comissionamento_por_funcionario as get_comissionamento_por_funcionario_peticionamento_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    get_comparativo_cancelados as get_comparativo_cancelados_peticionamento_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    get_comparativo_mediana_tempo_peticionado as get_comparativo_mediana_tempo_peticionado_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    get_comparativo_peticionados_automaticamente as get_comparativo_peticionados_automaticamente_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    get_comparativo_peticionados_manualmente as get_comparativo_peticionados_manualmente_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    get_comparativo_protocolados_total as get_comparativo_protocolados_total_peticionamento_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    get_comparativo_retorno_org_doc as get_comparativo_retorno_org_doc_peticionamento_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    get_comparativo_retorno_pendencia as get_comparativo_retorno_pendencia_peticionamento_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    get_comparativo_tempo_medio_peticionado as get_comparativo_tempo_medio_peticionado_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    get_comparativo_ticket_medio_confeccionado as get_comparativo_ticket_medio_confeccionado_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    get_comparativo_total_peticionados as get_comparativo_total_peticionados_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    get_comparativo_valor_causa_confeccionado as get_comparativo_valor_causa_confeccionado_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    get_media_peticionado_por_funcionario as get_media_peticionado_por_funcionario_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    get_media_tempo_peticionado as get_media_tempo_peticionado_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    get_mediana_tempo_peticionado as get_mediana_tempo_peticionado_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    get_peticionados_automaticamente as get_peticionados_automaticamente_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    get_peticionados_manualmente as get_peticionados_manualmente_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    get_peticionados_por_dia_por_funcionario as get_peticionados_por_dia_por_funcionario_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    get_protocolados_por_funcionario as get_protocolados_por_funcionario_peticionamento_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    get_protocolados_total as get_protocolados_total_peticionamento_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    get_represados as get_represados_peticionamento_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    get_retorno_org_doc as get_retorno_org_doc_peticionamento_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    get_retorno_pendencia as get_retorno_pendencia_peticionamento_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    get_ticket_medio_confeccionado as get_ticket_medio_confeccionado_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    get_total_peticionados as get_total_peticionados_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    get_valor_causa_confeccionado as get_valor_causa_confeccionado_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    get_valor_causa_por_funcionario as get_valor_causa_por_funcionario_peticionamento_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    get_valor_causa_protocolado_por_funcionario as get_valor_causa_protocolado_por_funcionario_peticionamento_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    group_peticionados_por_dia as group_peticionados_por_dia_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    group_peticionados_por_funcionario as group_peticionados_por_funcionario_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    group_peticionados_por_materia as group_peticionados_por_materia_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    group_peticionados_por_mes as group_peticionados_por_mes_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    group_protocolados_por_materia as group_protocolados_por_materia_peticionamento_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    group_represados_por_funcionario as group_represados_por_funcionario_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    group_represados_por_materia as group_represados_por_materia_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    group_represados_por_mes as group_represados_por_mes_lexpre,
)
from app.analyses.NG.peticionamento_lexpre import (
    list_export_rows as list_export_rows_peticionamento_lexpre,
)
from app.analyses.v1_routes import (
    ChartDataPoint,
    ComissionamentoPeticionamentoLexpreRow,
    PeticionamentoLexpreNGResponse,
    PeticionamentoLexpreNGStats,
    PeticionamentoLexpreStat,
    PeticionamentoLexpreValorStat,
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
        list_funcionarios_peticionamento_lexpre,
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

    # --- v1: _build_peticionamento_lexpre_response (sem mudança daqui para baixo) ---
    rows_sem_materia = filter_peticionamento_lexpre_por_escritorio(
        await ctx.source.fetch("log_setor_demanda_lexpre_NG"), escritorio_id=escritorio_id
    )
    opcoes = opcoes_filtro(rows_sem_materia)  # V2: antes dos filtros
    rows_sem_materia = filter_peticionamento_lexpre_por_area_atuacao(
        rows_sem_materia, area_atuacao_id
    )
    rows_sem_materia = filter_peticionamento_lexpre_por_uf(rows_sem_materia, uf)
    rows_sem_materia = filter_peticionamento_lexpre_por_funcionarios(rows_sem_materia, funcionario)
    rows = filter_peticionamento_lexpre_por_materia(rows_sem_materia, materia)

    hoje = date.today()
    inicio, fim = (
        (from_date, to_date) if (from_date and to_date) else (date(hoje.year, hoje.month, 1), hoje)
    )

    # No sistema, uma demanda pode sair do Peticionamento para QUALQUER setor —
    # só a saída com destino Protocolo é uma confecção de fato; saídas para
    # Pendências/Organização de Documentos são devoluções (ver
    # get_retorno_org_doc/get_retorno_pendencia), não entram em "peticionados".
    idx = indexar_movimentacoes_peticionamento_lexpre(rows)
    # `saidas_todas` (sem filtro de destino) é a base de "Cancelados" — uma demanda
    # cancelada não tem destino pareado e seria descartada por `_filtrar_peticionados_reais`.
    saidas_todas = saidas_setor_peticionamento_lexpre(rows, SETOR_PETICIONAMENTO_IDS_LEXPRE)
    saidas = filtrar_peticionados_reais_lexpre(saidas_todas, idx)
    entradas_por_demanda = entradas_por_demanda_peticionamento_lexpre(
        entradas_setor_peticionamento_lexpre(rows, SETOR_PETICIONAMENTO_IDS_LEXPRE)
    )
    saidas_periodo = filter_saidas_peticionamento_lexpre_by_date_range(saidas, inicio, fim)
    saidas_todas_periodo = filter_saidas_peticionamento_lexpre_by_date_range(
        saidas_todas, inicio, fim
    )
    # Base de pagamento da comissão (01/10/2026, pedido do usuário): ancorada em
    # DATA_PROTOCOLO, não em DATA (saída) — ver docstring de
    # `get_comissionamento_por_funcionario`/`_filter_saidas_by_protocolo_date_range`.
    saidas_protocoladas_periodo = filter_saidas_peticionamento_lexpre_by_protocolo_date_range(
        saidas, inicio, fim
    )

    # Recorte GERAL (sem filtro de matéria) — só para a taxa de resolução do
    # comissionamento, que deve refletir a produtividade geral do funcionário,
    # não a fatia recortada pela matéria filtrada na página.
    idx_geral = indexar_movimentacoes_peticionamento_lexpre(rows_sem_materia)
    saidas_geral = filtrar_peticionados_reais_lexpre(
        saidas_setor_peticionamento_lexpre(rows_sem_materia, SETOR_PETICIONAMENTO_IDS_LEXPRE),
        idx_geral,
    )
    entradas_por_demanda_geral = entradas_por_demanda_peticionamento_lexpre(
        entradas_setor_peticionamento_lexpre(rows_sem_materia, SETOR_PETICIONAMENTO_IDS_LEXPRE)
    )
    saidas_periodo_geral = filter_saidas_peticionamento_lexpre_by_date_range(
        saidas_geral, inicio, fim
    )
    represados_por_funcionario_geral = {
        r["name"]: int(r["value"])
        for r in group_represados_por_funcionario_lexpre(rows_sem_materia)
    }

    peticionados_por_dia_por_func = get_peticionados_por_dia_por_funcionario_lexpre(
        saidas_periodo, entradas_por_demanda
    )

    response = PeticionamentoLexpreNGResponse(
        stats=PeticionamentoLexpreNGStats(
            total_peticionados=PeticionamentoLexpreStat(
                total=get_total_peticionados_lexpre(saidas_periodo),
                comparativo=get_comparativo_total_peticionados_lexpre(rows, inicio, fim),
            ),
            peticionados_manualmente=PeticionamentoLexpreStat(
                total=get_peticionados_manualmente_lexpre(saidas_periodo),
                comparativo=get_comparativo_peticionados_manualmente_lexpre(rows, inicio, fim),
            ),
            peticionados_automaticamente=PeticionamentoLexpreStat(
                total=get_peticionados_automaticamente_lexpre(saidas_periodo),
                comparativo=get_comparativo_peticionados_automaticamente_lexpre(rows, inicio, fim),
            ),
            cancelados=PeticionamentoLexpreStat(
                total=get_cancelados_peticionamento_lexpre(saidas_todas_periodo),
                comparativo=get_comparativo_cancelados_peticionamento_lexpre(rows, inicio, fim),
            ),
            protocolados_total=PeticionamentoLexpreStat(
                total=get_protocolados_total_peticionamento_lexpre(saidas_protocoladas_periodo),
                comparativo=get_comparativo_protocolados_total_peticionamento_lexpre(
                    rows, inicio, fim
                ),
            ),
            valor_causa_confeccionado=PeticionamentoLexpreValorStat(
                total=get_valor_causa_confeccionado_lexpre(saidas_periodo),
                comparativo=get_comparativo_valor_causa_confeccionado_lexpre(rows, inicio, fim),
            ),
            ticket_medio_confeccionado=PeticionamentoLexpreValorStat(
                total=get_ticket_medio_confeccionado_lexpre(saidas_periodo),
                comparativo=get_comparativo_ticket_medio_confeccionado_lexpre(rows, inicio, fim),
            ),
            media_tempo_peticionado=get_media_tempo_peticionado_lexpre(
                saidas_periodo, entradas_por_demanda
            ),
            mediana_tempo_peticionado=get_mediana_tempo_peticionado_lexpre(
                saidas_periodo, entradas_por_demanda
            ),
            comparativo_tempo_medio_peticionado=get_comparativo_tempo_medio_peticionado_lexpre(
                rows, inicio, fim
            ),
            comparativo_mediana_tempo_peticionado=get_comparativo_mediana_tempo_peticionado_lexpre(
                rows, inicio, fim
            ),
            represados=get_represados_peticionamento_lexpre(rows),
            retorno_org_doc=get_retorno_org_doc_peticionamento_lexpre(rows),
            retorno_pendencia=get_retorno_pendencia_peticionamento_lexpre(rows),
            comparativo_retorno_org_doc=get_comparativo_retorno_org_doc_peticionamento_lexpre(
                rows, inicio, fim
            ),
            comparativo_retorno_pendencia=get_comparativo_retorno_pendencia_peticionamento_lexpre(
                rows, inicio, fim
            ),
        ),
        peticionados_por_materia=[
            ChartDataPoint(**x) for x in group_peticionados_por_materia_lexpre(saidas_periodo)
        ],
        protocolados_por_materia=[
            ChartDataPoint(**x)
            for x in group_protocolados_por_materia_peticionamento_lexpre(
                saidas_protocoladas_periodo
            )
        ],
        represados_por_materia=[
            ChartDataPoint(**x) for x in group_represados_por_materia_lexpre(rows)
        ],
        # Evolução mês a mês usa o histórico completo (sem recorte de período) —
        # mesmo critério do dashboard antigo (banco `ng`).
        peticionados_por_mes=[
            ChartDataPoint(**x) for x in group_peticionados_por_mes_lexpre(saidas)
        ],
        represados_por_mes=[ChartDataPoint(**x) for x in group_represados_por_mes_lexpre(rows)],
        peticionados_por_dia=[
            ChartDataPoint(**x) for x in group_peticionados_por_dia_lexpre(saidas_periodo)
        ],
        peticionados_por_dia_por_funcionario={
            k: [ChartDataPoint(**i) for i in v]
            for k, v in peticionados_por_dia_por_func["por_funcionario"].items()
            if not funcionario or k in set(funcionario)
        },
        represados_por_funcionario=[
            ChartDataPoint(**x)
            for x in _restringir_por_funcionarios_selecionados(
                group_represados_por_funcionario_lexpre(rows), funcionario
            )
        ],
        peticionados_por_funcionario=[
            ChartDataPoint(**x)
            for x in _restringir_por_funcionarios_selecionados(
                group_peticionados_por_funcionario_lexpre(saidas_periodo, entradas_por_demanda),
                funcionario,
            )
        ],
        protocolados_por_funcionario=[
            ChartDataPoint(**x)
            for x in _restringir_por_funcionarios_selecionados(
                get_protocolados_por_funcionario_peticionamento_lexpre(
                    saidas_protocoladas_periodo, entradas_por_demanda
                ),
                funcionario,
            )
        ],
        media_peticionado_por_funcionario=[
            ChartDataPoint(**x)
            for x in _restringir_por_funcionarios_selecionados(
                get_media_peticionado_por_funcionario_lexpre(
                    saidas_periodo, entradas_por_demanda, inicio, fim
                ),
                funcionario,
            )
        ],
        valor_causa_por_funcionario=[
            ChartDataPoint(**x)
            for x in _restringir_por_funcionarios_selecionados(
                get_valor_causa_por_funcionario_peticionamento_lexpre(
                    saidas_periodo, entradas_por_demanda
                ),
                funcionario,
            )
        ],
        valor_causa_protocolado_por_funcionario=[
            ChartDataPoint(**x)
            for x in _restringir_por_funcionarios_selecionados(
                get_valor_causa_protocolado_por_funcionario_peticionamento_lexpre(
                    saidas_protocoladas_periodo, entradas_por_demanda
                ),
                funcionario,
            )
        ],
        comissionamento_por_funcionario=[
            ComissionamentoPeticionamentoLexpreRow(**x)
            for x in _restringir_por_funcionarios_selecionados(
                get_comissionamento_por_funcionario_peticionamento_lexpre(
                    saidas_protocoladas_periodo,
                    entradas_por_demanda,
                    saidas_periodo_geral,
                    entradas_por_demanda_geral,
                    represados_por_funcionario_geral,
                ),
                funcionario,
                key="funcionario",
            )
        ],
        funcionarios_peticionamento=list_funcionarios_peticionamento_lexpre(rows),
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

    # --- v1: _rows_peticionamento_lexpre_export (sem mudança) ---
    rows = filter_peticionamento_lexpre_por_escritorio(
        await ctx.source.fetch("log_setor_demanda_lexpre_NG"), escritorio_id=escritorio_id
    )
    rows = filter_peticionamento_lexpre_por_materia(rows, materia)
    rows = filter_peticionamento_lexpre_por_area_atuacao(rows, area_atuacao_id)
    rows = filter_peticionamento_lexpre_por_uf(rows, uf)
    rows = filter_peticionamento_lexpre_por_funcionarios(rows, funcionario)

    hoje = date.today()
    inicio, fim = (
        (from_date, to_date) if (from_date and to_date) else (date(hoje.year, hoje.month, 1), hoje)
    )
    return list_export_rows_peticionamento_lexpre(rows, inicio, fim)


# Copiados da v1 sem mudança (_CAMPOS_EXPORT_PETICIONAMENTO_LEXPRE_NG, _LABELS_EXPORT_PETICIONAMENTO_LEXPRE_NG).
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
    key="peticionamento-lexpre",
    source_db="lexpre",
    source_label="LexPre",
    build=build,
    queries=QUERIES,
    # Mesmos parâmetros da v1 (GET /peticionamento-lexpre).
    filters={"materia": str, "funcionario": str, "area_atuacao_id": int, "uf": str},
    commission_fields=("comissionamento_por_funcionario",),
    export=ExportSpec(
        fields=CAMPOS_EXPORT,
        labels=LABELS_EXPORT,
        sheet_name="Peticionamento (LexPre)",
        rows=export_rows,
    ),
)
