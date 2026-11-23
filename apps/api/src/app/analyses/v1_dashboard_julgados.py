"""Dashboards "genéricos" da v1 (ramos de _get_dashboard_response) usados pela V2 — cópia SEM mudança.

Origem: api_dashboards/src/app/dashboard_routes.py (linha na v1 ao lado de cada bloco).
Gerado por scripts/copiar_v1/gerar_generico.py (banco lexflow). Únicas trocas, marcadas com "V2:":
  * fetch_*: buscam pela fonte da V2 (`usar_fonte`), com o recorte de situação do processo da v1;
  * _get_dashboard_response: mesmo início da v1 (fontes, datas, _f/_a), só com os ramos abaixo;
  * fontes de outro banco saem de FETCHES_BY_DASHBOARD (chegam vazias, como na v1 com a fonte fora do ar).
Dashboards: julgados_acordaos_NG, julgados_acordaos_LA, julgados_acordaos_RJ.
"""

import asyncio
import logging
import time
from contextvars import ContextVar
from app.analyses.common import periodo  # V2: período e variação vs período anterior num módulo só
from app.analyses.common import conversao  # V2: conversões dos valores do banco num módulo só
from app.analyses.common import memo  # V2: cache por pedido (a mesma conta uma vez por pedido)
from app.analyses.LA.julgados_acordao_LA import (
    CATEGORIAS_2G_VALIDAS_JULGADOS_LA,
    JulgadosAcordaoFiltrosLA,
    filtrar_acordaos_julgados_LA,
    get_comparativos_acordao_julgados_LA,
    get_improcedencia_acordao_totais_julgados_LA,
    get_julgados_acordao_campos_vazios_LA,
    get_julgados_acordao_dados_faltando_LA,
    get_kpis_acordao_julgados_LA,
    get_opcoes_uf_julgados_acordao_LA,
    get_ranking_relatores_acordao_julgados_LA,
    get_ranking_relatores_improcedencia_julgados_LA,
    get_total_acordaos_julgados_LA,
    group_acordao_embargos_resultado_julgados_LA,
    group_acordao_improcedentes_por_comarca_julgados_LA,
    group_acordao_por_ano_ajuizamento_julgados_LA,
    group_acordao_por_comarca_julgados_LA,
    group_acordao_por_competencia_julgados_LA,
    group_acordao_por_materia_julgados_LA,
    group_acordao_por_motivo_extincao_julgados_LA,
    group_acordao_por_motivo_improcedencia_julgados_LA,
    group_julgados_acordao_extintos_por_mes_LA,
    group_julgados_acordao_improcedentes_por_mes_LA,
    group_julgados_acordao_procedentes_por_mes_LA,
    list_acordaos_julgados_LA,
)
from app.analyses.LA.julgados_sentenca_LA import (
    get_opcoes_comarca_julgados_LA,
)
from app.analyses.NG.comercial_geral import (
    filter_comercial_geral_por_area_atuacao,
)
from app.analyses.NG.julgados_acordao import (
    CATEGORIAS_2G_VALIDAS_JULGADOS_NG,
    JulgadosAcordaoFiltros,
    filtrar_acordaos_julgados_NG,
    get_comparativos_acordao_julgados_NG,
    get_improcedencia_acordao_totais_julgados_NG,
    get_improcedencia_acordao_tribunal_superior_julgados_NG,
    get_julgados_acordao_campos_vazios_NG,
    get_julgados_acordao_dados_faltando_NG,
    get_kpis_acordao_julgados_NG,
    get_opcoes_uf_julgados_acordao_NG,
    get_ranking_relatores_acordao_julgados_NG,
    get_ranking_relatores_improcedencia_julgados_NG,
    get_total_acordaos_julgados_NG,
    group_acordao_embargos_resultado_julgados_NG,
    group_acordao_improcedentes_por_comarca_julgados_NG,
    group_acordao_por_ano_ajuizamento_julgados_NG,
    group_acordao_por_comarca_julgados_NG,
    group_acordao_por_competencia_julgados_NG,
    group_acordao_por_materia_julgados_NG,
    group_acordao_por_motivo_extincao_julgados_NG,
    group_acordao_por_motivo_improcedencia_julgados_NG,
    group_julgados_acordao_extintos_por_mes_NG,
    group_julgados_acordao_improcedentes_por_mes_NG,
    group_julgados_acordao_procedentes_por_mes_NG,
    list_acordaos_julgados_NG,
)
from app.analyses.NG.julgados_sentenca import (
    get_opcoes_comarca_julgados_NG,
)
from app.analyses.RJ.julgados_acordao_RJ import (
    CATEGORIAS_2G_VALIDAS_JULGADOS_RJ,
    JulgadosAcordaoFiltrosRJ,
    filtrar_acordaos_julgados_RJ,
    get_comparativos_acordao_julgados_RJ,
    get_improcedencia_acordao_totais_julgados_RJ,
    get_julgados_acordao_campos_vazios_RJ,
    get_julgados_acordao_dados_faltando_RJ,
    get_kpis_acordao_julgados_RJ,
    get_opcoes_uf_julgados_acordao_RJ,
    get_ranking_relatores_acordao_julgados_RJ,
    get_ranking_relatores_improcedencia_julgados_RJ,
    get_total_acordaos_julgados_RJ,
    group_acordao_embargos_resultado_julgados_RJ,
    group_acordao_improcedentes_por_comarca_julgados_RJ,
    group_acordao_por_ano_ajuizamento_julgados_RJ,
    group_acordao_por_comarca_julgados_RJ,
    group_acordao_por_competencia_julgados_RJ,
    group_acordao_por_materia_julgados_RJ,
    group_acordao_por_motivo_extincao_julgados_RJ,
    group_acordao_por_motivo_improcedencia_julgados_RJ,
    group_julgados_acordao_extintos_por_mes_RJ,
    group_julgados_acordao_improcedentes_por_mes_RJ,
    group_julgados_acordao_procedentes_por_mes_RJ,
    list_acordaos_julgados_RJ,
)
from app.analyses.RJ.julgados_sentenca_RJ import (
    get_opcoes_comarca_julgados_RJ,
)
from app.analyses.common.matriz_julgamento import (
    STATUS_EMBARGO_ORDEM,
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
_fonte_ctx: ContextVar[Any] = ContextVar("fonte_v1_generico_lexflow")

def usar_fonte(fonte):
    """Define a fonte das buscas deste contexto; devolve o token para `_fonte_ctx.reset`."""
    return _fonte_ctx.set(fonte)


@memo.por_pedido(contexto=(_fonte_ctx, _situacoes_processo_ctx), copiar=False)
async def _fetch_v2(query_name: str) -> List[Dict[str, Any]]:
    return aplicar_filtro_situacao_processo(query_name, await _fonte_ctx.get().fetch(query_name))


# V2: v1 dashboard_routes.py:3122 -> fetch_data_with_cache('julgados', ...)
async def fetch_julgados_NG() -> List[Dict[str, Any]]:
    return await _fetch_v2('julgados')


# V2: v1 dashboard_routes.py:3125 -> fetch_data_with_cache('julgados', ...)
async def fetch_julgados_LA() -> List[Dict[str, Any]]:
    return await _fetch_v2('julgados')


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


# v1: dashboard_routes.py:31387
_RESULTADOS_EMBARGOS_VALIDOS_JULGADOS: frozenset[str] = frozenset(s.lower() for s in STATUS_EMBARGO_ORDEM)


# v1: dashboard_routes.py:31513
def _parse_julgados_acordao_filtros(
    materia: Optional[List[str]] = None,
    relator: Optional[List[str]] = None,
    comarca: Optional[List[str]] = None,
    competencia: Optional[List[str]] = None,
    categoria: Optional[List[str]] = None,
    uf: Optional[List[str]] = None,
    motivo_extincao: Optional[List[str]] = None,
    ano_ajuizamento: Optional[List[str]] = None,
    resultado_embargos: Optional[List[str]] = None,
) -> Optional[JulgadosAcordaoFiltros]:
    """Parser dos filtros interativos cumulativos do dashboard Julgados Acórdãos (NG)."""
    def _to_set(valores: Optional[List[str]]) -> set[str]:
        result: set[str] = set()
        if valores:
            for raw in valores:
                t = str(raw or "").strip()
                if t:
                    result.add(t)
        return result

    materias = _to_set(materia)
    relatores = _to_set(relator)
    comarcas = _to_set(comarca)
    competencias = _to_set(competencia)
    categorias = _to_set(categoria)
    ufs = {u.upper() for u in _to_set(uf)}
    motivos_extincao = _to_set(motivo_extincao)
    anos_ajuizamento = _to_set(ano_ajuizamento)
    resultados_embargos = {r.lower() for r in _to_set(resultado_embargos)}

    for chave in categorias:
        if chave not in CATEGORIAS_2G_VALIDAS_JULGADOS_NG:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Categoria inválida: '{chave}'. "
                    f"Valores: {sorted(CATEGORIAS_2G_VALIDAS_JULGADOS_NG)}"
                ),
            )
    for chave in resultados_embargos:
        if chave not in _RESULTADOS_EMBARGOS_VALIDOS_JULGADOS:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Resultado de embargos inválido: '{chave}'. "
                    f"Valores: {sorted(_RESULTADOS_EMBARGOS_VALIDOS_JULGADOS)}"
                ),
            )

    filtros = JulgadosAcordaoFiltros(
        materias=frozenset(materias) if materias else None,
        relatores=frozenset(relatores) if relatores else None,
        comarcas=frozenset(comarcas) if comarcas else None,
        competencias=frozenset(competencias) if competencias else None,
        categorias=frozenset(categorias) if categorias else None,
        ufs=frozenset(ufs) if ufs else None,
        motivos_extincao=frozenset(motivos_extincao) if motivos_extincao else None,
        anos_ajuizamento=frozenset(anos_ajuizamento) if anos_ajuizamento else None,
        resultados_embargos=frozenset(resultados_embargos) if resultados_embargos else None,
    )
    return filtros if filtros.ativo() else None


