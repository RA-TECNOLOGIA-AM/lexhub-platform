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


# v1: dashboard_routes.py:3930
class ChartDataPoint(BaseModel):
    name: str
    value: float
    percent: Optional[float] = None
    valor_causa: Optional[float] = None
    valor_sentenca: Optional[float] = None
    valor_execucao: Optional[float] = None
    id_1g: Optional[int] = None
    id_2g: Optional[int] = None
    tipo: Optional[str] = None
    tempo_medio_dias: Optional[float] = None
    uf: Optional[str] = None
    concluidos: Optional[float] = None
    abertas: Optional[float] = None


# v1: dashboard_routes.py:3946
class ProcessoDadoFaltando(BaseModel):
    """Um processo com um campo faltando (alimenta o alerta clicável "Atenção" dos
    dashboards de Execução/Execução Acordos/Julgados — número do processo + qual
    informação falta, pra o usuário ir preencher no sistema de origem)."""

    numero_processo: str
    campo: str


# v1: dashboard_routes.py:3955
class InvestimentoCliquesLeadsPoint(BaseModel):
    name: str
    investimento: float
    cliques: int
    leads: int


# v1: dashboard_routes.py:3962
class RubricaCampanhaPoint(BaseModel):
    name: str
    ra: int
    ng: int


# v1: dashboard_routes.py:3968
class NpsRespostaRow(BaseModel):
    id: int
    cliente: str
    telefone: str
    data: str
    classificacao: str
    av_prob_ind: int
    av_confianca: Optional[int] = None
    av_nivel_info: Optional[int] = None
    av_tempo_resposta: Optional[int] = None
    feedback_positivo: str
    feedback_melhoria: str
    etapa_preocupacao: str
    comentario: str


# v1: dashboard_routes.py:3984
class NpsFeedbackMelhoriaRow(BaseModel):
    id: int
    cliente: str
    telefone: str
    data: str
    classificacao: str
    av_prob_ind: int
    feedback_melhoria: str


# v1: dashboard_routes.py:3994
class NpsFeedbackPositivoRow(BaseModel):
    id: int
    cliente: str
    telefone: str
    data: str
    classificacao: str
    av_prob_ind: int
    feedback_positivo: str


# v1: dashboard_routes.py:4004
class NpsComentarioRow(BaseModel):
    id: int
    cliente: str
    telefone: str
    data: str
    classificacao: str
    av_prob_ind: int
    comentario: str


# v1: dashboard_routes.py:4014
class RecursalRankingMagistradoRow(BaseModel):
    name: str
    initials: str
    total_casos: int
    taxa_sucesso: float
    fav: int
    des: int
    outros: int
    percent_fav: float
    percent_des: float
    percent_outros: float


# v1: dashboard_routes.py:4027
class JulgadosSentencaListaRow(BaseModel):
    id: Optional[int] = None
    numero_processo: str
    fase: str
    subfase: str
    status_1g: str
    uf: str
    juiz: str
    data_sentenca: Optional[str] = None
    status_sentenca_embargos: str
    data_sentenca_embargos: Optional[str] = None


# v1: dashboard_routes.py:4040
class JulgadosAcordaoListaRow(BaseModel):
    id: Optional[int] = None
    numero_processo: str
    fase: str
    subfase: str
    status_2g: str
    uf: str
    relator: str
    data_acordao: Optional[str] = None
    status_acordao_embargos: str
    data_acordao_embargos: Optional[str] = None


# v1: dashboard_routes.py:4053
class ExecucaoAcordosListaRow(BaseModel):
    id: Optional[int] = None
    numero_processo: str
    uf: str
    data_execucao: Optional[str] = None
    valor_execucao: Optional[float] = None
    subfase: str


# v1: dashboard_routes.py:4062
class RecursalAtividadeTarefaRow(BaseModel):
    id: int
    status: str
    descricao: str
    pessoa_setor: str
    funcionario: str
    atividade: str
    prazo: Optional[str] = None
    em_andamento: bool = False
    vencida: bool = False
    vence_hoje: bool = False
    concluida: bool = False
    funcionario_atribuido: Optional[str] = None
    funcionario_encerramento: Optional[str] = None
    criado_em: Optional[str] = None
    concluido_em: Optional[str] = None
    operacao: Optional[str] = None
    encerrado_pelo_responsavel: Optional[bool] = None
    numero_processo: Optional[str] = None
    valor_execucao: Optional[float] = None
    valor_sentenca: Optional[float] = None
    valor_acordao: Optional[float] = None


# v1: dashboard_routes.py:4086
class DilacaoPorFuncionarioRow(BaseModel):
    funcionario: str
    qtd_dilacoes: int
    total_encerrados: int
    qtd_resolvidos: int
    taxa_dilacao: float


# v1: dashboard_routes.py:4094
class EmendasManifestacoesResolvidosPorUfRow(BaseModel):
    uf: str
    qtd_manifestacao: int
    qtd_dilacao: int
    qtd_total: int


# v1: dashboard_routes.py:4101
class EmendasManifestacoesComissaoRow(BaseModel):
    funcionario: str
    agenda_finalizada: int
    agenda_total: int
    agenda_percentual: float
    elegivel: bool
    faixa: Optional[str] = None
    qtd_manifestacao: int
    valor_manifestacao: float
    qtd_x_valor_manifestacao: float
    qtd_dilacao: int
    valor_dilacao: float
    qtd_x_valor_dilacao: float
    valor_comissao: float
    resolvidos_por_uf: Optional[List[EmendasManifestacoesResolvidosPorUfRow]] = None


# v1: dashboard_routes.py:4118
class RecursalAtividadesListaFiltrosOpcoes(BaseModel):
    funcionarios: List[str]
    atividades: List[str]
    status: List[str]
    situacoes: List[Dict[str, str]]


# v1: dashboard_routes.py:4125
class ExecucaoAtrasoBucket(BaseModel):
    dias: int
    label: str
    descricao: str
    count: int
    pct: float


# v1: dashboard_routes.py:4133
class ExecucaoAtrasosDetalhamento(BaseModel):
    total: int
    buckets: List[ExecucaoAtrasoBucket]


# v1: dashboard_routes.py:4138
class RubricaTotalRow(BaseModel):
    rubrica: str
    acoes: int
    valor_am: float
    total: float


# v1: dashboard_routes.py:4145
class ComissionamentoOrgDocRow(BaseModel):
    funcionario: str
    qtd_resolvidos: int
    valor_causa_gerado: float
    valor_comissao: float


# v1: dashboard_routes.py:4152
class ComissionamentoProtocoloRow(BaseModel):
    funcionario: str
    qtd_protocolados: int
    comissao_unitaria: Optional[float] = None
    valor_comissao: float


# v1: dashboard_routes.py:4159
class ComissionamentoPeticionamentoRow(BaseModel):
    funcionario: str
    qtd_acoes_massa: int
    valor_acoes_massa: float
    qtd_x_valor_massa: float
    qtd_acoes_especificas: int
    valor_acoes_especificas: float
    qtd_x_valor_especificas: float
    taxa_resolvidos: Optional[float] = None
    valor_comissao: float


# v1: dashboard_routes.py:4171
class ComissionamentoPendenciaRow(BaseModel):
    funcionario: str
    taxa_resolvido: Optional[float] = None
    taxa_cancelamento: Optional[float] = None
    qtd_resolvido: int
    valor: float
    qtd_x_valor: float
    comissao: float


# v1: dashboard_routes.py:4181
class ComissionamentoPublicacaoRow(BaseModel):
    funcionario: str
    qtd_lidas: int
    qtd_certas: int
    qtd_erradas: int
    valor_certa: float
    valor_errada: float
    comissao: float


# v1: dashboard_routes.py:4191
class ComissionamentoAndamentoRow(BaseModel):
    funcionario: str
    media_avaliacao: Optional[float] = None
    qtd_atendimentos: int
    valor_unitario: float
    valor_comissao: float


# v1: dashboard_routes.py:4199
class ComissionamentoComercialRow(BaseModel):
    atendente: str
    acoes: int
    comissao_base: float
    valor_fm: float
    proporcional_am_pa: float
    proporcional_pb: float
    comissao_com_fm: float


# v1: dashboard_routes.py:4209
class ComissionamentoComercialLARow(BaseModel):
    atendente: str
    acoes: int
    comissao_base: float
    valor_fm: float
    comissao_com_fm: float


# v1: dashboard_routes.py:4217
class TotalLeadsPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4222
class TotalClientesFechadosPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4227
class TaxaFechamentoGeralPorAtendente(BaseModel):
    total: float
    por_atendente: Dict[str, float]


# v1: dashboard_routes.py:4232
class TotalLeadsCampanhaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4237
class TotalClientesFechadosCampanhaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4242
class TaxaFechamentoCampanhaPorCliente(BaseModel):
    total: float
    por_atendente: Dict[str, float]


# v1: dashboard_routes.py:4247
class TotalLeadsIndicacaoAtivaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4252
class TaxaFechamentoIndicacaoAtivaPorAtendente(BaseModel):
    total: float
    por_atendente: Dict[str, float]


# v1: dashboard_routes.py:4257
class TotalClientesFechadosIndicacaoAtivaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4262
class TotalLeadsIndicacaoPassivaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4267
class TotalClientesFechadosIndicacaoPassivaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4272
class TaxaFechamentoIndicacaoPassivaPorAtendente(BaseModel):
    total: float
    por_atendente: Dict[str, float]


# v1: dashboard_routes.py:4277
class TotalLeadsRetornoAtivaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4282
class TotalClientesFechadosRetornoAtivaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4287
class TaxaFechamentoRetornoAtivaPorAtendente(BaseModel):
    total: float
    por_atendente: Dict[str, float]


# v1: dashboard_routes.py:4292
class TotalLeadsRetornoPassivaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4297
class TotalClientesFechadosRetornoPassivaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4302
class TaxaFechamentoRetornoPassivaPorAtendente(BaseModel):
    total: float
    por_atendente: Dict[str, float]


# v1: dashboard_routes.py:4307
class TotalLeadsResgateAtivaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4312
class TotalClientesFechadosResgateAtivaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4317
class TaxaFechamentoResgateAtivaPorAtendente(BaseModel):
    total: float
    por_atendente: Dict[str, float]


# v1: dashboard_routes.py:4322
class TotalLeadsResgatePassivaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4327
class TotalClientesFechadosResgatePassivaPorAtendente(BaseModel):
    total: int
    por_atendente: Dict[str, int]


# v1: dashboard_routes.py:4332
class TaxaFechamentoResgatePassivaPorAtendente(BaseModel):
    total: float
    por_atendente: Dict[str, float]


