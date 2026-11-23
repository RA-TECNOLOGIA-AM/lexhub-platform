"""Dashboards "genéricos" da v1 (ramos de _get_dashboard_response) usados pela V2 — cópia SEM mudança.

Origem: api_dashboards/src/app/dashboard_routes.py (linha na v1 ao lado de cada bloco).
Gerado por scripts/copiar_v1/gerar_generico.py (banco lexflow). Únicas trocas, marcadas com "V2:":
  * fetch_*: buscam pela fonte da V2 (`usar_fonte`), com o recorte de situação do processo da v1;
  * _get_dashboard_response: mesmo início da v1 (fontes, datas, _f/_a), só com os ramos abaixo;
  * fontes de outro banco saem de FETCHES_BY_DASHBOARD (chegam vazias, como na v1 com a fonte fora do ar).
Dashboards: emendas_manifestacoes_NG, emendas_manifestacoes_LA.
"""

import asyncio
import logging
import time
from contextvars import ContextVar
from app.analyses.common import periodo  # V2: período e variação vs período anterior num módulo só
from app.analyses.common import conversao  # V2: conversões dos valores do banco num módulo só
from app.analyses.common import memo  # V2: cache por pedido (a mesma conta uma vez por pedido)
from app.analyses.LA.emendas_manifestacoes_LA import (
    EmendasManifestacoesAtividadesFiltros,
    SITUACOES_VALIDAS_EMENDAS_MANIFESTACOES,
    filtrar_agendamentos_emendas_manifestacoes_LA,
    get_emendas_manifestacoes_comissionamento_por_funcionario_LA,
    get_emendas_manifestacoes_concluidas_por_dia_por_funcionario_LA,
    get_emendas_manifestacoes_concluidas_por_prazo_por_dia_por_funcionario_LA,
    get_kpis_atividades_emendas_manifestacoes_LA,
    get_kpis_emendas_manifestacoes_por_prazo_LA,
    get_media_emendas_manifestacoes_concluidas_por_funcionario_LA,
    get_media_emendas_manifestacoes_concluidas_por_prazo_por_funcionario_LA,
    get_opcoes_filtros_emendas_manifestacoes_LA,
    get_opcoes_filtros_emendas_manifestacoes_por_prazo_LA,
    group_emendas_manifestacoes_concluidas_por_dia_LA,
    group_emendas_manifestacoes_concluidas_por_mes_LA,
    group_emendas_manifestacoes_concluidas_por_prazo_por_dia_LA,
    group_emendas_manifestacoes_concluidas_por_prazo_por_mes_LA,
    group_emendas_manifestacoes_demandas_por_funcionario_LA,
    group_emendas_manifestacoes_demandas_por_funcionario_por_prazo_LA,
    group_emendas_manifestacoes_processos_por_atividade_LA,
    group_emendas_manifestacoes_processos_por_atividade_por_prazo_LA,
    list_emendas_manifestacoes_atividades_periodo_LA,
    list_emendas_manifestacoes_por_prazo_LA,
)
from app.analyses.NG.comercial_geral import (
    filter_comercial_geral_por_area_atuacao,
)
from app.analyses.NG.emendas_manifestacoes_NG import (
    EmendasManifestacoesAtividadesFiltrosNG,
    SITUACOES_VALIDAS_EMENDAS_MANIFESTACOES_NG,
    filtrar_agendamentos_emendas_manifestacoes_NG,
    get_comparativo_qtd_dilacoes_emendas_manifestacoes_NG,
    get_comparativo_qtd_manifestacoes_emendas_manifestacoes_NG,
    get_emendas_manifestacoes_comissionamento_por_funcionario_NG,
    get_emendas_manifestacoes_concluidas_por_dia_por_funcionario_NG,
    get_emendas_manifestacoes_concluidas_por_prazo_por_dia_por_funcionario_NG,
    get_kpis_atividades_emendas_manifestacoes_NG,
    get_kpis_emendas_manifestacoes_por_prazo_NG,
    get_media_emendas_manifestacoes_concluidas_por_funcionario_NG,
    get_media_emendas_manifestacoes_concluidas_por_prazo_por_funcionario_NG,
    get_opcoes_filtros_emendas_manifestacoes_NG,
    get_opcoes_filtros_emendas_manifestacoes_por_prazo_NG,
    get_opcoes_uf_emendas_manifestacoes_NG,
    group_emendas_manifestacoes_concluidas_por_dia_NG,
    group_emendas_manifestacoes_concluidas_por_mes_NG,
    group_emendas_manifestacoes_concluidas_por_prazo_por_dia_NG,
    group_emendas_manifestacoes_concluidas_por_prazo_por_mes_NG,
    group_emendas_manifestacoes_demandas_por_funcionario_NG,
    group_emendas_manifestacoes_demandas_por_funcionario_por_prazo_NG,
    group_emendas_manifestacoes_processos_por_atividade_NG,
    group_emendas_manifestacoes_processos_por_atividade_por_prazo_NG,
    list_emendas_manifestacoes_atividades_periodo_NG,
    list_emendas_manifestacoes_por_prazo_NG,
)
from app.utils import (
    parse_date_from_db,
)
from datetime import (
    date,
    datetime,
)
from fastapi import (
    HTTPException,
    Query,
)
import csv
import io
from pydantic import (
    BaseModel,
)
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)
from app.analyses.situacao_processo import _situacoes_processo_ctx, aplicar_filtro_situacao_processo
from app.sources import SourceUnavailable  # V2: fonte fora do ar vira 503 na casca