# v1: dashboard_routes.py:31882
def _parse_julgados_acordao_filtros_la(
    materia: Optional[List[str]] = None,
    relator: Optional[List[str]] = None,
    comarca: Optional[List[str]] = None,
    competencia: Optional[List[str]] = None,
    categoria: Optional[List[str]] = None,
    uf: Optional[List[str]] = None,
    motivo_extincao: Optional[List[str]] = None,
    ano_ajuizamento: Optional[List[str]] = None,
    resultado_embargos: Optional[List[str]] = None,
) -> Optional[JulgadosAcordaoFiltrosLA]:
    """Parser dos filtros interativos cumulativos do dashboard Julgados Acórdãos (LA)."""
    def _to_set(valores: Optional[List[str]]) -> set[str]:
        result: set[str] = set()
        if valores:
            for raw in valores:
                t = str(raw or "").strip()
                if t:
                    result.add(t)
        return result

    materias = _to_set(materia)
    relatores = _to_set(relator)
    comarcas = _to_set(comarca)
    competencias = _to_set(competencia)
    categorias = _to_set(categoria)
    ufs = {u.upper() for u in _to_set(uf)}
    motivos_extincao = _to_set(motivo_extincao)
    anos_ajuizamento = _to_set(ano_ajuizamento)
    resultados_embargos = {r.lower() for r in _to_set(resultado_embargos)}

    for chave in categorias:
        if chave not in CATEGORIAS_2G_VALIDAS_JULGADOS_LA:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Categoria inválida: '{chave}'. "
                    f"Valores: {sorted(CATEGORIAS_2G_VALIDAS_JULGADOS_LA)}"
                ),
            )
    for chave in resultados_embargos:
        if chave not in _RESULTADOS_EMBARGOS_VALIDOS_JULGADOS:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Resultado de embargos inválido: '{chave}'. "
                    f"Valores: {sorted(_RESULTADOS_EMBARGOS_VALIDOS_JULGADOS)}"
                ),
            )

    filtros = JulgadosAcordaoFiltrosLA(
        materias=frozenset(materias) if materias else None,
        relatores=frozenset(relatores) if relatores else None,
        comarcas=frozenset(comarcas) if comarcas else None,
        competencias=frozenset(competencias) if competencias else None,
        categorias=frozenset(categorias) if categorias else None,
        ufs=frozenset(ufs) if ufs else None,
        motivos_extincao=frozenset(motivos_extincao) if motivos_extincao else None,
        anos_ajuizamento=frozenset(anos_ajuizamento) if anos_ajuizamento else None,
        resultados_embargos=frozenset(resultados_embargos) if resultados_embargos else None,
    )
    return filtros if filtros.ativo() else None


