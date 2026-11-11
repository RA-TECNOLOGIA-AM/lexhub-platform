"""Pendências (LexPre) — cálculo da v1 ligado à casca da V2.

Corpo de `_build_pendencia_lexpre_response` e `_rows_pendencia_lexpre_export`
(api_dashboards/src/app/dashboard_routes.py) copiado SEM mudar a lógica, com os mesmos nomes da v1.
Só a entrada mudou (mesmas trocas do protocolo_lexpre.py; também fetch_setor_func_lexpre() ->
ctx.source.fetch("setor_func_lexpre_NG")). Novo na V2: `opcoes_filtro` (sem matéria: a v1 não filtra).
"""

from datetime import date
from typing import Any

from app.analyses.NG.pendencia_setor_lexpre import (
    SETOR_PENDENCIAS_IDS as SETOR_PENDENCIAS_IDS_LEXPRE,
)
from app.analyses.NG.pendencia_setor_lexpre import (
    _construir_visitas as construir_visitas_pendencia_lexpre,
)
from app.analyses.NG.pendencia_setor_lexpre import (
    _indexar_movimentacoes as indexar_movimentacoes_pendencia_lexpre,
)
from app.analyses.NG.pendencia_setor_lexpre import (
    _normalizar_materia,
    filter_pendencia_lexpre_por_area_atuacao,
    filter_pendencia_lexpre_por_escritorio,
    filter_pendencia_lexpre_por_funcionarios,
    filter_pendencia_lexpre_por_uf,
    list_funcionarios_pendencia_lexpre,
)
from app.analyses.NG.pendencia_setor_lexpre import (
    _visitas_periodo as visitas_periodo_pendencia_lexpre,
)
from app.analyses.NG.pendencia_setor_lexpre import (
    build_funcionarios_do_setor as build_funcionarios_do_setor_pendencia_lexpre,
)
from app.analyses.NG.pendencia_setor_lexpre import (
    get_comparativo_mediana_tempo_resolvidos as get_comparativo_mediana_tempo_resolvidos_pendencia_lexpre,
)
from app.analyses.NG.pendencia_setor_lexpre import (
    get_comparativo_pendencias_resolvidas as get_comparativo_pendencias_resolvidas_lexpre,
)
from app.analyses.NG.pendencia_setor_lexpre import (
    get_comparativo_tempo_medio_resolvidos as get_comparativo_tempo_medio_resolvidos_pendencia_lexpre,
)
from app.analyses.NG.pendencia_setor_lexpre import (
    get_media_resolvidas_por_funcionario as get_media_resolvidas_por_funcionario_pendencia_lexpre,
)
from app.analyses.NG.pendencia_setor_lexpre import (
    get_media_tempo_resolvidos as get_media_tempo_resolvidos_pendencia_lexpre,
)
from app.analyses.NG.pendencia_setor_lexpre import (
    get_mediana_tempo_resolvidos as get_mediana_tempo_resolvidos_pendencia_lexpre,
)
from app.analyses.NG.pendencia_setor_lexpre import (
    get_pendencias_canceladas as get_pendencias_canceladas_lexpre,
)
from app.analyses.NG.pendencia_setor_lexpre import (
    get_pendencias_comissionamento_por_funcionario as get_pendencias_comissionamento_por_funcionario_lexpre,
)
from app.analyses.NG.pendencia_setor_lexpre import (
    get_pendencias_nao_resolvidas as get_pendencias_nao_resolvidas_lexpre,
)
from app.analyses.NG.pendencia_setor_lexpre import (
    get_pendencias_nao_resolvidas_com_atraso as get_pendencias_nao_resolvidas_com_atraso_lexpre,
)
from app.analyses.NG.pendencia_setor_lexpre import (
    get_pendencias_resolvidas as get_pendencias_resolvidas_lexpre,
)
from app.analyses.NG.pendencia_setor_lexpre import (
    get_pendencias_taxa_canceladas as get_pendencias_taxa_canceladas_lexpre,
)
from app.analyses.NG.pendencia_setor_lexpre import (
    get_pendencias_taxa_nao_resolvidos as get_pendencias_taxa_nao_resolvidos_lexpre,
)
from app.analyses.NG.pendencia_setor_lexpre import (
    get_pendencias_taxa_resolvidos as get_pendencias_taxa_resolvidos_lexpre,
)
from app.analyses.NG.pendencia_setor_lexpre import (
    get_pendencias_total as get_pendencias_total_lexpre,
)
from app.analyses.NG.pendencia_setor_lexpre import (
    get_pendencias_triagem as get_pendencias_triagem_lexpre,
)
from app.analyses.NG.pendencia_setor_lexpre import (
    get_resolvidas_por_dia_por_funcionario as get_resolvidas_por_dia_por_funcionario_pendencia_lexpre,
)
from app.analyses.NG.pendencia_setor_lexpre import (
    group_nao_resolvidas_por_origem as group_nao_resolvidas_por_origem_pendencia_lexpre,
)
from app.analyses.NG.pendencia_setor_lexpre import (
    group_resolvidas_por_dia as group_resolvidas_por_dia_pendencia_lexpre,
)
from app.analyses.NG.pendencia_setor_lexpre import (
    group_resolvidas_por_mes as group_resolvidas_por_mes_pendencia_lexpre,
)
from app.analyses.NG.pendencia_setor_lexpre import (
    list_export_rows as list_export_rows_pendencia_lexpre,
)
from app.analyses.v1_routes import (
    ChartDataPoint,
    PendenciaLexpreComissaoRow,
    PendenciaLexpreNGResponse,
    PendenciaLexpreNGStats,
    _restringir_por_funcionarios_selecionados,
)
from app.dashboards.base import DashboardContext, DashboardModule, ExportSpec
from app.dashboards.opcoes_lexpre import opcoes_filtro_setor