# V2: fonte do banco de origem (no lugar de fetch_data_with_cache da v1). A casca passa a fonte do
# dashboard (SourceFetcher, já com o cache de 5 min) por `usar_fonte`; o recorte de situação do processo
# é o mesmo que a v1 aplica em fetch_data_with_cache.
_fonte_ctx: ContextVar[Any] = ContextVar("fonte_v1_generico_lexflow")

def usar_fonte(fonte):
    """Define a fonte das buscas deste contexto; devolve o token para `_fonte_ctx.reset`."""
    return _fonte_ctx.set(fonte)


@memo.por_pedido(contexto=(_fonte_ctx, _situacoes_processo_ctx), copiar=False)
async def _fetch_v2(query_name: str) -> List[Dict[str, Any]]:
    return aplicar_filtro_situacao_processo(query_name, await _fonte_ctx.get().fetch(query_name))


# V2: v1 dashboard_routes.py:2961 -> fetch_data_with_cache('agendamentos_setor_emendas_manifestacoes_NG', ...)
async def fetch_agendamentos_setor_emendas_manifestacoes_NG() -> List[Dict[str, Any]]:
    return await _fetch_v2('agendamentos_setor_emendas_manifestacoes_NG')


# V2: v1 dashboard_routes.py:2955 -> fetch_data_with_cache('agendamentos_setor_emendas_manifestacoes_LA', ...)
async def fetch_agendamentos_setor_emendas_manifestacoes_LA() -> List[Dict[str, Any]]:
    return await _fetch_v2('agendamentos_setor_emendas_manifestacoes_LA')


# v1: dashboard_routes.py:2280
logger = logging.getLogger(__name__)


# v1: dashboard_routes.py:3151
def _resolve_date_range(
    from_date: Optional[date],
    to_date: Optional[date],
) -> Tuple[Optional[date], Optional[date]]:
    """Normaliza o intervalo: se from_date sem to_date, usa hoje como fim."""
    return periodo.resolver_intervalo(from_date, to_date)


# v1: dashboard_routes.py:3161
_to_date = conversao.para_data  # V2: era uma cópia local (app/analyses/common/conversao.py)


# v1: dashboard_routes.py:3173
# V2: _in_range virou parte de periodo.filtrar_por_colunas (era usado só lá).


# v1: dashboard_routes.py:3183
def _filter_by_columns(
    data: List[Dict[str, Any]],
    columns: List[str],
    from_date: Optional[date],
    to_date: Optional[date],
) -> List[Dict[str, Any]]:
    """
    Filtra registros verificando as colunas na ordem fornecida.
    Inclui o registro se QUALQUER coluna tiver data dentro do intervalo (OR lógico).
    Colunas são verificadas em caixa-alta e caixa-baixa automaticamente.
    """
    return periodo.filtrar_por_colunas(data, columns, from_date, to_date, para_data=_to_date)


# v1: dashboard_routes.py:3213
_FILTER_COLUMNS: Dict[str, List[str]] = {
    "tickets":              ["data_criacao"],
    "andamento_processual": ["ENTRADA"],
    "comercial_geral":      ["ASSINATURA"],
    "actions":              ["ENTRADA", "ASSINADO_EM"],
    "protocolos":           ["SAIDA"],
    "peticionamento":       ["DATA_CONFECCAO"],
    "org_doc":              ["SAIDA", "ENTRADA"],
    "pendencias":           ["ENTRADA"],
    "execucao":             ["DATA_EXECUCAO"],
    "execucao_RJ":          ["DATA_EXECUCAO"],
    "execucao_acordos_NG":  ["DATA_EXECUCAO"],
    "execucao_acordos_LA":  ["DATA_EXECUCAO"],
    "execucao_acordos_RJ":  ["DATA_EXECUCAO"],
    "publicacoes_NG":       ["DATA_DISPONIBILIZACAO", "DATA_CONCLUSAO"],
    "publicacoes_RJ":       ["DATA_DISPONIBILIZACAO", "DATA_CONCLUSAO"],
    # LA
    "comercial_LA":            ["ASSINADO_EM"],
    "actions_LA":              ["ENTRADA", "ASSINADO_EM"],
    "protocolo_LA":            ["SAIDA"],
    "peticionamento_LA":       ["SAIDA"],
    "org_doc_LA":              ["SAIDA"],
    "pendencias_LA":           ["ENTRADA"],
    "execucao_LA":             ["DATA_EXECUCAO"],
    "controle_processo_LA":    ["DATA_AJUIZAMENTO", "DATA_LOG_ULTIMA_ENTRADA"],
    "controle_processo_NG":    ["DATA_AJUIZAMENTO", "DATA_LOG_ULTIMA_ENTRADA"],
    "andamento_processual_LA": ["ENTRADA"],
    "pendencia_LA":            ["ENTRADA"],
    "publicacoes_LA":          ["DATA_DISPONIBILIZACAO", "DATA_CONCLUSAO"],
    "estrategico_geral":       ["SAIDA"],
    # Julgados: sem entrada aqui — o filtro de data (e o comparativo com o
    # período anterior) é feito dentro de `analyses/NG/julgados.py`, que
    # precisa do dado bruto (sem pré-filtro) para calcular o período anterior.
    # NPS
    "nps_NG":                  ["DATA"],
    "nps_LA":                  ["DATA"],
    # Marketing
    "marketing_NG":            ["ASSINATURA"],
    "marketing_lexpre_NG":     ["ENTRADA"],
    "facebook_ads":            ["date"],
    "trackeamento_ng_2":       ["DATA_TRACKEAMENTO"],
}