# v1: dashboard_routes.py:4371
class DashboardStats(BaseModel):
    # Tickets
    total_tickets: Optional[int] = None
    tickets_ag_atendimento: Optional[int] = None
    tickets_atendimento: Optional[int] = None
    total_encerrados: Optional[int] = None
    tickets_cancelados: Optional[int] = None
    tickets_reprovados: Optional[int] = None
    duracao_atendimento: Optional[float] = None
    taxa_resolucao: Optional[float] = None
    total_tickets_periodo_anterior: Optional[int] = None
    tickets_abertos: Optional[int] = None
    tickets_resolvidos: Optional[int] = None
    tickets_hoje: Optional[int] = None
    tickets_semana: Optional[int] = None
    tickets_mes: Optional[int] = None

    # Andamento Processual
    total_andamento_processual: Optional[int] = None
    andamento_processual_resolvidos: Optional[int] = None
    andamento_processual_nao_resolvidos: Optional[int] = None
    media_avaliacao: Optional[float] = None
    taxa_resolvidos: Optional[float] = None
    taxa_nao_resolvidos: Optional[float] = None
    media_espera: Optional[float] = None
    mediana_espera: Optional[float] = None
    media_atendimento: Optional[float] = None
    mediana_atendimento: Optional[float] = None
    funcionarios_andamento_processual: Optional[List[str]] = None
    funcionarios_andamento_filtro: Optional[List[str]] = None
    funcionario_andamento_filtro: Optional[str] = None
    funcionarios_filtro: Optional[List[str]] = None

    # Comercial Geral
    clientes_campanha_RA: Optional[int] = None
    clientes_campanha_NG: Optional[int] = None
    clientes_indicacao: Optional[int] = None
    clientes_redes_sociais: Optional[int] = None
    clientes_retorno: Optional[int] = None
    clientes_site: Optional[int] = None
    clientes_resgate: Optional[int] = None
    clientes_parceiros_externos: Optional[int] = None
    clientes_todos: Optional[int] = None
    clientes_cancelados: Optional[int] = None
    acoes_fechadas: Optional[int] = None
    total_rubricas_reunidas_fechadas: Optional[int] = None
    total_rubricas_reunidas_fechadas_LA: Optional[int] = None
    taxa_aproveitamento: Optional[float] = None
    comparativo_clientes_campanha_NG: Optional[float] = None
    comparativo_clientes_campanha_RA: Optional[float] = None
    comparativo_clientes_redes_sociais: Optional[float] = None
    comparativo_clientes_indicacao: Optional[float] = None
    comparativo_clientes_retorno: Optional[float] = None
    comparativo_clientes_resgate: Optional[float] = None
    comparativo_clientes_site: Optional[float] = None
    comparativo_clientes_parceiros_externos: Optional[float] = None
    comparativo_acoes_fechadas: Optional[float] = None
    acoes_fechadas_periodo_anterior: Optional[float] = None
    comparativo_clientes_todos: Optional[float] = None
    clientes_todos_periodo_anterior: Optional[float] = None
    comparativo_clientes_cancelados: Optional[float] = None
    comparativo_taxa_aproveitamento: Optional[float] = None
    valor_causa_confeccionado: Optional[float] = None
    ticket_medio_confeccionado: Optional[float] = None
    ticket_medio_protocolado: Optional[float] = None
    comparativo_ticket_medio_protocolado: Optional[float] = None
    tempo_medio_contratacao_protocolo: Optional[float] = None
    mediana_tempo_contratacao_protocolo: Optional[float] = None
    comparativo_tempo_medio_contratacao_protocolo: Optional[float] = None
    comparativo_mediana_tempo_contratacao_protocolo: Optional[float] = None
    comissao_base: Optional[float] = None
    atendentes_comerciais: Optional[List[str]] = None
    atendentes_comerciais_filtro: Optional[List[str]] = None
    atendente_comercial_filtro: Optional[str] = None
    funcionario_filtro: Optional[str] = None
    ufs_comercial_ng_opcoes: Optional[List[str]] = None
    uf_comercial_ng_filtro: Optional[str] = None
    segmentos_comercial_ng_opcoes: Optional[List[str]] = None
    segmentos_comercial_la_opcoes: Optional[List[str]] = None
    segmento_comercial_ng_filtro: Optional[str] = None
    segmento_comercial_la_filtro: Optional[str] = None
    area_atuacao_id_filtro: Optional[Union[int, List[int]]] = None

    # Actions NG
    total_leads: Optional[int] = None
    qtde_total_leads_anuncio_RA: Optional[int] = None
    qtde_total_leads_anuncio_NG: Optional[int] = None
    taxa_leads_geral: Optional[float] = None
    taxa_leads_anuncio_RA: Optional[float] = None
    taxa_leads_anuncio_NG: Optional[float] = None
    comparativo_leads_geral: Optional[float] = None
    comparativo_leads_anuncio_RA: Optional[float] = None
    comparativo_leads_anuncio_NG: Optional[float] = None
    comparativo_taxa_leads_geral: Optional[float] = None
    comparativo_taxa_leads_anuncio_RA: Optional[float] = None
    comparativo_taxa_leads_anuncio_NG: Optional[float] = None

    # Actions LA
    total_leads_LA: Optional[int] = None
    total_leads_anuncio_LA: Optional[int] = None
    taxa_leads_geral_LA: Optional[float] = None
    taxa_leads_anuncio_LA: Optional[float] = None

    # Protocolo NG
    protocolos_resolvidos: Optional[int] = None
    protocolados_de_reajuizamento: Optional[int] = None
    nao_protocolados: Optional[int] = None
    nao_protocolados_de_reajuizamento: Optional[int] = None
    valor_causa_protocolo_novo: Optional[float] = None
    comparativo_protocolos_resolvidos: Optional[float] = None
    protocolos_resolvidos_periodo_anterior: Optional[float] = None
    comparativo_valor_causa_protocolo: Optional[float] = None
    valor_causa_protocolo_periodo_anterior: Optional[float] = None
    valor_causa_protocolo_2026: Optional[float] = None
    meta_anual_comercial: Optional[float] = None
    media_tempo_protocolado: Optional[float] = None
    mediana_tempo_protocolado: Optional[float] = None
    comparativo_nao_protocolados: Optional[float] = None
    comparativo_tempo_medio_protocolos_resolvidos: Optional[float] = None
    fator_multiplicador: Optional[float] = None
    valor_por_estado_am_pa: Optional[float] = None
    valor_por_estado_pb: Optional[float] = None
    proporcional_am_pa: Optional[float] = None
    proporcional_pb: Optional[float] = None
    comissao_com_fm: Optional[float] = None
    ufs_protocolo_opcoes: Optional[List[str]] = None
    uf_protocolo_filtro: Optional[List[str]] = None
    ufs_peticionamento_opcoes: Optional[List[str]] = None
    uf_peticionamento_filtro: Optional[str] = None
    ufs_org_doc_opcoes: Optional[List[str]] = None
    uf_org_doc_filtro: Optional[str] = None
    ufs_pendencias_opcoes: Optional[List[str]] = None
    uf_pendencias_filtro: Optional[str] = None
    ufs_peticionamento_LA_opcoes: Optional[List[str]] = None
    uf_peticionamento_LA_filtro: Optional[str] = None
    ufs_org_doc_LA_opcoes: Optional[List[str]] = None
    uf_org_doc_LA_filtro: Optional[str] = None
    ufs_pendencia_LA_opcoes: Optional[List[str]] = None
    uf_pendencia_LA_filtro: Optional[str] = None

    # Organização de Documentos NG
    resolvidos_total: Optional[int] = None
    organizados_manualmente: Optional[int] = None
    organizados_e_peticionados_automaticamente: Optional[int] = None
    nao_organizados: Optional[int] = None
    cancelados: Optional[int] = None
    retorno_pet: Optional[int] = None
    retorno_pendencia: Optional[int] = None
    resolvidos_reajuizamento: Optional[int] = None
    comparativo_resolvidos_total: Optional[float] = None
    comparativo_organizados_manualmente: Optional[float] = None
    comparativo_resolvidos_reajuizamento: Optional[float] = None
    comparativo_organizados_e_peticionados_automaticamente: Optional[float] = None
    comparativo_cancelados: Optional[float] = None
    media_tempo_resolvidos: Optional[float] = None
    mediana_tempo_resolvidos: Optional[float] = None
    comparativo_tempo_medio_resolvidos_org_doc: Optional[float] = None

    # Organização de Documentos LA
    total_organizados_LA: Optional[int] = None
    total_organizados_manualmente_LA: Optional[int] = None
    total_organizados_automaticamente_LA: Optional[int] = None
    nao_organizados_LA: Optional[int] = None
    retorno_pendencia_LA: Optional[int] = None
    cancelados_LA: Optional[int] = None
    media_tempo_resolvidos_LA: Optional[float] = None
    mediana_tempo_resolvidos_LA: Optional[float] = None
    comparativo_resolvidos_total_LA: Optional[float] = None
    comparativo_organizados_manualmente_LA: Optional[float] = None
    comparativo_organizados_automaticamente_LA: Optional[float] = None
    comparativo_retorno_pendencia_LA: Optional[float] = None
    comparativo_cancelados_LA: Optional[float] = None

    # Pendências NG
    pendencias_total: Optional[int] = None
    pendencias_nao_resolvidas: Optional[int] = None
    pendencias_nao_resolvidas_com_atraso: Optional[int] = None
    pendencias_resolvidas: Optional[int] = None
    pendencias_canceladas: Optional[int] = None
    pendencias_taxa_nao_resolvidos: Optional[float] = None
    pendencias_taxa_resolvidos: Optional[float] = None
    pendencias_taxa_canceladas: Optional[float] = None
    pendencias_nao_resolvidas_reajuizamento: Optional[int] = None
    pendencias_resolvidas_reajuizamento: Optional[int] = None
    pendencias_triagem: Optional[int] = None
    media_tempo_resolvidos_pendencia: Optional[float] = None
    mediana_tempo_resolvidos_pendencia: Optional[float] = None
    comparativo_pendencias_resolvidas: Optional[float] = None
    comparativo_tempo_medio_pendencias_resolvidas: Optional[float] = None

    # Peticionamento NG
    total_peticionados: Optional[int] = None
    peticionados_automaticamente: Optional[int] = None
    peticionados_manualmente: Optional[int] = None
    nao_peticionados: Optional[int] = None
    resolvidos_reajuizamento_pet: Optional[int] = None
    nao_resolvidos_reajuizamento: Optional[int] = None
    media_tempo_peticionado: Optional[float] = None
    mediana_tempo_peticionado: Optional[float] = None
    comparativo_peticionados: Optional[float] = None
    comparativo_tempo_medio_peticionado: Optional[float] = None
    processos_em_revisao: Optional[int] = None
    comparativo_mediana_tempo_pet: Optional[float] = None
    comparativo_peticionados_manualmente: Optional[float] = None
    comparativo_peticionados_automaticamente: Optional[float] = None
    comparativo_peticionados_reajuizamento: Optional[float] = None
    comparativo_nao_peticionados_reajuizamento: Optional[float] = None
    comparativo_valor_causa_confeccionado: Optional[float] = None
    comparativo_ticket_medio_confeccionado: Optional[float] = None
    peticionamento_taxa_resolvidos: Optional[float] = None
    peticionamento_taxa_nao_resolvidos: Optional[float] = None

    # Execução NG
    total_em_execucao: Optional[int] = None
    valor_total_em_execucao: Optional[float] = None
    total_valor_execucao_vazio: Optional[int] = None
    total_valor_execucao_vazio_detalhe: Optional[List[ProcessoDadoFaltando]] = None
    valor_honorarios_total_execucao: Optional[float] = None
    valor_em_execucao: Optional[float] = None
    valor_remanescente_em_execucao: Optional[float] = None
    estoque_inicial: Optional[int] = None
    tre: Optional[float] = None
    total_saida_execucao_periodo: Optional[int] = None
    total_incontroverso_saida_execucao_periodo: Optional[int] = None
    valor_execucao_saida_periodo: Optional[float] = None
    valor_incontroverso_saida_execucao_periodo: Optional[float] = None
    valor_ted_saida_execucao_periodo: Optional[float] = None
    taxa_recuperacao_execucao: Optional[float] = None
    media_tempo_execucao: Optional[float] = None
    taxa_atualizacao_execucao_NG: Optional[Dict[str, Any]] = None
    duracoes_tempo_execucao_NG: Optional[List[float]] = None
    mediana_tempo_execucao: Optional[float] = None
    execucao_materia_filtro: Optional[Union[str, List[str]]] = None
    execucao_subfase_filtro: Optional[Union[str, List[str]]] = None
    execucao_ano_ajuizamento_filtro: Optional[str] = None

    # Execução Acordos NG
    total_em_execucao_acordos_NG: Optional[int] = None
    valor_total_em_execucao_acordos_NG: Optional[float] = None
    total_valor_alcada_final_vazio_acordos_NG: Optional[int] = None
    total_valor_alcada_final_vazio_acordos_NG_detalhe: Optional[List[ProcessoDadoFaltando]] = None
    estoque_inicial_execucao_acordos_NG: Optional[int] = None
    tre_execucao_acordos_NG: Optional[float] = None
    total_entrada_execucao_acordos_periodo_NG: Optional[int] = None
    valor_entrada_execucao_acordos_periodo_NG: Optional[float] = None
    total_saida_execucao_acordos_periodo_NG: Optional[int] = None
    valor_saida_execucao_acordos_periodo_NG: Optional[float] = None
    valor_ted_saida_execucao_acordos_periodo_NG: Optional[float] = None
    media_tempo_execucao_acordos_NG: Optional[float] = None
    duracoes_tempo_execucao_acordos_NG: Optional[List[float]] = None
    mediana_tempo_execucao_acordos_NG: Optional[float] = None
    total_atividades_execucao_acordos_NG: Optional[int] = None
    atividades_execucao_em_andamento_acordos_NG: Optional[int] = None
    atividades_execucao_vencidas_acordos_NG: Optional[int] = None
    atividades_execucao_vencem_hoje_acordos_NG: Optional[int] = None
    atividades_execucao_concluidas_acordos_NG: Optional[int] = None
    media_mensal_atividades_execucao_acordos_NG: Optional[float] = None
    total_por_prazo_execucao_acordos_NG: Optional[int] = None
    por_prazo_em_andamento_execucao_acordos_NG: Optional[int] = None
    por_prazo_vencidas_execucao_acordos_NG: Optional[int] = None
    por_prazo_vencem_hoje_execucao_acordos_NG: Optional[int] = None
    por_prazo_concluidas_execucao_acordos_NG: Optional[int] = None
    total_diligencias_execucao_acordos_NG: Optional[int] = None
    total_diligencias_expedicao_alvara_execucao_acordos_NG: Optional[int] = None
    cumpridas_diligencias_expedicao_alvara_execucao_acordos_NG: Optional[int] = None
    valor_diligencias_expedicao_alvara_execucao_acordos_NG: Optional[float] = None
    execucao_acordos_materia_filtro_NG: Optional[Union[str, List[str]]] = None
    execucao_acordos_subfase_filtro_NG: Optional[List[str]] = None
    execucao_acordos_tipo_acao_filtro_NG: Optional[str] = None
    execucao_acordos_sentenca_filtro_NG: Optional[str] = None
    execucao_acordos_uf_filtro_NG: Optional[List[str]] = None
    execucao_acordos_uf_opcoes_NG: Optional[List[str]] = None
    execucao_acordos_ano_ajuizamento_filtro_NG: Optional[str] = None
    execucao_acordos_processo_filtro_NG: Optional[str] = None
    execucao_acordos_comarca_filtro_NG: Optional[List[str]] = None
    execucao_acordos_comarca_opcoes_NG: Optional[List[str]] = None
    execucao_acordos_materia_opcoes_NG: Optional[List[str]] = None
    execucao_acordos_subfase_opcoes_NG: Optional[List[str]] = None
    execucao_acordos_diligencia_tipo_filtro_NG: Optional[str] = None
    execucao_acordos_diligencia_colaborador_filtro_NG: Optional[str] = None
    total_fechamento_acordos_NG: Optional[int] = None
    total_em_execucao_acordos_LA: Optional[int] = None
    valor_total_em_execucao_acordos_LA: Optional[float] = None
    total_valor_alcada_final_vazio_acordos_LA: Optional[int] = None
    total_valor_alcada_final_vazio_acordos_LA_detalhe: Optional[List[ProcessoDadoFaltando]] = None
    estoque_inicial_execucao_acordos_LA: Optional[int] = None
    tre_execucao_acordos_LA: Optional[float] = None
    total_entrada_execucao_acordos_periodo_LA: Optional[int] = None
    valor_entrada_execucao_acordos_periodo_LA: Optional[float] = None
    total_saida_execucao_acordos_periodo_LA: Optional[int] = None
    valor_saida_execucao_acordos_periodo_LA: Optional[float] = None
    valor_ted_saida_execucao_acordos_periodo_LA: Optional[float] = None
    media_tempo_execucao_acordos_LA: Optional[float] = None
    duracoes_tempo_execucao_acordos_LA: Optional[List[float]] = None
    mediana_tempo_execucao_acordos_LA: Optional[float] = None
    total_atividades_execucao_acordos_LA: Optional[int] = None
    atividades_execucao_em_andamento_acordos_LA: Optional[int] = None
    atividades_execucao_vencidas_acordos_LA: Optional[int] = None
    atividades_execucao_vencem_hoje_acordos_LA: Optional[int] = None
    atividades_execucao_concluidas_acordos_LA: Optional[int] = None
    media_mensal_atividades_execucao_acordos_LA: Optional[float] = None
    total_por_prazo_execucao_acordos_LA: Optional[int] = None
    por_prazo_em_andamento_execucao_acordos_LA: Optional[int] = None
    por_prazo_vencidas_execucao_acordos_LA: Optional[int] = None
    por_prazo_vencem_hoje_execucao_acordos_LA: Optional[int] = None
    por_prazo_concluidas_execucao_acordos_LA: Optional[int] = None
    total_diligencias_execucao_acordos_LA: Optional[int] = None
    total_diligencias_expedicao_alvara_execucao_acordos_LA: Optional[int] = None
    cumpridas_diligencias_expedicao_alvara_execucao_acordos_LA: Optional[int] = None
    valor_diligencias_expedicao_alvara_execucao_acordos_LA: Optional[float] = None
    execucao_acordos_materia_filtro_LA: Optional[Union[str, List[str]]] = None
    execucao_acordos_subfase_filtro_LA: Optional[Union[str, List[str]]] = None
    execucao_acordos_tipo_acao_filtro_LA: Optional[str] = None
    execucao_acordos_sentenca_filtro_LA: Optional[str] = None
    execucao_acordos_uf_filtro_LA: Optional[List[str]] = None
    execucao_acordos_uf_opcoes_LA: Optional[List[str]] = None
    execucao_acordos_ano_ajuizamento_filtro_LA: Optional[str] = None
    execucao_acordos_processo_filtro_LA: Optional[str] = None
    execucao_acordos_comarca_filtro_LA: Optional[List[str]] = None
    execucao_acordos_comarca_opcoes_LA: Optional[List[str]] = None
    execucao_acordos_materia_opcoes_LA: Optional[List[str]] = None
    execucao_acordos_subfase_opcoes_LA: Optional[List[str]] = None
    execucao_acordos_diligencia_tipo_filtro_LA: Optional[str] = None
    execucao_acordos_diligencia_colaborador_filtro_LA: Optional[str] = None
    total_fechamento_acordos_LA: Optional[int] = None
    total_em_execucao_acordos_RJ: Optional[int] = None
    valor_total_em_execucao_acordos_RJ: Optional[float] = None
    total_valor_alcada_final_vazio_acordos_RJ: Optional[int] = None
    total_valor_alcada_final_vazio_acordos_RJ_detalhe: Optional[List[ProcessoDadoFaltando]] = None
    estoque_inicial_execucao_acordos_RJ: Optional[int] = None
    tre_execucao_acordos_RJ: Optional[float] = None
    total_entrada_execucao_acordos_periodo_RJ: Optional[int] = None
    valor_entrada_execucao_acordos_periodo_RJ: Optional[float] = None
    total_saida_execucao_acordos_periodo_RJ: Optional[int] = None
    valor_saida_execucao_acordos_periodo_RJ: Optional[float] = None
    valor_ted_saida_execucao_acordos_periodo_RJ: Optional[float] = None
    media_tempo_execucao_acordos_RJ: Optional[float] = None
    duracoes_tempo_execucao_acordos_RJ: Optional[List[float]] = None
    mediana_tempo_execucao_acordos_RJ: Optional[float] = None
    total_atividades_execucao_acordos_RJ: Optional[int] = None
    atividades_execucao_em_andamento_acordos_RJ: Optional[int] = None
    atividades_execucao_vencidas_acordos_RJ: Optional[int] = None
    atividades_execucao_vencem_hoje_acordos_RJ: Optional[int] = None
    atividades_execucao_concluidas_acordos_RJ: Optional[int] = None
    media_mensal_atividades_execucao_acordos_RJ: Optional[float] = None
    total_por_prazo_execucao_acordos_RJ: Optional[int] = None
    por_prazo_em_andamento_execucao_acordos_RJ: Optional[int] = None
    por_prazo_vencidas_execucao_acordos_RJ: Optional[int] = None
    por_prazo_vencem_hoje_execucao_acordos_RJ: Optional[int] = None
    por_prazo_concluidas_execucao_acordos_RJ: Optional[int] = None
    total_diligencias_execucao_acordos_RJ: Optional[int] = None
    total_diligencias_expedicao_alvara_execucao_acordos_RJ: Optional[int] = None
    cumpridas_diligencias_expedicao_alvara_execucao_acordos_RJ: Optional[int] = None
    valor_diligencias_expedicao_alvara_execucao_acordos_RJ: Optional[float] = None
    execucao_acordos_materia_filtro_RJ: Optional[Union[str, List[str]]] = None
    execucao_acordos_subfase_filtro_RJ: Optional[Union[str, List[str]]] = None
    execucao_acordos_tipo_acao_filtro_RJ: Optional[str] = None
    execucao_acordos_sentenca_filtro_RJ: Optional[str] = None
    execucao_acordos_uf_filtro_RJ: Optional[List[str]] = None
    execucao_acordos_uf_opcoes_RJ: Optional[List[str]] = None
    execucao_acordos_ano_ajuizamento_filtro_RJ: Optional[str] = None
    execucao_acordos_processo_filtro_RJ: Optional[str] = None
    execucao_acordos_comarca_filtro_RJ: Optional[List[str]] = None
    execucao_acordos_comarca_opcoes_RJ: Optional[List[str]] = None
    execucao_acordos_materia_opcoes_RJ: Optional[List[str]] = None
    execucao_acordos_subfase_opcoes_RJ: Optional[List[str]] = None
    execucao_acordos_diligencia_tipo_filtro_RJ: Optional[str] = None
    execucao_acordos_diligencia_colaborador_filtro_RJ: Optional[str] = None
    total_fechamento_acordos_RJ: Optional[int] = None

    total_atividades_execucao_NG: Optional[int] = None
    atividades_execucao_em_andamento_NG: Optional[int] = None
    total_atividades_criadas_execucao_NG: Optional[int] = None
    atividades_criadas_em_andamento_execucao_NG: Optional[int] = None
    atividades_execucao_abertas_NG: Optional[int] = None
    atividades_execucao_vencidas_NG: Optional[int] = None
    atividades_execucao_vencem_hoje_NG: Optional[int] = None
    atividades_execucao_concluidas_NG: Optional[int] = None
    media_mensal_atividades_execucao_NG: Optional[float] = None
    total_por_prazo_execucao_NG: Optional[int] = None
    por_prazo_em_andamento_execucao_NG: Optional[int] = None
    por_prazo_vencidas_execucao_NG: Optional[int] = None
    por_prazo_vencem_hoje_execucao_NG: Optional[int] = None
    por_prazo_concluidas_execucao_NG: Optional[int] = None
    total_diligencias_execucao_NG: Optional[int] = None
    total_diligencias_expedicao_alvara_execucao_NG: Optional[int] = None
    cumpridas_diligencias_expedicao_alvara_execucao_NG: Optional[int] = None
    valor_diligencias_expedicao_alvara_execucao_NG: Optional[float] = None
    execucao_diligencia_tipo_filtro_NG: Optional[str] = None
    execucao_diligencia_colaborador_filtro_NG: Optional[str] = None
    execucao_uf_filtro_NG: Optional[List[str]] = None
    execucao_uf_opcoes_NG: Optional[List[str]] = None
    execucao_comarca_filtro_NG: Optional[List[str]] = None
    execucao_comarca_opcoes_NG: Optional[List[str]] = None
    execucao_materia_opcoes_NG: Optional[List[str]] = None
    execucao_subfase_opcoes_NG: Optional[List[str]] = None

    # Execução RJ (Condenação)
    total_em_execucao_RJ: Optional[int] = None
    valor_total_em_execucao_RJ: Optional[float] = None
    total_valor_execucao_vazio_RJ: Optional[int] = None
    total_valor_execucao_vazio_RJ_detalhe: Optional[List[ProcessoDadoFaltando]] = None
    valor_honorarios_total_execucao_RJ: Optional[float] = None
    valor_em_execucao_RJ: Optional[float] = None
    valor_remanescente_em_execucao_RJ: Optional[float] = None
    estoque_inicial_RJ: Optional[int] = None
    tre_RJ: Optional[float] = None
    total_saida_execucao_periodo_RJ: Optional[int] = None
    total_incontroverso_saida_execucao_periodo_RJ: Optional[int] = None
    valor_execucao_saida_periodo_RJ: Optional[float] = None
    valor_incontroverso_saida_execucao_periodo_RJ: Optional[float] = None
    valor_ted_saida_execucao_periodo_RJ: Optional[float] = None
    taxa_recuperacao_execucao_RJ: Optional[float] = None
    media_tempo_execucao_RJ: Optional[float] = None
    taxa_atualizacao_execucao_RJ: Optional[Dict[str, Any]] = None
    duracoes_tempo_execucao_RJ: Optional[List[float]] = None
    mediana_tempo_execucao_RJ: Optional[float] = None
    execucao_materia_filtro_RJ: Optional[Union[str, List[str]]] = None
    execucao_subfase_filtro_RJ: Optional[Union[str, List[str]]] = None
    execucao_ano_ajuizamento_filtro_RJ: Optional[str] = None
    total_atividades_execucao_RJ: Optional[int] = None
    atividades_execucao_em_andamento_RJ: Optional[int] = None
    atividades_execucao_vencidas_RJ: Optional[int] = None
    atividades_execucao_vencem_hoje_RJ: Optional[int] = None
    atividades_execucao_concluidas_RJ: Optional[int] = None
    total_atividades_criadas_execucao_RJ: Optional[int] = None
    atividades_criadas_em_andamento_execucao_RJ: Optional[int] = None
    atividades_execucao_abertas_RJ: Optional[int] = None
    media_mensal_atividades_execucao_RJ: Optional[float] = None
    total_por_prazo_execucao_RJ: Optional[int] = None
    por_prazo_em_andamento_execucao_RJ: Optional[int] = None
    por_prazo_vencidas_execucao_RJ: Optional[int] = None
    por_prazo_vencem_hoje_execucao_RJ: Optional[int] = None
    por_prazo_concluidas_execucao_RJ: Optional[int] = None
    total_diligencias_execucao_RJ: Optional[int] = None
    total_diligencias_expedicao_alvara_execucao_RJ: Optional[int] = None
    cumpridas_diligencias_expedicao_alvara_execucao_RJ: Optional[int] = None
    valor_diligencias_expedicao_alvara_execucao_RJ: Optional[float] = None
    execucao_diligencia_tipo_filtro_RJ: Optional[str] = None
    execucao_diligencia_colaborador_filtro_RJ: Optional[str] = None
    execucao_uf_filtro_RJ: Optional[List[str]] = None
    execucao_uf_opcoes_RJ: Optional[List[str]] = None
    execucao_comarca_filtro_RJ: Optional[List[str]] = None
    execucao_comarca_opcoes_RJ: Optional[List[str]] = None
    execucao_materia_opcoes_RJ: Optional[List[str]] = None
    execucao_subfase_opcoes_RJ: Optional[List[str]] = None

    # Comercial LA
    clientes_campanha_LA: Optional[int] = None
    clientes_indicacao_LA: Optional[int] = None
    clientes_redes_sociais_LA: Optional[int] = None
    clientes_retorno_LA: Optional[int] = None
    clientes_parceiro_LA: Optional[int] = None
    clientes_externos_LA: Optional[int] = None
    clientes_todos_LA: Optional[int] = None
    clientes_cancelados_LA: Optional[int] = None
    acoes_fechadas_LA: Optional[int] = None
    taxa_aproveitamento_LA: Optional[float] = None
    comparativo_clientes_campanha_LA: Optional[float] = None
    comparativo_clientes_indicacao_LA: Optional[float] = None
    comparativo_clientes_externos_LA: Optional[float] = None
    comparativo_clientes_parceiro_LA: Optional[float] = None
    comparativo_clientes_retorno_LA: Optional[float] = None
    comparativo_clientes_redes_sociais_LA: Optional[float] = None
    comparativo_clientes_cancelados_LA: Optional[float] = None
    comparativo_acoes_fechadas_LA: Optional[float] = None
    acoes_fechadas_periodo_anterior_LA: Optional[float] = None
    comparativo_taxa_aproveitamento_LA: Optional[float] = None
    comparativo_clientes_total_LA: Optional[float] = None
    clientes_total_periodo_anterior_LA: Optional[float] = None
    comissao_base_LA: Optional[float] = None
    tempo_medio_contratacao_protocolo_LA: Optional[float] = None
    mediana_tempo_contratacao_protocolo_LA: Optional[float] = None
    comparativo_tempo_medio_contratacao_protocolo_LA: Optional[float] = None
    comparativo_mediana_tempo_contratacao_protocolo_LA: Optional[float] = None

    # Protocolo LA
    protocolos_resolvidos_LA: Optional[int] = None
    protocolos_represados_LA: Optional[int] = None
    valor_causa_protocolado_LA: Optional[float] = None
    ticket_medio_protocolos_resolvidos_LA: Optional[float] = None
    media_tempo_protocolo_LA: Optional[float] = None
    mediana_tempo_protocolo_LA: Optional[float] = None
    comparativo_protocolos_resolvidos_LA: Optional[float] = None
    protocolos_resolvidos_periodo_anterior_LA: Optional[float] = None
    comparativo_valor_causa_protocolado_LA: Optional[float] = None
    valor_causa_protocolado_periodo_anterior_LA: Optional[float] = None
    comparativo_ticket_medio_protocolos_resolvidos_LA: Optional[float] = None
    comparativo_tempo_medio_protocolos_resolvidos_LA: Optional[float] = None
    comparativo_mediana_tempo_protocolos_resolvidos_LA: Optional[float] = None
    taxa_protocolados_LA: Optional[float] = None
    entradas_protocolo_LA: Optional[int] = None
    valor_causa_protocolado_LA_2026: Optional[float] = None
    meta_anual_comercial_LA: Optional[float] = None
    fator_multiplicador_LA: Optional[float] = None
    comissao_com_fm_LA: Optional[float] = None

    # Estratégico Geral (NG + LA)
    protocolos_resolvidos_geral: Optional[int] = None
    estrategico_geral_fase_inicial_total_processos: Optional[int] = None
    estrategico_geral_fase_inicial_valor_causa_total: Optional[float] = None
    estrategico_geral_fase_recursal_total_processos: Optional[int] = None
    estrategico_geral_fase_recursal_valor_causa_total: Optional[float] = None
    estrategico_geral_fase_recursal_valor_sentenca_total: Optional[float] = None
    estrategico_geral_fase_execucao_total_processos: Optional[int] = None
    estrategico_geral_fase_execucao_valor_causa_total: Optional[float] = None
    estrategico_geral_fase_execucao_valor_execucao_total: Optional[float] = None
    estrategico_geral_escritorio_filtro: Optional[str] = None
    estrategico_geral_escritorios_filtro: Optional[List[str]] = None
    estrategico_geral_comarcas_filtro: Optional[List[str]] = None

    # Peticionamento LA
    total_confeccionados_LA: Optional[int] = None
    confeccionados_manualmente_LA: Optional[int] = None
    confeccionados_automaticamente_LA: Optional[int] = None
    nao_confeccionados_LA: Optional[int] = None
    valor_causa_confeccionado_LA: Optional[float] = None
    ticket_medio_confeccionado_LA: Optional[float] = None
    tempo_medio_confeccao_LA: Optional[float] = None
    mediana_tempo_confeccao_LA: Optional[float] = None
    comparativo_confeccionados_LA: Optional[float] = None
    comparativo_confeccionados_automaticamente_LA: Optional[float] = None
    comparativo_confeccionados_manualmente_LA: Optional[float] = None
    comparativo_valor_causa_confeccionado_LA: Optional[float] = None
    comparativo_ticket_medio_confeccionado_LA: Optional[float] = None
    comparativo_tempo_medio_confeccionado_LA: Optional[float] = None
    comparativo_mediana_tempo_confeccionado_LA: Optional[float] = None
    peticionamento_taxa_resolvidos_LA: Optional[float] = None
    peticionamento_taxa_nao_resolvidos_LA: Optional[float] = None
    peticionamento_taxa_retorno_protocolo_LA: Optional[float] = None
    peticionamento_qtd_retorno_protocolo_LA: Optional[int] = None
    peticionamento_qtd_entrada_protocolo_LA: Optional[int] = None

    # Andamento Processual LA
    total_andamento_processual_LA: Optional[int] = None
    andamento_processual_resolvidos_LA: Optional[int] = None
    andamento_processual_nao_resolvidos_LA: Optional[int] = None
    media_avaliacao_LA: Optional[float] = None
    taxa_resolvidos_LA: Optional[float] = None
    taxa_nao_resolvidos_LA: Optional[float] = None
    media_espera_LA: Optional[float] = None
    mediana_espera_LA: Optional[float] = None
    media_atendimento_LA: Optional[float] = None
    mediana_atendimento_LA: Optional[float] = None

    # Execução LA
    total_em_execucao_LA: Optional[int] = None
    valor_total_em_execucao_LA: Optional[float] = None
    total_valor_execucao_vazio_LA: Optional[int] = None
    total_valor_execucao_vazio_LA_detalhe: Optional[List[ProcessoDadoFaltando]] = None
    valor_honorarios_total_execucao_LA: Optional[float] = None
    valor_em_execucao_LA: Optional[float] = None
    valor_remanescente_em_execucao_LA: Optional[float] = None
    estoque_inicial_LA: Optional[int] = None
    tre_LA: Optional[float] = None
    total_saida_execucao_periodo_LA: Optional[int] = None
    total_incontroverso_saida_execucao_periodo_LA: Optional[int] = None
    valor_execucao_saida_periodo_LA: Optional[float] = None
    valor_incontroverso_saida_execucao_periodo_LA: Optional[float] = None
    valor_ted_saida_execucao_periodo_LA: Optional[float] = None
    taxa_recuperacao_execucao_LA: Optional[float] = None
    media_tempo_execucao_LA: Optional[float] = None
    taxa_atualizacao_execucao_LA: Optional[Dict[str, Any]] = None
    duracoes_tempo_execucao_LA: Optional[List[float]] = None
    mediana_tempo_execucao_LA: Optional[float] = None
    execucao_materia_filtro_LA: Optional[Union[str, List[str]]] = None
    execucao_subfase_filtro_LA: Optional[Union[str, List[str]]] = None
    execucao_ano_ajuizamento_filtro_LA: Optional[str] = None
    execucao_comarca_filtro_LA: Optional[List[str]] = None
    execucao_comarca_opcoes_LA: Optional[List[str]] = None
    execucao_uf_filtro_LA: Optional[List[str]] = None
    execucao_uf_opcoes_LA: Optional[List[str]] = None
    execucao_materia_opcoes_LA: Optional[List[str]] = None
    execucao_subfase_opcoes_LA: Optional[List[str]] = None
    total_atividades_execucao_LA: Optional[int] = None
    atividades_execucao_em_andamento_LA: Optional[int] = None
    total_atividades_criadas_execucao_LA: Optional[int] = None
    atividades_criadas_em_andamento_execucao_LA: Optional[int] = None
    atividades_execucao_abertas_LA: Optional[int] = None
    atividades_execucao_vencidas_LA: Optional[int] = None
    atividades_execucao_vencem_hoje_LA: Optional[int] = None
    atividades_execucao_concluidas_LA: Optional[int] = None
    media_mensal_atividades_execucao_LA: Optional[float] = None
    total_por_prazo_execucao_LA: Optional[int] = None
    por_prazo_em_andamento_execucao_LA: Optional[int] = None
    por_prazo_vencidas_execucao_LA: Optional[int] = None
    por_prazo_vencem_hoje_execucao_LA: Optional[int] = None
    por_prazo_concluidas_execucao_LA: Optional[int] = None

    # Fase Recursal LA (setor_recurso / LexFlow)
    total_recursal_LA: Optional[int] = None
    entrada_recursal_LA: Optional[int] = None
    valor_causa_acordo_recursal_LA: Optional[float] = None
    total_sentenca_favoravel_recurso_LA: Optional[int] = None
    total_sentenca_desfavoravel_recurso_LA: Optional[int] = None
    total_procedente_1g_recurso_LA: Optional[int] = None
    total_parcialmente_procedente_recurso_LA: Optional[int] = None
    total_sentenca_extincao_recurso_LA: Optional[int] = None
    total_sentenca_parcialmente_favoravel_recurso_LA: Optional[int] = None
    valor_causa_sentenca_favoravel_recurso_LA: Optional[float] = None
    valor_causa_sentenca_desfavoravel_recurso_LA: Optional[float] = None
    valor_causa_sentenca_procedente_1g_recurso_LA: Optional[float] = None
    valor_causa_sentenca_parcialmente_procedente_recurso_LA: Optional[float] = None
    valor_causa_sentenca_extincao_recurso_LA: Optional[float] = None
    valor_causa_sentenca_parcialmente_favoravel_recurso_LA: Optional[float] = None
    total_acordao_desfavoravel_recurso_LA: Optional[int] = None
    total_acordao_favoravel_recurso_LA: Optional[int] = None
    total_acordao_parcialmente_favoravel_recurso_LA: Optional[int] = None
    total_acordao_parcial_retomada_recurso_LA: Optional[int] = None
    total_acordao_extincao_recurso_LA: Optional[int] = None
    valor_causa_acordao_desfavoravel_recurso_LA: Optional[float] = None
    valor_causa_acordao_favoravel_recurso_LA: Optional[float] = None
    valor_causa_acordao_parcialmente_favoravel_recurso_LA: Optional[float] = None
    valor_causa_acordao_parcial_retomada_recurso_LA: Optional[float] = None
    valor_causa_acordao_extincao_recurso_LA: Optional[float] = None
    total_decisoes_recursal_LA: Optional[int] = None
    # Decisões recursais — Matriz de Julgamento (mérito 1G × 2G), 8 buckets
    total_mantido_ganho_recurso_LA: Optional[int] = None
    total_ganho_ampliado_recurso_LA: Optional[int] = None
    total_revertido_ganho_recurso_LA: Optional[int] = None
    total_ganho_reduzido_recurso_LA: Optional[int] = None
    total_mantido_perda_recurso_LA: Optional[int] = None
    total_revertido_perda_recurso_LA: Optional[int] = None
    total_extincao_reajuizar_recurso_LA: Optional[int] = None
    total_instrucao_retomada_recurso_LA: Optional[int] = None
    percent_mantido_ganho_recursal_LA: Optional[float] = None
    percent_ganho_ampliado_recursal_LA: Optional[float] = None
    percent_revertido_ganho_recursal_LA: Optional[float] = None
    percent_ganho_reduzido_recursal_LA: Optional[float] = None
    percent_mantido_perda_recursal_LA: Optional[float] = None
    percent_revertido_perda_recursal_LA: Optional[float] = None
    percent_extincao_reajuizar_recursal_LA: Optional[float] = None
    percent_instrucao_retomada_recursal_LA: Optional[float] = None
    valor_causa_mantido_ganho_recurso_LA: Optional[float] = None
    valor_causa_ganho_ampliado_recurso_LA: Optional[float] = None
    valor_causa_revertido_ganho_recurso_LA: Optional[float] = None
    valor_causa_ganho_reduzido_recurso_LA: Optional[float] = None
    valor_causa_mantido_perda_recurso_LA: Optional[float] = None
    valor_causa_revertido_perda_recurso_LA: Optional[float] = None
    valor_causa_extincao_reajuizar_recurso_LA: Optional[float] = None
    valor_causa_instrucao_retomada_recurso_LA: Optional[float] = None
    total_atividades_recursos_LA: Optional[int] = None
    atividades_recursos_em_andamento_LA: Optional[int] = None
    atividades_recursos_vencidas_LA: Optional[int] = None
    atividades_recursos_vencem_hoje_LA: Optional[int] = None
    atividades_recursos_concluidas_LA: Optional[int] = None
    # Mesmos KPIs de atividades, usando PRAZO como eixo temporal (toggle "Por prazo").
    total_por_prazo_atividades_recursos_LA: Optional[int] = None
    por_prazo_em_andamento_atividades_recursos_LA: Optional[int] = None
    por_prazo_vencidas_atividades_recursos_LA: Optional[int] = None
    por_prazo_vencem_hoje_atividades_recursos_LA: Optional[int] = None
    por_prazo_concluidas_atividades_recursos_LA: Optional[int] = None

    # Recursal NG
    total_recursal_NG: Optional[int] = None
    entrada_recursal_NG: Optional[int] = None
    valor_causa_acordo_recursal_NG: Optional[float] = None
    total_sentenca_favoravel_recurso_NG: Optional[int] = None
    total_sentenca_desfavoravel_recurso_NG: Optional[int] = None
    total_procedente_1g_recurso_NG: Optional[int] = None
    total_parcialmente_procedente_recurso_NG: Optional[int] = None
    total_sentenca_extincao_recurso_NG: Optional[int] = None
    total_sentenca_parcialmente_favoravel_recurso_NG: Optional[int] = None
    valor_causa_sentenca_favoravel_recurso_NG: Optional[float] = None
    valor_causa_sentenca_desfavoravel_recurso_NG: Optional[float] = None
    valor_causa_sentenca_procedente_1g_recurso_NG: Optional[float] = None
    valor_causa_sentenca_parcialmente_procedente_recurso_NG: Optional[float] = None
    valor_causa_sentenca_extincao_recurso_NG: Optional[float] = None
    valor_causa_sentenca_parcialmente_favoravel_recurso_NG: Optional[float] = None
    total_acordao_desfavoravel_recurso_NG: Optional[int] = None
    total_acordao_favoravel_recurso_NG: Optional[int] = None
    total_acordao_parcialmente_favoravel_recurso_NG: Optional[int] = None
    total_acordao_parcial_retomada_recurso_NG: Optional[int] = None
    total_acordao_extincao_recurso_NG: Optional[int] = None
    valor_causa_acordao_desfavoravel_recurso_NG: Optional[float] = None
    valor_causa_acordao_favoravel_recurso_NG: Optional[float] = None
    valor_causa_acordao_parcialmente_favoravel_recurso_NG: Optional[float] = None
    valor_causa_acordao_parcial_retomada_recurso_NG: Optional[float] = None
    valor_causa_acordao_extincao_recurso_NG: Optional[float] = None
    total_decisoes_recursal_NG: Optional[int] = None
    # Decisões recursais — Matriz de Julgamento (mérito 1G × 2G), 8 buckets
    total_mantido_ganho_recurso_NG: Optional[int] = None
    total_ganho_ampliado_recurso_NG: Optional[int] = None
    total_revertido_ganho_recurso_NG: Optional[int] = None
    total_ganho_reduzido_recurso_NG: Optional[int] = None
    total_mantido_perda_recurso_NG: Optional[int] = None
    total_revertido_perda_recurso_NG: Optional[int] = None
    total_extincao_reajuizar_recurso_NG: Optional[int] = None
    total_instrucao_retomada_recurso_NG: Optional[int] = None
    percent_mantido_ganho_recursal_NG: Optional[float] = None
    percent_ganho_ampliado_recursal_NG: Optional[float] = None
    percent_revertido_ganho_recursal_NG: Optional[float] = None
    percent_ganho_reduzido_recursal_NG: Optional[float] = None
    percent_mantido_perda_recursal_NG: Optional[float] = None
    percent_revertido_perda_recursal_NG: Optional[float] = None
    percent_extincao_reajuizar_recursal_NG: Optional[float] = None
    percent_instrucao_retomada_recursal_NG: Optional[float] = None
    valor_causa_mantido_ganho_recurso_NG: Optional[float] = None
    valor_causa_ganho_ampliado_recurso_NG: Optional[float] = None
    valor_causa_revertido_ganho_recurso_NG: Optional[float] = None
    valor_causa_ganho_reduzido_recurso_NG: Optional[float] = None
    valor_causa_mantido_perda_recurso_NG: Optional[float] = None
    valor_causa_revertido_perda_recurso_NG: Optional[float] = None
    valor_causa_extincao_reajuizar_recurso_NG: Optional[float] = None
    valor_causa_instrucao_retomada_recurso_NG: Optional[float] = None
    total_atividades_recursos_NG: Optional[int] = None
    atividades_recursos_em_andamento_NG: Optional[int] = None
    atividades_recursos_vencidas_NG: Optional[int] = None
    atividades_recursos_vencem_hoje_NG: Optional[int] = None
    atividades_recursos_concluidas_NG: Optional[int] = None
    # Mesmos KPIs de atividades, usando PRAZO como eixo temporal (toggle "Por prazo").
    total_por_prazo_atividades_recursos_NG: Optional[int] = None
    por_prazo_em_andamento_atividades_recursos_NG: Optional[int] = None
    por_prazo_vencidas_atividades_recursos_NG: Optional[int] = None
    por_prazo_vencem_hoje_atividades_recursos_NG: Optional[int] = None
    por_prazo_concluidas_atividades_recursos_NG: Optional[int] = None
    # Cumprido e encaminhado como "RECURSO CANCELADO" — análise de viabilidade equivocada.
    avr_retorno_recurso_cancelado_NG: Optional[int] = None
    # Cumprido e encaminhado como "RECURSO CANCELADO" — perda de prazo.
    retorno_cr_recurso_cancelado_NG: Optional[int] = None
    # Meta de Provimento Mensal — processos providos (ID_2G) no período.
    provimento_mensal_qtd_NG: Optional[int] = None
    provimento_mensal_meta_NG: Optional[int] = None
    # Recursal RJ
    total_recursal_RJ: Optional[int] = None
    entrada_recursal_RJ: Optional[int] = None
    valor_causa_acordo_recursal_RJ: Optional[float] = None
    total_sentenca_favoravel_recurso_RJ: Optional[int] = None
    total_sentenca_desfavoravel_recurso_RJ: Optional[int] = None
    total_procedente_1g_recurso_RJ: Optional[int] = None
    total_parcialmente_procedente_recurso_RJ: Optional[int] = None
    total_sentenca_extincao_recurso_RJ: Optional[int] = None
    total_sentenca_parcialmente_favoravel_recurso_RJ: Optional[int] = None
    valor_causa_sentenca_favoravel_recurso_RJ: Optional[float] = None
    valor_causa_sentenca_desfavoravel_recurso_RJ: Optional[float] = None
    valor_causa_sentenca_procedente_1g_recurso_RJ: Optional[float] = None
    valor_causa_sentenca_parcialmente_procedente_recurso_RJ: Optional[float] = None
    valor_causa_sentenca_extincao_recurso_RJ: Optional[float] = None
    valor_causa_sentenca_parcialmente_favoravel_recurso_RJ: Optional[float] = None
    total_acordao_desfavoravel_recurso_RJ: Optional[int] = None
    total_acordao_favoravel_recurso_RJ: Optional[int] = None
    total_acordao_parcialmente_favoravel_recurso_RJ: Optional[int] = None
    total_acordao_parcial_retomada_recurso_RJ: Optional[int] = None
    total_acordao_extincao_recurso_RJ: Optional[int] = None
    valor_causa_acordao_desfavoravel_recurso_RJ: Optional[float] = None
    valor_causa_acordao_favoravel_recurso_RJ: Optional[float] = None
    valor_causa_acordao_parcialmente_favoravel_recurso_RJ: Optional[float] = None
    valor_causa_acordao_parcial_retomada_recurso_RJ: Optional[float] = None
    valor_causa_acordao_extincao_recurso_RJ: Optional[float] = None
    total_decisoes_recursal_RJ: Optional[int] = None
    # Decisões recursais — Matriz de Julgamento (mérito 1G × 2G), 8 buckets
    total_mantido_ganho_recurso_RJ: Optional[int] = None
    total_ganho_ampliado_recurso_RJ: Optional[int] = None
    total_revertido_ganho_recurso_RJ: Optional[int] = None
    total_ganho_reduzido_recurso_RJ: Optional[int] = None
    total_mantido_perda_recurso_RJ: Optional[int] = None
    total_revertido_perda_recurso_RJ: Optional[int] = None
    total_extincao_reajuizar_recurso_RJ: Optional[int] = None
    total_instrucao_retomada_recurso_RJ: Optional[int] = None
    percent_mantido_ganho_recursal_RJ: Optional[float] = None
    percent_ganho_ampliado_recursal_RJ: Optional[float] = None
    percent_revertido_ganho_recursal_RJ: Optional[float] = None
    percent_ganho_reduzido_recursal_RJ: Optional[float] = None
    percent_mantido_perda_recursal_RJ: Optional[float] = None
    percent_revertido_perda_recursal_RJ: Optional[float] = None
    percent_extincao_reajuizar_recursal_RJ: Optional[float] = None
    percent_instrucao_retomada_recursal_RJ: Optional[float] = None
    valor_causa_mantido_ganho_recurso_RJ: Optional[float] = None
    valor_causa_ganho_ampliado_recurso_RJ: Optional[float] = None
    valor_causa_revertido_ganho_recurso_RJ: Optional[float] = None
    valor_causa_ganho_reduzido_recurso_RJ: Optional[float] = None
    valor_causa_mantido_perda_recurso_RJ: Optional[float] = None
    valor_causa_revertido_perda_recurso_RJ: Optional[float] = None
    valor_causa_extincao_reajuizar_recurso_RJ: Optional[float] = None
    valor_causa_instrucao_retomada_recurso_RJ: Optional[float] = None
    total_atividades_recursos_RJ: Optional[int] = None
    atividades_recursos_em_andamento_RJ: Optional[int] = None
    atividades_recursos_vencidas_RJ: Optional[int] = None
    atividades_recursos_vencem_hoje_RJ: Optional[int] = None
    atividades_recursos_concluidas_RJ: Optional[int] = None
    # Mesmos KPIs de atividades, usando PRAZO como eixo temporal (toggle "Por prazo").
    total_por_prazo_atividades_recursos_RJ: Optional[int] = None
    por_prazo_em_andamento_atividades_recursos_RJ: Optional[int] = None
    por_prazo_vencidas_atividades_recursos_RJ: Optional[int] = None
    por_prazo_vencem_hoje_atividades_recursos_RJ: Optional[int] = None
    por_prazo_concluidas_atividades_recursos_RJ: Optional[int] = None
    # Cumprido e encaminhado como "RECURSO CANCELADO" — análise de viabilidade equivocada.
    avr_retorno_recurso_cancelado_RJ: Optional[int] = None
    # Cumprido e encaminhado como "RECURSO CANCELADO" — perda de prazo.
    retorno_cr_recurso_cancelado_RJ: Optional[int] = None
    # Meta de Provimento Mensal — processos providos (ID_2G) no período.
    provimento_mensal_qtd_RJ: Optional[int] = None
    provimento_mensal_meta_RJ: Optional[int] = None
    # Extintos · 2º Grau (painel do Recursal RJ) — no NG vêm do controle_processo_NG.
    controle_processo_extintos_com_merito_2g_qtd_recursal_RJ: Optional[int] = None
    controle_processo_extintos_com_merito_2g_valor_causa_acordao_recursal_RJ: Optional[float] = None
    controle_processo_extintos_com_merito_2g_por_tipo_sentenca_valor_acordao_recursal_RJ: Optional[List[Dict[str, Any]]] = None
    controle_processo_extintos_sem_merito_2g_qtd_recursal_RJ: Optional[int] = None
    controle_processo_extintos_sem_merito_2g_valor_causa_acordao_recursal_RJ: Optional[float] = None
    controle_processo_taxa_provimento_2g_recursal_RJ: Optional[float] = None

    # Pendências Intermediárias LA (LexFlow)
    total_atividades_intermediarias_LA: Optional[int] = None
    atividades_intermediarias_em_andamento_LA: Optional[int] = None
    atividades_intermediarias_vencidas_LA: Optional[int] = None
    atividades_intermediarias_vencem_hoje_LA: Optional[int] = None
    atividades_intermediarias_concluidas_LA: Optional[int] = None
    # Pendências Intermediárias LA — Por Prazo
    total_por_prazo_intermediarias_LA: Optional[int] = None
    por_prazo_em_andamento_intermediarias_LA: Optional[int] = None
    por_prazo_vencidas_intermediarias_LA: Optional[int] = None
    por_prazo_vencem_hoje_intermediarias_LA: Optional[int] = None
    por_prazo_concluidas_intermediarias_LA: Optional[int] = None
    # Pendências Intermediárias LA — Dilações
    dilacoes_intermediarias_total_encerrados_LA: Optional[int] = None
    dilacoes_intermediarias_count_LA: Optional[int] = None
    dilacoes_intermediarias_taxa_LA: Optional[float] = None
    dilacoes_intermediarias_faixa_LA: Optional[str] = None

    # Pendências Intermediárias NG (LexFlow)
    total_atividades_intermediarias_NG: Optional[int] = None
    atividades_intermediarias_em_andamento_NG: Optional[int] = None
    atividades_intermediarias_vencidas_NG: Optional[int] = None
    atividades_intermediarias_vencem_hoje_NG: Optional[int] = None
    atividades_intermediarias_concluidas_NG: Optional[int] = None
    # Pendências Intermediárias NG — Por Prazo
    total_por_prazo_intermediarias_NG: Optional[int] = None
    por_prazo_em_andamento_intermediarias_NG: Optional[int] = None
    por_prazo_vencidas_intermediarias_NG: Optional[int] = None
    por_prazo_vencem_hoje_intermediarias_NG: Optional[int] = None
    por_prazo_concluidas_intermediarias_NG: Optional[int] = None
    # Pendências Intermediárias NG — Dilações
    dilacoes_intermediarias_total_encerrados_NG: Optional[int] = None
    dilacoes_intermediarias_count_NG: Optional[int] = None
    dilacoes_intermediarias_taxa_NG: Optional[float] = None
    dilacoes_intermediarias_faixa_NG: Optional[str] = None

    # Emendas e Manifestações LA (LexFlow — Setor Intermediárias)
    total_atividades_emendas_manifestacoes_LA: Optional[int] = None
    atividades_emendas_manifestacoes_em_andamento_LA: Optional[int] = None
    atividades_emendas_manifestacoes_vencidas_LA: Optional[int] = None
    atividades_emendas_manifestacoes_vencem_hoje_LA: Optional[int] = None
    atividades_emendas_manifestacoes_concluidas_LA: Optional[int] = None
    # Emendas e Manifestações LA — Por Prazo
    total_por_prazo_emendas_manifestacoes_LA: Optional[int] = None
    por_prazo_em_andamento_emendas_manifestacoes_LA: Optional[int] = None
    por_prazo_vencidas_emendas_manifestacoes_LA: Optional[int] = None
    por_prazo_vencem_hoje_emendas_manifestacoes_LA: Optional[int] = None
    por_prazo_concluidas_emendas_manifestacoes_LA: Optional[int] = None

    # Emendas e Manifestações NG (LexFlow — Setor Manifestação)
    total_atividades_emendas_manifestacoes_NG: Optional[int] = None
    atividades_emendas_manifestacoes_em_andamento_NG: Optional[int] = None
    atividades_emendas_manifestacoes_vencidas_NG: Optional[int] = None
    atividades_emendas_manifestacoes_vencem_hoje_NG: Optional[int] = None
    atividades_emendas_manifestacoes_concluidas_NG: Optional[int] = None
    # Emendas e Manifestações NG — Por Prazo
    total_por_prazo_emendas_manifestacoes_NG: Optional[int] = None
    por_prazo_em_andamento_emendas_manifestacoes_NG: Optional[int] = None
    por_prazo_vencidas_emendas_manifestacoes_NG: Optional[int] = None
    por_prazo_vencem_hoje_emendas_manifestacoes_NG: Optional[int] = None
    por_prazo_concluidas_emendas_manifestacoes_NG: Optional[int] = None
    comparativo_qtd_manifestacoes_emendas_manifestacoes_NG: Optional[float] = None
    comparativo_qtd_dilacoes_emendas_manifestacoes_NG: Optional[float] = None
    emendas_manifestacoes_uf_opcoes_NG: Optional[List[str]] = None

    # Réplicas LA (LexFlow — Setor Réplicas)
    total_atividades_replicas_LA: Optional[int] = None
    atividades_replicas_em_andamento_LA: Optional[int] = None
    atividades_replicas_vencidas_LA: Optional[int] = None
    atividades_replicas_vencem_hoje_LA: Optional[int] = None
    atividades_replicas_concluidas_LA: Optional[int] = None
    # Réplicas LA — Por Prazo
    total_por_prazo_replicas_LA: Optional[int] = None
    por_prazo_em_andamento_replicas_LA: Optional[int] = None
    por_prazo_vencidas_replicas_LA: Optional[int] = None
    por_prazo_vencem_hoje_replicas_LA: Optional[int] = None
    por_prazo_concluidas_replicas_LA: Optional[int] = None
    # Réplicas LA — Taxa de procedência (1G)
    replicas_procedencia_total_processos_LA: Optional[int] = None
    replicas_procedencia_total_decididos_LA: Optional[int] = None
    replicas_procedencia_procedentes_LA: Optional[int] = None
    replicas_procedencia_pendentes_LA: Optional[int] = None
    replicas_taxa_procedencia_LA: Optional[float] = None

    # Réplicas NG (LexFlow — Setor Réplica)
    total_atividades_replicas_NG: Optional[int] = None
    atividades_replicas_em_andamento_NG: Optional[int] = None
    atividades_replicas_vencidas_NG: Optional[int] = None
    atividades_replicas_vencem_hoje_NG: Optional[int] = None
    atividades_replicas_concluidas_NG: Optional[int] = None
    # Réplicas NG — Por Prazo
    total_por_prazo_replicas_NG: Optional[int] = None
    por_prazo_em_andamento_replicas_NG: Optional[int] = None
    por_prazo_vencidas_replicas_NG: Optional[int] = None
    por_prazo_vencem_hoje_replicas_NG: Optional[int] = None
    por_prazo_concluidas_replicas_NG: Optional[int] = None
    # Réplicas NG — Taxa de procedência (1G)
    replicas_procedencia_total_processos_NG: Optional[int] = None
    replicas_procedencia_total_decididos_NG: Optional[int] = None
    replicas_procedencia_procedentes_NG: Optional[int] = None
    replicas_procedencia_pendentes_NG: Optional[int] = None
    replicas_taxa_procedencia_NG: Optional[float] = None
    # Reajuizamento LA (LexFlow — Setor Reajuizamento)
    total_atividades_reajuizamento_LA: Optional[int] = None
    atividades_reajuizamento_em_andamento_LA: Optional[int] = None
    atividades_reajuizamento_vencidas_LA: Optional[int] = None
    atividades_reajuizamento_vencem_hoje_LA: Optional[int] = None
    atividades_reajuizamento_concluidas_LA: Optional[int] = None
    # Reajuizamento LA — Decisão em "Avaliar Reajuizamento"
    reajuizamento_decisao_total_avaliadas_LA: Optional[int] = None
    reajuizamento_decisao_reajuizar_LA: Optional[int] = None
    reajuizamento_decisao_nao_reajuizar_LA: Optional[int] = None
    reajuizamento_taxa_decisao_reajuizar_LA: Optional[float] = None
    reajuizamento_ja_reajuizados_LA: Optional[int] = None

    # Controle de Processo LA (LexFlow)
    total_controle_processo_LA: Optional[int] = None
    controle_processo_situacao_filtro_LA: Optional[str] = None
    controle_processo_fase_filtro_LA: Optional[str] = None
    controle_processo_total_na_fase_LA: Optional[int] = None
    controle_processo_qtd_subfases_na_fase_LA: Optional[int] = None
    controle_processo_fase_inicial_qtd_LA: Optional[int] = None
    controle_processo_fase_inicial_valor_causa_LA: Optional[float] = None
    controle_processo_fase_recursal_qtd_LA: Optional[int] = None
    controle_processo_fase_recursal_valor_causa_LA: Optional[float] = None
    controle_processo_fase_execucao_qtd_LA: Optional[int] = None
    controle_processo_fase_execucao_valor_causa_execucao_LA: Optional[float] = None
    controle_processo_fase_arquivado_procedente_qtd_LA: Optional[int] = None
    controle_processo_fase_arquivado_procedente_valor_causa_LA: Optional[float] = None
    controle_processo_fase_arquivado_improcedente_qtd_LA: Optional[int] = None
    controle_processo_fase_arquivado_improcedente_valor_causa_LA: Optional[float] = None
    controle_processo_fase_transito_julgado_qtd_LA: Optional[int] = None
    controle_processo_fase_transito_julgado_valor_causa_LA: Optional[float] = None
    controle_processo_extintos_com_merito_qtd_LA: Optional[int] = None
    controle_processo_extintos_com_merito_valor_causa_LA: Optional[float] = None
    controle_processo_extintos_com_merito_por_tipo_sentenca_LA: Optional[List[Dict[str, Any]]] = None
    controle_processo_extintos_com_merito_2g_qtd_LA: Optional[int] = None
    controle_processo_extintos_com_merito_2g_valor_causa_LA: Optional[float] = None
    controle_processo_extintos_com_merito_2g_por_tipo_sentenca_LA: Optional[List[Dict[str, Any]]] = None
    controle_processo_extintos_com_merito_2g_valor_causa_acordao_LA: Optional[float] = None
    controle_processo_extintos_com_merito_2g_por_tipo_sentenca_valor_acordao_LA: Optional[List[Dict[str, Any]]] = None
    controle_processo_extintos_sem_merito_qtd_LA: Optional[int] = None
    controle_processo_extintos_sem_merito_valor_causa_LA: Optional[float] = None
    controle_processo_extintos_sem_merito_2g_qtd_LA: Optional[int] = None
    controle_processo_extintos_sem_merito_2g_valor_causa_LA: Optional[float] = None
    controle_processo_extintos_sem_merito_2g_valor_causa_acordao_LA: Optional[float] = None
    controle_processo_taxa_provimento_2g_LA: Optional[float] = None
    # Recursal (todas as situações, inclui arquivado) — usado só pelo painel Extintos do Recursal.
    controle_processo_extintos_com_merito_2g_qtd_recursal_LA: Optional[int] = None
    controle_processo_extintos_com_merito_2g_valor_causa_acordao_recursal_LA: Optional[float] = None
    controle_processo_extintos_com_merito_2g_por_tipo_sentenca_valor_acordao_recursal_LA: Optional[List[Dict[str, Any]]] = None
    controle_processo_extintos_sem_merito_2g_qtd_recursal_LA: Optional[int] = None
    controle_processo_extintos_sem_merito_2g_valor_causa_acordao_recursal_LA: Optional[float] = None
    controle_processo_taxa_provimento_2g_recursal_LA: Optional[float] = None
    controle_processo_log_inicial_indeferida_qtd_LA: Optional[int] = None
    controle_processo_log_inicial_indeferida_valor_causa_LA: Optional[float] = None
    controle_processo_log_recursal_nao_provido_qtd_LA: Optional[int] = None
    controle_processo_log_recursal_nao_provido_valor_causa_LA: Optional[float] = None
    controle_processo_fase_inicial_media_dias_LA: Optional[float] = None
    controle_processo_fase_recursal_media_dias_LA: Optional[float] = None
    controle_processo_fase_execucao_media_dias_LA: Optional[float] = None
    controle_processo_fase_inicial_mediana_dias_LA: Optional[float] = None
    controle_processo_fase_recursal_mediana_dias_LA: Optional[float] = None
    controle_processo_fase_execucao_mediana_dias_LA: Optional[float] = None
    controle_processo_fase_inicial_comparativo_media_dias_LA: Optional[float] = None
    controle_processo_fase_recursal_comparativo_media_dias_LA: Optional[float] = None
    controle_processo_fase_execucao_comparativo_media_dias_LA: Optional[float] = None
    controle_processo_fase_inicial_comparativo_mediana_dias_LA: Optional[float] = None
    controle_processo_fase_recursal_comparativo_mediana_dias_LA: Optional[float] = None
    controle_processo_fase_execucao_comparativo_mediana_dias_LA: Optional[float] = None

    total_controle_processo_NG: Optional[int] = None
    controle_processo_valor_causa_total_NG: Optional[float] = None
    controle_processo_situacao_filtro_NG: Optional[str] = None
    controle_processo_uf_filtro_NG: Optional[List[str]] = None
    controle_processo_uf_opcoes_NG: Optional[List[str]] = None
    controle_processo_fase_filtro_NG: Optional[str] = None
    controle_processo_total_na_fase_NG: Optional[int] = None
    controle_processo_qtd_subfases_na_fase_NG: Optional[int] = None
    controle_processo_fase_inicial_qtd_NG: Optional[int] = None
    controle_processo_fase_inicial_valor_causa_NG: Optional[float] = None
    controle_processo_fase_recursal_qtd_NG: Optional[int] = None
    controle_processo_fase_recursal_valor_causa_NG: Optional[float] = None
    controle_processo_fase_execucao_qtd_NG: Optional[int] = None
    controle_processo_fase_execucao_valor_causa_execucao_NG: Optional[float] = None
    controle_processo_fase_arquivado_procedente_qtd_NG: Optional[int] = None
    controle_processo_fase_arquivado_procedente_valor_causa_NG: Optional[float] = None
    controle_processo_fase_arquivado_improcedente_qtd_NG: Optional[int] = None
    controle_processo_fase_arquivado_improcedente_valor_causa_NG: Optional[float] = None
    controle_processo_fase_transito_julgado_qtd_NG: Optional[int] = None
    controle_processo_fase_transito_julgado_valor_causa_NG: Optional[float] = None
    controle_processo_extintos_com_merito_qtd_NG: Optional[int] = None
    controle_processo_extintos_com_merito_valor_causa_NG: Optional[float] = None
    controle_processo_extintos_com_merito_por_tipo_sentenca_NG: Optional[List[Dict[str, Any]]] = None
    controle_processo_extintos_com_merito_2g_qtd_NG: Optional[int] = None
    controle_processo_extintos_com_merito_2g_valor_causa_NG: Optional[float] = None
    controle_processo_extintos_com_merito_2g_por_tipo_sentenca_NG: Optional[List[Dict[str, Any]]] = None
    controle_processo_extintos_com_merito_2g_valor_causa_acordao_NG: Optional[float] = None
    controle_processo_extintos_com_merito_2g_por_tipo_sentenca_valor_acordao_NG: Optional[List[Dict[str, Any]]] = None
    controle_processo_extintos_sem_merito_qtd_NG: Optional[int] = None
    controle_processo_extintos_sem_merito_valor_causa_NG: Optional[float] = None
    controle_processo_extintos_sem_merito_2g_qtd_NG: Optional[int] = None
    controle_processo_extintos_sem_merito_2g_valor_causa_NG: Optional[float] = None
    controle_processo_extintos_sem_merito_2g_valor_causa_acordao_NG: Optional[float] = None
    controle_processo_taxa_provimento_2g_NG: Optional[float] = None
    # Recursal (todas as situações, inclui arquivado) — usado só pelo painel Extintos do Recursal.
    controle_processo_extintos_com_merito_2g_qtd_recursal_NG: Optional[int] = None
    controle_processo_extintos_com_merito_2g_valor_causa_acordao_recursal_NG: Optional[float] = None
    controle_processo_extintos_com_merito_2g_por_tipo_sentenca_valor_acordao_recursal_NG: Optional[List[Dict[str, Any]]] = None
    controle_processo_extintos_sem_merito_2g_qtd_recursal_NG: Optional[int] = None
    controle_processo_extintos_sem_merito_2g_valor_causa_acordao_recursal_NG: Optional[float] = None
    controle_processo_taxa_provimento_2g_recursal_NG: Optional[float] = None
    controle_processo_log_inicial_indeferida_qtd_NG: Optional[int] = None
    controle_processo_log_inicial_indeferida_valor_causa_NG: Optional[float] = None
    controle_processo_log_recursal_nao_provido_qtd_NG: Optional[int] = None
    controle_processo_log_recursal_nao_provido_valor_causa_NG: Optional[float] = None
    controle_processo_fase_inicial_media_dias_NG: Optional[float] = None
    controle_processo_fase_recursal_media_dias_NG: Optional[float] = None
    controle_processo_fase_execucao_media_dias_NG: Optional[float] = None
    controle_processo_fase_inicial_mediana_dias_NG: Optional[float] = None
    controle_processo_fase_recursal_mediana_dias_NG: Optional[float] = None
    controle_processo_fase_execucao_mediana_dias_NG: Optional[float] = None
    controle_processo_fase_inicial_comparativo_media_dias_NG: Optional[float] = None
    controle_processo_fase_recursal_comparativo_media_dias_NG: Optional[float] = None
    controle_processo_fase_execucao_comparativo_media_dias_NG: Optional[float] = None
    controle_processo_fase_inicial_comparativo_mediana_dias_NG: Optional[float] = None
    controle_processo_fase_recursal_comparativo_mediana_dias_NG: Optional[float] = None
    controle_processo_fase_execucao_comparativo_mediana_dias_NG: Optional[float] = None

    # Pendências LA
    pendencias_total_LA: Optional[int] = None
    pendencias_nao_resolvidas_LA: Optional[int] = None
    pendencias_nao_resolvidas_com_atraso_LA: Optional[int] = None
    pendencias_resolvidas_LA: Optional[int] = None
    pendencias_canceladas_LA: Optional[int] = None
    pendencias_taxa_nao_resolvidos_LA: Optional[float] = None
    pendencias_taxa_resolvidos_LA: Optional[float] = None
    pendencias_taxa_canceladas_LA: Optional[float] = None
    pendencias_triagem_LA: Optional[int] = None
    media_tempo_resolvidos_pendencia_LA: Optional[float] = None
    mediana_tempo_resolvidos_pendencia_LA: Optional[float] = None
    comparativo_pendencias_resolvidas_LA: Optional[float] = None
    comparativo_tempo_medio_pendencias_resolvidas_LA: Optional[float] = None

    # Publicações LA (LexFlow)
    publicacoes_recebidas_periodo_LA: Optional[int] = None
    publicacoes_tratadas_periodo_LA: Optional[int] = None
    publicacoes_pendentes_LA: Optional[int] = None
    media_tempo_tratamento_publicacoes_LA: Optional[float] = None
    publicacoes_com_data_disponibilizacao_LA: Optional[int] = None
    publicacoes_cumpridas_mesmo_dia_chegada_LA: Optional[int] = None
    pct_tratadas_mesmo_dia_publicacoes_LA: Optional[float] = None
    dia_referencia_publicacoes_LA: Optional[str] = None
    publicacoes_tratadas_ultimo_dia_LA: Optional[int] = None
    publicacoes_recebidas_dia_referencia_LA: Optional[int] = None
    publicacoes_cumpridas_mesmo_dia_dia_referencia_LA: Optional[int] = None
    publicacoes_recebidas_hoje_LA: Optional[int] = None
    publicacoes_com_agendamento_apos_finalizacao_LA: Optional[int] = None
    publicacoes_sem_agendamento_apos_finalizacao_LA: Optional[int] = None
    publicacoes_pendentes_zeradas_no_periodo_LA: Optional[int] = None

    # Publicações NG (LexFlow)
    publicacoes_recebidas_periodo_NG: Optional[int] = None
    publicacoes_tratadas_periodo_NG: Optional[int] = None
    publicacoes_pendentes_NG: Optional[int] = None
    media_tempo_tratamento_publicacoes_NG: Optional[float] = None
    publicacoes_com_data_disponibilizacao_NG: Optional[int] = None
    publicacoes_cumpridas_mesmo_dia_chegada_NG: Optional[int] = None
    pct_tratadas_mesmo_dia_publicacoes_NG: Optional[float] = None
    dia_referencia_publicacoes_NG: Optional[str] = None
    publicacoes_tratadas_ultimo_dia_NG: Optional[int] = None
    publicacoes_recebidas_dia_referencia_NG: Optional[int] = None
    publicacoes_cumpridas_mesmo_dia_dia_referencia_NG: Optional[int] = None
    publicacoes_recebidas_hoje_NG: Optional[int] = None
    publicacoes_com_agendamento_apos_finalizacao_NG: Optional[int] = None
    publicacoes_sem_agendamento_apos_finalizacao_NG: Optional[int] = None
    publicacoes_pendentes_zeradas_no_periodo_NG: Optional[int] = None

    # Publicações RJ (LexFlow)
    publicacoes_recebidas_periodo_RJ: Optional[int] = None
    publicacoes_tratadas_periodo_RJ: Optional[int] = None
    publicacoes_pendentes_RJ: Optional[int] = None
    media_tempo_tratamento_publicacoes_RJ: Optional[float] = None
    publicacoes_com_data_disponibilizacao_RJ: Optional[int] = None
    publicacoes_cumpridas_mesmo_dia_chegada_RJ: Optional[int] = None
    pct_tratadas_mesmo_dia_publicacoes_RJ: Optional[float] = None
    dia_referencia_publicacoes_RJ: Optional[str] = None
    publicacoes_tratadas_ultimo_dia_RJ: Optional[int] = None
    publicacoes_recebidas_dia_referencia_RJ: Optional[int] = None
    publicacoes_cumpridas_mesmo_dia_dia_referencia_RJ: Optional[int] = None
    publicacoes_recebidas_hoje_RJ: Optional[int] = None
    publicacoes_com_agendamento_apos_finalizacao_RJ: Optional[int] = None
    publicacoes_sem_agendamento_apos_finalizacao_RJ: Optional[int] = None
    publicacoes_pendentes_zeradas_no_periodo_RJ: Optional[int] = None

    # NPS NG
    nps_total_respostas: Optional[int] = None
    nps_score: Optional[float] = None
    nps_taxa_confianca: Optional[float] = None
    nps_nivel_informacao: Optional[float] = None
    nps_nivel_indicacao: Optional[float] = None
    nps_media_tempo_resposta: Optional[float] = None
    nps_total_promotores: Optional[int] = None
    nps_total_neutros: Optional[int] = None
    nps_total_detratores: Optional[int] = None

    # Marketing NG
    marketing_ng_total_clientes: Optional[int] = None
    marketing_ng_media_idade: Optional[float] = None
    marketing_ng_triados_total_clientes: Optional[int] = None
    marketing_ng_triados_media_idade: Optional[float] = None
    marketing_ng_facebook_cliques: Optional[int] = None
    marketing_ng_facebook_pageview: Optional[int] = None
    marketing_ng_facebook_leads: Optional[int] = None
    marketing_ng_facebook_valor_gasto: Optional[float] = None
    marketing_ng_facebook_cac_campanha: Optional[float] = None
    marketing_ng_facebook_cac_geral: Optional[float] = None
    marketing_ng_facebook_roas_campanha: Optional[float] = None
    marketing_ng_facebook_roas_geral: Optional[float] = None
    marketing_ng_clientes_campanha: Optional[int] = None
    marketing_ng_leads: Optional[int] = None
    marketing_ng_indicacao_ativa: Optional[int] = None
    marketing_ng_indicacao_passiva: Optional[int] = None
    marketing_ng_retorno_ativa: Optional[int] = None
    marketing_ng_retorno_passiva: Optional[int] = None
    marketing_ng_campanha_ra: Optional[int] = None
    marketing_ng_campanha_ng: Optional[int] = None
    marketing_ng_conversao_ra: Optional[float] = None
    marketing_ng_conversao_ng: Optional[float] = None
    marketing_ng_protocolados_ra: Optional[int] = None
    marketing_ng_protocolados_ng: Optional[int] = None
    marketing_ng_valor_causa_ra: Optional[float] = None
    marketing_ng_valor_causa_ng: Optional[float] = None
    marketing_ng_ticket_medio_ra: Optional[float] = None
    marketing_ng_ticket_medio_ng: Optional[float] = None
    marketing_ng_total_trackeamento: Optional[int] = None
    marketing_ng_processos_assinados: Optional[int] = None
    marketing_ng_leads_ng: Optional[int] = None
    marketing_ng_acoes_ng: Optional[int] = None
    marketing_ng_aproveitamento_ng: Optional[float] = None
    marketing_ng_cpl_ng: Optional[float] = None
    marketing_ng_org_leads_facebook: Optional[int] = None
    marketing_ng_org_leads_instagram: Optional[int] = None
    marketing_ng_org_leads_site: Optional[int] = None
    marketing_ng_org_leads_google: Optional[int] = None
    marketing_ng_org_total_leads: Optional[int] = None
    marketing_ng_org_contratos: Optional[int] = None
    marketing_ng_org_acoes: Optional[int] = None
    marketing_ng_org_aproveitamento: Optional[float] = None
    marketing_ng_org_taxa_fechamento: Optional[float] = None
    marketing_ng_org_valor_causa: Optional[float] = None
    marketing_ng_org_ticket_medio: Optional[float] = None

    # Marketing LexPre NG (perfil de clientes)
    marketing_lexpre_ng_total_clientes: Optional[int] = None
    marketing_lexpre_ng_media_idade: Optional[float] = None
    marketing_lexpre_ng_triados_total_clientes: Optional[int] = None
    marketing_lexpre_ng_triados_media_idade: Optional[float] = None
    marketing_lexpre_ng_facebook_cliques: Optional[int] = None
    marketing_lexpre_ng_facebook_pageview: Optional[int] = None
    marketing_lexpre_ng_facebook_leads: Optional[int] = None
    marketing_lexpre_ng_facebook_valor_gasto: Optional[float] = None
    marketing_lexpre_ng_facebook_cac_campanha: Optional[float] = None
    marketing_lexpre_ng_facebook_cac_geral: Optional[float] = None
    marketing_lexpre_ng_facebook_roas_campanha: Optional[float] = None
    marketing_lexpre_ng_facebook_roas_geral: Optional[float] = None
    marketing_lexpre_ng_clientes_campanha: Optional[int] = None
    marketing_lexpre_ng_leads: Optional[int] = None
    marketing_lexpre_ng_indicacao_ativa: Optional[int] = None
    marketing_lexpre_ng_indicacao_passiva: Optional[int] = None
    marketing_lexpre_ng_retorno_ativa: Optional[int] = None
    marketing_lexpre_ng_retorno_passiva: Optional[int] = None
    marketing_lexpre_ng_campanha: Optional[int] = None
    marketing_lexpre_ng_conversao_campanha: Optional[float] = None
    marketing_lexpre_ng_protocolados_campanha: Optional[int] = None
    marketing_lexpre_ng_valor_causa_campanha: Optional[float] = None
    marketing_lexpre_ng_ticket_medio_campanha: Optional[float] = None
    marketing_lexpre_ng_total_trackeamento: Optional[int] = None
    marketing_lexpre_ng_processos_assinados: Optional[int] = None
    marketing_lexpre_ng_leads_campanha: Optional[int] = None
    marketing_lexpre_ng_acoes_campanha: Optional[int] = None
    marketing_lexpre_ng_aproveitamento_campanha: Optional[float] = None
    marketing_lexpre_ng_cpl_campanha: Optional[float] = None
    marketing_lexpre_ng_org_leads_facebook: Optional[int] = None
    marketing_lexpre_ng_org_leads_instagram: Optional[int] = None
    marketing_lexpre_ng_org_leads_site: Optional[int] = None
    marketing_lexpre_ng_org_leads_google: Optional[int] = None
    marketing_lexpre_ng_org_total_leads: Optional[int] = None
    marketing_lexpre_ng_org_contratos: Optional[int] = None
    marketing_lexpre_ng_org_acoes: Optional[int] = None
    marketing_lexpre_ng_org_aproveitamento: Optional[float] = None
    marketing_lexpre_ng_org_taxa_fechamento: Optional[float] = None
    marketing_lexpre_ng_org_valor_causa: Optional[float] = None
    marketing_lexpre_ng_org_ticket_medio: Optional[float] = None

    # Julgados NG
    julgados_sentenca_total_NG: Optional[int] = None
    julgados_sentenca_procedentes_NG: Optional[int] = None
    julgados_sentenca_improcedentes_NG: Optional[int] = None
    julgados_sentenca_extintos_NG: Optional[int] = None
    julgados_sentenca_tempo_medio_dias_NG: Optional[float] = None
    julgados_sentenca_embargos_tempo_medio_dias_NG: Optional[float] = None
    julgados_sentenca_valor_procedentes_NG: Optional[float] = None
    julgados_sentenca_embargados_NG: Optional[int] = None
    julgados_sentenca_revertidos_NG: Optional[int] = None
    comparativo_julgados_sentenca_total_NG: Optional[float] = None
    comparativo_julgados_sentenca_procedentes_NG: Optional[float] = None
    comparativo_julgados_sentenca_improcedentes_NG: Optional[float] = None
    comparativo_julgados_sentenca_extintos_NG: Optional[float] = None
    comparativo_julgados_sentenca_tempo_medio_dias_NG: Optional[float] = None
    comparativo_julgados_sentenca_valor_procedentes_NG: Optional[float] = None
    comparativo_julgados_sentenca_embargados_NG: Optional[float] = None
    comparativo_julgados_sentenca_revertidos_NG: Optional[float] = None
    julgados_uf_opcoes_NG: Optional[List[str]] = None
    julgados_sentenca_sem_juiz_NG: Optional[int] = None
    julgados_sentenca_sem_materia_NG: Optional[int] = None
    julgados_sentenca_sem_comarca_NG: Optional[int] = None
    julgados_sentenca_sem_competencia_NG: Optional[int] = None
    julgados_sentenca_sem_uf_NG: Optional[int] = None
    julgados_sentenca_sem_valor_pe_NG: Optional[int] = None
    julgados_sentenca_merito_sem_data_NG: Optional[int] = None
    julgados_sentenca_data_sem_merito_NG: Optional[int] = None
    julgados_sentenca_dados_faltando_NG: Optional[List[ProcessoDadoFaltando]] = None
    # Julgados Sentenças NG — Estudos de Extinção
    julgados_extincao_valor_NG: Optional[float] = None
    julgados_extincao_total_estoque_NG: Optional[int] = None
    julgados_extincao_valor_estoque_NG: Optional[float] = None
    julgados_comarca_opcoes_NG: Optional[List[str]] = None
    julgados_sentenca_total_estoque_NG: Optional[int] = None
    julgados_extincao_revertida_2g_NG: Optional[int] = None
    julgados_extincao_revertida_2g_estoque_NG: Optional[int] = None
    # Julgados Sentenças NG — Estudo das Improcedências (11/11/2026)
    julgados_improcedencia_valor_NG: Optional[float] = None
    julgados_improcedencia_total_estoque_NG: Optional[int] = None
    julgados_improcedencia_valor_estoque_NG: Optional[float] = None
    julgados_improcedencia_revertida_2g_NG: Optional[int] = None
    julgados_improcedencia_revertida_2g_estoque_NG: Optional[int] = None
    # Julgados Acórdãos NG
    julgados_acordao_total_NG: Optional[int] = None
    julgados_acordao_procedentes_NG: Optional[int] = None
    julgados_acordao_improcedentes_NG: Optional[int] = None
    julgados_acordao_extintos_NG: Optional[int] = None
    julgados_acordao_nao_classificados_NG: Optional[int] = None
    julgados_acordao_tempo_medio_dias_NG: Optional[float] = None
    julgados_acordao_embargos_tempo_medio_dias_NG: Optional[float] = None
    julgados_acordao_valor_procedentes_NG: Optional[float] = None
    julgados_acordao_valor_fixado_procedentes_NG: Optional[float] = None
    julgados_acordao_embargados_NG: Optional[int] = None
    julgados_acordao_revertidos_NG: Optional[int] = None
    comparativo_julgados_acordao_total_NG: Optional[float] = None
    comparativo_julgados_acordao_procedentes_NG: Optional[float] = None
    comparativo_julgados_acordao_improcedentes_NG: Optional[float] = None
    comparativo_julgados_acordao_extintos_NG: Optional[float] = None
    comparativo_julgados_acordao_nao_classificados_NG: Optional[float] = None
    comparativo_julgados_acordao_tempo_medio_dias_NG: Optional[float] = None
    comparativo_julgados_acordao_valor_procedentes_NG: Optional[float] = None
    comparativo_julgados_acordao_valor_fixado_procedentes_NG: Optional[float] = None
    comparativo_julgados_acordao_embargados_NG: Optional[float] = None
    comparativo_julgados_acordao_revertidos_NG: Optional[float] = None
    julgados_acordao_uf_opcoes_NG: Optional[List[str]] = None
    julgados_acordao_sem_relator_NG: Optional[int] = None
    julgados_acordao_sem_materia_NG: Optional[int] = None
    julgados_acordao_sem_comarca_NG: Optional[int] = None
    julgados_acordao_sem_competencia_NG: Optional[int] = None
    julgados_acordao_sem_uf_NG: Optional[int] = None
    julgados_acordao_sem_valor_pe_NG: Optional[int] = None
    julgados_acordao_merito_sem_data_NG: Optional[int] = None
    julgados_acordao_data_sem_merito_NG: Optional[int] = None
    julgados_acordao_dados_faltando_NG: Optional[List[ProcessoDadoFaltando]] = None
    # Julgados Acórdãos NG — Estudo das Improcedências (11/11/2026)
    julgados_acordao_improcedencia_valor_NG: Optional[float] = None
    julgados_acordao_improcedencia_total_estoque_NG: Optional[int] = None
    julgados_acordao_improcedencia_valor_estoque_NG: Optional[float] = None
    julgados_acordao_improcedencia_stj_NG: Optional[int] = None
    julgados_acordao_improcedencia_stf_NG: Optional[int] = None
    julgados_acordao_improcedencia_stj_estoque_NG: Optional[int] = None
    julgados_acordao_improcedencia_stf_estoque_NG: Optional[int] = None
    julgados_acordao_total_estoque_NG: Optional[int] = None
    # Julgados Sentenças LA
    julgados_sentenca_total_LA: Optional[int] = None
    julgados_sentenca_procedentes_LA: Optional[int] = None
    julgados_sentenca_improcedentes_LA: Optional[int] = None
    julgados_sentenca_extintos_LA: Optional[int] = None
    julgados_sentenca_tempo_medio_dias_LA: Optional[float] = None
    julgados_sentenca_embargos_tempo_medio_dias_LA: Optional[float] = None
    julgados_sentenca_valor_procedentes_LA: Optional[float] = None
    julgados_sentenca_embargados_LA: Optional[int] = None
    julgados_sentenca_revertidos_LA: Optional[int] = None
    comparativo_julgados_sentenca_total_LA: Optional[float] = None
    comparativo_julgados_sentenca_procedentes_LA: Optional[float] = None
    comparativo_julgados_sentenca_improcedentes_LA: Optional[float] = None
    comparativo_julgados_sentenca_extintos_LA: Optional[float] = None
    comparativo_julgados_sentenca_tempo_medio_dias_LA: Optional[float] = None
    comparativo_julgados_sentenca_valor_procedentes_LA: Optional[float] = None
    comparativo_julgados_sentenca_embargados_LA: Optional[float] = None
    comparativo_julgados_sentenca_revertidos_LA: Optional[float] = None
    julgados_uf_opcoes_LA: Optional[List[str]] = None
    julgados_sentenca_sem_juiz_LA: Optional[int] = None
    julgados_sentenca_sem_materia_LA: Optional[int] = None
    julgados_sentenca_sem_comarca_LA: Optional[int] = None
    julgados_sentenca_sem_competencia_LA: Optional[int] = None
    julgados_sentenca_sem_uf_LA: Optional[int] = None
    julgados_sentenca_sem_valor_pe_LA: Optional[int] = None
    julgados_sentenca_merito_sem_data_LA: Optional[int] = None
    julgados_sentenca_data_sem_merito_LA: Optional[int] = None
    julgados_sentenca_dados_faltando_LA: Optional[List[ProcessoDadoFaltando]] = None
    # Julgados Sentenças LA — Estudos de Extinção
    julgados_extincao_valor_LA: Optional[float] = None
    julgados_extincao_total_estoque_LA: Optional[int] = None
    julgados_extincao_valor_estoque_LA: Optional[float] = None
    julgados_comarca_opcoes_LA: Optional[List[str]] = None
    julgados_sentenca_total_estoque_LA: Optional[int] = None
    julgados_extincao_revertida_2g_LA: Optional[int] = None
    julgados_extincao_revertida_2g_estoque_LA: Optional[int] = None
    # Julgados Sentenças LA — Estudo das Improcedências (11/11/2026)
    julgados_improcedencia_valor_LA: Optional[float] = None
    julgados_improcedencia_total_estoque_LA: Optional[int] = None
    julgados_improcedencia_valor_estoque_LA: Optional[float] = None
    julgados_improcedencia_revertida_2g_LA: Optional[int] = None
    julgados_improcedencia_revertida_2g_estoque_LA: Optional[int] = None
    # Julgados Sentenças RJ
    julgados_sentenca_total_RJ: Optional[int] = None
    julgados_sentenca_procedentes_RJ: Optional[int] = None
    julgados_sentenca_improcedentes_RJ: Optional[int] = None
    julgados_sentenca_extintos_RJ: Optional[int] = None
    julgados_sentenca_tempo_medio_dias_RJ: Optional[float] = None
    julgados_sentenca_embargos_tempo_medio_dias_RJ: Optional[float] = None
    julgados_sentenca_valor_procedentes_RJ: Optional[float] = None
    julgados_sentenca_embargados_RJ: Optional[int] = None
    julgados_sentenca_revertidos_RJ: Optional[int] = None
    comparativo_julgados_sentenca_total_RJ: Optional[float] = None
    comparativo_julgados_sentenca_procedentes_RJ: Optional[float] = None
    comparativo_julgados_sentenca_improcedentes_RJ: Optional[float] = None
    comparativo_julgados_sentenca_extintos_RJ: Optional[float] = None
    comparativo_julgados_sentenca_tempo_medio_dias_RJ: Optional[float] = None
    comparativo_julgados_sentenca_valor_procedentes_RJ: Optional[float] = None
    comparativo_julgados_sentenca_embargados_RJ: Optional[float] = None
    comparativo_julgados_sentenca_revertidos_RJ: Optional[float] = None
    julgados_uf_opcoes_RJ: Optional[List[str]] = None
    julgados_sentenca_sem_juiz_RJ: Optional[int] = None
    julgados_sentenca_sem_materia_RJ: Optional[int] = None
    julgados_sentenca_sem_comarca_RJ: Optional[int] = None
    julgados_sentenca_sem_competencia_RJ: Optional[int] = None
    julgados_sentenca_sem_uf_RJ: Optional[int] = None
    julgados_sentenca_sem_valor_pe_RJ: Optional[int] = None
    julgados_sentenca_merito_sem_data_RJ: Optional[int] = None
    julgados_sentenca_data_sem_merito_RJ: Optional[int] = None
    julgados_sentenca_dados_faltando_RJ: Optional[List[ProcessoDadoFaltando]] = None
    # Julgados Sentenças RJ — Estudos de Extinção
    julgados_extincao_valor_RJ: Optional[float] = None
    julgados_extincao_total_estoque_RJ: Optional[int] = None
    julgados_extincao_valor_estoque_RJ: Optional[float] = None
    julgados_comarca_opcoes_RJ: Optional[List[str]] = None
    julgados_sentenca_total_estoque_RJ: Optional[int] = None
    julgados_extincao_revertida_2g_RJ: Optional[int] = None
    julgados_extincao_revertida_2g_estoque_RJ: Optional[int] = None
    # Julgados Sentenças RJ — Estudo das Improcedências (11/11/2026)
    julgados_improcedencia_valor_RJ: Optional[float] = None
    julgados_improcedencia_total_estoque_RJ: Optional[int] = None
    julgados_improcedencia_valor_estoque_RJ: Optional[float] = None
    julgados_improcedencia_revertida_2g_RJ: Optional[int] = None
    julgados_improcedencia_revertida_2g_estoque_RJ: Optional[int] = None
    # Julgados Acórdãos LA
    julgados_acordao_total_LA: Optional[int] = None
    julgados_acordao_procedentes_LA: Optional[int] = None
    julgados_acordao_improcedentes_LA: Optional[int] = None
    julgados_acordao_extintos_LA: Optional[int] = None
    julgados_acordao_nao_classificados_LA: Optional[int] = None
    julgados_acordao_tempo_medio_dias_LA: Optional[float] = None
    julgados_acordao_embargos_tempo_medio_dias_LA: Optional[float] = None
    julgados_acordao_valor_procedentes_LA: Optional[float] = None
    julgados_acordao_valor_fixado_procedentes_LA: Optional[float] = None
    julgados_acordao_embargados_LA: Optional[int] = None
    julgados_acordao_revertidos_LA: Optional[int] = None
    comparativo_julgados_acordao_total_LA: Optional[float] = None
    comparativo_julgados_acordao_procedentes_LA: Optional[float] = None
    comparativo_julgados_acordao_improcedentes_LA: Optional[float] = None
    comparativo_julgados_acordao_extintos_LA: Optional[float] = None
    comparativo_julgados_acordao_nao_classificados_LA: Optional[float] = None
    comparativo_julgados_acordao_tempo_medio_dias_LA: Optional[float] = None
    comparativo_julgados_acordao_valor_procedentes_LA: Optional[float] = None
    comparativo_julgados_acordao_valor_fixado_procedentes_LA: Optional[float] = None
    comparativo_julgados_acordao_embargados_LA: Optional[float] = None
    comparativo_julgados_acordao_revertidos_LA: Optional[float] = None
    julgados_acordao_uf_opcoes_LA: Optional[List[str]] = None
    julgados_acordao_sem_relator_LA: Optional[int] = None
    julgados_acordao_sem_materia_LA: Optional[int] = None
    julgados_acordao_sem_comarca_LA: Optional[int] = None
    julgados_acordao_sem_competencia_LA: Optional[int] = None
    julgados_acordao_sem_uf_LA: Optional[int] = None
    julgados_acordao_sem_valor_pe_LA: Optional[int] = None
    julgados_acordao_merito_sem_data_LA: Optional[int] = None
    julgados_acordao_data_sem_merito_LA: Optional[int] = None
    julgados_acordao_dados_faltando_LA: Optional[List[ProcessoDadoFaltando]] = None
    # Julgados Acórdãos LA — Estudo das Improcedências (11/11/2026)
    julgados_acordao_improcedencia_valor_LA: Optional[float] = None
    julgados_acordao_improcedencia_total_estoque_LA: Optional[int] = None
    julgados_acordao_improcedencia_valor_estoque_LA: Optional[float] = None
    julgados_acordao_total_estoque_LA: Optional[int] = None
    # Julgados Acórdãos RJ
    julgados_acordao_total_RJ: Optional[int] = None
    julgados_acordao_procedentes_RJ: Optional[int] = None
    julgados_acordao_improcedentes_RJ: Optional[int] = None
    julgados_acordao_extintos_RJ: Optional[int] = None
    julgados_acordao_nao_classificados_RJ: Optional[int] = None
    julgados_acordao_tempo_medio_dias_RJ: Optional[float] = None
    julgados_acordao_embargos_tempo_medio_dias_RJ: Optional[float] = None
    julgados_acordao_valor_procedentes_RJ: Optional[float] = None
    julgados_acordao_valor_fixado_procedentes_RJ: Optional[float] = None
    julgados_acordao_embargados_RJ: Optional[int] = None
    julgados_acordao_revertidos_RJ: Optional[int] = None
    comparativo_julgados_acordao_total_RJ: Optional[float] = None
    comparativo_julgados_acordao_procedentes_RJ: Optional[float] = None
    comparativo_julgados_acordao_improcedentes_RJ: Optional[float] = None
    comparativo_julgados_acordao_extintos_RJ: Optional[float] = None
    comparativo_julgados_acordao_nao_classificados_RJ: Optional[float] = None
    comparativo_julgados_acordao_tempo_medio_dias_RJ: Optional[float] = None
    comparativo_julgados_acordao_valor_procedentes_RJ: Optional[float] = None
    comparativo_julgados_acordao_valor_fixado_procedentes_RJ: Optional[float] = None
    comparativo_julgados_acordao_embargados_RJ: Optional[float] = None
    comparativo_julgados_acordao_revertidos_RJ: Optional[float] = None
    julgados_acordao_uf_opcoes_RJ: Optional[List[str]] = None
    julgados_acordao_sem_relator_RJ: Optional[int] = None
    julgados_acordao_sem_materia_RJ: Optional[int] = None
    julgados_acordao_sem_comarca_RJ: Optional[int] = None
    julgados_acordao_sem_competencia_RJ: Optional[int] = None
    julgados_acordao_sem_uf_RJ: Optional[int] = None
    julgados_acordao_sem_valor_pe_RJ: Optional[int] = None
    julgados_acordao_merito_sem_data_RJ: Optional[int] = None
    julgados_acordao_data_sem_merito_RJ: Optional[int] = None
    julgados_acordao_dados_faltando_RJ: Optional[List[ProcessoDadoFaltando]] = None
    # Julgados Acórdãos RJ — Estudo das Improcedências (11/11/2026)
    julgados_acordao_improcedencia_valor_RJ: Optional[float] = None
    julgados_acordao_improcedencia_total_estoque_RJ: Optional[int] = None
    julgados_acordao_improcedencia_valor_estoque_RJ: Optional[float] = None
    julgados_acordao_total_estoque_RJ: Optional[int] = None