QUERIES = ("log_setor_demanda_lexpre_NG", "setor_func_lexpre_NG")


def opcoes_filtro(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Novo na V2: valores possíveis dos filtros, nas linhas da unidade ANTES dos filtros."""
    return opcoes_filtro_setor(
        rows,
        _normalizar_materia,
        list_funcionarios_pendencia_lexpre,
        ("funcionarios", "ufs", "areas"),
    )


async def build(ctx: DashboardContext) -> dict:
    # --- entrada (V2) ---
    escritorio_id = int(ctx.unit_ref)
    from_date = ctx.period.start
    to_date = ctx.period.end
    funcionario = ctx.filters["funcionario"]
    area_atuacao_id = ctx.filters["area_atuacao_id"]
    uf = ctx.filters["uf"]

    # --- v1: _build_pendencia_lexpre_response (sem mudança daqui para baixo) ---
    rows = filter_pendencia_lexpre_por_escritorio(
        await ctx.source.fetch("log_setor_demanda_lexpre_NG"), escritorio_id=escritorio_id
    )
    opcoes = opcoes_filtro(rows)  # V2: antes dos filtros
    rows = filter_pendencia_lexpre_por_area_atuacao(rows, area_atuacao_id)
    rows = filter_pendencia_lexpre_por_uf(rows, uf)
    rows = filter_pendencia_lexpre_por_funcionarios(rows, funcionario)

    hoje = date.today()
    inicio, fim = (
        (from_date, to_date) if (from_date and to_date) else (date(hoje.year, hoje.month, 1), hoje)
    )

    idx = indexar_movimentacoes_pendencia_lexpre(rows)
    funcionarios_pendencia_ids = build_funcionarios_do_setor_pendencia_lexpre(
        await ctx.source.fetch("setor_func_lexpre_NG"), SETOR_PENDENCIAS_IDS_LEXPRE
    )
    visitas = construir_visitas_pendencia_lexpre(
        rows, SETOR_PENDENCIAS_IDS_LEXPRE, funcionarios_pendencia_ids
    )
    visitas_periodo = visitas_periodo_pendencia_lexpre(visitas, inicio, fim)

    resolvidas_por_dia_por_func = get_resolvidas_por_dia_por_funcionario_pendencia_lexpre(
        visitas_periodo
    )

    response = PendenciaLexpreNGResponse(
        stats=PendenciaLexpreNGStats(
            pendencias_total=get_pendencias_total_lexpre(visitas_periodo),
            pendencias_resolvidas=get_pendencias_resolvidas_lexpre(visitas_periodo),
            pendencias_canceladas=get_pendencias_canceladas_lexpre(visitas_periodo),
            pendencias_taxa_resolvidos=get_pendencias_taxa_resolvidos_lexpre(visitas_periodo),
            pendencias_taxa_nao_resolvidos=get_pendencias_taxa_nao_resolvidos_lexpre(
                visitas_periodo
            ),
            pendencias_taxa_canceladas=get_pendencias_taxa_canceladas_lexpre(visitas_periodo),
            media_tempo_resolvidos_pendencia=get_media_tempo_resolvidos_pendencia_lexpre(
                visitas_periodo
            ),
            mediana_tempo_resolvidos_pendencia=get_mediana_tempo_resolvidos_pendencia_lexpre(
                visitas_periodo
            ),
            comparativo_pendencias_resolvidas=get_comparativo_pendencias_resolvidas_lexpre(
                visitas, inicio, fim
            ),
            comparativo_tempo_medio_resolvidos_pendencia=get_comparativo_tempo_medio_resolvidos_pendencia_lexpre(
                visitas, inicio, fim
            ),
            comparativo_mediana_tempo_resolvidos_pendencia=get_comparativo_mediana_tempo_resolvidos_pendencia_lexpre(
                visitas, inicio, fim
            ),
            pendencias_nao_resolvidas=get_pendencias_nao_resolvidas_lexpre(visitas),
            pendencias_nao_resolvidas_com_atraso=get_pendencias_nao_resolvidas_com_atraso_lexpre(
                visitas, hoje
            ),
            pendencias_triagem=get_pendencias_triagem_lexpre(rows),
        ),
        pendencias_nao_resolvidas_por_origem=[
            ChartDataPoint(**x)
            for x in group_nao_resolvidas_por_origem_pendencia_lexpre(visitas, idx)
        ],
        # Evolução mês a mês usa o histórico completo (sem recorte de período) —
        # mesmo critério dos outros dashboards lexpre para essa série.
        pendencias_resolvidas_por_mes=[
            ChartDataPoint(**x) for x in group_resolvidas_por_mes_pendencia_lexpre(visitas)
        ],
        pendencias_resolvidas_por_dia=[
            ChartDataPoint(**x) for x in group_resolvidas_por_dia_pendencia_lexpre(visitas_periodo)
        ],
        pendencias_resolvidas_por_dia_por_funcionario={
            k: [ChartDataPoint(**i) for i in v]
            for k, v in resolvidas_por_dia_por_func["por_funcionario"].items()
            if not funcionario or k in set(funcionario)
        },
        media_pendencias_resolvidas_por_funcionario=[
            ChartDataPoint(**x)
            for x in _restringir_por_funcionarios_selecionados(
                get_media_resolvidas_por_funcionario_pendencia_lexpre(visitas_periodo), funcionario
            )
        ],
        funcionarios_pendencias=list_funcionarios_pendencia_lexpre(rows),
        comissionamento_pendencias_por_funcionario=[
            PendenciaLexpreComissaoRow(**x)
            for x in _restringir_por_funcionarios_selecionados(
                get_pendencias_comissionamento_por_funcionario_lexpre(visitas_periodo),
                funcionario,
                key="funcionario",
            )
        ],
    )
    # --- saída (V2): o JSON da v1 + opcoes_filtro ---
    return {**response.model_dump(), "opcoes_filtro": opcoes}


async def export_rows(ctx: DashboardContext) -> list[dict]:
    # --- entrada (V2) ---
    escritorio_id = int(ctx.unit_ref)
    from_date = ctx.period.start
    to_date = ctx.period.end
    funcionario = ctx.filters["funcionario"]
    area_atuacao_id = ctx.filters["area_atuacao_id"]
    uf = ctx.filters["uf"]

    # --- v1: _rows_pendencia_lexpre_export (sem mudança) ---
    rows = filter_pendencia_lexpre_por_escritorio(
        await ctx.source.fetch("log_setor_demanda_lexpre_NG"), escritorio_id=escritorio_id
    )
    rows = filter_pendencia_lexpre_por_area_atuacao(rows, area_atuacao_id)
    rows = filter_pendencia_lexpre_por_uf(rows, uf)
    rows = filter_pendencia_lexpre_por_funcionarios(rows, funcionario)

    hoje = date.today()
    inicio, fim = (
        (from_date, to_date) if (from_date and to_date) else (date(hoje.year, hoje.month, 1), hoje)
    )
    idx = indexar_movimentacoes_pendencia_lexpre(rows)
    funcionarios_pendencia_ids = build_funcionarios_do_setor_pendencia_lexpre(
        await ctx.source.fetch("setor_func_lexpre_NG"), SETOR_PENDENCIAS_IDS_LEXPRE
    )
    return list_export_rows_pendencia_lexpre(rows, idx, inicio, fim, funcionarios_pendencia_ids)


# Copiados da v1 sem mudança (_CAMPOS_EXPORT_PENDENCIA_LEXPRE_NG, _LABELS_EXPORT_PENDENCIA_LEXPRE_NG).
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
    queries=QUERIES,
    # Mesmos parâmetros da v1 (GET /pendencia-lexpre: sem matéria).
    filters={"funcionario": str, "area_atuacao_id": int, "uf": str},
    commission_fields=("comissionamento_pendencias_por_funcionario",),
    export=ExportSpec(
        fields=CAMPOS_EXPORT,
        labels=LABELS_EXPORT,
        sheet_name="Pendências (LexPre)",
        rows=export_rows,
    ),
)