# v1: dashboard_routes.py:3257
def filter_data(
    key: str,
    data: List[Dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> List[Dict[str, Any]]:
    """Aplica o filtro de data à fonte identificada por `key`."""
    columns = _FILTER_COLUMNS.get(key)
    if not columns:
        return data
    return _filter_by_columns(data, columns, from_date, to_date)


# v1: dashboard_routes.py:3283
def _per_func_to_chart(
    raw: Dict[str, Any],
) -> Tuple[List[str], Dict[str, List[Dict[str, Any]]]]:
    """
    Extrai a estrutura retornada por get_*_por_dia_por_funcionario().
    Retorna (lista_funcionarios, {func: [{name, value}]}).
    """
    funcionarios: List[str] = raw.get("funcionarios", [])
    por_funcionario: Dict[str, List[Dict[str, Any]]] = {
        k: [{"name": x["name"], "value": x["value"]} for x in v]
        for k, v in raw.get("por_funcionario", {}).items()
    }
    return funcionarios, por_funcionario


# V2: os modelos de resposta da v1 ficam num módulo só (app/analyses/v1_modelos.py).
from app.analyses.v1_modelos import (  # noqa: F401  (usados aqui e por quem importa deste módulo)
    ChartDataPoint,
    ProcessoDadoFaltando,
    InvestimentoCliquesLeadsPoint,
    RubricaCampanhaPoint,
    NpsRespostaRow,
    NpsFeedbackMelhoriaRow,
    NpsFeedbackPositivoRow,
    NpsComentarioRow,
    RecursalRankingMagistradoRow,
    JulgadosSentencaListaRow,
    JulgadosAcordaoListaRow,
    ExecucaoAcordosListaRow,
    RecursalAtividadeTarefaRow,
    DilacaoPorFuncionarioRow,
    EmendasManifestacoesResolvidosPorUfRow,
    EmendasManifestacoesComissaoRow,
    RecursalAtividadesListaFiltrosOpcoes,
    ExecucaoAtrasoBucket,
    ExecucaoAtrasosDetalhamento,
    RubricaTotalRow,
    ComissionamentoOrgDocRow,
    ComissionamentoProtocoloRow,
    ComissionamentoPeticionamentoRow,
    ComissionamentoPendenciaRow,
    ComissionamentoPublicacaoRow,
    ComissionamentoAndamentoRow,
    ComissionamentoComercialRow,
    ComissionamentoComercialLARow,
    TotalLeadsPorAtendente,
    TotalClientesFechadosPorAtendente,
    TaxaFechamentoGeralPorAtendente,
    TotalLeadsCampanhaPorAtendente,
    TotalClientesFechadosCampanhaPorAtendente,
    TaxaFechamentoCampanhaPorCliente,
    TotalLeadsIndicacaoAtivaPorAtendente,
    TaxaFechamentoIndicacaoAtivaPorAtendente,
    TotalClientesFechadosIndicacaoAtivaPorAtendente,
    TotalLeadsIndicacaoPassivaPorAtendente,
    TotalClientesFechadosIndicacaoPassivaPorAtendente,
    TaxaFechamentoIndicacaoPassivaPorAtendente,
    TotalLeadsRetornoAtivaPorAtendente,
    TotalClientesFechadosRetornoAtivaPorAtendente,
    TaxaFechamentoRetornoAtivaPorAtendente,
    TotalLeadsRetornoPassivaPorAtendente,
    TotalClientesFechadosRetornoPassivaPorAtendente,
    TaxaFechamentoRetornoPassivaPorAtendente,
    TotalLeadsResgateAtivaPorAtendente,
    TotalClientesFechadosResgateAtivaPorAtendente,
    TaxaFechamentoResgateAtivaPorAtendente,
    TotalLeadsResgatePassivaPorAtendente,
    TotalClientesFechadosResgatePassivaPorAtendente,
    TaxaFechamentoResgatePassivaPorAtendente,
    DashboardStats,
    Activity,
    DashboardResponse,
)


# v1: dashboard_routes.py:20179
def _gerar_csv_export_generico(headers: List[str], data_rows: List[List[str]]) -> bytes:
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(headers)
    for linha in data_rows:
        writer.writerow(linha)
    return output.getvalue().encode("utf-8-sig")


# v1: dashboard_routes.py:20188
def _gerar_xlsx_export_generico(
    headers: List[str],
    data_rows: List[List[str]],
    sheet_name: str = "Dados",
) -> bytes:
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name
    ws.append(headers)
    for linha in data_rows:
        ws.append(linha)

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


# v1: dashboard_routes.py:30343
def _parse_emendas_manifestacoes_filtros(
    funcionario: Optional[List[str]] = None,
    atividade: Optional[List[str]] = None,
    status: Optional[List[str]] = None,
    situacao: Optional[List[str]] = None,
) -> Optional[EmendasManifestacoesAtividadesFiltros]:
    """Parser de filtros cumulativos da seção Atividades (agendamentos Emendas e Manifestações)."""
    funcionarios: set[str] = set()
    if funcionario:
        for nome in funcionario:
            t = str(nome or "").strip()
            if t:
                funcionarios.add(t)

    atividades: set[str] = set()
    if atividade:
        for raw in atividade:
            t = str(raw or "").strip()
            if t:
                atividades.add(t)

    status_set: set[str] = set()
    if status:
        for raw in status:
            t = str(raw or "").strip()
            if t:
                status_set.add(t)

    situacoes: set[str] = set()
    if situacao:
        for raw in situacao:
            chave = str(raw or "").strip()
            if not chave:
                continue
            if chave not in SITUACOES_VALIDAS_EMENDAS_MANIFESTACOES:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Situação inválida: '{chave}'. "
                        f"Valores: {sorted(SITUACOES_VALIDAS_EMENDAS_MANIFESTACOES)}"
                    ),
                )
            situacoes.add(chave)

    filtros = EmendasManifestacoesAtividadesFiltros(
        funcionarios=frozenset(funcionarios) if funcionarios else None,
        atividades=frozenset(atividades) if atividades else None,
        status=frozenset(status_set) if status_set else None,
        situacoes=frozenset(situacoes) if situacoes else None,
    )
    return filtros if filtros.ativo() else None


