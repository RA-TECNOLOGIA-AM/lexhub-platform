"""Dashboards "genéricos" da v1 (ramos de _get_dashboard_response) usados pela V2 — cópia SEM mudança.

Origem: api_dashboards/src/app/dashboard_routes.py (linha na v1 ao lado de cada bloco).
Gerado por scripts/copiar_v1/gerar_generico.py (banco laadv). Únicas trocas, marcadas com "V2:":
  * fetch_*: buscam pela fonte da V2 (`usar_fonte`), com o recorte de situação do processo da v1;
  * _get_dashboard_response: mesmo início da v1 (fontes, datas, _f/_a), só com os ramos abaixo;
  * fontes de outro banco saem de FETCHES_BY_DASHBOARD (chegam vazias, como na v1 com a fonte fora do ar).
Dashboards: protocolo_LA, peticionamento_LA, org_doc_LA, pendencia_LA.
"""

import asyncio
import logging
import time
from contextvars import ContextVar
from app.analyses.common import periodo  # V2: período e variação vs período anterior num módulo só
from app.analyses.common import conversao  # V2: conversões dos valores do banco num módulo só
from app.analyses.common import memo  # V2: cache por pedido (a mesma conta uma vez por pedido)
from app.analyses.LA.org_doc_LA import (
    filter_org_doc_LA_por_funcionarios,
    filter_org_doc_LA_por_materia,
    filter_org_doc_LA_por_uf,
    get_cancelados_LA,
    get_comissionamento_por_funcionario_LA,
    get_comparativo_cancelados_LA,
    get_comparativo_organizados_automaticamente_LA,
    get_comparativo_organizados_manualmente_LA,
    get_comparativo_resolvidos_total_LA,
    get_comparativo_retorno_pendencia_LA,
    get_media_resolvidos_por_funcionario_LA,
    get_media_tempo_resolvidos_LA,
    get_mediana_tempo_resolvidos_LA,
    get_nao_organizados_LA,
    get_nao_organizados_por_atendente_LA,
    get_resolvidos_por_dia_por_funcionario_LA,
    get_retorno_pendencia_LA,
    get_total_organizados_LA,
    get_total_organizados_automaticamente_LA,
    get_total_organizados_manualmente_LA,
    get_valor_causa_por_funcionario_LA,
    group_nao_organizados_por_funcionario_LA,
    group_nao_organizados_total_por_materia_LA,
    group_nao_organizados_total_por_mes_LA,
    group_organizados_por_funcionario_LA,
    group_organizados_total_por_materia_LA,
    group_resolvidos_por_dia_LA,
    group_resolvidos_total_por_mes_LA,
    list_ufs_org_doc_LA,
)
from app.analyses.LA.pendencia_LA import (
    filter_pendencia_LA_por_funcionarios,
    filter_pendencia_LA_por_uf,
    get_media_pendencias_resolvidas_por_funcionario_LA,
    get_media_tempo_resolvidos_pendencia_LA,
    get_mediana_tempo_resolvidos_pendencia_LA,
    get_pendencias_canceladas_LA,
    get_pendencias_comissionamento_por_funcionario_LA,
    get_pendencias_nao_resolvidas_LA,
    get_pendencias_nao_resolvidas_com_atraso_LA,
    get_pendencias_nao_resolvidas_por_atendente_LA,
    get_pendencias_nao_resolvidas_por_origem_LA,
    get_pendencias_resolvidas_LA,
    get_pendencias_resolvidas_por_dia_por_funcionario_LA,
    get_pendencias_taxa_canceladas_LA,
    get_pendencias_taxa_nao_resolvidos_LA,
    get_pendencias_taxa_resolvidos_LA,
    get_pendencias_total_LA,
    get_pendencias_triagem_LA,
    group_pendencias_resolvidas_por_dia_LA,
    group_pendencias_resolvidas_por_mes_LA,
    list_ufs_pendencia_LA,
)
from app.analyses.LA.peticionamento_LA import (
    filter_peticionamento_LA_por_funcionarios,
    filter_peticionamento_LA_por_materia,
    filter_peticionamento_LA_por_uf,
    get_comparativo_confeccionados_LA,
    get_comparativo_confeccionados_automaticamente_LA,
    get_comparativo_confeccionados_manualmente_LA,
    get_comparativo_mediana_tempo_confeccionadoLA,
    get_comparativo_tempo_medio_confeccionado_LA,
    get_comparativo_ticket_medio_confeccionado_LA,
    get_comparativo_valor_causa_confeccionado_LA,
    get_confeccionados_por_dia_por_funcionario_LA,
    get_media_confeccionado_por_funcionario_LA,
    get_media_tempo_confeccionado_LA,
    get_mediana_tempo_confeccionado_LA,
    get_nao_confeccionados_LA,
    get_peticionamento_comissionamento_por_funcionario_LA,
    get_peticionamento_qtd_entrada_protocolo_LA,
    get_peticionamento_qtd_retorno_protocolo_LA,
    get_peticionamento_taxa_nao_resolvidos_LA,
    get_peticionamento_taxa_resolvidos_LA,
    get_peticionamento_taxa_retorno_protocolo_LA,
    get_ticket_medio_confeccionados_LA,
    get_total_confeccionados_LA,
    get_total_confeccionados_automaticamente_LA,
    get_total_confeccionados_manualmente_LA,
    get_valor_causa_confeccionado_LA,
    get_valor_causa_confeccionado_por_funcionario_LA,
    group_confeccionados_por_dia_LA,
    group_confeccionados_por_funcionario_LA,
    group_confeccionados_por_materia_LA,
    group_confeccionados_por_mes_LA,
    group_nao_confeccionados_por_funcionario_LA,
    group_nao_confeccionados_por_materia_LA,
    group_nao_confeccionados_por_mes_LA,
    list_ufs_peticionamento_LA,
)
from app.analyses.LA.protocolo_LA import (
    META_VALOR_CAUSA_2026_LA,
    filter_protocolo_LA_por_funcionarios,
    filter_protocolo_LA_por_materia,
    filter_protocolo_LA_por_sistema,
    get_comissao_com_fm_LA,
    get_comparativo_mediana_tempo_contratacao_protocolado_LA,
    get_comparativo_mediana_tempo_protocolos_resolvidos_LA,
    get_comparativo_protocolos_resolvidos_LA,
    get_comparativo_tempo_medio_contratacao_protocolado_LA,
    get_comparativo_tempo_medio_protocolos_resolvidos_LA,
    get_comparativo_ticket_medio_protocolos_resolvidos_LA,
    get_comparativo_valor_causa_protocolado_LA,
    get_entradas_protocolo_LA,
    get_fator_multiplicador_LA,
    get_media_protocolados_por_funcionario_LA,
    get_media_tempo_contratacao_protocolado_LA,
    get_media_tempo_protocolado_LA,
    get_mediana_tempo_contratacao_protocolado_LA,
    get_mediana_tempo_protocolado_LA,
    get_nao_protocolados_por_atendente_LA,
    get_protocolados_por_dia_por_funcionario_LA,
    get_protocolo_comissionamento_por_funcionario_LA,
    get_protocolos_represados_LA,
    get_protocolos_resolvidos_LA,
    get_protocolos_resolvidos_periodo_anterior_LA,
    get_protocolos_resolvidos_por_atendente_LA,
    get_taxa_protocolados_LA,
    get_ticket_medio_protocolos_resolvidos_LA,
    get_valor_causa_nao_protocolado_por_atendente_LA,
    get_valor_causa_protocolado_LA,
    get_valor_causa_protocolado_LA_2026,
    get_valor_causa_protocolado_periodo_anterior_LA,
    get_valor_causa_protocolado_por_atendente_LA,
    get_valor_causa_protocolado_por_funcionario_LA,
    group_protocolados_por_dia_LA,
    group_protocolados_por_funcionario_LA,
    group_protocolados_por_materia_LA,
    group_protocolados_por_mes_LA,
    group_protocolados_por_sistema_LA,
    group_represados_por_funcionario_LA,
    group_represados_por_materia_LA,
    group_represados_por_mes_LA,
    group_valor_causa_protocolados_por_dia_LA,
    group_valor_causa_protocolados_por_mes_LA,
)
from app.analyses.NG.comercial_geral import (
    filter_comercial_geral_por_area_atuacao,
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
_fonte_ctx: ContextVar[Any] = ContextVar("fonte_v1_generico_laadv")

def usar_fonte(fonte):
    """Define a fonte das buscas deste contexto; devolve o token para `_fonte_ctx.reset`."""
    return _fonte_ctx.set(fonte)


@memo.por_pedido(contexto=(_fonte_ctx, _situacoes_processo_ctx), copiar=False)
async def _fetch_v2(query_name: str) -> List[Dict[str, Any]]:
    return aplicar_filtro_situacao_processo(query_name, await _fonte_ctx.get().fetch(query_name))


# V2: v1 dashboard_routes.py:2861 -> fetch_data_with_cache('setor_protocolo_LA', ...)
async def fetch_protocolo_LA() -> List[Dict[str, Any]]:
    return await _fetch_v2('setor_protocolo_LA')


# V2: v1 dashboard_routes.py:2837 -> fetch_data_with_cache('comercial_geral_LA', ...)
async def fetch_comercial_LA() -> List[Dict[str, Any]]:
    return await _fetch_v2('comercial_geral_LA')


# V2: v1 dashboard_routes.py:2858 -> fetch_data_with_cache('setor_confeccao_LA', ...)
async def fetch_peticionamento_LA() -> List[Dict[str, Any]]:
    return await _fetch_v2('setor_confeccao_LA')


# V2: v1 dashboard_routes.py:2855 -> fetch_data_with_cache('setor_org_documentos_LA', ...)
async def fetch_org_doc_LA() -> List[Dict[str, Any]]:
    return await _fetch_v2('setor_org_documentos_LA')


# V2: v1 dashboard_routes.py:2840 -> fetch_data_with_cache('setor_pendencia_LA', ...)
async def fetch_pendencias_LA() -> List[Dict[str, Any]]:
    return await _fetch_v2('setor_pendencia_LA')


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


# v1: dashboard_routes.py:3270
def dict_to_chart_data(
    d: Dict[str, Any],
    *,
    sort: bool = True,
    cast_int: bool = False,
) -> List[Dict[str, Any]]:
    """Converte dict {nome: valor} para lista [{name, value}], ordenada decrescente."""
    items = list(d.items())
    if sort:
        items = sorted(items, key=lambda x: x[1], reverse=True)
    return [{"name": k, "value": int(v) if cast_int else v} for k, v in items]


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


# v1: dashboard_routes.py:3412
def _expandir_valores_query_lista(valores: Optional[List[str]]) -> List[str]:
    """Expande parâmetros repetidos e valores separados por vírgula."""
    if not valores:
        return []
    saida: List[str] = []
    for raw in valores:
        if raw is None:
            continue
        for parte in str(raw).split(","):
            t = parte.strip()
            if t:
                saida.append(t)
    return saida


# v1: dashboard_routes.py:3588
def _normalizar_funcionarios_query(funcionarios: Optional[List[str]]) -> List[str]:
    """Lista única de nomes de funcionário vindos da query (trim, sem vazios)."""
    vistos: set[str] = set()
    saida: List[str] = []
    for raw in _expandir_valores_query_lista(funcionarios):
        if raw not in vistos:
            vistos.add(raw)
            saida.append(raw)
    return saida


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


# v1: dashboard_routes.py:10848
def _build_org_doc_LA_stats(
    org_doc_LA: List[Dict],
    all_org_doc_LA: List[Dict],
    from_date: Optional[date],
    to_date: Optional[date],
) -> Tuple[Dict, Dict]:
    func_raw = get_resolvidos_por_dia_por_funcionario_LA(org_doc_LA)
    funcionarios, por_dia_por_func = _per_func_to_chart(func_raw)

    stats = {
        "total_organizados_LA": get_total_organizados_LA(org_doc_LA),
        "nao_organizados_LA": get_nao_organizados_LA(org_doc_LA),
        "total_organizados_manualmente_LA": get_total_organizados_manualmente_LA(org_doc_LA),
        "total_organizados_automaticamente_LA": get_total_organizados_automaticamente_LA(org_doc_LA),
        "retorno_pendencia_LA": get_retorno_pendencia_LA(org_doc_LA),
        "cancelados_LA": get_cancelados_LA(org_doc_LA),
        "media_tempo_resolvidos_LA": get_media_tempo_resolvidos_LA(org_doc_LA),
        "mediana_tempo_resolvidos_LA": get_mediana_tempo_resolvidos_LA(org_doc_LA),
        "comparativo_resolvidos_total_LA": get_comparativo_resolvidos_total_LA(org_doc_LA, all_organizados=all_org_doc_LA, from_date=from_date, to_date=to_date),
        "comparativo_organizados_manualmente_LA": get_comparativo_organizados_manualmente_LA(org_doc_LA, all_organizados=all_org_doc_LA, from_date=from_date, to_date=to_date),
        "comparativo_organizados_automaticamente_LA": get_comparativo_organizados_automaticamente_LA(org_doc_LA, all_organizados=all_org_doc_LA, from_date=from_date, to_date=to_date),
        "comparativo_retorno_pendencia_LA": get_comparativo_retorno_pendencia_LA(org_doc_LA, all_organizados=all_org_doc_LA, from_date=from_date, to_date=to_date),
        "comparativo_cancelados_LA": get_comparativo_cancelados_LA(org_doc_LA, all_organizados=all_org_doc_LA, from_date=from_date, to_date=to_date),
    }
    charts = {
        "nao_organizados_por_atendente_LA": [ChartDataPoint(**x) for x in dict_to_chart_data(get_nao_organizados_por_atendente_LA(all_org_doc_LA), cast_int=True)],
        "nao_organizados_por_funcionario_LA": [ChartDataPoint(**x) for x in group_nao_organizados_por_funcionario_LA(org_doc_LA)],
        "organizados_por_funcionario_LA": [ChartDataPoint(**x) for x in group_organizados_por_funcionario_LA(org_doc_LA)],
        "valor_causa_por_funcionario_LA": [ChartDataPoint(**x) for x in get_valor_causa_por_funcionario_LA(org_doc_LA)],
        "comissionamento_org_doc_LA_por_funcionario": [ComissionamentoOrgDocRow(**x) for x in get_comissionamento_por_funcionario_LA(org_doc_LA)],
        "media_resolvidos_por_funcionario_LA": [ChartDataPoint(**x) for x in get_media_resolvidos_por_funcionario_LA(org_doc_LA)],
        "organizados_total_por_materia_LA": [ChartDataPoint(**x) for x in group_organizados_total_por_materia_LA(org_doc_LA)],
        "nao_organizados_total_por_materia_LA": [ChartDataPoint(**x) for x in group_nao_organizados_total_por_materia_LA(org_doc_LA)],
        "nao_organizados_total_por_mes_LA": [ChartDataPoint(**x) for x in group_nao_organizados_total_por_mes_LA(all_org_doc_LA)],
        "resolvidos_total_por_mes_LA": [ChartDataPoint(**x) for x in group_resolvidos_total_por_mes_LA(all_org_doc_LA)],
        "resolvidos_por_dia_LA": [ChartDataPoint(**x) for x in group_resolvidos_por_dia_LA(org_doc_LA)],
        "funcionarios_org_doc_LA": funcionarios,
        "resolvidos_por_dia_por_funcionario_LA": {k: [ChartDataPoint(**i) for i in v] for k, v in por_dia_por_func.items()},
    }
    return stats, charts


# v1: dashboard_routes.py:10890
def _build_protocolo_LA_stats(
    protocolo_LA: List[Dict],
    all_protocolo_LA: List[Dict],
    from_date: Optional[date],
    to_date: Optional[date],
    comercial_LA: Optional[List[Dict]] = None,
) -> Tuple[Dict, Dict]:
    func_raw = get_protocolados_por_dia_por_funcionario_LA(protocolo_LA)
    funcionarios, por_dia_por_func = _per_func_to_chart(func_raw)
    pool_com_fm = get_comissao_com_fm_LA(protocolo_LA, comercial_LA or [])
    taxa_prot_la = get_taxa_protocolados_LA(protocolo_LA, all_protocolo_LA, from_date, to_date)

    stats = {
        "protocolos_resolvidos_LA": get_protocolos_resolvidos_LA(protocolo_LA),
        "protocolos_represados_LA": get_protocolos_represados_LA(protocolo_LA),
        "valor_causa_protocolado_LA": get_valor_causa_protocolado_LA(protocolo_LA),
        "ticket_medio_protocolos_resolvidos_LA": get_ticket_medio_protocolos_resolvidos_LA(protocolo_LA),
        "media_tempo_protocolo_LA": get_media_tempo_protocolado_LA(protocolo_LA),
        "mediana_tempo_protocolo_LA": get_mediana_tempo_protocolado_LA(protocolo_LA),
        "comparativo_tempo_medio_protocolos_resolvidos_LA": get_comparativo_tempo_medio_protocolos_resolvidos_LA(protocolo_LA, all_protocolos=all_protocolo_LA, from_date=from_date, to_date=to_date),
        "comparativo_mediana_tempo_protocolos_resolvidos_LA": get_comparativo_mediana_tempo_protocolos_resolvidos_LA(protocolo_LA, all_protocolos=all_protocolo_LA, from_date=from_date, to_date=to_date),
        "taxa_protocolados_LA": taxa_prot_la,
        "entradas_protocolo_LA": get_entradas_protocolo_LA(all_protocolo_LA, from_date, to_date),
        "comparativo_protocolos_resolvidos_LA": get_comparativo_protocolos_resolvidos_LA(protocolo_LA, all_protocolos=all_protocolo_LA, from_date=from_date, to_date=to_date),
        "protocolos_resolvidos_periodo_anterior_LA": get_protocolos_resolvidos_periodo_anterior_LA(protocolo_LA, all_protocolos=all_protocolo_LA, from_date=from_date, to_date=to_date),
        "comparativo_valor_causa_protocolado_LA": get_comparativo_valor_causa_protocolado_LA(protocolo_LA, all_protocolos=all_protocolo_LA, from_date=from_date, to_date=to_date),
        "valor_causa_protocolado_periodo_anterior_LA": get_valor_causa_protocolado_periodo_anterior_LA(protocolo_LA, all_protocolos=all_protocolo_LA, from_date=from_date, to_date=to_date),
        "comparativo_ticket_medio_protocolos_resolvidos_LA": get_comparativo_ticket_medio_protocolos_resolvidos_LA(protocolo_LA, all_protocolos=all_protocolo_LA, from_date=from_date, to_date=to_date),
        "valor_causa_protocolado_LA_2026": get_valor_causa_protocolado_LA_2026(all_protocolo_LA),
        "meta_anual_comercial_LA": META_VALOR_CAUSA_2026_LA,
        "fator_multiplicador_LA": get_fator_multiplicador_LA(protocolo_LA),
        "comissao_com_fm_LA": pool_com_fm,
        "tempo_medio_contratacao_protocolo_LA": get_media_tempo_contratacao_protocolado_LA(protocolo_LA),
        "mediana_tempo_contratacao_protocolo_LA": get_mediana_tempo_contratacao_protocolado_LA(protocolo_LA),
        "comparativo_tempo_medio_contratacao_protocolo_LA": get_comparativo_tempo_medio_contratacao_protocolado_LA(protocolo_LA, all_protocolos=all_protocolo_LA, from_date=from_date, to_date=to_date),
        "comparativo_mediana_tempo_contratacao_protocolo_LA": get_comparativo_mediana_tempo_contratacao_protocolado_LA(protocolo_LA, all_protocolos=all_protocolo_LA, from_date=from_date, to_date=to_date),
    }
    charts = {
        "valor_causa_protocolado_por_atendente_LA": [ChartDataPoint(**x) for x in dict_to_chart_data(get_valor_causa_protocolado_por_atendente_LA(protocolo_LA))],
        "valor_causa_nao_protocolado_por_atendente_LA": [ChartDataPoint(**x) for x in dict_to_chart_data(get_valor_causa_nao_protocolado_por_atendente_LA(all_protocolo_LA))],
        "protocolos_resolvidos_por_atendente_LA": [ChartDataPoint(**x) for x in dict_to_chart_data(get_protocolos_resolvidos_por_atendente_LA(protocolo_LA), cast_int=True)],
        "nao_protocolados_por_atendente_LA": [ChartDataPoint(**x) for x in dict_to_chart_data(get_nao_protocolados_por_atendente_LA(all_protocolo_LA), cast_int=True)],
        "protocolados_por_dia_LA": [ChartDataPoint(**x) for x in group_protocolados_por_dia_LA(protocolo_LA)],
        "valor_causa_protocolados_por_dia_LA": [ChartDataPoint(**x) for x in group_valor_causa_protocolados_por_dia_LA(protocolo_LA)],
        "funcionarios_protocolo_LA": funcionarios,
        "protocolados_por_dia_por_funcionario_LA": {k: [ChartDataPoint(**i) for i in v] for k, v in por_dia_por_func.items()},
        "protocolados_por_materia_LA": [ChartDataPoint(**x) for x in group_protocolados_por_materia_LA(protocolo_LA)],
        "protocololados_por_funcionario_LA": [ChartDataPoint(**x) for x in group_protocolados_por_funcionario_LA(protocolo_LA)],
        "represados_protocolo_por_materia_LA": [ChartDataPoint(**x) for x in group_represados_por_materia_LA(all_protocolo_LA)],
        "represados_protocolo_por_funcionario_LA": [ChartDataPoint(**x) for x in group_represados_por_funcionario_LA(all_protocolo_LA)],
        "valor_causa_protocolo_por_funcionario_LA": [ChartDataPoint(**x) for x in dict_to_chart_data(get_valor_causa_protocolado_por_funcionario_LA(protocolo_LA))],
        "comissionamento_protocolo_LA_por_funcionario": [ComissionamentoProtocoloRow(**x) for x in get_protocolo_comissionamento_por_funcionario_LA(protocolo_LA, taxa=taxa_prot_la)],
        "protocolados_por_sistema_LA": [ChartDataPoint(**x) for x in group_protocolados_por_sistema_LA(protocolo_LA)],
        "protocolados_por_mes_LA": [ChartDataPoint(**x) for x in group_protocolados_por_mes_LA(protocolo_LA)],
        "valor_causa_protocolados_por_mes_LA": [ChartDataPoint(**x) for x in group_valor_causa_protocolados_por_mes_LA(protocolo_LA)],
        "media_protocolados_por_funcionario_LA": [ChartDataPoint(**x) for x in get_media_protocolados_por_funcionario_LA(protocolo_LA, from_date=from_date, to_date=to_date)],
        "represados_por_mes_LA": [ChartDataPoint(**x) for x in group_represados_por_mes_LA(protocolo_LA)],
    }
    return stats, charts


# v1: dashboard_routes.py:10951
def _build_peticionamento_LA_stats(
    peticionamento_LA: List[Dict],
    all_peticionamento_LA: List[Dict],
    from_date: Optional[date],
    to_date: Optional[date],
    peticionamento_LA_taxa: Optional[List[Dict]] = None,
    all_peticionamento_LA_taxa: Optional[List[Dict]] = None,
) -> Tuple[Dict, Dict]:
    func_raw = get_confeccionados_por_dia_por_funcionario_LA(peticionamento_LA)
    funcionarios, por_dia_por_func = _per_func_to_chart(func_raw)

    stats = {
        "total_confeccionados_LA": get_total_confeccionados_LA(peticionamento_LA),
        "confeccionados_manualmente_LA": get_total_confeccionados_manualmente_LA(peticionamento_LA),
        "confeccionados_automaticamente_LA": get_total_confeccionados_automaticamente_LA(peticionamento_LA),
        "nao_confeccionados_LA": get_nao_confeccionados_LA(all_peticionamento_LA),
        "valor_causa_confeccionado_LA": get_valor_causa_confeccionado_LA(peticionamento_LA),
        "ticket_medio_confeccionado_LA": get_ticket_medio_confeccionados_LA(peticionamento_LA),
        "tempo_medio_confeccao_LA": get_media_tempo_confeccionado_LA(peticionamento_LA),
        "mediana_tempo_confeccao_LA": get_mediana_tempo_confeccionado_LA(peticionamento_LA),
        "comparativo_confeccionados_LA": get_comparativo_confeccionados_LA(peticionamento_LA, all_peticionados=all_peticionamento_LA, from_date=from_date, to_date=to_date),
        "comparativo_confeccionados_automaticamente_LA": get_comparativo_confeccionados_automaticamente_LA(peticionamento_LA, all_peticionados=all_peticionamento_LA, from_date=from_date, to_date=to_date),
        "comparativo_confeccionados_manualmente_LA": get_comparativo_confeccionados_manualmente_LA(peticionamento_LA, all_peticionados=all_peticionamento_LA, from_date=from_date, to_date=to_date),
        "comparativo_valor_causa_confeccionado_LA": get_comparativo_valor_causa_confeccionado_LA(peticionamento_LA, all_peticionados=all_peticionamento_LA, from_date=from_date, to_date=to_date),
        "comparativo_ticket_medio_confeccionado_LA": get_comparativo_ticket_medio_confeccionado_LA(peticionamento_LA, all_peticionados=all_peticionamento_LA, from_date=from_date, to_date=to_date),
        "comparativo_tempo_medio_confeccionado_LA": get_comparativo_tempo_medio_confeccionado_LA(peticionamento_LA, all_peticionados=all_peticionamento_LA, from_date=from_date, to_date=to_date),
        "comparativo_mediana_tempo_confeccionado_LA": get_comparativo_mediana_tempo_confeccionadoLA(peticionamento_LA, all_peticionados=all_peticionamento_LA, from_date=from_date, to_date=to_date),
        "peticionamento_taxa_resolvidos_LA": get_peticionamento_taxa_resolvidos_LA(peticionamento_LA, all_peticionamento_LA),
        "peticionamento_taxa_nao_resolvidos_LA": get_peticionamento_taxa_nao_resolvidos_LA(peticionamento_LA, all_peticionamento_LA),
        "peticionamento_taxa_retorno_protocolo_LA": get_peticionamento_taxa_retorno_protocolo_LA(peticionamento_LA),
        "peticionamento_qtd_retorno_protocolo_LA": get_peticionamento_qtd_retorno_protocolo_LA(peticionamento_LA),
        "peticionamento_qtd_entrada_protocolo_LA": get_peticionamento_qtd_entrada_protocolo_LA(peticionamento_LA),
    }
    charts = {
        "confeccionados_por_dia_LA": [ChartDataPoint(**x) for x in group_confeccionados_por_dia_LA(peticionamento_LA)],
        "funcionarios_confeccao_LA": funcionarios,
        "confeccionados_por_dia_por_funcionario_LA": {k: [ChartDataPoint(**i) for i in v] for k, v in por_dia_por_func.items()},
        "confeccionados_por_materia_LA": [ChartDataPoint(**x) for x in group_confeccionados_por_materia_LA(peticionamento_LA)],
        "nao_confeccionados_por_materia_LA": [ChartDataPoint(**x) for x in group_nao_confeccionados_por_materia_LA(all_peticionamento_LA)],
        "confeccionados_por_funcionario_LA": [ChartDataPoint(**x) for x in group_confeccionados_por_funcionario_LA(peticionamento_LA)],
        "nao_confeccionados_por_funcionario_LA": [ChartDataPoint(**x) for x in group_nao_confeccionados_por_funcionario_LA(all_peticionamento_LA)],
        "valor_confeccionado_por_funcionario_LA": [ChartDataPoint(**x) for x in dict_to_chart_data(get_valor_causa_confeccionado_por_funcionario_LA(peticionamento_LA))],
        "media_confeccionado_por_funcionario_LA": [ChartDataPoint(**x) for x in get_media_confeccionado_por_funcionario_LA(peticionamento_LA, from_date=from_date, to_date=to_date)],
        "confeccionados_por_mes_LA": [ChartDataPoint(**x) for x in group_confeccionados_por_mes_LA(peticionamento_LA)],
        "nao_confeccionados_por_mes_LA": [ChartDataPoint(**x) for x in group_nao_confeccionados_por_mes_LA(peticionamento_LA)],
        "comissionamento_peticionamento_LA_por_funcionario": [
            ComissionamentoPeticionamentoRow(**x)
            for x in get_peticionamento_comissionamento_por_funcionario_LA(
                peticionamento_LA, all_peticionamento_LA, peticionamento_LA_taxa, all_peticionamento_LA_taxa,
            )
        ],
    }
    return stats, charts


# v1: dashboard_routes.py:11040
def _build_pendencias_LA_stats(
    pendencias_LA: List[Dict],
    all_pendencias_LA: List[Dict],
    from_date: Optional[date],
    to_date: Optional[date],
) -> Tuple[Dict, Dict]:
    func_raw = get_pendencias_resolvidas_por_dia_por_funcionario_LA(pendencias_LA)
    funcionarios, por_dia_por_func = _per_func_to_chart(func_raw)

    stats = {
        "pendencias_total_LA": get_pendencias_total_LA(pendencias_LA),
        "pendencias_nao_resolvidas_LA": get_pendencias_nao_resolvidas_LA(pendencias_LA),
        "pendencias_nao_resolvidas_com_atraso_LA": get_pendencias_nao_resolvidas_com_atraso_LA(pendencias_LA),
        "pendencias_resolvidas_LA": get_pendencias_resolvidas_LA(pendencias_LA),
        "pendencias_canceladas_LA": get_pendencias_canceladas_LA(pendencias_LA),
        "pendencias_taxa_nao_resolvidos_LA": get_pendencias_taxa_nao_resolvidos_LA(pendencias_LA),
        "pendencias_taxa_resolvidos_LA": get_pendencias_taxa_resolvidos_LA(pendencias_LA),
        "pendencias_taxa_canceladas_LA": get_pendencias_taxa_canceladas_LA(pendencias_LA),
        "pendencias_triagem_LA": get_pendencias_triagem_LA(pendencias_LA),
        "media_tempo_resolvidos_pendencia_LA": get_media_tempo_resolvidos_pendencia_LA(pendencias_LA),
        "mediana_tempo_resolvidos_pendencia_LA": get_mediana_tempo_resolvidos_pendencia_LA(pendencias_LA),
    }
    charts = {
        "pendencias_nao_resolvidas_por_atendente_LA": [ChartDataPoint(**x) for x in dict_to_chart_data(get_pendencias_nao_resolvidas_por_atendente_LA(all_pendencias_LA), cast_int=True)],
        # CORRIGIDO: chaves com sufixo _LA para não sobrescrever dados NG no dashboard comercial
        "pendencias_nao_resolvidas_por_origem_LA": [ChartDataPoint(**x) for x in get_pendencias_nao_resolvidas_por_origem_LA(pendencias_LA)],
        "pendencias_resolvidas_por_mes_LA": [ChartDataPoint(**x) for x in group_pendencias_resolvidas_por_mes_LA(pendencias_LA)],
        "media_pendencias_resolvidas_por_funcionario_LA": [ChartDataPoint(**x) for x in get_media_pendencias_resolvidas_por_funcionario_LA(pendencias_LA)],
        "pendencias_resolvidas_por_dia_LA": [ChartDataPoint(**x) for x in group_pendencias_resolvidas_por_dia_LA(pendencias_LA)],
        "funcionarios_pendencias_LA": funcionarios,
        "pendencias_resolvidas_por_dia_por_funcionario_LA": {k: [ChartDataPoint(**i) for i in v] for k, v in por_dia_por_func.items()},
        "comissionamento_pendencias_LA_por_funcionario": [
            ComissionamentoPendenciaRow(**x) for x in get_pendencias_comissionamento_por_funcionario_LA(pendencias_LA)
        ],
    }
    return stats, charts


# V2: só os dashboards desta cópia (v1: FETCHES_BY_DASHBOARD, mesmas fontes e chaves).
FETCHES_BY_DASHBOARD: Dict[str, List[Tuple[str, Any]]] = {
    "protocolo_LA": [("protocolo_LA", fetch_protocolo_LA), ("comercial_LA", fetch_comercial_LA)],
    "peticionamento_LA": [("peticionamento_LA", fetch_peticionamento_LA)],
    "org_doc_LA": [("org_doc_LA", fetch_org_doc_LA)],
    "pendencia_LA": [("pendencia_LA", fetch_pendencias_LA)],
}
DASHBOARD_NAMES = set(FETCHES_BY_DASHBOARD)


# v1: dashboard_routes.py:11255 — V2: início igual, só os ramos de protocolo_LA, peticionamento_LA, org_doc_LA, pendencia_LA
async def _get_dashboard_response(  # V2: só os parâmetros usados por estes dashboards
    dashboard_name: str,
    from_date: Optional[date],
    to_date: Optional[date],
    funcionario: Optional[List[str]] = None,
    materia: Optional[Union[str, List[str]]] = None,
    sistema: Optional[str] = None,
    uf_peticionamento_LA: Optional[str] = None,
    uf_org_doc_LA: Optional[str] = None,
    uf_pendencia_LA: Optional[str] = None,
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
    if dashboard_name == "org_doc_LA":
        funcs_od_la = _normalizar_funcionarios_query(funcionario)
        ufs_org_doc_LA_opcoes = list_ufs_org_doc_LA(_f("org_doc_LA"))
        uf_org_doc_LA_filtro = (
            str(uf_org_doc_LA).strip().upper()
            if uf_org_doc_LA and str(uf_org_doc_LA).strip()
            else None
        )
        od_la = filter_org_doc_LA_por_uf(
            filter_org_doc_LA_por_funcionarios(
                filter_org_doc_LA_por_materia(_f("org_doc_LA"), materia),
                funcs_od_la,
            ),
            uf_org_doc_LA_filtro,
        )
        all_od_la = filter_org_doc_LA_por_uf(
            filter_org_doc_LA_por_funcionarios(
                filter_org_doc_LA_por_materia(_a("org_doc_LA"), materia),
                funcs_od_la,
            ),
            uf_org_doc_LA_filtro,
        )
        stats, charts = _build_org_doc_LA_stats(od_la, all_od_la, from_date, to_date)
        stats["ufs_org_doc_LA_opcoes"] = ufs_org_doc_LA_opcoes
        stats["uf_org_doc_LA_filtro"] = uf_org_doc_LA_filtro
        stats["funcionarios_filtro"] = funcs_od_la or None
        stats["funcionario_filtro"] = ", ".join(funcs_od_la) if funcs_od_la else None
        logger.info("Dashboard 'org_doc_LA' processado em %.2fs", time.time() - t0)
        return DashboardResponse(dashboard="org_doc_LA", stats=DashboardStats(**stats), **charts)
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
    if dashboard_name == "protocolo_LA":
        funcs_pla = _normalizar_funcionarios_query(funcionario)
        pla = filter_protocolo_LA_por_sistema(
            filter_protocolo_LA_por_funcionarios(
                filter_protocolo_LA_por_materia(_f("protocolo_LA"), materia),
                funcs_pla,
            ),
            sistema,
        )
        all_pla = filter_protocolo_LA_por_sistema(
            filter_protocolo_LA_por_funcionarios(
                filter_protocolo_LA_por_materia(_a("protocolo_LA"), materia),
                funcs_pla,
            ),
            sistema,
        )
        stats, charts = _build_protocolo_LA_stats(pla, all_pla, from_date, to_date, comercial_LA=_f("comercial_LA"))
        logger.info("Dashboard 'protocolo_LA' processado em %.2fs", time.time() - t0)
        return DashboardResponse(dashboard="protocolo_LA", stats=DashboardStats(**stats), **charts)
    if dashboard_name == "peticionamento_LA":
        funcs_pet_la = _normalizar_funcionarios_query(funcionario)
        ufs_peticionamento_LA_opcoes = list_ufs_peticionamento_LA(_f("peticionamento_LA"))
        uf_peticionamento_LA_filtro = (
            str(uf_peticionamento_LA).strip().upper()
            if uf_peticionamento_LA and str(uf_peticionamento_LA).strip()
            else None
        )
        pet_la = filter_peticionamento_LA_por_uf(
            filter_peticionamento_LA_por_funcionarios(
                filter_peticionamento_LA_por_materia(_f("peticionamento_LA"), materia),
                funcs_pet_la,
            ),
            uf_peticionamento_LA_filtro,
        )
        all_pet_la = filter_peticionamento_LA_por_uf(
            filter_peticionamento_LA_por_funcionarios(
                filter_peticionamento_LA_por_materia(_a("peticionamento_LA"), materia),
                funcs_pet_la,
            ),
            uf_peticionamento_LA_filtro,
        )
        # Sem filtro de matéria: usado só para a taxa de resolvidos do comissionamento,
        # que deve refletir a taxa GERAL do funcionário, não a taxa recortada pela matéria filtrada.
        pet_la_taxa = filter_peticionamento_LA_por_uf(
            filter_peticionamento_LA_por_funcionarios(_f("peticionamento_LA"), funcs_pet_la),
            uf_peticionamento_LA_filtro,
        )
        all_pet_la_taxa = filter_peticionamento_LA_por_uf(
            filter_peticionamento_LA_por_funcionarios(_a("peticionamento_LA"), funcs_pet_la),
            uf_peticionamento_LA_filtro,
        )
        stats, charts = _build_peticionamento_LA_stats(
            pet_la, all_pet_la, from_date, to_date, pet_la_taxa, all_pet_la_taxa,
        )
        stats["ufs_peticionamento_LA_opcoes"] = ufs_peticionamento_LA_opcoes
        stats["uf_peticionamento_LA_filtro"] = uf_peticionamento_LA_filtro
        stats["funcionarios_filtro"] = funcs_pet_la or None
        stats["funcionario_filtro"] = ", ".join(funcs_pet_la) if funcs_pet_la else None
        logger.info("Dashboard 'peticionamento_LA' processado em %.2fs", time.time() - t0)
        return DashboardResponse(dashboard="peticionamento_LA", stats=DashboardStats(**stats), **charts)
    # V2: (bloco de outros dashboards da v1 omitido)
    if dashboard_name == "pendencia_LA":
        ufs_pendencia_LA_opcoes = list_ufs_pendencia_LA(_f("pendencia_LA"))
        uf_pendencia_LA_filtro = (
            str(uf_pendencia_LA).strip().upper()
            if uf_pendencia_LA and str(uf_pendencia_LA).strip()
            else None
        )
        funcs_pend_la = _normalizar_funcionarios_query(funcionario)
        pendencias = filter_pendencia_LA_por_uf(
            filter_pendencia_LA_por_funcionarios(_f("pendencia_LA"), funcs_pend_la),
            uf_pendencia_LA_filtro,
        )
        all_pend = filter_pendencia_LA_por_uf(
            filter_pendencia_LA_por_funcionarios(_a("pendencia_LA"), funcs_pend_la),
            uf_pendencia_LA_filtro,
        )
        stats, charts = _build_pendencias_LA_stats(pendencias, all_pend, from_date, to_date)
        stats["ufs_pendencia_LA_opcoes"] = ufs_pendencia_LA_opcoes
        stats["uf_pendencia_LA_filtro"] = uf_pendencia_LA_filtro
        return DashboardResponse(dashboard="pendencia_LA", stats=DashboardStats(**stats), **charts)
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


# v1: dashboard_routes.py:29126 (rota sem os decoradores)
async def get_protocolo_LA_dashboard(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    materia: Optional[List[str]] = Query(
        None,
        description="Filtra pela matéria normalizada (igual `org_doc_LA`: ex. Sem materia, código antes de ' - ').",
    ),
    funcionario: Optional[List[str]] = Query(
        None,
        description="Filtra pelos responsáveis LA (repita o parâmetro para vários; rótulos como nos gráficos).",
    ),
    sistema: Optional[str] = Query(
        None,
        description="Filtra pelo sistema (rótulo igual ao `name` de protocolados_por_sistema_LA, ex. Sem sistema).",
    ),
    area_atuacao_id: Optional[List[int]] = Query(None, description="Filtra processos pela área de atuação (ID)."),
):
    """Dashboard de Protocolo LA."""
    return await _get_dashboard_response(
        "protocolo_LA",
        from_date,
        to_date,
        materia=materia,
        funcionario=funcionario,
        sistema=sistema,
        area_atuacao_id=area_atuacao_id,
    )


# v1: dashboard_routes.py:29290 (rota sem os decoradores)
async def get_peticionamento_LA_dashboard(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    materia: Optional[List[str]] = Query(
        None,
        description="Filtra pela matéria normalizada (igual `org_doc_LA`: ex. Sem materia, código antes de ' - ').",
    ),
    funcionario: Optional[List[str]] = Query(
        None,
        description="Filtra pelos responsáveis LA (repita o parâmetro para vários; rótulos como nos gráficos).",
    ),
    uf_peticionamento_LA: Optional[str] = Query(
        None,
        description="Filtra peticionamento LA pela UF. Valores disponíveis em GET /peticionamento_LA/ufs.",
    ),
    area_atuacao_id: Optional[List[int]] = Query(None, description="Filtra processos pela área de atuação (ID)."),
):
    """Dashboard de Peticionamento LA."""
    return await _get_dashboard_response(
        "peticionamento_LA",
        from_date,
        to_date,
        materia=materia,
        funcionario=funcionario,
        uf_peticionamento_LA=uf_peticionamento_LA,
        area_atuacao_id=area_atuacao_id,
    )


# v1: dashboard_routes.py:23088 (rota sem os decoradores)
async def get_org_doc_LA_dashboard(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    materia: Optional[List[str]] = Query(
        None,
        description="Filtra pela matéria normalizada (igual ao `name` dos gráficos por matéria LA).",
    ),
    funcionario: Optional[List[str]] = Query(
        None,
        description="Filtra pelos responsáveis LA (repita o parâmetro para vários; rótulos como nos gráficos).",
    ),
    uf_org_doc_LA: Optional[str] = Query(
        None,
        description="Filtra org. documentos LA pela UF. Valores disponíveis em GET /org_doc_LA/ufs.",
    ),
    area_atuacao_id: Optional[List[int]] = Query(None, description="Filtra processos pela área de atuação (ID)."),
):
    """Dashboard de Organização de Documentos LA."""
    return await _get_dashboard_response(
        "org_doc_LA",
        from_date,
        to_date,
        materia=materia,
        funcionario=funcionario,
        uf_org_doc_LA=uf_org_doc_LA,
        area_atuacao_id=area_atuacao_id,
    )


# v1: dashboard_routes.py:29693 (rota sem os decoradores)
async def get_pendencia_LA_dashboard(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    funcionario: Optional[List[str]] = Query(
        None,
        description="Filtra pelos responsáveis LA (repita o parâmetro para vários; igual pendências / protocolo NG).",
    ),
    uf_pendencia_LA: Optional[str] = Query(
        None,
        description="Filtra pendências LA pela UF. Valores disponíveis em GET /pendencia_LA/ufs.",
    ),
    area_atuacao_id: Optional[List[int]] = Query(None, description="Filtra processos pela área de atuação (ID)."),
):
    """Dashboard de Pendências LA."""
    return await _get_dashboard_response(
        "pendencia_LA",
        from_date,
        to_date,
        funcionario=funcionario,
        uf_pendencia_LA=uf_pendencia_LA,
        area_atuacao_id=area_atuacao_id,
    )


# V2: dashboard da v1 -> handler da rota e queries que ele busca (para a casca e o aquecedor do cache).
HANDLERS = {"protocolo_LA": get_protocolo_LA_dashboard, "peticionamento_LA": get_peticionamento_LA_dashboard, "org_doc_LA": get_org_doc_LA_dashboard, "pendencia_LA": get_pendencia_LA_dashboard}
QUERIES_POR_DASHBOARD = {'protocolo_LA': ('setor_protocolo_LA', 'comercial_geral_LA'), 'peticionamento_LA': ('setor_confeccao_LA',), 'org_doc_LA': ('setor_org_documentos_LA',), 'pendencia_LA': ('setor_pendencia_LA',)}
