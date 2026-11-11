"""Protocolo (LexPre) — cálculo da v1 ligado à casca da V2.

Corpo de `_build_protocolo_lexpre_response` e `_rows_protocolo_lexpre_export`
(api_dashboards/src/app/dashboard_routes.py) copiado SEM mudar a lógica, com os mesmos nomes da v1.
Só a entrada mudou:

    v1                                              aqui
    await fetch_log_setor_demanda_lexpre_ng()  ->  await ctx.source.fetch("log_setor_demanda_lexpre_NG")
    escritorio_id (ESCRITORIO_NGAM etc.)        ->  int(ctx.unit_ref)          (app.unit_source_refs)
    from_date / to_date (+ padrão do mês)       ->  ctx.period.start / end     (padrão já aplicado pela casca)
    materia, funcionario, area_atuacao_id, uf   ->  ctx.filters[...]            ([] = sem filtro)

Funções de análise: app/analyses/NG/protocolo_setor_lexpre.py e app/analyses/v1_routes.py (cópias da v1).
Novo na V2: `opcoes_filtro` (valores dos filtros nas linhas da unidade, antes de aplicar os filtros).
A casca cuida de `meta`, acesso, comissão (todos x só a própria) e dos campos novos da V2 (null).
"""

from typing import Any

from app.analyses.NG.protocolo_setor_lexpre import (
    SETOR_PROTOCOLO_IDS as SETOR_PROTOCOLO_IDS_LEXPRE,
)
from app.analyses.NG.protocolo_setor_lexpre import (
    _entradas_por_demanda as entradas_por_demanda_protocolo_lexpre,
)
from app.analyses.NG.protocolo_setor_lexpre import (
    _entradas_setor as entradas_setor_protocolo_lexpre,
)
from app.analyses.NG.protocolo_setor_lexpre import (
    _filter_saidas_by_date_range as filter_saidas_protocolo_lexpre_by_date_range,
)
from app.analyses.NG.protocolo_setor_lexpre import (
    _filtrar_protocolados_reais as filtrar_protocolados_reais_lexpre,
)
from app.analyses.NG.protocolo_setor_lexpre import (
    _normalizar_materia,
    filter_protocolo_lexpre_por_area_atuacao,
    filter_protocolo_lexpre_por_escritorio,
    filter_protocolo_lexpre_por_funcionarios,
    filter_protocolo_lexpre_por_materia,
    filter_protocolo_lexpre_por_uf,
    list_funcionarios_protocolo_lexpre,
)
from app.analyses.NG.protocolo_setor_lexpre import (
    _saidas_setor as saidas_setor_protocolo_lexpre,
)
from app.analyses.NG.protocolo_setor_lexpre import (
    get_comissionamento_por_funcionario as get_comissionamento_por_funcionario_protocolo_lexpre,
)
from app.analyses.NG.protocolo_setor_lexpre import (
    get_comparativo_devolvido_org_doc as get_comparativo_devolvido_org_doc_protocolo_lexpre,
)
from app.analyses.NG.protocolo_setor_lexpre import (
    get_comparativo_devolvido_pendencia as get_comparativo_devolvido_pendencia_protocolo_lexpre,
)
from app.analyses.NG.protocolo_setor_lexpre import (
    get_comparativo_devolvido_peticionamento as get_comparativo_devolvido_peticionamento_protocolo_lexpre,
)
from app.analyses.NG.protocolo_setor_lexpre import (
    get_comparativo_mediana_tempo_protocolado as get_comparativo_mediana_tempo_protocolado_lexpre,
)
from app.analyses.NG.protocolo_setor_lexpre import (
    get_comparativo_protocolados_total as get_comparativo_protocolados_total_lexpre,
)
from app.analyses.NG.protocolo_setor_lexpre import (
    get_comparativo_tempo_medio_protocolado as get_comparativo_tempo_medio_protocolado_lexpre,
)
from app.analyses.NG.protocolo_setor_lexpre import (
    get_comparativo_ticket_medio_protocolado as get_comparativo_ticket_medio_protocolado_lexpre_setor,
)
from app.analyses.NG.protocolo_setor_lexpre import (
    get_comparativo_valor_causa_protocolado as get_comparativo_valor_causa_protocolado_lexpre_setor,
)
from app.analyses.NG.protocolo_setor_lexpre import (
    get_devolvido_org_doc as get_devolvido_org_doc_protocolo_lexpre,
)
from app.analyses.NG.protocolo_setor_lexpre import (
    get_devolvido_pendencia as get_devolvido_pendencia_protocolo_lexpre,
)
from app.analyses.NG.protocolo_setor_lexpre import (
    get_devolvido_peticionamento as get_devolvido_peticionamento_protocolo_lexpre,
)
from app.analyses.NG.protocolo_setor_lexpre import (
    get_media_protocolados_por_funcionario as get_media_protocolados_por_funcionario_lexpre,
)
from app.analyses.NG.protocolo_setor_lexpre import (
    get_media_tempo_protocolado as get_media_tempo_protocolado_lexpre,
)
from app.analyses.NG.protocolo_setor_lexpre import (
    get_mediana_tempo_protocolado as get_mediana_tempo_protocolado_lexpre,
)
from app.analyses.NG.protocolo_setor_lexpre import (
    get_protocolados_por_dia_por_funcionario as get_protocolados_por_dia_por_funcionario_lexpre,
)
from app.analyses.NG.protocolo_setor_lexpre import (
    get_protocolados_total as get_protocolados_total_lexpre,
)
from app.analyses.NG.protocolo_setor_lexpre import (
    get_represados as get_represados_protocolo_lexpre,
)
from app.analyses.NG.protocolo_setor_lexpre import (
    get_ticket_medio_protocolado as get_ticket_medio_protocolado_lexpre_setor,
)
from app.analyses.NG.protocolo_setor_lexpre import (
    get_valor_causa_por_funcionario as get_valor_causa_por_funcionario_protocolo_lexpre,
)
from app.analyses.NG.protocolo_setor_lexpre import (
    get_valor_causa_protocolado as get_valor_causa_protocolado_lexpre_setor,
)
from app.analyses.NG.protocolo_setor_lexpre import (
    group_protocolados_por_dia as group_protocolados_por_dia_lexpre,
)
from app.analyses.NG.protocolo_setor_lexpre import (
    group_protocolados_por_funcionario as group_protocolados_por_funcionario_lexpre,
)
from app.analyses.NG.protocolo_setor_lexpre import (
    group_protocolados_por_materia as group_protocolados_por_materia_lexpre,
)
from app.analyses.NG.protocolo_setor_lexpre import (
    group_protocolados_por_mes as group_protocolados_por_mes_lexpre,
)
from app.analyses.NG.protocolo_setor_lexpre import (
    group_represados_por_funcionario as group_represados_por_funcionario_protocolo_lexpre,
)
from app.analyses.NG.protocolo_setor_lexpre import (
    group_represados_por_materia as group_represados_por_materia_protocolo_lexpre,
)
from app.analyses.NG.protocolo_setor_lexpre import (
    group_represados_por_mes as group_represados_por_mes_protocolo_lexpre,
)
from app.analyses.NG.protocolo_setor_lexpre import (
    list_export_rows as list_export_rows_protocolo_lexpre,
)
from app.analyses.v1_routes import (
    ChartDataPoint,
    ProtocoloLexpreComissionamentoRow,
    ProtocoloLexpreNGResponse,
    ProtocoloLexpreNGStats,
    ProtocoloLexpreStat,
    ProtocoloLexpreValorStat,
    _filtrar_lexpre_por_ufs,
    _restringir_por_funcionarios_selecionados,
)
from app.dashboards.base import DashboardContext, DashboardModule, ExportSpec