# v1: dashboard_routes.py:30433
def _parse_emendas_manifestacoes_filtros_ng(
    funcionario: Optional[List[str]] = None,
    atividade: Optional[List[str]] = None,
    status: Optional[List[str]] = None,
    situacao: Optional[List[str]] = None,
    uf: Optional[List[str]] = None,
) -> Optional[EmendasManifestacoesAtividadesFiltrosNG]:
    """Parser de filtros cumulativos da seção Atividades (agendamentos Emendas e Manifestações NG)."""
    funcionarios: set[str] = set()
    if funcionario:
        for nome in funcionario:
            t = str(nome or "").strip()
            if t:
                funcionarios.add(t)

    atividades: set[str] = set()
    if atividade:
        for raw in atividade:
            t = str(raw or "").strip()
            if t:
                atividades.add(t)

    status_set: set[str] = set()
    if status:
        for raw in status:
            t = str(raw or "").strip()
            if t:
                status_set.add(t)

    situacoes: set[str] = set()
    if situacao:
        for raw in situacao:
            chave = str(raw or "").strip()
            if not chave:
                continue
            if chave not in SITUACOES_VALIDAS_EMENDAS_MANIFESTACOES_NG:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Situação inválida: '{chave}'. "
                        f"Valores: {sorted(SITUACOES_VALIDAS_EMENDAS_MANIFESTACOES_NG)}"
                    ),
                )
            situacoes.add(chave)

    ufs: set[str] = set()
    if uf:
        for raw in uf:
            t = str(raw or "").strip().upper()
            if t:
                ufs.add(t)

    filtros = EmendasManifestacoesAtividadesFiltrosNG(
        funcionarios=frozenset(funcionarios) if funcionarios else None,
        atividades=frozenset(atividades) if atividades else None,
        status=frozenset(status_set) if status_set else None,
        situacoes=frozenset(situacoes) if situacoes else None,
        ufs=frozenset(ufs) if ufs else None,
    )
    return filtros if filtros.ativo() else None


# v1: dashboard_routes.py:30541
_HEADERS_EXPORT_EMENDAS_MANIFESTACOES = [
    "ID",
    "Nº Processo",
    "Descrição",
    "Operação",
    "Status",
    "Responsável",
    "Encerrado pelo responsável",
    "Setor / Atividade",
    "Atividade",
    "Criado em",
    "Prazo",
    "Em andamento",
    "Vencida",
    "Vence hoje",
    "Concluída",
]


# v1: dashboard_routes.py:30560
def _linhas_export_emendas_manifestacoes(
    rows: List[RecursalAtividadeTarefaRow],
) -> List[List[Any]]:
    def _sim_nao(v: Optional[bool]) -> str:
        if v is None:
            return ""
        return "Sim" if v else "Não"

    data_rows: List[List[Any]] = []
    for row in rows:
        data_rows.append([
            row.id,
            row.numero_processo or "",
            row.descricao,
            row.operacao or "",
            row.status,
            row.funcionario_atribuido or row.funcionario,
            _sim_nao(row.encerrado_pelo_responsavel),
            row.pessoa_setor,
            row.atividade,
            row.criado_em or "",
            row.prazo or "",
            _sim_nao(row.em_andamento),
            _sim_nao(row.vencida),
            _sim_nao(row.vence_hoje),
            _sim_nao(row.concluida),
        ])
    return data_rows


# v1: dashboard_routes.py:30590
def _gerar_arquivo_export_emendas_manifestacoes(
    data_rows: List[List[Any]], formato: str
) -> Tuple[bytes, str, str]:
    if formato == "xlsx":
        file_bytes = _gerar_xlsx_export_generico(
            _HEADERS_EXPORT_EMENDAS_MANIFESTACOES,
            data_rows,
            sheet_name="Emendas e Manifestações",
        )
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        file_bytes = _gerar_csv_export_generico(_HEADERS_EXPORT_EMENDAS_MANIFESTACOES, data_rows)
        media_type = "text/csv; charset=utf-8"
    extensao = "xlsx" if formato == "xlsx" else "csv"
    return file_bytes, media_type, extensao


# V2: só os dashboards desta cópia (v1: FETCHES_BY_DASHBOARD, mesmas fontes e chaves).
FETCHES_BY_DASHBOARD: Dict[str, List[Tuple[str, Any]]] = {
    "emendas_manifestacoes_NG": [("agendamentos_setor_emendas_manifestacoes_NG", fetch_agendamentos_setor_emendas_manifestacoes_NG)],
    "emendas_manifestacoes_LA": [("agendamentos_setor_emendas_manifestacoes_LA", fetch_agendamentos_setor_emendas_manifestacoes_LA)],
}
DASHBOARD_NAMES = set(FETCHES_BY_DASHBOARD)