# v1: dashboard_routes.py:5810
class Activity(BaseModel):
    id: str
    type: str
    title: str
    description: str
    time: str
    user: str
    # Tickets: campos extraídos do log do Discord (opcionais para os demais usos)
    categoria: Optional[str] = None
    status: Optional[str] = None
    servidor: Optional[str] = None
    ticket_numero: Optional[str] = None
    anydesk: Optional[str] = None
    url: Optional[str] = None
    minutos_atras: Optional[int] = None


# v1: dashboard_routes.py:5827
class DashboardResponse(BaseModel):
    dashboard: str
    stats: DashboardStats

    # Tickets
    tickets_por_categoria: Optional[List[ChartDataPoint]] = None
    tickets_por_subcategoria: Optional[List[ChartDataPoint]] = None
    tickets_por_abertura: Optional[List[ChartDataPoint]] = None
    tickets_por_fechamento: Optional[List[ChartDataPoint]] = None
    tickets_por_mes: Optional[List[ChartDataPoint]] = None
    tickets_por_status: Optional[List[ChartDataPoint]] = None
    tickets_abertos_por_servidor: Optional[List[ChartDataPoint]] = None
    tickets_encerrados_por_servidor: Optional[List[ChartDataPoint]] = None
    recent_activities: Optional[List[Activity]] = None
    tickets_media_encerrados_por_colaborador: Optional[List[ChartDataPoint]] = None

    # Controle de Processo LA
    controle_processo_por_fase_LA: Optional[List[ChartDataPoint]] = None
    controle_processo_por_subfase_LA: Optional[List[ChartDataPoint]] = None
    controle_processo_por_fase_NG: Optional[List[ChartDataPoint]] = None
    controle_processo_por_subfase_NG: Optional[List[ChartDataPoint]] = None
    controle_processo_fase_inicial_media_dias_por_mes_LA: Optional[List[ChartDataPoint]] = None
    controle_processo_fase_recursal_media_dias_por_mes_LA: Optional[List[ChartDataPoint]] = None
    controle_processo_fase_execucao_media_dias_por_mes_LA: Optional[List[ChartDataPoint]] = None
    controle_processo_fase_inicial_media_dias_por_mes_NG: Optional[List[ChartDataPoint]] = None
    controle_processo_fase_recursal_media_dias_por_mes_NG: Optional[List[ChartDataPoint]] = None
    controle_processo_fase_execucao_media_dias_por_mes_NG: Optional[List[ChartDataPoint]] = None
    estrategico_geral_fase_inicial_por_subfase: Optional[List[ChartDataPoint]] = None
    estrategico_geral_fase_recursal_por_subfase: Optional[List[ChartDataPoint]] = None
    estrategico_geral_fase_execucao_por_subfase: Optional[List[ChartDataPoint]] = None
    estrategico_geral_juridico_por_comarca: Optional[List[ChartDataPoint]] = None

    # Comercial Geral NG
    acoes_fechadas_por_atendente: Optional[List[ChartDataPoint]] = None
    acoes_fechadas_diariamente: Optional[List[ChartDataPoint]] = None
    acoes_fechadas_campanha_NG_por_rubrica: Optional[List[ChartDataPoint]] = None
    acoes_fechadas_campanha_RA_por_rubrica: Optional[List[ChartDataPoint]] = None
    acoes_fechadas_indicacao_por_rubrica: Optional[List[ChartDataPoint]] = None
    acoes_fechadas_retorno_por_rubrica: Optional[List[ChartDataPoint]] = None
    acoes_fechadas_resgate_por_rubrica: Optional[List[ChartDataPoint]] = None
    acoes_fechadas_redes_sociais_por_rubrica: Optional[List[ChartDataPoint]] = None
    acoes_fechadas_site_por_rubrica: Optional[List[ChartDataPoint]] = None
    total_acoes_fechadas_por_rubrica: Optional[List[ChartDataPoint]] = None
    rubricas_total: Optional[List[RubricaTotalRow]] = None
    comissionamento_comercial_por_atendente: Optional[List[ComissionamentoComercialRow]] = None
    comissionamento_comercial_LA_por_atendente: Optional[List[ComissionamentoComercialLARow]] = None
    contratos_fechados_diariamente_por_atendente: Optional[List[ChartDataPoint]] = None
    contratos_fechados_por_mes: Optional[List[ChartDataPoint]] = None
    processos_fechados_por_mes: Optional[List[ChartDataPoint]] = None
    contratos_fechados_por_dia: Optional[List[ChartDataPoint]] = None
    acoes_fechadas_por_dia: Optional[List[ChartDataPoint]] = None
    total_leads_por_atendente: Optional[TotalLeadsPorAtendente] = None
    total_leads_campanha_por_atendente: Optional[TotalLeadsCampanhaPorAtendente] = None
    total_clientes_fechados_por_atendente: Optional[TotalClientesFechadosPorAtendente] = None
    total_clientes_fechados_campanha_por_atendente: Optional[TotalClientesFechadosCampanhaPorAtendente] = None
    taxa_fechamento_geral_por_atendente: Optional[TaxaFechamentoGeralPorAtendente] = None
    taxa_fechamento_campanha_por_cliente: Optional[TaxaFechamentoCampanhaPorCliente] = None
    valor_causa_protocolo_novo_por_atendente: Optional[List[ChartDataPoint]] = None
    valor_causa_protocolo_nao_protocolado_por_atendente: Optional[List[ChartDataPoint]] = None
    protocolos_resolvidos_por_atendente: Optional[List[ChartDataPoint]] = None
    nao_protocolados_por_atendente: Optional[List[ChartDataPoint]] = None
    total_leads_indicacao_ativa_por_atendente: Optional[TotalLeadsIndicacaoAtivaPorAtendente] = None
    total_clientes_fechados_indicacao_ativa_por_atendente: Optional[TotalClientesFechadosIndicacaoAtivaPorAtendente] = None
    taxa_fechamento_indicacao_ativa_por_atendente: Optional[TaxaFechamentoIndicacaoAtivaPorAtendente] = None
    total_leads_indicacao_passiva_por_atendente: Optional[TotalLeadsIndicacaoPassivaPorAtendente] = None
    total_clientes_fechados_indicacao_passiva_por_atendente: Optional[TotalClientesFechadosIndicacaoPassivaPorAtendente] = None
    taxa_fechamento_indicacao_passiva_por_atendente: Optional[TaxaFechamentoIndicacaoPassivaPorAtendente] = None
    total_leads_retorno_ativa_por_atendente: Optional[TotalLeadsRetornoAtivaPorAtendente] = None
    total_clientes_fechados_retorno_ativa_por_atendente: Optional[TotalClientesFechadosRetornoAtivaPorAtendente] = None
    taxa_fechamento_retorno_ativa_por_atendente: Optional[TaxaFechamentoRetornoAtivaPorAtendente] = None
    total_leads_retorno_passiva_por_atendente: Optional[TotalLeadsRetornoPassivaPorAtendente] = None
    total_clientes_fechados_retorno_passiva_por_atendente: Optional[TotalClientesFechadosRetornoPassivaPorAtendente] = None
    taxa_fechamento_retorno_passiva_por_atendente: Optional[TaxaFechamentoRetornoPassivaPorAtendente] = None
    total_leads_resgate_ativa_por_atendente: Optional[TotalLeadsResgateAtivaPorAtendente] = None
    total_clientes_fechados_resgate_ativa_por_atendente: Optional[TotalClientesFechadosResgateAtivaPorAtendente] = None
    taxa_fechamento_resgate_ativa_por_atendente: Optional[TaxaFechamentoResgateAtivaPorAtendente] = None
    total_leads_resgate_passiva_por_atendente: Optional[TotalLeadsResgatePassivaPorAtendente] = None
    total_clientes_fechados_resgate_passiva_por_atendente: Optional[TotalClientesFechadosResgatePassivaPorAtendente] = None
    taxa_fechamento_resgate_passiva_por_atendente: Optional[TaxaFechamentoResgatePassivaPorAtendente] = None
    nao_peticionados_por_atendente: Optional[List[ChartDataPoint]] = None
    nao_organizados_por_atendente: Optional[List[ChartDataPoint]] = None
    pendencias_nao_resolvidas_por_atendente: Optional[List[ChartDataPoint]] = None
    protocolos_resolvidos_por_atendente_expandido: Optional[List[ChartDataPoint]] = None
    nao_protocolados_por_atendente_expandido: Optional[List[ChartDataPoint]] = None
    nao_peticionados_por_atendente_expandido: Optional[List[ChartDataPoint]] = None
    nao_organizados_por_atendente_expandido: Optional[List[ChartDataPoint]] = None
    pendencias_nao_resolvidas_por_atendente_expandido: Optional[List[ChartDataPoint]] = None

    # Comercial LA
    acoes_fechadas_por_atendente_LA: Optional[List[ChartDataPoint]] = None
    acoes_fechadas_diariamente_por_atendente_LA: Optional[List[ChartDataPoint]] = None
    contratos_fechados_diariamente_por_atendente_LA: Optional[List[ChartDataPoint]] = None
    contratos_fechados_por_mes_LA: Optional[List[ChartDataPoint]] = None
    processos_fechados_por_mes_LA: Optional[List[ChartDataPoint]] = None
    contratos_fechados_por_dia_LA: Optional[List[ChartDataPoint]] = None
    acoes_fechadas_por_dia_LA: Optional[List[ChartDataPoint]] = None
    valor_causa_protocolado_por_atendente_LA: Optional[List[ChartDataPoint]] = None
    valor_causa_nao_protocolado_por_atendente_LA: Optional[List[ChartDataPoint]] = None
    protocolos_resolvidos_por_atendente_LA: Optional[List[ChartDataPoint]] = None
    nao_protocolados_por_atendente_LA: Optional[List[ChartDataPoint]] = None
    nao_peticionados_por_atendente_LA: Optional[List[ChartDataPoint]] = None
    nao_organizados_por_atendente_LA: Optional[List[ChartDataPoint]] = None
    pendencias_nao_resolvidas_por_atendente_LA: Optional[List[ChartDataPoint]] = None
    total_acoes_fechadas_por_rubrica_LA: Optional[List[ChartDataPoint]] = None
    acoes_fechadas_campanha_LA_por_rubrica: Optional[List[ChartDataPoint]] = None
    acoes_fechadas_indicacao_LA_por_rubrica: Optional[List[ChartDataPoint]] = None
    acoes_fechadas_retorno_LA_por_rubrica: Optional[List[ChartDataPoint]] = None
    acoes_fechadas_redes_sociais_LA_por_rubrica: Optional[List[ChartDataPoint]] = None
    acoes_fechadas_parceiros_LA_por_rubrica: Optional[List[ChartDataPoint]] = None
    acoes_fechadas_externos_LA_por_rubrica: Optional[List[ChartDataPoint]] = None

    # Andamento Processual NG
    andamento_processual_total_por_mes: Optional[List[ChartDataPoint]] = None
    andamento_processual_por_colaborador: Optional[List[ChartDataPoint]] = None
    andamento_processual_por_colaborador_avaliacao: Optional[List[ChartDataPoint]] = None
    comissionamento_andamento_por_funcionario: Optional[List[ComissionamentoAndamentoRow]] = None

    # Andamento Processual LA
    andamento_processual_total_por_mes_LA: Optional[List[ChartDataPoint]] = None
    andamento_processual_por_colaborador_LA: Optional[List[ChartDataPoint]] = None
    andamento_processual_por_colaborador_avaliacao_LA: Optional[List[ChartDataPoint]] = None
    comissionamento_andamento_LA_por_funcionario: Optional[List[ComissionamentoAndamentoRow]] = None

    # Pendências NG
    pendencias_nao_resolvidas_por_origem: Optional[List[ChartDataPoint]] = None
    pendencias_resolvidas_por_mes: Optional[List[ChartDataPoint]] = None
    media_pendencias_resolvidas_por_funcionario: Optional[List[ChartDataPoint]] = None
    pendencias_resolvidas_por_dia: Optional[List[ChartDataPoint]] = None
    funcionarios_pendencias: Optional[List[str]] = None
    pendencias_resolvidas_por_dia_por_funcionario: Optional[Dict[str, List[ChartDataPoint]]] = None
    comissionamento_pendencias_por_funcionario: Optional[List[ComissionamentoPendenciaRow]] = None

    # Pendências LA
    pendencias_nao_resolvidas_por_origem_LA: Optional[List[ChartDataPoint]] = None
    pendencias_resolvidas_por_mes_LA: Optional[List[ChartDataPoint]] = None
    media_pendencias_resolvidas_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    pendencias_resolvidas_por_dia_LA: Optional[List[ChartDataPoint]] = None
    funcionarios_pendencias_LA: Optional[List[str]] = None
    pendencias_resolvidas_por_dia_por_funcionario_LA: Optional[Dict[str, List[ChartDataPoint]]] = None
    comissionamento_pendencias_LA_por_funcionario: Optional[List[ComissionamentoPendenciaRow]] = None

    # Org. Documentos NG
    resolvidos_total_por_materia: Optional[List[ChartDataPoint]] = None
    nao_organizados_total_por_materia: Optional[List[ChartDataPoint]] = None
    nao_organizados_por_funcionario: Optional[List[ChartDataPoint]] = None
    resolvidos_por_funcionario: Optional[List[ChartDataPoint]] = None
    media_resolvidos_por_funcionario: Optional[List[ChartDataPoint]] = None
    resolvidos_total_por_mes: Optional[List[ChartDataPoint]] = None
    valor_causa_por_funcionario: Optional[List[ChartDataPoint]] = None
    comissionamento_por_funcionario: Optional[List[ComissionamentoOrgDocRow]] = None
    nao_resolvidos_total_por_mes: Optional[List[ChartDataPoint]] = None
    resolvidos_por_dia_org: Optional[List[ChartDataPoint]] = None
    funcionarios_org_doc: Optional[List[str]] = None                                # CORRIGIDO: sem duplicatas
    resolvidos_por_dia_por_funcionario_org: Optional[Dict[str, List[ChartDataPoint]]] = None  # CORRIGIDO: sem duplicatas

    # Org. Documentos LA
    nao_organizados_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    organizados_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    valor_causa_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    comissionamento_org_doc_LA_por_funcionario: Optional[List[ComissionamentoOrgDocRow]] = None
    media_resolvidos_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    organizados_total_por_materia_LA: Optional[List[ChartDataPoint]] = None
    nao_organizados_total_por_materia_LA: Optional[List[ChartDataPoint]] = None
    resolvidos_por_dia_LA: Optional[List[ChartDataPoint]] = None
    funcionarios_org_doc_LA: Optional[List[str]] = None
    resolvidos_por_dia_por_funcionario_LA: Optional[Dict[str, List[ChartDataPoint]]] = None
    nao_organizados_total_por_mes_LA: Optional[List[ChartDataPoint]] = None
    resolvidos_total_por_mes_LA: Optional[List[ChartDataPoint]] = None

    # Protocolo NG
    protocolados_por_materia: Optional[List[ChartDataPoint]] = None
    protocolados_por_funcionario: Optional[List[ChartDataPoint]] = None
    protocolados_por_sistema: Optional[List[ChartDataPoint]] = None
    nao_protocolados_por_materia: Optional[List[ChartDataPoint]] = None
    nao_protocolados_por_funcionario: Optional[List[ChartDataPoint]] = None
    valor_causa_protocolo_novo_por_funcionario: Optional[List[ChartDataPoint]] = None
    media_protocolados_por_funcionario: Optional[List[ChartDataPoint]] = None
    comissionamento_protocolo_por_funcionario: Optional[List[ComissionamentoProtocoloRow]] = None
    protocolados_por_mes: Optional[List[ChartDataPoint]] = None
    valor_causa_protocolados_por_mes: Optional[List[ChartDataPoint]] = None
    nao_protocolados_por_mes: Optional[List[ChartDataPoint]] = None
    protocolados_por_dia: Optional[List[ChartDataPoint]] = None
    valor_causa_protocolados_por_dia: Optional[List[ChartDataPoint]] = None
    funcionarios_protocolo: Optional[List[str]] = None
    protocolados_por_dia_por_funcionario: Optional[Dict[str, List[ChartDataPoint]]] = None

    # Peticionamento NG
    peticionados_por_materia: Optional[List[ChartDataPoint]] = None
    nao_peticionados_por_materia: Optional[List[ChartDataPoint]] = None
    peticionados_por_dia: Optional[List[ChartDataPoint]] = None
    funcionarios_peticionamento: Optional[List[str]] = None
    peticionados_por_dia_por_funcionario: Optional[Dict[str, List[ChartDataPoint]]] = None
    media_peticionado_por_funcionario: Optional[List[ChartDataPoint]] = None
    valor_peticionado_por_funcionario: Optional[List[ChartDataPoint]] = None
    peticionados_por_funcionario: Optional[List[ChartDataPoint]] = None
    nao_peticionados_por_funcionario: Optional[List[ChartDataPoint]] = None
    peticionados_por_mes: Optional[List[ChartDataPoint]] = None
    nao_peticionados_por_mes: Optional[List[ChartDataPoint]] = None
    comissionamento_peticionamento_por_funcionario: Optional[List[ComissionamentoPeticionamentoRow]] = None

    # Protocolo LA
    protocolados_por_materia_LA: Optional[List[ChartDataPoint]] = None
    protocololados_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    represados_protocolo_por_materia_LA: Optional[List[ChartDataPoint]] = None
    represados_protocolo_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    valor_causa_protocolo_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    comissionamento_protocolo_LA_por_funcionario: Optional[List[ComissionamentoProtocoloRow]] = None
    protocolados_por_sistema_LA: Optional[List[ChartDataPoint]] = None
    protocolados_por_mes_LA: Optional[List[ChartDataPoint]] = None
    valor_causa_protocolados_por_mes_LA: Optional[List[ChartDataPoint]] = None
    represados_por_mes_LA: Optional[List[ChartDataPoint]] = None
    media_protocolados_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    protocolados_por_funcionario_por_dia_LA: Optional[List[ChartDataPoint]] = None
    protocolados_por_dia_LA: Optional[List[ChartDataPoint]] = None
    valor_causa_protocolados_por_dia_LA: Optional[List[ChartDataPoint]] = None
    funcionarios_protocolo_LA: Optional[List[str]] = None
    protocolados_por_dia_por_funcionario_LA: Optional[Dict[str, List[ChartDataPoint]]] = None

    # Peticionamento LA
    confeccionados_por_materia_LA: Optional[List[ChartDataPoint]] = None
    nao_confeccionados_por_materia_LA: Optional[List[ChartDataPoint]] = None
    confeccionados_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    nao_confeccionados_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    valor_confeccionado_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    media_confeccionado_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    confeccionados_por_dia_LA: Optional[List[ChartDataPoint]] = None
    funcionarios_confeccao_LA: Optional[List[str]] = None
    confeccionados_por_dia_por_funcionario_LA: Optional[Dict[str, List[ChartDataPoint]]] = None
    confeccionados_por_mes_LA: Optional[List[ChartDataPoint]] = None
    nao_confeccionados_por_mes_LA: Optional[List[ChartDataPoint]] = None
    comissionamento_peticionamento_LA_por_funcionario: Optional[List[ComissionamentoPeticionamentoRow]] = None

    # Publicações LA
    publicacoes_recebidas_por_dia_LA: Optional[List[ChartDataPoint]] = None
    publicacoes_tratadas_por_dia_LA: Optional[List[ChartDataPoint]] = None
    publicacoes_por_tribunal_LA: Optional[List[ChartDataPoint]] = None
    publicacoes_por_tipo_documento_LA: Optional[List[ChartDataPoint]] = None
    publicacoes_por_materia_LA: Optional[List[ChartDataPoint]] = None
    publicacoes_por_orgao_LA: Optional[List[ChartDataPoint]] = None
    publicacoes_por_comarca_LA: Optional[List[ChartDataPoint]] = None
    publicacoes_cumprido_por_leitor_LA: Optional[List[ChartDataPoint]] = None
    publicacoes_pendentes_por_leitor_LA: Optional[List[ChartDataPoint]] = None
    publicacoes_pendentes_por_dias_atraso_LA: Optional[List[ChartDataPoint]] = None
    publicacoes_agendamento_apos_finalizacao_por_atividade_LA: Optional[List[ChartDataPoint]] = None
    publicacoes_agendamento_apos_finalizacao_por_setor_LA: Optional[List[ChartDataPoint]] = None
    publicacoes_lista_LA: Optional[List[RecursalAtividadeTarefaRow]] = None
    comissionamento_publicacoes_LA_por_funcionario: Optional[List[ComissionamentoPublicacaoRow]] = None

    # Publicações NG
    publicacoes_recebidas_por_dia_NG: Optional[List[ChartDataPoint]] = None
    publicacoes_tratadas_por_dia_NG: Optional[List[ChartDataPoint]] = None
    publicacoes_visualizadas_por_dia_NG: Optional[List[ChartDataPoint]] = None
    publicacoes_por_tribunal_NG: Optional[List[ChartDataPoint]] = None
    publicacoes_por_tipo_documento_NG: Optional[List[ChartDataPoint]] = None
    publicacoes_por_materia_NG: Optional[List[ChartDataPoint]] = None
    publicacoes_por_orgao_NG: Optional[List[ChartDataPoint]] = None
    publicacoes_por_comarca_NG: Optional[List[ChartDataPoint]] = None
    publicacoes_cumprido_por_leitor_NG: Optional[List[ChartDataPoint]] = None
    publicacoes_pendentes_por_leitor_NG: Optional[List[ChartDataPoint]] = None
    publicacoes_pendentes_por_dias_atraso_NG: Optional[List[ChartDataPoint]] = None
    publicacoes_agendamento_apos_finalizacao_por_atividade_NG: Optional[List[ChartDataPoint]] = None
    publicacoes_agendamento_apos_finalizacao_por_setor_NG: Optional[List[ChartDataPoint]] = None
    publicacoes_lista_NG: Optional[List[RecursalAtividadeTarefaRow]] = None
    comissionamento_publicacoes_NG_por_funcionario: Optional[List[ComissionamentoPublicacaoRow]] = None

    # Publicações RJ
    publicacoes_recebidas_por_dia_RJ: Optional[List[ChartDataPoint]] = None
    publicacoes_tratadas_por_dia_RJ: Optional[List[ChartDataPoint]] = None
    publicacoes_visualizadas_por_dia_RJ: Optional[List[ChartDataPoint]] = None
    publicacoes_por_tribunal_RJ: Optional[List[ChartDataPoint]] = None
    publicacoes_por_tipo_documento_RJ: Optional[List[ChartDataPoint]] = None
    publicacoes_por_materia_RJ: Optional[List[ChartDataPoint]] = None
    publicacoes_por_orgao_RJ: Optional[List[ChartDataPoint]] = None
    publicacoes_por_comarca_RJ: Optional[List[ChartDataPoint]] = None
    publicacoes_cumprido_por_leitor_RJ: Optional[List[ChartDataPoint]] = None
    publicacoes_pendentes_por_leitor_RJ: Optional[List[ChartDataPoint]] = None
    publicacoes_pendentes_por_dias_atraso_RJ: Optional[List[ChartDataPoint]] = None
    publicacoes_agendamento_apos_finalizacao_por_atividade_RJ: Optional[List[ChartDataPoint]] = None
    publicacoes_agendamento_apos_finalizacao_por_setor_RJ: Optional[List[ChartDataPoint]] = None
    publicacoes_lista_RJ: Optional[List[RecursalAtividadeTarefaRow]] = None
    comissionamento_publicacoes_RJ_por_funcionario: Optional[List[ComissionamentoPublicacaoRow]] = None

    # Execução NG
    execucao_por_subfase: Optional[List[ChartDataPoint]] = None
    valor_execucao_por_subfase: Optional[List[ChartDataPoint]] = None
    execucao_por_comarca_total: Optional[List[ChartDataPoint]] = None
    execucao_por_comarca_entrada: Optional[List[ChartDataPoint]] = None
    execucao_por_comarca_saida: Optional[List[ChartDataPoint]] = None
    execucao_valor_por_comarca_total: Optional[List[ChartDataPoint]] = None
    execucao_valor_por_comarca_entrada: Optional[List[ChartDataPoint]] = None
    execucao_valor_por_comarca_saida: Optional[List[ChartDataPoint]] = None
    execucao_por_materia: Optional[List[ChartDataPoint]] = None
    valor_execucao_por_materia: Optional[List[ChartDataPoint]] = None
    execucao_por_ano_ajuizamento_NG: Optional[List[ChartDataPoint]] = None
    execucao_por_faixa_ultima_movimentacao: Optional[List[ChartDataPoint]] = None
    valor_saida_execucao_por_mes: Optional[List[ChartDataPoint]] = None
    valor_execucao_saida_periodo_por_mes: Optional[List[ChartDataPoint]] = None
    valor_remanescente_por_mes: Optional[List[ChartDataPoint]] = None
    quantidade_saida_execucao_por_mes: Optional[List[ChartDataPoint]] = None
    quantidade_entrada_execucao_por_mes: Optional[List[ChartDataPoint]] = None
    valor_entrada_execucao_por_mes: Optional[List[ChartDataPoint]] = None
    execucao_media_tempo_por_mes: Optional[List[ChartDataPoint]] = None
    execucao_estoque_quantidade_por_mes: Optional[List[ChartDataPoint]] = None
    execucao_estoque_valor_por_mes: Optional[List[ChartDataPoint]] = None
    execucao_processos_por_atividade_NG: Optional[List[ChartDataPoint]] = None
    execucao_atividades_ativas_por_atividade_NG: Optional[List[ChartDataPoint]] = None
    execucao_atividades_criadas_por_atividade_NG: Optional[List[ChartDataPoint]] = None
    execucao_atividades_ativas_por_atividade_por_prazo_NG: Optional[List[ChartDataPoint]] = None
    execucao_processos_por_atividade_por_prazo_NG: Optional[List[ChartDataPoint]] = None
    execucao_demandas_por_funcionario_NG: Optional[List[Dict[str, Any]]] = None
    execucao_demandas_por_funcionario_completo_NG: Optional[List[Dict[str, Any]]] = None
    execucao_taxa_conclusao_por_funcionario_NG: Optional[List[Dict[str, Any]]] = None
    execucao_entrada_fluxo_cs_por_mes_NG: Optional[List[Dict[str, Any]]] = None
    execucao_alvara_expedido_lista_NG: Optional[List[Dict[str, Any]]] = None
    execucao_alvaras_expedidos_por_dia_NG: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_alvaras_expedidos_por_dia_NG: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_alvara_expedido_lista_NG: Optional[List[Dict[str, Any]]] = None
    execucao_demandas_por_funcionario_por_prazo_NG: Optional[List[Dict[str, Any]]] = None
    execucao_demandas_por_funcionario_por_prazo_completo_NG: Optional[List[Dict[str, Any]]] = None
    execucao_valor_recuperado_por_funcionario_NG: Optional[List[ChartDataPoint]] = None
    execucao_resolvidos_por_dia_NG: Optional[List[ChartDataPoint]] = None
    execucao_resolvidos_por_dia_por_prazo_NG: Optional[List[ChartDataPoint]] = None
    execucao_media_resolvidos_por_funcionario_NG: Optional[List[ChartDataPoint]] = None
    execucao_media_resolvidos_por_funcionario_por_prazo_NG: Optional[List[ChartDataPoint]] = None
    execucao_nao_cumprido_por_motivo_NG: Optional[List[ChartDataPoint]] = None
    execucao_atividades_lista_NG: Optional[List[RecursalAtividadeTarefaRow]] = None
    execucao_atividades_abertas_NG: Optional[List[RecursalAtividadeTarefaRow]] = None
    execucao_atividades_lista_por_prazo_NG: Optional[List[RecursalAtividadeTarefaRow]] = None
    execucao_atividades_lista_filtros_opcoes_NG: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    execucao_atividades_lista_filtros_opcoes_por_prazo_NG: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    execucao_atrasos_detalhamento_NG: Optional[ExecucaoAtrasosDetalhamento] = None
    execucao_diligencias_por_processo_NG: Optional[List[ChartDataPoint]] = None
    execucao_diligencias_por_funcionario_NG: Optional[List[Dict[str, Any]]] = None
    execucao_diligencias_expedicao_alvara_processos_NG: Optional[List[ExecucaoAcordosListaRow]] = None

    # Execução RJ (Condenação)
    execucao_por_subfase_RJ: Optional[List[ChartDataPoint]] = None
    valor_execucao_por_subfase_RJ: Optional[List[ChartDataPoint]] = None
    execucao_por_comarca_total_RJ: Optional[List[ChartDataPoint]] = None
    execucao_por_comarca_entrada_RJ: Optional[List[ChartDataPoint]] = None
    execucao_por_comarca_saida_RJ: Optional[List[ChartDataPoint]] = None
    execucao_valor_por_comarca_total_RJ: Optional[List[ChartDataPoint]] = None
    execucao_valor_por_comarca_entrada_RJ: Optional[List[ChartDataPoint]] = None
    execucao_valor_por_comarca_saida_RJ: Optional[List[ChartDataPoint]] = None
    execucao_por_materia_RJ: Optional[List[ChartDataPoint]] = None
    valor_execucao_por_materia_RJ: Optional[List[ChartDataPoint]] = None
    execucao_por_ano_ajuizamento_RJ: Optional[List[ChartDataPoint]] = None
    valor_saida_execucao_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    valor_execucao_saida_periodo_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    valor_remanescente_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    quantidade_saida_execucao_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    quantidade_entrada_execucao_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    valor_entrada_execucao_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    execucao_media_tempo_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    execucao_estoque_quantidade_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    execucao_estoque_valor_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    execucao_processos_por_atividade_RJ: Optional[List[ChartDataPoint]] = None
    execucao_atividades_ativas_por_atividade_RJ: Optional[List[ChartDataPoint]] = None
    execucao_atividades_criadas_por_atividade_RJ: Optional[List[ChartDataPoint]] = None
    execucao_taxa_conclusao_por_funcionario_RJ: Optional[List[Dict[str, Any]]] = None
    execucao_entrada_fluxo_cs_por_mes_RJ: Optional[List[Dict[str, Any]]] = None
    execucao_alvara_expedido_lista_RJ: Optional[List[Dict[str, Any]]] = None
    execucao_alvaras_expedidos_por_dia_RJ: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_alvaras_expedidos_por_dia_RJ: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_alvara_expedido_lista_RJ: Optional[List[Dict[str, Any]]] = None
    execucao_atividades_abertas_RJ: Optional[List[RecursalAtividadeTarefaRow]] = None
    execucao_atividades_ativas_por_atividade_por_prazo_RJ: Optional[List[ChartDataPoint]] = None
    execucao_processos_por_atividade_por_prazo_RJ: Optional[List[ChartDataPoint]] = None
    execucao_demandas_por_funcionario_RJ: Optional[List[Dict[str, Any]]] = None
    execucao_demandas_por_funcionario_completo_RJ: Optional[List[Dict[str, Any]]] = None
    execucao_demandas_por_funcionario_por_prazo_RJ: Optional[List[Dict[str, Any]]] = None
    execucao_demandas_por_funcionario_por_prazo_completo_RJ: Optional[List[Dict[str, Any]]] = None
    execucao_valor_recuperado_por_funcionario_RJ: Optional[List[ChartDataPoint]] = None
    execucao_resolvidos_por_dia_RJ: Optional[List[ChartDataPoint]] = None
    execucao_resolvidos_por_dia_por_prazo_RJ: Optional[List[ChartDataPoint]] = None
    execucao_media_resolvidos_por_funcionario_RJ: Optional[List[ChartDataPoint]] = None
    execucao_media_resolvidos_por_funcionario_por_prazo_RJ: Optional[List[ChartDataPoint]] = None
    execucao_nao_cumprido_por_motivo_RJ: Optional[List[ChartDataPoint]] = None
    execucao_atividades_lista_RJ: Optional[List[RecursalAtividadeTarefaRow]] = None
    execucao_atividades_lista_por_prazo_RJ: Optional[List[RecursalAtividadeTarefaRow]] = None
    execucao_atividades_lista_filtros_opcoes_RJ: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    execucao_atividades_lista_filtros_opcoes_por_prazo_RJ: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    execucao_atrasos_detalhamento_RJ: Optional[ExecucaoAtrasosDetalhamento] = None
    execucao_diligencias_por_processo_RJ: Optional[List[ChartDataPoint]] = None
    execucao_diligencias_por_funcionario_RJ: Optional[List[Dict[str, Any]]] = None
    execucao_diligencias_expedicao_alvara_processos_RJ: Optional[List[ExecucaoAcordosListaRow]] = None

    # Execução Acordos NG
    execucao_acordos_por_subfase_NG: Optional[List[ChartDataPoint]] = None
    valor_execucao_acordos_por_subfase_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_comarca_total_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_comarca_entrada_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_comarca_saida_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_valor_por_comarca_total_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_valor_por_comarca_entrada_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_valor_por_comarca_saida_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_materia_NG: Optional[List[ChartDataPoint]] = None
    valor_execucao_acordos_por_materia_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_ano_ajuizamento_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_tipo_acao_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_sentenca_NG: Optional[List[ChartDataPoint]] = None
    valor_saida_execucao_acordos_por_mes_NG: Optional[List[ChartDataPoint]] = None
    quantidade_saida_execucao_acordos_por_mes_NG: Optional[List[ChartDataPoint]] = None
    quantidade_entrada_execucao_acordos_por_mes_NG: Optional[List[ChartDataPoint]] = None
    valor_entrada_execucao_acordos_por_mes_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_media_tempo_por_mes_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_estoque_quantidade_por_mes_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_estoque_valor_por_mes_NG: Optional[List[ChartDataPoint]] = None
    fechamento_acordo_por_subfase_NG: Optional[List[ChartDataPoint]] = None
    valor_fechamento_acordo_por_subfase_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_lista_entrada_NG: Optional[List[ExecucaoAcordosListaRow]] = None
    execucao_acordos_lista_saida_NG: Optional[List[ExecucaoAcordosListaRow]] = None
    execucao_acordos_lista_total_NG: Optional[List[ExecucaoAcordosListaRow]] = None
    execucao_acordos_processos_por_atividade_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_atividades_ativas_por_atividade_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_atividades_ativas_por_atividade_por_prazo_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_processos_por_atividade_por_prazo_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_demandas_por_funcionario_NG: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_demandas_por_funcionario_completo_NG: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_demandas_por_funcionario_por_prazo_NG: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_demandas_por_funcionario_por_prazo_completo_NG: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_resolvidos_por_dia_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_resolvidos_por_dia_por_prazo_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_media_resolvidos_por_funcionario_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_media_resolvidos_por_funcionario_por_prazo_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_nao_cumprido_por_motivo_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_atividades_lista_NG: Optional[List[RecursalAtividadeTarefaRow]] = None
    execucao_acordos_atividades_lista_por_prazo_NG: Optional[List[RecursalAtividadeTarefaRow]] = None
    execucao_acordos_atividades_lista_filtros_opcoes_NG: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    execucao_acordos_atividades_lista_filtros_opcoes_por_prazo_NG: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    execucao_acordos_atrasos_detalhamento_NG: Optional[ExecucaoAtrasosDetalhamento] = None
    execucao_acordos_diligencias_por_processo_NG: Optional[List[ChartDataPoint]] = None
    execucao_acordos_diligencias_por_funcionario_NG: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_diligencias_expedicao_alvara_processos_NG: Optional[List[ExecucaoAcordosListaRow]] = None
    execucao_acordos_por_subfase_LA: Optional[List[ChartDataPoint]] = None
    valor_execucao_acordos_por_subfase_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_comarca_total_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_comarca_entrada_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_comarca_saida_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_valor_por_comarca_total_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_valor_por_comarca_entrada_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_valor_por_comarca_saida_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_materia_LA: Optional[List[ChartDataPoint]] = None
    valor_execucao_acordos_por_materia_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_ano_ajuizamento_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_tipo_acao_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_sentenca_LA: Optional[List[ChartDataPoint]] = None
    valor_saida_execucao_acordos_por_mes_LA: Optional[List[ChartDataPoint]] = None
    quantidade_saida_execucao_acordos_por_mes_LA: Optional[List[ChartDataPoint]] = None
    quantidade_entrada_execucao_acordos_por_mes_LA: Optional[List[ChartDataPoint]] = None
    valor_entrada_execucao_acordos_por_mes_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_media_tempo_por_mes_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_estoque_quantidade_por_mes_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_estoque_valor_por_mes_LA: Optional[List[ChartDataPoint]] = None
    fechamento_acordo_por_subfase_LA: Optional[List[ChartDataPoint]] = None
    valor_fechamento_acordo_por_subfase_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_lista_entrada_LA: Optional[List[ExecucaoAcordosListaRow]] = None
    execucao_acordos_lista_saida_LA: Optional[List[ExecucaoAcordosListaRow]] = None
    execucao_acordos_lista_total_LA: Optional[List[ExecucaoAcordosListaRow]] = None
    execucao_acordos_processos_por_atividade_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_atividades_ativas_por_atividade_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_atividades_ativas_por_atividade_por_prazo_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_processos_por_atividade_por_prazo_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_demandas_por_funcionario_LA: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_demandas_por_funcionario_completo_LA: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_demandas_por_funcionario_por_prazo_LA: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_demandas_por_funcionario_por_prazo_completo_LA: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_resolvidos_por_dia_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_resolvidos_por_dia_por_prazo_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_media_resolvidos_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_media_resolvidos_por_funcionario_por_prazo_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_nao_cumprido_por_motivo_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_atividades_lista_LA: Optional[List[RecursalAtividadeTarefaRow]] = None
    execucao_acordos_atividades_lista_por_prazo_LA: Optional[List[RecursalAtividadeTarefaRow]] = None
    execucao_acordos_atividades_lista_filtros_opcoes_LA: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    execucao_acordos_atividades_lista_filtros_opcoes_por_prazo_LA: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    execucao_acordos_atrasos_detalhamento_LA: Optional[ExecucaoAtrasosDetalhamento] = None
    execucao_acordos_diligencias_por_processo_LA: Optional[List[ChartDataPoint]] = None
    execucao_acordos_diligencias_por_funcionario_LA: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_diligencias_expedicao_alvara_processos_LA: Optional[List[ExecucaoAcordosListaRow]] = None
    execucao_acordos_por_subfase_RJ: Optional[List[ChartDataPoint]] = None
    valor_execucao_acordos_por_subfase_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_comarca_total_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_comarca_entrada_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_comarca_saida_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_valor_por_comarca_total_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_valor_por_comarca_entrada_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_valor_por_comarca_saida_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_materia_RJ: Optional[List[ChartDataPoint]] = None
    valor_execucao_acordos_por_materia_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_ano_ajuizamento_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_tipo_acao_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_por_sentenca_RJ: Optional[List[ChartDataPoint]] = None
    valor_saida_execucao_acordos_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    quantidade_saida_execucao_acordos_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    quantidade_entrada_execucao_acordos_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    valor_entrada_execucao_acordos_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_media_tempo_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_estoque_quantidade_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_estoque_valor_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    fechamento_acordo_por_subfase_RJ: Optional[List[ChartDataPoint]] = None
    valor_fechamento_acordo_por_subfase_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_lista_entrada_RJ: Optional[List[ExecucaoAcordosListaRow]] = None
    execucao_acordos_lista_saida_RJ: Optional[List[ExecucaoAcordosListaRow]] = None
    execucao_acordos_lista_total_RJ: Optional[List[ExecucaoAcordosListaRow]] = None
    execucao_acordos_processos_por_atividade_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_atividades_ativas_por_atividade_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_atividades_ativas_por_atividade_por_prazo_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_processos_por_atividade_por_prazo_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_demandas_por_funcionario_RJ: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_demandas_por_funcionario_completo_RJ: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_demandas_por_funcionario_por_prazo_RJ: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_demandas_por_funcionario_por_prazo_completo_RJ: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_resolvidos_por_dia_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_resolvidos_por_dia_por_prazo_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_media_resolvidos_por_funcionario_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_media_resolvidos_por_funcionario_por_prazo_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_nao_cumprido_por_motivo_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_atividades_lista_RJ: Optional[List[RecursalAtividadeTarefaRow]] = None
    execucao_acordos_atividades_lista_por_prazo_RJ: Optional[List[RecursalAtividadeTarefaRow]] = None
    execucao_acordos_atividades_lista_filtros_opcoes_RJ: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    execucao_acordos_atividades_lista_filtros_opcoes_por_prazo_RJ: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    execucao_acordos_atrasos_detalhamento_RJ: Optional[ExecucaoAtrasosDetalhamento] = None
    execucao_acordos_diligencias_por_processo_RJ: Optional[List[ChartDataPoint]] = None
    execucao_acordos_diligencias_por_funcionario_RJ: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_diligencias_expedicao_alvara_processos_RJ: Optional[List[ExecucaoAcordosListaRow]] = None

    # Execução LA
    execucao_por_subfase_LA: Optional[List[ChartDataPoint]] = None
    valor_execucao_por_subfase_LA: Optional[List[ChartDataPoint]] = None
    execucao_por_comarca_total_LA: Optional[List[ChartDataPoint]] = None
    execucao_por_comarca_entrada_LA: Optional[List[ChartDataPoint]] = None
    execucao_por_comarca_saida_LA: Optional[List[ChartDataPoint]] = None
    execucao_valor_por_comarca_total_LA: Optional[List[ChartDataPoint]] = None
    execucao_valor_por_comarca_entrada_LA: Optional[List[ChartDataPoint]] = None
    execucao_valor_por_comarca_saida_LA: Optional[List[ChartDataPoint]] = None
    recursal_por_status_1g_LA: Optional[List[ChartDataPoint]] = None
    recursal_por_status_2g_LA: Optional[List[ChartDataPoint]] = None
    recursal_por_subfase_LA: Optional[List[ChartDataPoint]] = None
    recursal_por_materia_LA: Optional[List[ChartDataPoint]] = None
    recursal_por_competencia_LA: Optional[List[ChartDataPoint]] = None
    recursal_por_vara_LA: Optional[List[ChartDataPoint]] = None
    recursal_decisoes_LA: Optional[List[ChartDataPoint]] = None
    recursal_processos_por_atividade_LA: Optional[List[ChartDataPoint]] = None
    recursal_demandas_por_funcionario_LA: Optional[List[Dict[str, Any]]] = None
    recursal_resolvidos_por_dia_LA: Optional[List[ChartDataPoint]] = None
    recursal_resolvidos_por_mes_LA: Optional[List[ChartDataPoint]] = None
    funcionarios_recursal_LA: Optional[List[str]] = None
    recursal_resolvidos_por_dia_por_funcionario_LA: Optional[Dict[str, List[ChartDataPoint]]] = None
    recursal_media_resolvidos_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    recursal_atividades_lista_LA: Optional[List[RecursalAtividadeTarefaRow]] = None
    recursal_atividades_lista_filtros_opcoes_LA: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    ranking_juizes_recursal_LA: Optional[List[RecursalRankingMagistradoRow]] = None
    # Recursal NG
    recursal_por_status_1g_NG: Optional[List[ChartDataPoint]] = None
    recursal_por_status_2g_NG: Optional[List[ChartDataPoint]] = None
    recursal_por_subfase_NG: Optional[List[ChartDataPoint]] = None
    recursal_por_materia_NG: Optional[List[ChartDataPoint]] = None
    recursal_por_competencia_NG: Optional[List[ChartDataPoint]] = None
    recursal_por_vara_NG: Optional[List[ChartDataPoint]] = None
    recursal_decisoes_NG: Optional[List[ChartDataPoint]] = None
    recursal_processos_por_atividade_NG: Optional[List[ChartDataPoint]] = None
    recursal_demandas_por_funcionario_NG: Optional[List[Dict[str, Any]]] = None
    recursal_resolvidos_por_dia_NG: Optional[List[ChartDataPoint]] = None
    recursal_resolvidos_por_mes_NG: Optional[List[ChartDataPoint]] = None
    funcionarios_recursal_NG: Optional[List[str]] = None
    recursal_resolvidos_por_dia_por_funcionario_NG: Optional[Dict[str, List[ChartDataPoint]]] = None
    recursal_media_resolvidos_por_funcionario_NG: Optional[List[ChartDataPoint]] = None
    recursal_atividades_lista_NG: Optional[List[RecursalAtividadeTarefaRow]] = None
    recursal_atividades_lista_filtros_opcoes_NG: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    ranking_juizes_recursal_NG: Optional[List[RecursalRankingMagistradoRow]] = None
    ranking_relatores_recursal_NG: Optional[List[RecursalRankingMagistradoRow]] = None
    # Recursal RJ
    recursal_por_status_1g_RJ: Optional[List[ChartDataPoint]] = None
    recursal_por_status_2g_RJ: Optional[List[ChartDataPoint]] = None
    recursal_por_subfase_RJ: Optional[List[ChartDataPoint]] = None
    recursal_por_materia_RJ: Optional[List[ChartDataPoint]] = None
    recursal_por_competencia_RJ: Optional[List[ChartDataPoint]] = None
    recursal_por_vara_RJ: Optional[List[ChartDataPoint]] = None
    recursal_decisoes_RJ: Optional[List[ChartDataPoint]] = None
    recursal_processos_por_atividade_RJ: Optional[List[ChartDataPoint]] = None
    recursal_demandas_por_funcionario_RJ: Optional[List[Dict[str, Any]]] = None
    recursal_resolvidos_por_dia_RJ: Optional[List[ChartDataPoint]] = None
    recursal_resolvidos_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    funcionarios_recursal_RJ: Optional[List[str]] = None
    recursal_resolvidos_por_dia_por_funcionario_RJ: Optional[Dict[str, List[ChartDataPoint]]] = None
    recursal_media_resolvidos_por_funcionario_RJ: Optional[List[ChartDataPoint]] = None
    recursal_atividades_lista_RJ: Optional[List[RecursalAtividadeTarefaRow]] = None
    recursal_atividades_lista_filtros_opcoes_RJ: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    ranking_juizes_recursal_RJ: Optional[List[RecursalRankingMagistradoRow]] = None
    ranking_relatores_recursal_RJ: Optional[List[RecursalRankingMagistradoRow]] = None
    # Julgados NG
    ranking_juizes_sentenca_julgados_NG: Optional[List[RecursalRankingMagistradoRow]] = None
    julgados_por_materia_NG: Optional[List[ChartDataPoint]] = None
    julgados_por_competencia_NG: Optional[List[ChartDataPoint]] = None
    julgados_por_comarca_NG: Optional[List[ChartDataPoint]] = None
    julgados_por_motivo_extincao_NG: Optional[List[ChartDataPoint]] = None
    julgados_extincao_por_comarca_NG: Optional[List[ChartDataPoint]] = None
    julgados_extincao_por_comarca_estoque_NG: Optional[List[ChartDataPoint]] = None
    julgados_extincao_por_motivo_estoque_NG: Optional[List[ChartDataPoint]] = None
    julgados_extincao_por_juiz_NG: Optional[List[ChartDataPoint]] = None
    julgados_extincao_por_juiz_estoque_NG: Optional[List[ChartDataPoint]] = None
    # Julgados Sentenças NG — Estudo das Improcedências (11/11/2026)
    julgados_improcedencia_por_comarca_NG: Optional[List[ChartDataPoint]] = None
    julgados_improcedencia_por_comarca_estoque_NG: Optional[List[ChartDataPoint]] = None
    julgados_improcedencia_por_motivo_NG: Optional[List[ChartDataPoint]] = None
    julgados_improcedencia_por_motivo_estoque_NG: Optional[List[ChartDataPoint]] = None
    julgados_improcedencia_por_juiz_NG: Optional[List[ChartDataPoint]] = None
    julgados_improcedencia_por_juiz_estoque_NG: Optional[List[ChartDataPoint]] = None
    julgados_por_ano_ajuizamento_NG: Optional[List[ChartDataPoint]] = None
    julgados_sentenca_embargos_resultado_NG: Optional[List[ChartDataPoint]] = None
    julgados_sentenca_procedentes_por_mes_NG: Optional[List[ChartDataPoint]] = None
    julgados_sentenca_improcedentes_por_mes_NG: Optional[List[ChartDataPoint]] = None
    julgados_sentenca_extintos_por_mes_NG: Optional[List[ChartDataPoint]] = None
    julgados_sentenca_lista_NG: Optional[List[JulgadosSentencaListaRow]] = None
    # Julgados Acórdãos NG
    ranking_relatores_acordao_julgados_NG: Optional[List[RecursalRankingMagistradoRow]] = None
    julgados_acordao_por_materia_NG: Optional[List[ChartDataPoint]] = None
    julgados_acordao_por_competencia_NG: Optional[List[ChartDataPoint]] = None
    julgados_acordao_por_comarca_NG: Optional[List[ChartDataPoint]] = None
    julgados_acordao_por_motivo_extincao_NG: Optional[List[ChartDataPoint]] = None
    julgados_acordao_por_ano_ajuizamento_NG: Optional[List[ChartDataPoint]] = None
    julgados_acordao_embargos_resultado_NG: Optional[List[ChartDataPoint]] = None
    julgados_acordao_procedentes_por_mes_NG: Optional[List[ChartDataPoint]] = None
    julgados_acordao_improcedentes_por_mes_NG: Optional[List[ChartDataPoint]] = None
    julgados_acordao_extintos_por_mes_NG: Optional[List[ChartDataPoint]] = None
    julgados_acordao_lista_NG: Optional[List[JulgadosAcordaoListaRow]] = None
    # Julgados Acórdãos NG — Estudo das Improcedências (11/11/2026)
    julgados_acordao_improcedencia_por_comarca_NG: Optional[List[ChartDataPoint]] = None
    julgados_acordao_improcedencia_por_comarca_estoque_NG: Optional[List[ChartDataPoint]] = None
    julgados_acordao_improcedencia_por_motivo_NG: Optional[List[ChartDataPoint]] = None
    julgados_acordao_improcedencia_por_motivo_estoque_NG: Optional[List[ChartDataPoint]] = None
    julgados_acordao_improcedencia_por_relator_NG: Optional[List[ChartDataPoint]] = None
    julgados_acordao_improcedencia_por_relator_estoque_NG: Optional[List[ChartDataPoint]] = None
    # Julgados Sentenças LA
    ranking_juizes_sentenca_julgados_LA: Optional[List[RecursalRankingMagistradoRow]] = None
    julgados_por_materia_LA: Optional[List[ChartDataPoint]] = None
    julgados_por_competencia_LA: Optional[List[ChartDataPoint]] = None
    julgados_por_comarca_LA: Optional[List[ChartDataPoint]] = None
    julgados_por_motivo_extincao_LA: Optional[List[ChartDataPoint]] = None
    julgados_extincao_por_comarca_LA: Optional[List[ChartDataPoint]] = None
    julgados_extincao_por_comarca_estoque_LA: Optional[List[ChartDataPoint]] = None
    julgados_extincao_por_motivo_estoque_LA: Optional[List[ChartDataPoint]] = None
    julgados_extincao_por_juiz_LA: Optional[List[ChartDataPoint]] = None
    julgados_extincao_por_juiz_estoque_LA: Optional[List[ChartDataPoint]] = None
    # Julgados Sentenças LA — Estudo das Improcedências (11/11/2026)
    julgados_improcedencia_por_comarca_LA: Optional[List[ChartDataPoint]] = None
    julgados_improcedencia_por_comarca_estoque_LA: Optional[List[ChartDataPoint]] = None
    julgados_improcedencia_por_motivo_LA: Optional[List[ChartDataPoint]] = None
    julgados_improcedencia_por_motivo_estoque_LA: Optional[List[ChartDataPoint]] = None
    julgados_improcedencia_por_juiz_LA: Optional[List[ChartDataPoint]] = None
    julgados_improcedencia_por_juiz_estoque_LA: Optional[List[ChartDataPoint]] = None
    julgados_por_ano_ajuizamento_LA: Optional[List[ChartDataPoint]] = None
    julgados_sentenca_embargos_resultado_LA: Optional[List[ChartDataPoint]] = None
    julgados_sentenca_procedentes_por_mes_LA: Optional[List[ChartDataPoint]] = None
    julgados_sentenca_improcedentes_por_mes_LA: Optional[List[ChartDataPoint]] = None
    julgados_sentenca_extintos_por_mes_LA: Optional[List[ChartDataPoint]] = None
    julgados_sentenca_lista_LA: Optional[List[JulgadosSentencaListaRow]] = None
    # Julgados Sentenças RJ
    ranking_juizes_sentenca_julgados_RJ: Optional[List[RecursalRankingMagistradoRow]] = None
    julgados_por_materia_RJ: Optional[List[ChartDataPoint]] = None
    julgados_por_competencia_RJ: Optional[List[ChartDataPoint]] = None
    julgados_por_comarca_RJ: Optional[List[ChartDataPoint]] = None
    julgados_por_motivo_extincao_RJ: Optional[List[ChartDataPoint]] = None
    julgados_extincao_por_comarca_RJ: Optional[List[ChartDataPoint]] = None
    julgados_extincao_por_comarca_estoque_RJ: Optional[List[ChartDataPoint]] = None
    julgados_extincao_por_motivo_estoque_RJ: Optional[List[ChartDataPoint]] = None
    julgados_extincao_por_juiz_RJ: Optional[List[ChartDataPoint]] = None
    julgados_extincao_por_juiz_estoque_RJ: Optional[List[ChartDataPoint]] = None
    # Julgados Sentenças RJ — Estudo das Improcedências (11/11/2026)
    julgados_improcedencia_por_comarca_RJ: Optional[List[ChartDataPoint]] = None
    julgados_improcedencia_por_comarca_estoque_RJ: Optional[List[ChartDataPoint]] = None
    julgados_improcedencia_por_motivo_RJ: Optional[List[ChartDataPoint]] = None
    julgados_improcedencia_por_motivo_estoque_RJ: Optional[List[ChartDataPoint]] = None
    julgados_improcedencia_por_juiz_RJ: Optional[List[ChartDataPoint]] = None
    julgados_improcedencia_por_juiz_estoque_RJ: Optional[List[ChartDataPoint]] = None
    julgados_por_ano_ajuizamento_RJ: Optional[List[ChartDataPoint]] = None
    julgados_sentenca_embargos_resultado_RJ: Optional[List[ChartDataPoint]] = None
    julgados_sentenca_procedentes_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    julgados_sentenca_improcedentes_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    julgados_sentenca_extintos_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    julgados_sentenca_lista_RJ: Optional[List[JulgadosSentencaListaRow]] = None
    # Julgados Acórdãos LA
    ranking_relatores_acordao_julgados_LA: Optional[List[RecursalRankingMagistradoRow]] = None
    julgados_acordao_por_materia_LA: Optional[List[ChartDataPoint]] = None
    julgados_acordao_por_competencia_LA: Optional[List[ChartDataPoint]] = None
    julgados_acordao_por_comarca_LA: Optional[List[ChartDataPoint]] = None
    julgados_acordao_por_motivo_extincao_LA: Optional[List[ChartDataPoint]] = None
    julgados_acordao_por_ano_ajuizamento_LA: Optional[List[ChartDataPoint]] = None
    julgados_acordao_embargos_resultado_LA: Optional[List[ChartDataPoint]] = None
    julgados_acordao_procedentes_por_mes_LA: Optional[List[ChartDataPoint]] = None
    julgados_acordao_improcedentes_por_mes_LA: Optional[List[ChartDataPoint]] = None
    julgados_acordao_extintos_por_mes_LA: Optional[List[ChartDataPoint]] = None
    julgados_acordao_lista_LA: Optional[List[JulgadosAcordaoListaRow]] = None
    # Julgados Acórdãos LA — Estudo das Improcedências (11/11/2026)
    julgados_acordao_improcedencia_por_comarca_LA: Optional[List[ChartDataPoint]] = None
    julgados_acordao_improcedencia_por_comarca_estoque_LA: Optional[List[ChartDataPoint]] = None
    julgados_acordao_improcedencia_por_motivo_LA: Optional[List[ChartDataPoint]] = None
    julgados_acordao_improcedencia_por_motivo_estoque_LA: Optional[List[ChartDataPoint]] = None
    julgados_acordao_improcedencia_por_relator_LA: Optional[List[ChartDataPoint]] = None
    julgados_acordao_improcedencia_por_relator_estoque_LA: Optional[List[ChartDataPoint]] = None
    # Julgados Acórdãos RJ
    ranking_relatores_acordao_julgados_RJ: Optional[List[RecursalRankingMagistradoRow]] = None
    julgados_acordao_por_materia_RJ: Optional[List[ChartDataPoint]] = None
    julgados_acordao_por_competencia_RJ: Optional[List[ChartDataPoint]] = None
    julgados_acordao_por_comarca_RJ: Optional[List[ChartDataPoint]] = None
    julgados_acordao_por_motivo_extincao_RJ: Optional[List[ChartDataPoint]] = None
    julgados_acordao_por_ano_ajuizamento_RJ: Optional[List[ChartDataPoint]] = None
    julgados_acordao_embargos_resultado_RJ: Optional[List[ChartDataPoint]] = None
    julgados_acordao_procedentes_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    julgados_acordao_improcedentes_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    julgados_acordao_extintos_por_mes_RJ: Optional[List[ChartDataPoint]] = None
    julgados_acordao_lista_RJ: Optional[List[JulgadosAcordaoListaRow]] = None
    # Julgados Acórdãos RJ — Estudo das Improcedências (11/11/2026)
    julgados_acordao_improcedencia_por_comarca_RJ: Optional[List[ChartDataPoint]] = None
    julgados_acordao_improcedencia_por_comarca_estoque_RJ: Optional[List[ChartDataPoint]] = None
    julgados_acordao_improcedencia_por_motivo_RJ: Optional[List[ChartDataPoint]] = None
    julgados_acordao_improcedencia_por_motivo_estoque_RJ: Optional[List[ChartDataPoint]] = None
    julgados_acordao_improcedencia_por_relator_RJ: Optional[List[ChartDataPoint]] = None
    julgados_acordao_improcedencia_por_relator_estoque_RJ: Optional[List[ChartDataPoint]] = None
    # Pendências Intermediárias LA
    intermediarias_processos_por_atividade_LA: Optional[List[ChartDataPoint]] = None
    intermediarias_demandas_por_funcionario_LA: Optional[List[Dict[str, Any]]] = None
    intermediarias_processos_por_atividade_por_prazo_LA: Optional[List[ChartDataPoint]] = None
    intermediarias_demandas_por_funcionario_por_prazo_LA: Optional[List[Dict[str, Any]]] = None
    intermediarias_atividades_lista_LA: Optional[List[RecursalAtividadeTarefaRow]] = None
    intermediarias_atividades_lista_filtros_opcoes_LA: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    dilacoes_intermediarias_por_funcionario_LA: Optional[List[DilacaoPorFuncionarioRow]] = None
    intermediarias_por_prazo_lista_LA: Optional[List[RecursalAtividadeTarefaRow]] = None
    intermediarias_por_prazo_lista_filtros_opcoes_LA: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    intermediarias_concluidas_por_mes_LA: Optional[List[ChartDataPoint]] = None
    intermediarias_concluidas_por_dia_LA: Optional[List[ChartDataPoint]] = None
    funcionarios_intermediarias_LA: Optional[List[str]] = None
    intermediarias_concluidas_por_dia_por_funcionario_LA: Optional[Dict[str, List[ChartDataPoint]]] = None
    media_intermediarias_concluidas_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    intermediarias_concluidas_por_prazo_por_mes_LA: Optional[List[ChartDataPoint]] = None
    intermediarias_concluidas_por_prazo_por_dia_LA: Optional[List[ChartDataPoint]] = None
    funcionarios_intermediarias_por_prazo_LA: Optional[List[str]] = None
    intermediarias_concluidas_por_prazo_por_dia_por_funcionario_LA: Optional[Dict[str, List[ChartDataPoint]]] = None
    media_intermediarias_concluidas_por_prazo_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    # Pendências Intermediárias NG
    intermediarias_processos_por_atividade_NG: Optional[List[ChartDataPoint]] = None
    intermediarias_demandas_por_funcionario_NG: Optional[List[Dict[str, Any]]] = None
    intermediarias_processos_por_atividade_por_prazo_NG: Optional[List[ChartDataPoint]] = None
    intermediarias_demandas_por_funcionario_por_prazo_NG: Optional[List[Dict[str, Any]]] = None
    intermediarias_atividades_lista_NG: Optional[List[RecursalAtividadeTarefaRow]] = None
    intermediarias_atividades_lista_filtros_opcoes_NG: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    dilacoes_intermediarias_por_funcionario_NG: Optional[List[DilacaoPorFuncionarioRow]] = None
    intermediarias_por_prazo_lista_NG: Optional[List[RecursalAtividadeTarefaRow]] = None
    intermediarias_por_prazo_lista_filtros_opcoes_NG: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    intermediarias_concluidas_por_mes_NG: Optional[List[ChartDataPoint]] = None
    intermediarias_concluidas_por_dia_NG: Optional[List[ChartDataPoint]] = None
    funcionarios_intermediarias_NG: Optional[List[str]] = None
    intermediarias_concluidas_por_dia_por_funcionario_NG: Optional[Dict[str, List[ChartDataPoint]]] = None
    media_intermediarias_concluidas_por_funcionario_NG: Optional[List[ChartDataPoint]] = None
    intermediarias_concluidas_por_prazo_por_mes_NG: Optional[List[ChartDataPoint]] = None
    intermediarias_concluidas_por_prazo_por_dia_NG: Optional[List[ChartDataPoint]] = None
    funcionarios_intermediarias_por_prazo_NG: Optional[List[str]] = None
    intermediarias_concluidas_por_prazo_por_dia_por_funcionario_NG: Optional[Dict[str, List[ChartDataPoint]]] = None
    media_intermediarias_concluidas_por_prazo_por_funcionario_NG: Optional[List[ChartDataPoint]] = None
    # Emendas e Manifestações LA
    emendas_manifestacoes_processos_por_atividade_LA: Optional[List[ChartDataPoint]] = None
    emendas_manifestacoes_demandas_por_funcionario_LA: Optional[List[Dict[str, Any]]] = None
    emendas_manifestacoes_processos_por_atividade_por_prazo_LA: Optional[List[ChartDataPoint]] = None
    emendas_manifestacoes_demandas_por_funcionario_por_prazo_LA: Optional[List[Dict[str, Any]]] = None
    emendas_manifestacoes_atividades_lista_LA: Optional[List[RecursalAtividadeTarefaRow]] = None
    emendas_manifestacoes_atividades_lista_filtros_opcoes_LA: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    emendas_manifestacoes_por_prazo_lista_LA: Optional[List[RecursalAtividadeTarefaRow]] = None
    emendas_manifestacoes_por_prazo_lista_filtros_opcoes_LA: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    emendas_manifestacoes_concluidas_por_mes_LA: Optional[List[ChartDataPoint]] = None
    emendas_manifestacoes_concluidas_por_dia_LA: Optional[List[ChartDataPoint]] = None
    funcionarios_emendas_manifestacoes_LA: Optional[List[str]] = None
    emendas_manifestacoes_concluidas_por_dia_por_funcionario_LA: Optional[Dict[str, List[ChartDataPoint]]] = None
    media_emendas_manifestacoes_concluidas_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    emendas_manifestacoes_concluidas_por_prazo_por_mes_LA: Optional[List[ChartDataPoint]] = None
    emendas_manifestacoes_concluidas_por_prazo_por_dia_LA: Optional[List[ChartDataPoint]] = None
    funcionarios_emendas_manifestacoes_por_prazo_LA: Optional[List[str]] = None
    emendas_manifestacoes_concluidas_por_prazo_por_dia_por_funcionario_LA: Optional[Dict[str, List[ChartDataPoint]]] = None
    media_emendas_manifestacoes_concluidas_por_prazo_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    emendas_manifestacoes_comissionamento_por_funcionario_LA: Optional[List[EmendasManifestacoesComissaoRow]] = None
    # Emendas e Manifestações NG
    emendas_manifestacoes_processos_por_atividade_NG: Optional[List[ChartDataPoint]] = None
    emendas_manifestacoes_demandas_por_funcionario_NG: Optional[List[Dict[str, Any]]] = None
    emendas_manifestacoes_processos_por_atividade_por_prazo_NG: Optional[List[ChartDataPoint]] = None
    emendas_manifestacoes_demandas_por_funcionario_por_prazo_NG: Optional[List[Dict[str, Any]]] = None
    emendas_manifestacoes_atividades_lista_NG: Optional[List[RecursalAtividadeTarefaRow]] = None
    emendas_manifestacoes_atividades_lista_filtros_opcoes_NG: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    emendas_manifestacoes_por_prazo_lista_NG: Optional[List[RecursalAtividadeTarefaRow]] = None
    emendas_manifestacoes_por_prazo_lista_filtros_opcoes_NG: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    emendas_manifestacoes_concluidas_por_mes_NG: Optional[List[ChartDataPoint]] = None
    emendas_manifestacoes_concluidas_por_dia_NG: Optional[List[ChartDataPoint]] = None
    funcionarios_emendas_manifestacoes_NG: Optional[List[str]] = None
    emendas_manifestacoes_concluidas_por_dia_por_funcionario_NG: Optional[Dict[str, List[ChartDataPoint]]] = None
    media_emendas_manifestacoes_concluidas_por_funcionario_NG: Optional[List[ChartDataPoint]] = None
    emendas_manifestacoes_concluidas_por_prazo_por_mes_NG: Optional[List[ChartDataPoint]] = None
    emendas_manifestacoes_concluidas_por_prazo_por_dia_NG: Optional[List[ChartDataPoint]] = None
    funcionarios_emendas_manifestacoes_por_prazo_NG: Optional[List[str]] = None
    emendas_manifestacoes_concluidas_por_prazo_por_dia_por_funcionario_NG: Optional[Dict[str, List[ChartDataPoint]]] = None
    media_emendas_manifestacoes_concluidas_por_prazo_por_funcionario_NG: Optional[List[ChartDataPoint]] = None
    emendas_manifestacoes_comissionamento_por_funcionario_NG: Optional[List[EmendasManifestacoesComissaoRow]] = None
    # Réplicas LA
    replicas_processos_por_atividade_LA: Optional[List[ChartDataPoint]] = None
    replicas_demandas_por_funcionario_LA: Optional[List[Dict[str, Any]]] = None
    replicas_processos_por_atividade_por_prazo_LA: Optional[List[ChartDataPoint]] = None
    replicas_demandas_por_funcionario_por_prazo_LA: Optional[List[Dict[str, Any]]] = None
    replicas_atividades_lista_LA: Optional[List[RecursalAtividadeTarefaRow]] = None
    replicas_atividades_lista_filtros_opcoes_LA: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    replicas_por_prazo_lista_LA: Optional[List[RecursalAtividadeTarefaRow]] = None
    replicas_por_prazo_lista_filtros_opcoes_LA: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    replicas_concluidas_por_mes_LA: Optional[List[ChartDataPoint]] = None
    replicas_concluidas_por_dia_LA: Optional[List[ChartDataPoint]] = None
    funcionarios_replicas_LA: Optional[List[str]] = None
    replicas_concluidas_por_dia_por_funcionario_LA: Optional[Dict[str, List[ChartDataPoint]]] = None
    media_replicas_concluidas_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    replicas_concluidas_por_prazo_por_mes_LA: Optional[List[ChartDataPoint]] = None
    replicas_concluidas_por_prazo_por_dia_LA: Optional[List[ChartDataPoint]] = None
    funcionarios_replicas_por_prazo_LA: Optional[List[str]] = None
    replicas_concluidas_por_prazo_por_dia_por_funcionario_LA: Optional[Dict[str, List[ChartDataPoint]]] = None
    media_replicas_concluidas_por_prazo_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    replicas_processos_por_atividade_NG: Optional[List[ChartDataPoint]] = None
    replicas_demandas_por_funcionario_NG: Optional[List[Dict[str, Any]]] = None
    replicas_processos_por_atividade_por_prazo_NG: Optional[List[ChartDataPoint]] = None
    replicas_demandas_por_funcionario_por_prazo_NG: Optional[List[Dict[str, Any]]] = None
    replicas_atividades_lista_NG: Optional[List[RecursalAtividadeTarefaRow]] = None
    replicas_atividades_lista_filtros_opcoes_NG: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    replicas_por_prazo_lista_NG: Optional[List[RecursalAtividadeTarefaRow]] = None
    replicas_por_prazo_lista_filtros_opcoes_NG: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    replicas_concluidas_por_mes_NG: Optional[List[ChartDataPoint]] = None
    replicas_concluidas_por_dia_NG: Optional[List[ChartDataPoint]] = None
    funcionarios_replicas_NG: Optional[List[str]] = None
    replicas_concluidas_por_dia_por_funcionario_NG: Optional[Dict[str, List[ChartDataPoint]]] = None
    media_replicas_concluidas_por_funcionario_NG: Optional[List[ChartDataPoint]] = None
    replicas_concluidas_por_prazo_por_mes_NG: Optional[List[ChartDataPoint]] = None
    replicas_concluidas_por_prazo_por_dia_NG: Optional[List[ChartDataPoint]] = None
    funcionarios_replicas_por_prazo_NG: Optional[List[str]] = None
    replicas_concluidas_por_prazo_por_dia_por_funcionario_NG: Optional[Dict[str, List[ChartDataPoint]]] = None
    media_replicas_concluidas_por_prazo_por_funcionario_NG: Optional[List[ChartDataPoint]] = None
    # Reajuizamento LA
    reajuizamento_processos_por_atividade_LA: Optional[List[ChartDataPoint]] = None
    reajuizamento_demandas_por_funcionario_LA: Optional[List[Dict[str, Any]]] = None
    reajuizamento_atividades_lista_LA: Optional[List[RecursalAtividadeTarefaRow]] = None
    reajuizamento_atividades_lista_filtros_opcoes_LA: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    reajuizamento_concluidas_por_mes_LA: Optional[List[ChartDataPoint]] = None
    reajuizamento_concluidas_por_dia_LA: Optional[List[ChartDataPoint]] = None
    funcionarios_reajuizamento_LA: Optional[List[str]] = None
    reajuizamento_concluidas_por_dia_por_funcionario_LA: Optional[Dict[str, List[ChartDataPoint]]] = None
    media_reajuizamento_concluidas_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    reajuizamento_motivo_extincao_LA: Optional[List[ChartDataPoint]] = None
    reajuizamento_status_processo_LA: Optional[List[ChartDataPoint]] = None
    reajuizamento_extincao_por_grau_LA: Optional[List[ChartDataPoint]] = None
    ranking_relatores_recursal_LA: Optional[List[RecursalRankingMagistradoRow]] = None
    execucao_por_materia_LA: Optional[List[ChartDataPoint]] = None
    valor_execucao_por_materia_LA: Optional[List[ChartDataPoint]] = None
    execucao_por_ano_ajuizamento_LA: Optional[List[ChartDataPoint]] = None
    execucao_por_faixa_ultima_movimentacao_LA: Optional[List[ChartDataPoint]] = None
    valor_saida_execucao_por_mes_LA: Optional[List[ChartDataPoint]] = None
    valor_execucao_saida_periodo_por_mes_LA: Optional[List[ChartDataPoint]] = None
    valor_remanescente_por_mes_LA: Optional[List[ChartDataPoint]] = None
    quantidade_saida_execucao_por_mes_LA: Optional[List[ChartDataPoint]] = None
    quantidade_entrada_execucao_por_mes_LA: Optional[List[ChartDataPoint]] = None
    valor_entrada_execucao_por_mes_LA: Optional[List[ChartDataPoint]] = None
    execucao_media_tempo_por_mes_LA: Optional[List[ChartDataPoint]] = None
    execucao_estoque_quantidade_por_mes_LA: Optional[List[ChartDataPoint]] = None
    execucao_estoque_valor_por_mes_LA: Optional[List[ChartDataPoint]] = None
    execucao_processos_por_atividade_LA: Optional[List[ChartDataPoint]] = None
    execucao_atividades_ativas_por_atividade_LA: Optional[List[ChartDataPoint]] = None
    execucao_atividades_criadas_por_atividade_LA: Optional[List[ChartDataPoint]] = None
    execucao_atividades_ativas_por_atividade_por_prazo_LA: Optional[List[ChartDataPoint]] = None
    execucao_processos_por_atividade_por_prazo_LA: Optional[List[ChartDataPoint]] = None
    execucao_demandas_por_funcionario_LA: Optional[List[Dict[str, Any]]] = None
    execucao_demandas_por_funcionario_completo_LA: Optional[List[Dict[str, Any]]] = None
    execucao_taxa_conclusao_por_funcionario_LA: Optional[List[Dict[str, Any]]] = None
    execucao_entrada_fluxo_cs_por_mes_LA: Optional[List[Dict[str, Any]]] = None
    execucao_alvara_expedido_lista_LA: Optional[List[Dict[str, Any]]] = None
    execucao_alvaras_expedidos_por_dia_LA: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_alvaras_expedidos_por_dia_LA: Optional[List[Dict[str, Any]]] = None
    execucao_acordos_alvara_expedido_lista_LA: Optional[List[Dict[str, Any]]] = None
    execucao_demandas_por_funcionario_por_prazo_LA: Optional[List[Dict[str, Any]]] = None
    execucao_demandas_por_funcionario_por_prazo_completo_LA: Optional[List[Dict[str, Any]]] = None
    execucao_valor_recuperado_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    execucao_resolvidos_por_dia_LA: Optional[List[ChartDataPoint]] = None
    execucao_resolvidos_por_dia_por_prazo_LA: Optional[List[ChartDataPoint]] = None
    execucao_media_resolvidos_por_funcionario_LA: Optional[List[ChartDataPoint]] = None
    execucao_media_resolvidos_por_funcionario_por_prazo_LA: Optional[List[ChartDataPoint]] = None
    execucao_nao_cumprido_por_motivo_LA: Optional[List[ChartDataPoint]] = None
    execucao_atividades_lista_LA: Optional[List[RecursalAtividadeTarefaRow]] = None
    execucao_atividades_abertas_LA: Optional[List[RecursalAtividadeTarefaRow]] = None
    execucao_atividades_lista_por_prazo_LA: Optional[List[RecursalAtividadeTarefaRow]] = None
    execucao_atividades_lista_filtros_opcoes_LA: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    execucao_atividades_lista_filtros_opcoes_por_prazo_LA: Optional[RecursalAtividadesListaFiltrosOpcoes] = None
    execucao_atrasos_detalhamento_LA: Optional[ExecucaoAtrasosDetalhamento] = None

    # NPS NG
    nps_por_classificacao: Optional[List[ChartDataPoint]] = None
    nps_por_nota: Optional[List[ChartDataPoint]] = None
    nps_por_mes: Optional[List[ChartDataPoint]] = None
    nps_respostas_tabela: Optional[List[NpsRespostaRow]] = None
    nps_feedbacks_melhoria: Optional[List[NpsFeedbackMelhoriaRow]] = None
    nps_feedbacks_positivos: Optional[List[NpsFeedbackPositivoRow]] = None
    nps_comentarios: Optional[List[NpsComentarioRow]] = None

    # Marketing NG
    marketing_ng_faixa_etaria: Optional[List[ChartDataPoint]] = None
    marketing_ng_genero: Optional[List[ChartDataPoint]] = None
    marketing_ng_origem: Optional[List[ChartDataPoint]] = None
    marketing_ng_ocupacao: Optional[List[ChartDataPoint]] = None
    marketing_ng_tipo_trafego: Optional[List[ChartDataPoint]] = None
    marketing_ng_dispositivo: Optional[List[ChartDataPoint]] = None
    marketing_ng_prospeccao: Optional[List[ChartDataPoint]] = None
    marketing_ng_faixa_salarial: Optional[List[ChartDataPoint]] = None

    # Marketing NG · Triados
    marketing_ng_triados_faixa_etaria: Optional[List[ChartDataPoint]] = None
    marketing_ng_triados_genero: Optional[List[ChartDataPoint]] = None
    marketing_ng_triados_origem: Optional[List[ChartDataPoint]] = None
    marketing_ng_triados_ocupacao: Optional[List[ChartDataPoint]] = None
    marketing_ng_triados_tipo_trafego: Optional[List[ChartDataPoint]] = None
    marketing_ng_triados_dispositivo: Optional[List[ChartDataPoint]] = None
    marketing_ng_triados_prospeccao: Optional[List[ChartDataPoint]] = None
    marketing_ng_triados_faixa_salarial: Optional[List[ChartDataPoint]] = None
    marketing_ng_triados_tipo_residencia: Optional[List[ChartDataPoint]] = None
    marketing_ng_triados_pessoas_dependentes: Optional[List[ChartDataPoint]] = None
    marketing_ng_funil_pipeline: Optional[List[ChartDataPoint]] = None
    marketing_ng_investimento_cliques_leads: Optional[List[InvestimentoCliquesLeadsPoint]] = None
    marketing_ng_rubrica_campanha: Optional[List[RubricaCampanhaPoint]] = None
    marketing_ng_rubrica_protocolado: Optional[List[RubricaCampanhaPoint]] = None
    marketing_ng_total_clientes_campanha: Optional[List[ChartDataPoint]] = None
    marketing_ng_protocolo_resolvido_total: Optional[List[ChartDataPoint]] = None
    marketing_ng_valor_causa_total: Optional[List[ChartDataPoint]] = None
    marketing_ng_trackeamento_categoria: Optional[List[ChartDataPoint]] = None
    marketing_ng_trackeamento_posicionamento: Optional[List[ChartDataPoint]] = None
    marketing_ng_trackeamento_canal_aquisicao: Optional[List[ChartDataPoint]] = None
    marketing_ng_trackeamento_campanha: Optional[List[ChartDataPoint]] = None
    marketing_ng_fechamento_categoria: Optional[List[ChartDataPoint]] = None
    marketing_ng_fechamento_posicionamento: Optional[List[ChartDataPoint]] = None
    marketing_ng_fechamento_canal_aquisicao: Optional[List[ChartDataPoint]] = None
    marketing_ng_fechamento_campanha: Optional[List[ChartDataPoint]] = None
    marketing_ng_ind_campanha: Optional[List[ChartDataPoint]] = None
    marketing_ng_ind_posicionamento: Optional[List[ChartDataPoint]] = None
    marketing_ng_ind_conjunto: Optional[List[ChartDataPoint]] = None
    marketing_ng_ind_criativo: Optional[List[ChartDataPoint]] = None
    marketing_ng_ind_categoria: Optional[List[ChartDataPoint]] = None
    marketing_ng_ind_rubricas: Optional[List[ChartDataPoint]] = None
    marketing_ng_org_campanha: Optional[List[ChartDataPoint]] = None
    marketing_ng_org_posicionamento: Optional[List[ChartDataPoint]] = None
    marketing_ng_org_conjunto: Optional[List[ChartDataPoint]] = None
    marketing_ng_org_criativo: Optional[List[ChartDataPoint]] = None
    marketing_ng_org_categoria: Optional[List[ChartDataPoint]] = None
    marketing_ng_org_rubricas_total: Optional[List[ChartDataPoint]] = None
    marketing_ng_org_rubricas_facebook: Optional[List[ChartDataPoint]] = None
    marketing_ng_org_rubricas_instagram: Optional[List[ChartDataPoint]] = None
    marketing_ng_org_rubricas_site: Optional[List[ChartDataPoint]] = None
    marketing_ng_org_rubricas_google: Optional[List[ChartDataPoint]] = None

    # Marketing LexPre NG (perfil de clientes)
    marketing_lexpre_ng_faixa_etaria: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_genero: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_origem: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_ocupacao: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_tipo_trafego: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_prospeccao: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_faixa_salarial: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_triados_faixa_etaria: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_triados_genero: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_triados_origem: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_triados_ocupacao: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_triados_tipo_trafego: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_triados_prospeccao: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_triados_faixa_salarial: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_triados_tipo_residencia: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_triados_pessoas_dependentes: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_investimento_cliques_leads: Optional[List[InvestimentoCliquesLeadsPoint]] = None
    marketing_lexpre_ng_total_clientes_campanha: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_protocolo_resolvido_total: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_valor_causa_total: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_rubrica_campanha: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_rubrica_protocolado: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_trackeamento_categoria: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_trackeamento_posicionamento: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_trackeamento_canal_aquisicao: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_trackeamento_campanha: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_fechamento_categoria: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_fechamento_posicionamento: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_fechamento_canal_aquisicao: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_fechamento_campanha: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_ind_campanha: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_ind_posicionamento: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_ind_conjunto: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_ind_criativo: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_ind_categoria: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_org_campanha: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_org_posicionamento: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_org_conjunto: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_org_criativo: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_org_categoria: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_org_rubricas_total: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_org_rubricas_facebook: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_org_rubricas_instagram: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_org_rubricas_site: Optional[List[ChartDataPoint]] = None
    marketing_lexpre_ng_org_rubricas_google: Optional[List[ChartDataPoint]] = None


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