# v1: dashboard_routes.py:32005
def _parse_julgados_acordao_filtros_rj(
    materia: Optional[List[str]] = None,
    relator: Optional[List[str]] = None,
    comarca: Optional[List[str]] = None,
    competencia: Optional[List[str]] = None,
    categoria: Optional[List[str]] = None,
    uf: Optional[List[str]] = None,
    motivo_extincao: Optional[List[str]] = None,
    ano_ajuizamento: Optional[List[str]] = None,
    resultado_embargos: Optional[List[str]] = None,
) -> Optional[JulgadosAcordaoFiltrosRJ]:
    """Parser dos filtros interativos cumulativos do dashboard Julgados Acórdãos (RJ)."""
    def _to_set(valores: Optional[List[str]]) -> set[str]:
        result: set[str] = set()
        if valores:
            for raw in valores:
                t = str(raw or "").strip()
                if t:
                    result.add(t)
        return result

    materias = _to_set(materia)
    relatores = _to_set(relator)
    comarcas = _to_set(comarca)
    competencias = _to_set(competencia)
    categorias = _to_set(categoria)
    ufs = {u.upper() for u in _to_set(uf)}
    motivos_extincao = _to_set(motivo_extincao)
    anos_ajuizamento = _to_set(ano_ajuizamento)
    resultados_embargos = {r.lower() for r in _to_set(resultado_embargos)}

    for chave in categorias:
        if chave not in CATEGORIAS_2G_VALIDAS_JULGADOS_RJ:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Categoria inválida: '{chave}'. "
                    f"Valores: {sorted(CATEGORIAS_2G_VALIDAS_JULGADOS_RJ)}"
                ),
            )
    for chave in resultados_embargos:
        if chave not in _RESULTADOS_EMBARGOS_VALIDOS_JULGADOS:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Resultado de embargos inválido: '{chave}'. "
                    f"Valores: {sorted(_RESULTADOS_EMBARGOS_VALIDOS_JULGADOS)}"
                ),
            )

    filtros = JulgadosAcordaoFiltrosRJ(
        materias=frozenset(materias) if materias else None,
        relatores=frozenset(relatores) if relatores else None,
        comarcas=frozenset(comarcas) if comarcas else None,
        competencias=frozenset(competencias) if competencias else None,
        categorias=frozenset(categorias) if categorias else None,
        ufs=frozenset(ufs) if ufs else None,
        motivos_extincao=frozenset(motivos_extincao) if motivos_extincao else None,
        anos_ajuizamento=frozenset(anos_ajuizamento) if anos_ajuizamento else None,
        resultados_embargos=frozenset(resultados_embargos) if resultados_embargos else None,
    )
    return filtros if filtros.ativo() else None


# V2: só os dashboards desta cópia (v1: FETCHES_BY_DASHBOARD, mesmas fontes e chaves).
FETCHES_BY_DASHBOARD: Dict[str, List[Tuple[str, Any]]] = {
    "julgados_acordaos_NG": [("julgados_NG", fetch_julgados_NG)],
    "julgados_acordaos_LA": [("julgados_LA", fetch_julgados_LA)],
    "julgados_acordaos_RJ": [("julgados_LA", fetch_julgados_LA)],
}
DASHBOARD_NAMES = set(FETCHES_BY_DASHBOARD)