# v1: dashboard_routes.py:11255 — V2: início igual, só os ramos de emendas_manifestacoes_NG, emendas_manifestacoes_LA
async def _get_dashboard_response(  # V2: só os parâmetros usados por estes dashboards
    dashboard_name: str,
    from_date: Optional[date],
    to_date: Optional[date],
    emendas_manifestacoes_atividades_filtros: Optional[EmendasManifestacoesAtividadesFiltros] = None,
    emendas_manifestacoes_atividades_filtros_ng: Optional[EmendasManifestacoesAtividadesFiltrosNG] = None,
    area_atuacao_id: Optional[Union[int, List[int]]] = None,
) -> DashboardResponse:
    if dashboard_name not in DASHBOARD_NAMES:
        raise HTTPException(status_code=404, detail=f"Dashboard '{dashboard_name}' não encontrado.")
    t0 = time.time()
    logger.info("Dashboard '%s' (from=%s, to=%s)", dashboard_name, from_date, to_date)
    from_date, to_date = _resolve_date_range(from_date, to_date)
    fetches_config = FETCHES_BY_DASHBOARD[dashboard_name]
    # V2: mesma busca da v1 (_gather_dashboard_fetches = gather com return_exceptions)
    results = await asyncio.gather(*[fn() for _, fn in fetches_config], return_exceptions=True)
    # V2: banco de origem fora do ar = 503 na casca (a v1 seguia com a fonte vazia quando havia mais de uma)
    for res in results:
        if isinstance(res, SourceUnavailable):
            raise res
    all_data: Dict[str, List] = {}
    source_errors: List[Tuple[str, Exception]] = []
    for (key, _), res in zip(fetches_config, results):
        if isinstance(res, Exception):
            source_errors.append((key, res))
            all_data[key] = []
        else:
            all_data[key] = res
    if source_errors:
        if len(fetches_config) == 1:
            failed_key, failed_exc = source_errors[0]
            logger.exception("Falha ao buscar fonte '%s' no dashboard '%s'", failed_key, dashboard_name, exc_info=failed_exc)
            if isinstance(failed_exc, HTTPException):
                raise failed_exc
            raise HTTPException(status_code=500, detail=f"Falha ao buscar dados de '{failed_key}'")
        for failed_key, failed_exc in source_errors:
            logger.warning("Fonte '%s' indisponível no dashboard '%s': %s", failed_key, dashboard_name, failed_exc)
    # V2: (variável só de outros dashboards da v1 omitida)
    # V2: (bloco de outros dashboards da v1 omitido)
    filtered_data: Dict[str, List] = {
        key: filter_data(key, data, from_date, to_date)
        for key, data in all_data.items()
    }
    # V2: (variável só de outros dashboards da v1 omitida)
    # V2: (variável só de outros dashboards da v1 omitida)
    # V2: (variável só de outros dashboards da v1 omitida)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (variável só de outros dashboards da v1 omitida)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (variável só de outros dashboards da v1 omitida)
    # V2: (variável só de outros dashboards da v1 omitida)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (variável só de outros dashboards da v1 omitida)
    # V2: (bloco de outros dashboards da v1 omitido)
    _PREPROTOCOLO_AREA_KEY = {
        "pendencia_LA":      "pendencia_LA",
        "org_doc_LA":        "org_doc_LA",
        "peticionamento_LA": "peticionamento_LA",
        "protocolo_LA":      "protocolo_LA",
        "pendencias":        "pendencias",
        "pendencias_RJ":     "pendencias",
        "org-documentos":    "org_doc",
        "org_doc_RJ":        "org_doc",
        "peticionamento":    "peticionamento",
        "peticionamento_RJ": "peticionamento",
        "protocolo":         "protocolos",
        "protocolo_RJ":      "protocolos",
    }
    if dashboard_name in _PREPROTOCOLO_AREA_KEY and area_atuacao_id is not None:
        _key = _PREPROTOCOLO_AREA_KEY[dashboard_name]
        area_atuacao_id_aplicado = area_atuacao_id
        filtered_data[_key] = filter_comercial_geral_por_area_atuacao(filtered_data.get(_key, []), area_atuacao_id)
        all_data[_key] = filter_comercial_geral_por_area_atuacao(all_data.get(_key, []), area_atuacao_id)
    def _f(key: str) -> List:
        return filtered_data.get(key, [])
    def _a(key: str) -> List:
        return all_data.get(key, [])
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    if dashboard_name == "emendas_manifestacoes_LA":
        ag_base = _a("agendamentos_setor_emendas_manifestacoes_LA")
        ag_filtrados = filtrar_agendamentos_emendas_manifestacoes_LA(
            ag_base,
            emendas_manifestacoes_atividades_filtros,
            from_date=from_date,
            to_date=to_date,
        )
        stats = get_kpis_atividades_emendas_manifestacoes_LA(
            ag_filtrados, from_date=from_date, to_date=to_date
        )
        stats.update(get_kpis_emendas_manifestacoes_por_prazo_LA(
            ag_filtrados, from_date=from_date, to_date=to_date
        ))
        func_raw = get_emendas_manifestacoes_concluidas_por_dia_por_funcionario_LA(
            ag_filtrados, from_date=from_date, to_date=to_date
        )
        funcionarios_emendas_manifestacoes, por_dia_por_func_emendas_manifestacoes = _per_func_to_chart(func_raw)
        func_prazo_raw = get_emendas_manifestacoes_concluidas_por_prazo_por_dia_por_funcionario_LA(
            ag_filtrados, from_date=from_date, to_date=to_date
        )
        funcionarios_emendas_manifestacoes_por_prazo, por_dia_por_func_emendas_manifestacoes_por_prazo = (
            _per_func_to_chart(func_prazo_raw)
        )
        charts = {
            "emendas_manifestacoes_concluidas_por_mes_LA": [
                ChartDataPoint(**x)
                for x in group_emendas_manifestacoes_concluidas_por_mes_LA(
                    ag_filtrados, from_date=from_date, to_date=to_date
                )
            ],
            "emendas_manifestacoes_concluidas_por_dia_LA": [
                ChartDataPoint(**x)
                for x in group_emendas_manifestacoes_concluidas_por_dia_LA(
                    ag_filtrados, from_date=from_date, to_date=to_date
                )
            ],
            "funcionarios_emendas_manifestacoes_LA": funcionarios_emendas_manifestacoes,
            "emendas_manifestacoes_concluidas_por_dia_por_funcionario_LA": {
                k: [ChartDataPoint(**i) for i in v]
                for k, v in por_dia_por_func_emendas_manifestacoes.items()
            },
            "media_emendas_manifestacoes_concluidas_por_funcionario_LA": [
                ChartDataPoint(**x)
                for x in get_media_emendas_manifestacoes_concluidas_por_funcionario_LA(
                    ag_filtrados, from_date=from_date, to_date=to_date
                )
            ],
            "emendas_manifestacoes_concluidas_por_prazo_por_mes_LA": [
                ChartDataPoint(**x)
                for x in group_emendas_manifestacoes_concluidas_por_prazo_por_mes_LA(
                    ag_filtrados, from_date=from_date, to_date=to_date
                )
            ],
            "emendas_manifestacoes_concluidas_por_prazo_por_dia_LA": [
                ChartDataPoint(**x)
                for x in group_emendas_manifestacoes_concluidas_por_prazo_por_dia_LA(
                    ag_filtrados, from_date=from_date, to_date=to_date
                )
            ],
            "funcionarios_emendas_manifestacoes_por_prazo_LA": funcionarios_emendas_manifestacoes_por_prazo,
            "emendas_manifestacoes_concluidas_por_prazo_por_dia_por_funcionario_LA": {
                k: [ChartDataPoint(**i) for i in v]
                for k, v in por_dia_por_func_emendas_manifestacoes_por_prazo.items()
            },
            "media_emendas_manifestacoes_concluidas_por_prazo_por_funcionario_LA": [
                ChartDataPoint(**x)
                for x in get_media_emendas_manifestacoes_concluidas_por_prazo_por_funcionario_LA(
                    ag_filtrados, from_date=from_date, to_date=to_date
                )
            ],
            "emendas_manifestacoes_processos_por_atividade_LA": [
                ChartDataPoint(**x)
                for x in group_emendas_manifestacoes_processos_por_atividade_LA(
                    ag_filtrados, from_date=from_date, to_date=to_date
                )
            ],
            "emendas_manifestacoes_demandas_por_funcionario_LA": group_emendas_manifestacoes_demandas_por_funcionario_LA(
                ag_filtrados, from_date=from_date, to_date=to_date
            ),
            "emendas_manifestacoes_atividades_lista_LA": [
                RecursalAtividadeTarefaRow(**x)
                for x in list_emendas_manifestacoes_atividades_periodo_LA(
                    ag_filtrados, from_date=from_date, to_date=to_date
                )
            ],
            "emendas_manifestacoes_atividades_lista_filtros_opcoes_LA": RecursalAtividadesListaFiltrosOpcoes(
                **get_opcoes_filtros_emendas_manifestacoes_LA(
                    ag_base, from_date=from_date, to_date=to_date
                )
            ),
            "emendas_manifestacoes_por_prazo_lista_LA": [
                RecursalAtividadeTarefaRow(**x)
                for x in list_emendas_manifestacoes_por_prazo_LA(
                    ag_filtrados, from_date=from_date, to_date=to_date
                )
            ],
            "emendas_manifestacoes_por_prazo_lista_filtros_opcoes_LA": RecursalAtividadesListaFiltrosOpcoes(
                **get_opcoes_filtros_emendas_manifestacoes_por_prazo_LA(
                    ag_base, from_date=from_date, to_date=to_date
                )
            ),
            "emendas_manifestacoes_processos_por_atividade_por_prazo_LA": [
                ChartDataPoint(**x)
                for x in group_emendas_manifestacoes_processos_por_atividade_por_prazo_LA(
                    ag_filtrados, from_date=from_date, to_date=to_date
                )
            ],
            "emendas_manifestacoes_demandas_por_funcionario_por_prazo_LA": group_emendas_manifestacoes_demandas_por_funcionario_por_prazo_LA(
                ag_filtrados, from_date=from_date, to_date=to_date
            ),
            "emendas_manifestacoes_comissionamento_por_funcionario_LA": [
                EmendasManifestacoesComissaoRow(**x)
                for x in get_emendas_manifestacoes_comissionamento_por_funcionario_LA(
                    ag_filtrados, from_date=from_date, to_date=to_date
                )
            ],
        }
        logger.info("Dashboard 'emendas_manifestacoes_LA' processado em %.2fs", time.time() - t0)
        return DashboardResponse(
            dashboard="emendas_manifestacoes_LA",
            stats=DashboardStats(**stats),
            **charts,
        )
    if dashboard_name == "emendas_manifestacoes_NG":
        ag_base = _a("agendamentos_setor_emendas_manifestacoes_NG")
        ag_filtrados = filtrar_agendamentos_emendas_manifestacoes_NG(
            ag_base,
            emendas_manifestacoes_atividades_filtros_ng,
            from_date=from_date,
            to_date=to_date,
        )
        stats = get_kpis_atividades_emendas_manifestacoes_NG(
            ag_filtrados, from_date=from_date, to_date=to_date
        )
        stats.update(get_kpis_emendas_manifestacoes_por_prazo_NG(
            ag_filtrados, from_date=from_date, to_date=to_date
        ))
        stats["comparativo_qtd_manifestacoes_emendas_manifestacoes_NG"] = (
            get_comparativo_qtd_manifestacoes_emendas_manifestacoes_NG(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        )
        stats["comparativo_qtd_dilacoes_emendas_manifestacoes_NG"] = (
            get_comparativo_qtd_dilacoes_emendas_manifestacoes_NG(
                ag_filtrados, from_date=from_date, to_date=to_date
            )
        )
        stats["emendas_manifestacoes_uf_opcoes_NG"] = get_opcoes_uf_emendas_manifestacoes_NG(ag_base)
        func_raw = get_emendas_manifestacoes_concluidas_por_dia_por_funcionario_NG(
            ag_filtrados, from_date=from_date, to_date=to_date
        )
        funcionarios_emendas_manifestacoes, por_dia_por_func_emendas_manifestacoes = _per_func_to_chart(func_raw)
        func_prazo_raw = get_emendas_manifestacoes_concluidas_por_prazo_por_dia_por_funcionario_NG(
            ag_filtrados, from_date=from_date, to_date=to_date
        )
        funcionarios_emendas_manifestacoes_por_prazo, por_dia_por_func_emendas_manifestacoes_por_prazo = (
            _per_func_to_chart(func_prazo_raw)
        )
        charts = {
            "emendas_manifestacoes_concluidas_por_mes_NG": [
                ChartDataPoint(**x)
                for x in group_emendas_manifestacoes_concluidas_por_mes_NG(
                    ag_filtrados, from_date=from_date, to_date=to_date
                )
            ],
            "emendas_manifestacoes_concluidas_por_dia_NG": [
                ChartDataPoint(**x)
                for x in group_emendas_manifestacoes_concluidas_por_dia_NG(
                    ag_filtrados, from_date=from_date, to_date=to_date
                )
            ],
            "funcionarios_emendas_manifestacoes_NG": funcionarios_emendas_manifestacoes,
            "emendas_manifestacoes_concluidas_por_dia_por_funcionario_NG": {
                k: [ChartDataPoint(**i) for i in v]
                for k, v in por_dia_por_func_emendas_manifestacoes.items()
            },
            "media_emendas_manifestacoes_concluidas_por_funcionario_NG": [
                ChartDataPoint(**x)
                for x in get_media_emendas_manifestacoes_concluidas_por_funcionario_NG(
                    ag_filtrados, from_date=from_date, to_date=to_date
                )
            ],
            "emendas_manifestacoes_concluidas_por_prazo_por_mes_NG": [
                ChartDataPoint(**x)
                for x in group_emendas_manifestacoes_concluidas_por_prazo_por_mes_NG(
                    ag_filtrados, from_date=from_date, to_date=to_date
                )
            ],
            "emendas_manifestacoes_concluidas_por_prazo_por_dia_NG": [
                ChartDataPoint(**x)
                for x in group_emendas_manifestacoes_concluidas_por_prazo_por_dia_NG(
                    ag_filtrados, from_date=from_date, to_date=to_date
                )
            ],
            "funcionarios_emendas_manifestacoes_por_prazo_NG": funcionarios_emendas_manifestacoes_por_prazo,
            "emendas_manifestacoes_concluidas_por_prazo_por_dia_por_funcionario_NG": {
                k: [ChartDataPoint(**i) for i in v]
                for k, v in por_dia_por_func_emendas_manifestacoes_por_prazo.items()
            },
            "media_emendas_manifestacoes_concluidas_por_prazo_por_funcionario_NG": [
                ChartDataPoint(**x)
                for x in get_media_emendas_manifestacoes_concluidas_por_prazo_por_funcionario_NG(
                    ag_filtrados, from_date=from_date, to_date=to_date
                )
            ],
            "emendas_manifestacoes_processos_por_atividade_NG": [
                ChartDataPoint(**x)
                for x in group_emendas_manifestacoes_processos_por_atividade_NG(
                    ag_filtrados, from_date=from_date, to_date=to_date
                )
            ],
            "emendas_manifestacoes_demandas_por_funcionario_NG": group_emendas_manifestacoes_demandas_por_funcionario_NG(
                ag_filtrados, from_date=from_date, to_date=to_date
            ),
            "emendas_manifestacoes_atividades_lista_NG": [
                RecursalAtividadeTarefaRow(**x)
                for x in list_emendas_manifestacoes_atividades_periodo_NG(
                    ag_filtrados, from_date=from_date, to_date=to_date
                )
            ],
            "emendas_manifestacoes_atividades_lista_filtros_opcoes_NG": RecursalAtividadesListaFiltrosOpcoes(
                **get_opcoes_filtros_emendas_manifestacoes_NG(
                    ag_base, from_date=from_date, to_date=to_date
                )
            ),
            "emendas_manifestacoes_por_prazo_lista_NG": [
                RecursalAtividadeTarefaRow(**x)
                for x in list_emendas_manifestacoes_por_prazo_NG(
                    ag_filtrados, from_date=from_date, to_date=to_date
                )
            ],
            "emendas_manifestacoes_por_prazo_lista_filtros_opcoes_NG": RecursalAtividadesListaFiltrosOpcoes(
                **get_opcoes_filtros_emendas_manifestacoes_por_prazo_NG(
                    ag_base, from_date=from_date, to_date=to_date
                )
            ),
            "emendas_manifestacoes_processos_por_atividade_por_prazo_NG": [
                ChartDataPoint(**x)
                for x in group_emendas_manifestacoes_processos_por_atividade_por_prazo_NG(
                    ag_filtrados, from_date=from_date, to_date=to_date
                )
            ],
            "emendas_manifestacoes_demandas_por_funcionario_por_prazo_NG": group_emendas_manifestacoes_demandas_por_funcionario_por_prazo_NG(
                ag_filtrados, from_date=from_date, to_date=to_date
            ),
            "emendas_manifestacoes_comissionamento_por_funcionario_NG": [
                EmendasManifestacoesComissaoRow(**x)
                for x in get_emendas_manifestacoes_comissionamento_por_funcionario_NG(
                    ag_filtrados, from_date=from_date, to_date=to_date
                )
            ],
        }
        logger.info("Dashboard 'emendas_manifestacoes_NG' processado em %.2fs", time.time() - t0)
        return DashboardResponse(
            dashboard="emendas_manifestacoes_NG",
            stats=DashboardStats(**stats),
            **charts,
        )
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    raise HTTPException(status_code=404, detail=f"Dashboard '{dashboard_name}' não encontrado.")


# v1: dashboard_routes.py:30497 (rota sem os decoradores)
async def get_emendas_manifestacoes_NG_dashboard(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    funcionario_emendas_manifestacoes: Optional[List[str]] = Query(
        None,
        description="Filtra agendamentos por funcionário (seção Atividades)",
    ),
    atividade_emendas_manifestacoes: Optional[List[str]] = Query(
        None,
        description="Filtra agendamentos por atividade",
    ),
    status_emendas_manifestacoes: Optional[List[str]] = Query(
        None,
        description="Filtra agendamentos por status",
    ),
    situacao_emendas_manifestacoes: Optional[List[str]] = Query(
        None,
        description="Filtra por situação: em_andamento, vencidas, vencem_hoje, concluidas",
    ),
    uf_emendas_manifestacoes: Optional[List[str]] = Query(
        None,
        description=(
            "Filtra por UF do processo (ex.: `AM`, `PA`, `PB`) — aceita múltiplos "
            "valores (`?uf_emendas_manifestacoes=AM&uf_emendas_manifestacoes=PA`). "
            "Omitido/vazio = todas as UFs."
        ),
    ),
):
    """Dashboard de Emendas e Manifestações (NG, setor Manifestação) — seção Atividades no período."""
    filtros = _parse_emendas_manifestacoes_filtros_ng(
        funcionario_emendas_manifestacoes,
        atividade_emendas_manifestacoes,
        status_emendas_manifestacoes,
        situacao_emendas_manifestacoes,
        uf_emendas_manifestacoes,
    )
    return await _get_dashboard_response(
        "emendas_manifestacoes_NG",
        from_date,
        to_date,
        emendas_manifestacoes_atividades_filtros_ng=filtros,
    )


# v1: dashboard_routes.py:30398 (rota sem os decoradores)
async def get_emendas_manifestacoes_LA_dashboard(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    funcionario_emendas_manifestacoes: Optional[List[str]] = Query(
        None,
        description="Filtra agendamentos por funcionário (seção Atividades)",
    ),
    atividade_emendas_manifestacoes: Optional[List[str]] = Query(
        None,
        description="Filtra agendamentos por atividade",
    ),
    status_emendas_manifestacoes: Optional[List[str]] = Query(
        None,
        description="Filtra agendamentos por status",
    ),
    situacao_emendas_manifestacoes: Optional[List[str]] = Query(
        None,
        description="Filtra por situação: em_andamento, vencidas, vencem_hoje, concluidas",
    ),
):
    """Dashboard de Emendas e Manifestações (LA, setor Intermediárias) — seção Atividades no período."""
    filtros = _parse_emendas_manifestacoes_filtros(
        funcionario_emendas_manifestacoes,
        atividade_emendas_manifestacoes,
        status_emendas_manifestacoes,
        situacao_emendas_manifestacoes,
    )
    return await _get_dashboard_response(
        "emendas_manifestacoes_LA",
        from_date,
        to_date,
        emendas_manifestacoes_atividades_filtros=filtros,
    )


# V2: dashboard da v1 -> handler da rota e queries que ele busca (para a casca e o aquecedor do cache).
HANDLERS = {"emendas_manifestacoes_NG": get_emendas_manifestacoes_NG_dashboard, "emendas_manifestacoes_LA": get_emendas_manifestacoes_LA_dashboard}
QUERIES_POR_DASHBOARD = {'emendas_manifestacoes_NG': ('agendamentos_setor_emendas_manifestacoes_NG',), 'emendas_manifestacoes_LA': ('agendamentos_setor_emendas_manifestacoes_LA',)}