QUERY = "log_setor_demanda_lexpre_NG"


def opcoes_filtro(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Novo na V2: valores possíveis de cada filtro, nas linhas da unidade ANTES dos filtros.

    Mesmos campos que os filtros da v1 comparam: MATERIA (normalizada), funcionários com entrada no
    setor (list_funcionarios_protocolo_lexpre, a mesma lista de GET /protocolo-lexpre/funcionarios),
    UF do cliente e área de atuação (AREA_ATUACAO_ID/NOME).
    """
    materias: dict[str, str] = {}
    ufs: set[str] = set()
    areas: dict[int, str] = {}
    for row in rows:
        materia = row.get("MATERIA")
        if materia is not None and str(materia).strip():
            materias.setdefault(_normalizar_materia(materia), str(materia).strip())
        uf = str(row.get("UF") or "").strip().upper()
        if uf:
            ufs.add(uf)
        area_id = row.get("AREA_ATUACAO_ID")
        if area_id is not None:
            areas.setdefault(int(area_id), str(row.get("AREA_ATUACAO_NOME") or area_id).strip())
    return {
        "materias": sorted(materias.values(), key=str.lower),
        "funcionarios": list_funcionarios_protocolo_lexpre(rows),
        "ufs": sorted(ufs),
        "areas": [
            {"id": i, "nome": n} for i, n in sorted(areas.items(), key=lambda a: a[1].lower())
        ],
    }


async def build(ctx: DashboardContext) -> dict:
    # --- entrada (V2) ---
    escritorio_id = int(ctx.unit_ref)
    materia = ctx.filters["materia"]
    funcionario = ctx.filters["funcionario"]
    area_atuacao_id = ctx.filters["area_atuacao_id"]
    uf = ctx.filters["uf"]
    inicio, fim = ctx.period.start, ctx.period.end

    # --- v1: _build_protocolo_lexpre_response (sem mudança daqui para baixo) ---
    rows = filter_protocolo_lexpre_por_escritorio(
        await ctx.source.fetch(QUERY), escritorio_id=escritorio_id
    )
    opcoes = opcoes_filtro(rows)  # V2: antes dos filtros
    rows = filter_protocolo_lexpre_por_materia(rows, materia)
    rows = filter_protocolo_lexpre_por_area_atuacao(rows, area_atuacao_id)
    # Aceita uma UF (dashboard próprio) ou várias (Controle de Processos NG, multi-UF).
    rows = _filtrar_lexpre_por_ufs(rows, [uf] if isinstance(uf, str) else uf)
    rows = filter_protocolo_lexpre_por_funcionarios(rows, funcionario)

    # "Protocolados" usa só as saídas cujo status chegou a "Aguardando Despacho
    # Inicial" — as demais saídas do setor (status ainda não resolvido) não
    # entram aqui; essas demandas seguem contabilizadas em "Represados" pelo
    # setor atual, sem rastreio de devolução por setor de destino.
    saidas = filtrar_protocolados_reais_lexpre(
        saidas_setor_protocolo_lexpre(rows, SETOR_PROTOCOLO_IDS_LEXPRE)
    )
    entradas_por_demanda = entradas_por_demanda_protocolo_lexpre(
        entradas_setor_protocolo_lexpre(rows, SETOR_PROTOCOLO_IDS_LEXPRE)
    )
    saidas_periodo = filter_saidas_protocolo_lexpre_by_date_range(saidas, inicio, fim)

    protocolados_por_dia_por_func = get_protocolados_por_dia_por_funcionario_lexpre(
        saidas_periodo, entradas_por_demanda
    )

    response = ProtocoloLexpreNGResponse(
        stats=ProtocoloLexpreNGStats(
            protocolados_total=ProtocoloLexpreStat(
                total=get_protocolados_total_lexpre(saidas_periodo),
                comparativo=get_comparativo_protocolados_total_lexpre(rows, inicio, fim),
            ),
            valor_causa_protocolado=ProtocoloLexpreValorStat(
                total=get_valor_causa_protocolado_lexpre_setor(saidas_periodo),
                comparativo=get_comparativo_valor_causa_protocolado_lexpre_setor(rows, inicio, fim),
            ),
            ticket_medio_protocolado=ProtocoloLexpreValorStat(
                total=get_ticket_medio_protocolado_lexpre_setor(saidas_periodo),
                comparativo=get_comparativo_ticket_medio_protocolado_lexpre_setor(
                    rows, inicio, fim
                ),
            ),
            media_tempo_protocolado=get_media_tempo_protocolado_lexpre(
                saidas_periodo, entradas_por_demanda
            ),
            mediana_tempo_protocolado=get_mediana_tempo_protocolado_lexpre(
                saidas_periodo, entradas_por_demanda
            ),
            comparativo_tempo_medio_protocolado=get_comparativo_tempo_medio_protocolado_lexpre(
                rows, inicio, fim
            ),
            comparativo_mediana_tempo_protocolado=get_comparativo_mediana_tempo_protocolado_lexpre(
                rows, inicio, fim
            ),
            represados=get_represados_protocolo_lexpre(rows),
            devolvido_peticionamento=get_devolvido_peticionamento_protocolo_lexpre(rows),
            devolvido_org_doc=get_devolvido_org_doc_protocolo_lexpre(rows),
            devolvido_pendencia=get_devolvido_pendencia_protocolo_lexpre(rows),
            comparativo_devolvido_peticionamento=get_comparativo_devolvido_peticionamento_protocolo_lexpre(
                rows, inicio, fim
            ),
            comparativo_devolvido_org_doc=get_comparativo_devolvido_org_doc_protocolo_lexpre(
                rows, inicio, fim
            ),
            comparativo_devolvido_pendencia=get_comparativo_devolvido_pendencia_protocolo_lexpre(
                rows, inicio, fim
            ),
        ),
        protocolados_por_materia=[
            ChartDataPoint(**x) for x in group_protocolados_por_materia_lexpre(saidas_periodo)
        ],
        represados_por_materia=[
            ChartDataPoint(**x) for x in group_represados_por_materia_protocolo_lexpre(rows)
        ],
        # Evolução mês a mês usa o histórico completo (sem recorte de período) —
        # mesmo critério do dashboard antigo (banco `ng`).
        protocolados_por_mes=[
            ChartDataPoint(**x) for x in group_protocolados_por_mes_lexpre(saidas)
        ],
        represados_por_mes=[
            ChartDataPoint(**x) for x in group_represados_por_mes_protocolo_lexpre(rows)
        ],
        protocolados_por_dia=[
            ChartDataPoint(**x) for x in group_protocolados_por_dia_lexpre(saidas_periodo)
        ],
        protocolados_por_dia_por_funcionario={
            k: [ChartDataPoint(**i) for i in v]
            for k, v in protocolados_por_dia_por_func["por_funcionario"].items()
            if not funcionario or k in set(funcionario)
        },
        represados_por_funcionario=[
            ChartDataPoint(**x)
            for x in _restringir_por_funcionarios_selecionados(
                group_represados_por_funcionario_protocolo_lexpre(rows), funcionario
            )
        ],
        protocolados_por_funcionario=[
            ChartDataPoint(**x)
            for x in _restringir_por_funcionarios_selecionados(
                group_protocolados_por_funcionario_lexpre(saidas_periodo, entradas_por_demanda),
                funcionario,
            )
        ],
        media_protocolados_por_funcionario=[
            ChartDataPoint(**x)
            for x in _restringir_por_funcionarios_selecionados(
                get_media_protocolados_por_funcionario_lexpre(
                    saidas_periodo, entradas_por_demanda, inicio, fim
                ),
                funcionario,
            )
        ],
        valor_causa_por_funcionario=[
            ChartDataPoint(**x)
            for x in _restringir_por_funcionarios_selecionados(
                get_valor_causa_por_funcionario_protocolo_lexpre(
                    saidas_periodo, entradas_por_demanda
                ),
                funcionario,
            )
        ],
        comissionamento_por_funcionario=[
            ProtocoloLexpreComissionamentoRow(**x)
            for x in _restringir_por_funcionarios_selecionados(
                get_comissionamento_por_funcionario_protocolo_lexpre(
                    saidas_periodo, entradas_por_demanda
                ),
                funcionario,
                key="funcionario",
            )
        ],
        funcionarios_protocolo=list_funcionarios_protocolo_lexpre(rows),
    )
    # --- saída (V2): o JSON da v1 + opcoes_filtro ---
    return {**response.model_dump(), "opcoes_filtro": opcoes}


async def export_rows(ctx: DashboardContext) -> list[dict]:
    # --- entrada (V2) ---
    escritorio_id = int(ctx.unit_ref)
    materia = ctx.filters["materia"]
    funcionario = ctx.filters["funcionario"]
    area_atuacao_id = ctx.filters["area_atuacao_id"]
    uf = ctx.filters["uf"]
    inicio, fim = ctx.period.start, ctx.period.end

    # --- v1: _rows_protocolo_lexpre_export (sem mudança) ---
    rows = filter_protocolo_lexpre_por_escritorio(
        await ctx.source.fetch(QUERY), escritorio_id=escritorio_id
    )
    rows = filter_protocolo_lexpre_por_materia(rows, materia)
    rows = filter_protocolo_lexpre_por_area_atuacao(rows, area_atuacao_id)
    rows = filter_protocolo_lexpre_por_uf(rows, uf)
    rows = filter_protocolo_lexpre_por_funcionarios(rows, funcionario)
    return list_export_rows_protocolo_lexpre(rows, inicio, fim)


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