# v1: dashboard_routes.py:11255 — V2: início igual, só os ramos de julgados_acordaos_NG, julgados_acordaos_LA, julgados_acordaos_RJ
async def _get_dashboard_response(  # V2: só os parâmetros usados por estes dashboards
    dashboard_name: str,
    from_date: Optional[date],
    to_date: Optional[date],
    julgados_acordao_filtros: Optional[JulgadosAcordaoFiltros] = None,
    julgados_acordao_filtros_la: Optional[JulgadosAcordaoFiltrosLA] = None,
    julgados_acordao_filtros_rj: Optional[JulgadosAcordaoFiltrosRJ] = None,
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
    if dashboard_name == "julgados_acordaos_NG":
        processos_julgados_acordao = filtrar_acordaos_julgados_NG(_a("julgados_NG"), julgados_acordao_filtros)
        stats = get_kpis_acordao_julgados_NG(processos_julgados_acordao, from_date=from_date, to_date=to_date)
        stats.update(
            get_comparativos_acordao_julgados_NG(processos_julgados_acordao, from_date=from_date, to_date=to_date)
        )
        stats["julgados_acordao_uf_opcoes_NG"] = get_opcoes_uf_julgados_acordao_NG(_a("julgados_NG"))
        stats.update(
            get_julgados_acordao_campos_vazios_NG(
                # Faixa de atenção: histórico todo, independente do período (06/11/2026)
                processos_julgados_acordao, from_date=None, to_date=None
            )
        )
        stats["julgados_acordao_dados_faltando_NG"] = get_julgados_acordao_dados_faltando_NG(
            # Faixa de atenção: histórico todo, independente do período (06/11/2026)
            processos_julgados_acordao, from_date=None, to_date=None
        )
        # Estudo das Improcedências (11/11/2026): mesma montagem do estudo da Sentença.
        _imp_ac_entrada_NG = get_improcedencia_acordao_totais_julgados_NG(
            processos_julgados_acordao, from_date=from_date, to_date=to_date
        )
        _imp_ac_estoque_NG = get_improcedencia_acordao_totais_julgados_NG(processos_julgados_acordao)
        stats["julgados_acordao_improcedencia_valor_NG"] = _imp_ac_entrada_NG["valor_causa"]
        stats["julgados_acordao_improcedencia_total_estoque_NG"] = _imp_ac_estoque_NG["total"]
        stats["julgados_acordao_improcedencia_valor_estoque_NG"] = _imp_ac_estoque_NG["valor_causa"]
        _imp_ac_sup_entrada_NG = get_improcedencia_acordao_tribunal_superior_julgados_NG(
            processos_julgados_acordao, from_date=from_date, to_date=to_date
        )
        _imp_ac_sup_estoque_NG = get_improcedencia_acordao_tribunal_superior_julgados_NG(processos_julgados_acordao)
        stats["julgados_acordao_improcedencia_stj_NG"] = _imp_ac_sup_entrada_NG["stj"]
        stats["julgados_acordao_improcedencia_stf_NG"] = _imp_ac_sup_entrada_NG["stf"]
        stats["julgados_acordao_improcedencia_stj_estoque_NG"] = _imp_ac_sup_estoque_NG["stj"]
        stats["julgados_acordao_improcedencia_stf_estoque_NG"] = _imp_ac_sup_estoque_NG["stf"]
        stats["julgados_acordao_total_estoque_NG"] = get_total_acordaos_julgados_NG(processos_julgados_acordao)
        stats["julgados_comarca_opcoes_NG"] = get_opcoes_comarca_julgados_NG(_a("julgados_NG"))
        charts = {
            "julgados_acordao_improcedencia_por_comarca_NG": [
                ChartDataPoint(**x)
                for x in group_acordao_improcedentes_por_comarca_julgados_NG(
                    processos_julgados_acordao, from_date=from_date, to_date=to_date
                )
            ],
            "julgados_acordao_improcedencia_por_comarca_estoque_NG": [
                ChartDataPoint(**x)
                for x in group_acordao_improcedentes_por_comarca_julgados_NG(processos_julgados_acordao)
            ],
            "julgados_acordao_improcedencia_por_motivo_NG": [
                ChartDataPoint(**x)
                for x in group_acordao_por_motivo_improcedencia_julgados_NG(
                    processos_julgados_acordao, from_date=from_date, to_date=to_date
                )
            ],
            "julgados_acordao_improcedencia_por_motivo_estoque_NG": [
                ChartDataPoint(**x)
                for x in group_acordao_por_motivo_improcedencia_julgados_NG(processos_julgados_acordao)
            ],
            "julgados_acordao_improcedencia_por_relator_NG": [
                ChartDataPoint(**x)
                for x in get_ranking_relatores_improcedencia_julgados_NG(
                    processos_julgados_acordao, from_date=from_date, to_date=to_date
                )
            ],
            "julgados_acordao_improcedencia_por_relator_estoque_NG": [
                ChartDataPoint(**x)
                for x in get_ranking_relatores_improcedencia_julgados_NG(processos_julgados_acordao)
            ],
            "ranking_relatores_acordao_julgados_NG": [
                RecursalRankingMagistradoRow(**x)
                for x in get_ranking_relatores_acordao_julgados_NG(
                    processos_julgados_acordao, from_date=from_date, to_date=to_date
                )
            ],
            "julgados_acordao_por_materia_NG": [
                ChartDataPoint(**x)
                for x in group_acordao_por_materia_julgados_NG(
                    processos_julgados_acordao, from_date=from_date, to_date=to_date
                )
            ],
            "julgados_acordao_por_competencia_NG": [
                ChartDataPoint(**x)
                for x in group_acordao_por_competencia_julgados_NG(
                    processos_julgados_acordao, from_date=from_date, to_date=to_date
                )
            ],
            "julgados_acordao_por_comarca_NG": [
                ChartDataPoint(**x)
                for x in group_acordao_por_comarca_julgados_NG(
                    processos_julgados_acordao, from_date=from_date, to_date=to_date
                )
            ],
            "julgados_acordao_por_motivo_extincao_NG": [
                ChartDataPoint(**x)
                for x in group_acordao_por_motivo_extincao_julgados_NG(
                    processos_julgados_acordao, from_date=from_date, to_date=to_date
                )
            ],
            "julgados_acordao_por_ano_ajuizamento_NG": [
                ChartDataPoint(**x)
                for x in group_acordao_por_ano_ajuizamento_julgados_NG(
                    processos_julgados_acordao, from_date=from_date, to_date=to_date
                )
            ],
            "julgados_acordao_embargos_resultado_NG": [
                ChartDataPoint(**x)
                for x in group_acordao_embargos_resultado_julgados_NG(
                    processos_julgados_acordao, from_date=from_date, to_date=to_date
                )
            ],
            "julgados_acordao_procedentes_por_mes_NG": [
                ChartDataPoint(**x)
                for x in group_julgados_acordao_procedentes_por_mes_NG(processos_julgados_acordao)
            ],
            "julgados_acordao_improcedentes_por_mes_NG": [
                ChartDataPoint(**x)
                for x in group_julgados_acordao_improcedentes_por_mes_NG(processos_julgados_acordao)
            ],
            "julgados_acordao_extintos_por_mes_NG": [
                ChartDataPoint(**x)
                for x in group_julgados_acordao_extintos_por_mes_NG(processos_julgados_acordao)
            ],
            "julgados_acordao_lista_NG": [
                JulgadosAcordaoListaRow(**x)
                for x in list_acordaos_julgados_NG(
                    processos_julgados_acordao, from_date=from_date, to_date=to_date
                )
            ],
        }
        logger.info("Dashboard 'julgados_acordaos_NG' processado em %.2fs", time.time() - t0)
        return DashboardResponse(dashboard="julgados_acordaos_NG", stats=DashboardStats(**stats), **charts)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    if dashboard_name == "julgados_acordaos_LA":
        processos_julgados_acordao_la = filtrar_acordaos_julgados_LA(
            _a("julgados_LA"), julgados_acordao_filtros_la
        )
        stats = get_kpis_acordao_julgados_LA(
            processos_julgados_acordao_la, from_date=from_date, to_date=to_date
        )
        stats.update(
            get_comparativos_acordao_julgados_LA(
                processos_julgados_acordao_la, from_date=from_date, to_date=to_date
            )
        )
        stats["julgados_acordao_uf_opcoes_LA"] = get_opcoes_uf_julgados_acordao_LA(_a("julgados_LA"))
        stats.update(
            get_julgados_acordao_campos_vazios_LA(
                # Faixa de atenção: histórico todo, independente do período (06/11/2026)
                processos_julgados_acordao_la, from_date=None, to_date=None
            )
        )
        stats["julgados_acordao_dados_faltando_LA"] = get_julgados_acordao_dados_faltando_LA(
            # Faixa de atenção: histórico todo, independente do período (06/11/2026)
            processos_julgados_acordao_la, from_date=None, to_date=None
        )
        # Estudo das Improcedências (11/11/2026): mesma montagem do NG, sem STJ/STF.
        _imp_ac_entrada_LA = get_improcedencia_acordao_totais_julgados_LA(
            processos_julgados_acordao_la, from_date=from_date, to_date=to_date
        )
        _imp_ac_estoque_LA = get_improcedencia_acordao_totais_julgados_LA(processos_julgados_acordao_la)
        stats["julgados_acordao_improcedencia_valor_LA"] = _imp_ac_entrada_LA["valor_causa"]
        stats["julgados_acordao_improcedencia_total_estoque_LA"] = _imp_ac_estoque_LA["total"]
        stats["julgados_acordao_improcedencia_valor_estoque_LA"] = _imp_ac_estoque_LA["valor_causa"]
        stats["julgados_acordao_total_estoque_LA"] = get_total_acordaos_julgados_LA(processos_julgados_acordao_la)
        stats["julgados_comarca_opcoes_LA"] = get_opcoes_comarca_julgados_LA(_a("julgados_LA"))
        charts = {
            "julgados_acordao_improcedencia_por_comarca_LA": [
                ChartDataPoint(**x)
                for x in group_acordao_improcedentes_por_comarca_julgados_LA(
                    processos_julgados_acordao_la, from_date=from_date, to_date=to_date
                )
            ],
            "julgados_acordao_improcedencia_por_comarca_estoque_LA": [
                ChartDataPoint(**x)
                for x in group_acordao_improcedentes_por_comarca_julgados_LA(processos_julgados_acordao_la)
            ],
            "julgados_acordao_improcedencia_por_motivo_LA": [
                ChartDataPoint(**x)
                for x in group_acordao_por_motivo_improcedencia_julgados_LA(
                    processos_julgados_acordao_la, from_date=from_date, to_date=to_date
                )
            ],
            "julgados_acordao_improcedencia_por_motivo_estoque_LA": [
                ChartDataPoint(**x)
                for x in group_acordao_por_motivo_improcedencia_julgados_LA(processos_julgados_acordao_la)
            ],
            "julgados_acordao_improcedencia_por_relator_LA": [
                ChartDataPoint(**x)
                for x in get_ranking_relatores_improcedencia_julgados_LA(
                    processos_julgados_acordao_la, from_date=from_date, to_date=to_date
                )
            ],
            "julgados_acordao_improcedencia_por_relator_estoque_LA": [
                ChartDataPoint(**x)
                for x in get_ranking_relatores_improcedencia_julgados_LA(processos_julgados_acordao_la)
            ],
            "ranking_relatores_acordao_julgados_LA": [
                RecursalRankingMagistradoRow(**x)
                for x in get_ranking_relatores_acordao_julgados_LA(
                    processos_julgados_acordao_la, from_date=from_date, to_date=to_date
                )
            ],
            "julgados_acordao_por_materia_LA": [
                ChartDataPoint(**x)
                for x in group_acordao_por_materia_julgados_LA(
                    processos_julgados_acordao_la, from_date=from_date, to_date=to_date
                )
            ],
            "julgados_acordao_por_competencia_LA": [
                ChartDataPoint(**x)
                for x in group_acordao_por_competencia_julgados_LA(
                    processos_julgados_acordao_la, from_date=from_date, to_date=to_date
                )
            ],
            "julgados_acordao_por_comarca_LA": [
                ChartDataPoint(**x)
                for x in group_acordao_por_comarca_julgados_LA(
                    processos_julgados_acordao_la, from_date=from_date, to_date=to_date
                )
            ],
            "julgados_acordao_por_motivo_extincao_LA": [
                ChartDataPoint(**x)
                for x in group_acordao_por_motivo_extincao_julgados_LA(
                    processos_julgados_acordao_la, from_date=from_date, to_date=to_date
                )
            ],
            "julgados_acordao_por_ano_ajuizamento_LA": [
                ChartDataPoint(**x)
                for x in group_acordao_por_ano_ajuizamento_julgados_LA(
                    processos_julgados_acordao_la, from_date=from_date, to_date=to_date
                )
            ],
            "julgados_acordao_embargos_resultado_LA": [
                ChartDataPoint(**x)
                for x in group_acordao_embargos_resultado_julgados_LA(
                    processos_julgados_acordao_la, from_date=from_date, to_date=to_date
                )
            ],
            "julgados_acordao_procedentes_por_mes_LA": [
                ChartDataPoint(**x)
                for x in group_julgados_acordao_procedentes_por_mes_LA(processos_julgados_acordao_la)
            ],
            "julgados_acordao_improcedentes_por_mes_LA": [
                ChartDataPoint(**x)
                for x in group_julgados_acordao_improcedentes_por_mes_LA(processos_julgados_acordao_la)
            ],
            "julgados_acordao_extintos_por_mes_LA": [
                ChartDataPoint(**x)
                for x in group_julgados_acordao_extintos_por_mes_LA(processos_julgados_acordao_la)
            ],
            "julgados_acordao_lista_LA": [
                JulgadosAcordaoListaRow(**x)
                for x in list_acordaos_julgados_LA(
                    processos_julgados_acordao_la, from_date=from_date, to_date=to_date
                )
            ],
        }
        logger.info("Dashboard 'julgados_acordaos_LA' processado em %.2fs", time.time() - t0)
        return DashboardResponse(dashboard="julgados_acordaos_LA", stats=DashboardStats(**stats), **charts)
    if dashboard_name == "julgados_acordaos_RJ":
        processos_julgados_acordao_rj = filtrar_acordaos_julgados_RJ(
            _a("julgados_LA"), julgados_acordao_filtros_rj
        )
        stats = get_kpis_acordao_julgados_RJ(
            processos_julgados_acordao_rj, from_date=from_date, to_date=to_date
        )
        stats.update(
            get_comparativos_acordao_julgados_RJ(
                processos_julgados_acordao_rj, from_date=from_date, to_date=to_date
            )
        )
        stats["julgados_acordao_uf_opcoes_RJ"] = get_opcoes_uf_julgados_acordao_RJ(_a("julgados_LA"))
        stats.update(
            get_julgados_acordao_campos_vazios_RJ(
                # Faixa de atenção: histórico todo, independente do período (06/11/2026)
                processos_julgados_acordao_rj, from_date=None, to_date=None
            )
        )
        stats["julgados_acordao_dados_faltando_RJ"] = get_julgados_acordao_dados_faltando_RJ(
            # Faixa de atenção: histórico todo, independente do período (06/11/2026)
            processos_julgados_acordao_rj, from_date=None, to_date=None
        )
        # Estudo das Improcedências (11/11/2026): mesma montagem do NG, sem STJ/STF.
        _imp_ac_entrada_RJ = get_improcedencia_acordao_totais_julgados_RJ(
            processos_julgados_acordao_rj, from_date=from_date, to_date=to_date
        )
        _imp_ac_estoque_RJ = get_improcedencia_acordao_totais_julgados_RJ(processos_julgados_acordao_rj)
        stats["julgados_acordao_improcedencia_valor_RJ"] = _imp_ac_entrada_RJ["valor_causa"]
        stats["julgados_acordao_improcedencia_total_estoque_RJ"] = _imp_ac_estoque_RJ["total"]
        stats["julgados_acordao_improcedencia_valor_estoque_RJ"] = _imp_ac_estoque_RJ["valor_causa"]
        stats["julgados_acordao_total_estoque_RJ"] = get_total_acordaos_julgados_RJ(processos_julgados_acordao_rj)
        stats["julgados_comarca_opcoes_RJ"] = get_opcoes_comarca_julgados_RJ(_a("julgados_LA"))
        charts = {
            "julgados_acordao_improcedencia_por_comarca_RJ": [
                ChartDataPoint(**x)
                for x in group_acordao_improcedentes_por_comarca_julgados_RJ(
                    processos_julgados_acordao_rj, from_date=from_date, to_date=to_date
                )
            ],
            "julgados_acordao_improcedencia_por_comarca_estoque_RJ": [
                ChartDataPoint(**x)
                for x in group_acordao_improcedentes_por_comarca_julgados_RJ(processos_julgados_acordao_rj)
            ],
            "julgados_acordao_improcedencia_por_motivo_RJ": [
                ChartDataPoint(**x)
                for x in group_acordao_por_motivo_improcedencia_julgados_RJ(
                    processos_julgados_acordao_rj, from_date=from_date, to_date=to_date
                )
            ],
            "julgados_acordao_improcedencia_por_motivo_estoque_RJ": [
                ChartDataPoint(**x)
                for x in group_acordao_por_motivo_improcedencia_julgados_RJ(processos_julgados_acordao_rj)
            ],
            "julgados_acordao_improcedencia_por_relator_RJ": [
                ChartDataPoint(**x)
                for x in get_ranking_relatores_improcedencia_julgados_RJ(
                    processos_julgados_acordao_rj, from_date=from_date, to_date=to_date
                )
            ],
            "julgados_acordao_improcedencia_por_relator_estoque_RJ": [
                ChartDataPoint(**x)
                for x in get_ranking_relatores_improcedencia_julgados_RJ(processos_julgados_acordao_rj)
            ],
            "ranking_relatores_acordao_julgados_RJ": [
                RecursalRankingMagistradoRow(**x)
                for x in get_ranking_relatores_acordao_julgados_RJ(
                    processos_julgados_acordao_rj, from_date=from_date, to_date=to_date
                )
            ],
            "julgados_acordao_por_materia_RJ": [
                ChartDataPoint(**x)
                for x in group_acordao_por_materia_julgados_RJ(
                    processos_julgados_acordao_rj, from_date=from_date, to_date=to_date
                )
            ],
            "julgados_acordao_por_competencia_RJ": [
                ChartDataPoint(**x)
                for x in group_acordao_por_competencia_julgados_RJ(
                    processos_julgados_acordao_rj, from_date=from_date, to_date=to_date
                )
            ],
            "julgados_acordao_por_comarca_RJ": [
                ChartDataPoint(**x)
                for x in group_acordao_por_comarca_julgados_RJ(
                    processos_julgados_acordao_rj, from_date=from_date, to_date=to_date
                )
            ],
            "julgados_acordao_por_motivo_extincao_RJ": [
                ChartDataPoint(**x)
                for x in group_acordao_por_motivo_extincao_julgados_RJ(
                    processos_julgados_acordao_rj, from_date=from_date, to_date=to_date
                )
            ],
            "julgados_acordao_por_ano_ajuizamento_RJ": [
                ChartDataPoint(**x)
                for x in group_acordao_por_ano_ajuizamento_julgados_RJ(
                    processos_julgados_acordao_rj, from_date=from_date, to_date=to_date
                )
            ],
            "julgados_acordao_embargos_resultado_RJ": [
                ChartDataPoint(**x)
                for x in group_acordao_embargos_resultado_julgados_RJ(
                    processos_julgados_acordao_rj, from_date=from_date, to_date=to_date
                )
            ],
            "julgados_acordao_procedentes_por_mes_RJ": [
                ChartDataPoint(**x)
                for x in group_julgados_acordao_procedentes_por_mes_RJ(processos_julgados_acordao_rj)
            ],
            "julgados_acordao_improcedentes_por_mes_RJ": [
                ChartDataPoint(**x)
                for x in group_julgados_acordao_improcedentes_por_mes_RJ(processos_julgados_acordao_rj)
            ],
            "julgados_acordao_extintos_por_mes_RJ": [
                ChartDataPoint(**x)
                for x in group_julgados_acordao_extintos_por_mes_RJ(processos_julgados_acordao_rj)
            ],
            "julgados_acordao_lista_RJ": [
                JulgadosAcordaoListaRow(**x)
                for x in list_acordaos_julgados_RJ(
                    processos_julgados_acordao_rj, from_date=from_date, to_date=to_date
                )
            ],
        }
        logger.info("Dashboard 'julgados_acordaos_RJ' processado em %.2fs", time.time() - t0)
        return DashboardResponse(dashboard="julgados_acordaos_RJ", stats=DashboardStats(**stats), **charts)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    # V2: (bloco de outros dashboards da v1 omitido)
    raise HTTPException(status_code=404, detail=f"Dashboard '{dashboard_name}' não encontrado.")


# v1: dashboard_routes.py:31579 (rota sem os decoradores)
async def get_julgados_acordaos_NG_dashboard(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    materia_julgados: Optional[List[str]] = Query(
        None, description="Filtra acórdãos por matéria (cumulativo)."
    ),
    relator_julgados: Optional[List[str]] = Query(
        None, description="Filtra acórdãos por relator (2G, cumulativo)."
    ),
    comarca_julgados: Optional[List[str]] = Query(
        None, description="Filtra acórdãos por comarca (cumulativo)."
    ),
    competencia_julgados: Optional[List[str]] = Query(
        None, description="Filtra acórdãos por competência (cumulativo)."
    ),
    categoria_julgados: Optional[List[str]] = Query(
        None,
        description="Filtra acórdãos por categoria: procedente, improcedente ou extinto (cumulativo).",
    ),
    uf_julgados: Optional[List[str]] = Query(
        None, description="Filtra acórdãos por UF (cumulativo)."
    ),
    motivo_extincao_julgados: Optional[List[str]] = Query(
        None, description="Filtra acórdãos extintos por motivo da extinção (cumulativo)."
    ),
    ano_ajuizamento_julgados: Optional[List[str]] = Query(
        None, description="Filtra acórdãos pelo ano de ajuizamento (distribuição) do processo (cumulativo)."
    ),
    resultado_embargos_julgados: Optional[List[str]] = Query(
        None, description="Filtra acórdãos embargados por resultado: revertido ou mantido (cumulativo)."
    ),
):
    """Dashboard Julgados Acórdãos — escritório NG (id 20).

    KPIs de Acórdão (2º Grau) no período, com base em ``DATA_ACORDAO``: total,
    procedentes, improcedentes e extintos, além de ranking de relatores e
    distribuição por matéria/competência/comarca/motivo de extinção. Todos os
    gráficos aceitam filtros interativos cumulativos (matéria, relator, comarca,
    competência, categoria, UF, motivo de extinção, ano de ajuizamento,
    resultado dos embargos).
    """
    filtros = _parse_julgados_acordao_filtros(
        materia_julgados,
        relator_julgados,
        comarca_julgados,
        competencia_julgados,
        categoria_julgados,
        uf_julgados,
        motivo_extincao_julgados,
        ano_ajuizamento_julgados,
        resultado_embargos_julgados,
    )
    return await _get_dashboard_response(
        "julgados_acordaos_NG", from_date, to_date, julgados_acordao_filtros=filtros
    )


# v1: dashboard_routes.py:31948 (rota sem os decoradores)
async def get_julgados_acordaos_LA_dashboard(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    materia_julgados: Optional[List[str]] = Query(
        None, description="Filtra acórdãos por matéria (cumulativo)."
    ),
    relator_julgados: Optional[List[str]] = Query(
        None, description="Filtra acórdãos por relator (2G, cumulativo)."
    ),
    comarca_julgados: Optional[List[str]] = Query(
        None, description="Filtra acórdãos por comarca (cumulativo)."
    ),
    competencia_julgados: Optional[List[str]] = Query(
        None, description="Filtra acórdãos por competência (cumulativo)."
    ),
    categoria_julgados: Optional[List[str]] = Query(
        None,
        description="Filtra acórdãos por categoria: procedente, improcedente ou extinto (cumulativo).",
    ),
    uf_julgados: Optional[List[str]] = Query(
        None, description="Filtra acórdãos por UF (cumulativo)."
    ),
    motivo_extincao_julgados: Optional[List[str]] = Query(
        None, description="Filtra acórdãos extintos por motivo da extinção (cumulativo)."
    ),
    ano_ajuizamento_julgados: Optional[List[str]] = Query(
        None, description="Filtra acórdãos pelo ano de ajuizamento (distribuição) do processo (cumulativo)."
    ),
    resultado_embargos_julgados: Optional[List[str]] = Query(
        None, description="Filtra acórdãos embargados por resultado: revertido ou mantido (cumulativo)."
    ),
):
    """Dashboard Julgados Acórdãos — escritório LA / Luis Albert AM (id 21).

    KPIs de Acórdão (2º Grau) no período, com base em ``DATA_ACORDAO``: total,
    procedentes, improcedentes e extintos, além de ranking de relatores e
    distribuição por matéria/competência/comarca/motivo de extinção. Todos os
    gráficos aceitam filtros interativos cumulativos (matéria, relator, comarca,
    competência, categoria, UF, motivo de extinção, ano de ajuizamento,
    resultado dos embargos).
    """
    filtros = _parse_julgados_acordao_filtros_la(
        materia_julgados,
        relator_julgados,
        comarca_julgados,
        competencia_julgados,
        categoria_julgados,
        uf_julgados,
        motivo_extincao_julgados,
        ano_ajuizamento_julgados,
        resultado_embargos_julgados,
    )
    return await _get_dashboard_response(
        "julgados_acordaos_LA", from_date, to_date, julgados_acordao_filtros_la=filtros
    )


# v1: dashboard_routes.py:32071 (rota sem os decoradores)
async def get_julgados_acordaos_RJ_dashboard(
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    materia_julgados: Optional[List[str]] = Query(
        None, description="Filtra acórdãos por matéria (cumulativo)."
    ),
    relator_julgados: Optional[List[str]] = Query(
        None, description="Filtra acórdãos por relator (2G, cumulativo)."
    ),
    comarca_julgados: Optional[List[str]] = Query(
        None, description="Filtra acórdãos por comarca (cumulativo)."
    ),
    competencia_julgados: Optional[List[str]] = Query(
        None, description="Filtra acórdãos por competência (cumulativo)."
    ),
    categoria_julgados: Optional[List[str]] = Query(
        None,
        description="Filtra acórdãos por categoria: procedente, improcedente ou extinto (cumulativo).",
    ),
    uf_julgados: Optional[List[str]] = Query(
        None, description="Filtra acórdãos por UF (cumulativo)."
    ),
    motivo_extincao_julgados: Optional[List[str]] = Query(
        None, description="Filtra acórdãos extintos por motivo da extinção (cumulativo)."
    ),
    ano_ajuizamento_julgados: Optional[List[str]] = Query(
        None, description="Filtra acórdãos pelo ano de ajuizamento (distribuição) do processo (cumulativo)."
    ),
    resultado_embargos_julgados: Optional[List[str]] = Query(
        None, description="Filtra acórdãos embargados por resultado: revertido ou mantido (cumulativo)."
    ),
):
    """Dashboard Julgados Acórdãos — escritório RJ / LAADV RJ (id 27) — réplica do LA.

    KPIs de Acórdão (2º Grau) no período, com base em ``DATA_ACORDAO``: total,
    procedentes, improcedentes e extintos, além de ranking de relatores e
    distribuição por matéria/competência/comarca/motivo de extinção. Todos os
    gráficos aceitam filtros interativos cumulativos (matéria, relator, comarca,
    competência, categoria, UF, motivo de extinção, ano de ajuizamento,
    resultado dos embargos).
    """
    filtros = _parse_julgados_acordao_filtros_rj(
        materia_julgados,
        relator_julgados,
        comarca_julgados,
        competencia_julgados,
        categoria_julgados,
        uf_julgados,
        motivo_extincao_julgados,
        ano_ajuizamento_julgados,
        resultado_embargos_julgados,
    )
    return await _get_dashboard_response(
        "julgados_acordaos_RJ", from_date, to_date, julgados_acordao_filtros_rj=filtros
    )


# V2: dashboard da v1 -> handler da rota e queries que ele busca (para a casca e o aquecedor do cache).
HANDLERS = {"julgados_acordaos_NG": get_julgados_acordaos_NG_dashboard, "julgados_acordaos_LA": get_julgados_acordaos_LA_dashboard, "julgados_acordaos_RJ": get_julgados_acordaos_RJ_dashboard}
QUERIES_POR_DASHBOARD = {'julgados_acordaos_NG': ('julgados',), 'julgados_acordaos_LA': ('julgados',), 'julgados_acordaos_RJ': ('julgados',)}
