# Funções de análises do setor de Execução (Condenação) — RJ
#
# Mirror de app/analyses/NG/execucao.py para o escritório Luis Albert RJ (LARJ,
# ID_ESCRITORIO=27). Mesma lógica de negócio; só muda o escritório-alvo e os
# nomes das funções (sufixo _RJ), seguindo o padrão já usado em
# app/analyses/RJ/execucao_acordos_RJ.py.

from __future__ import annotations

from app.analyses.common import unidade as _unidade  # V2: valores da unidade (common/unidade.py)
from app.analyses.familias import execucao as _familia  # V2: código único da família (familias/execucao.py)
import json
import unicodedata
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from app.analyses.common import textos  # V2: nomes e rótulos de texto num módulo só
from app.analyses.common import periodo  # V2: período e variação vs período anterior num módulo só
from app.analyses.common import conversao  # V2: conversões dos valores do banco num módulo só
from app.analyses.common import atividades  # V2: regras das atividades num módulo só
from app.analyses.common import memo  # V2: cache por pedido (a mesma conta uma vez por pedido)
from app.analyses.common import tempo  # V2: média/mediana de tempo num módulo só
from app.utils import ordem_mes  # V2: séries mês a mês em ordem cronológica
from app.utils import parse_date_from_db
from app.analyses.execucao_estoque_mensal import estoque_por_mes, indice_mes

# V2: os valores desta unidade para a família, lidos ao vivo deste módulo (common/unidade.py).
_VALORES_UNIDADE = _unidade.ValoresDoModulo(globals(), {"ID_ESCRITORIO": "ID_ESCRITORIO", "_ATIVIDADES": "_ATIVIDADES"})


# =============================================================================
# Constantes
# =============================================================================

ID_FASE_EXECUCAO = _familia.ID_FASE_EXECUCAO

ID_FASE_FINANCEIRO = _familia.ID_FASE_FINANCEIRO
ID_ESCRITORIO = 27
ID_SITUACAO_ATIVO = _familia.ID_SITUACAO_ATIVO

_COL_ID_ESCRITORIO = _familia._COL_ID_ESCRITORIO

_COL_ID_SITUACAO = _familia._COL_ID_SITUACAO

SEM_DATA_ULTIMA_MOVIMENTACAO = _familia.SEM_DATA_ULTIMA_MOVIMENTACAO

_MONTH_NAMES = _familia._MONTH_NAMES

_FAIXAS_ULTIMA_MOVIMENTACAO_ORDEM = _familia._FAIXAS_ULTIMA_MOVIMENTACAO_ORDEM


# =============================================================================
# 1 - Helpers internos
# =============================================================================

_to_date = _familia._to_date


_get_data_execucao_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_data_execucao)


_get_data_compensacao_alvara_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_data_compensacao_alvara)


_get_data_compensacao_alvara_incontroverso_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_data_compensacao_alvara_incontroverso)


_normalizar_titulo_extra = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._normalizar_titulo_extra)


_campos_extras = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._campos_extras)


_eventos_incontroverso = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._eventos_incontroverso)


_get_data_encerramento_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_data_encerramento)


_get_ultima_movimentacao_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ultima_movimentacao)


_get_data_distribuicao_rj = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_data_distribuicao)


_data_no_periodo = _familia._data_no_periodo


_converter_valor = _familia._converter_valor


_to_int = _familia._to_int


_base_execucao_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._base_execucao)


_get_valor_execucao_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_valor_execucao)


_get_valor_ted_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_valor_ted)


_get_valor_incontroverso_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_valor_incontroverso)


_get_valor_remanescente_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_valor_remanescente)


_get_valor_execucao_em_aberto_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_valor_execucao_em_aberto)


_get_valor_honorarios_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_valor_honorarios)


_processo_em_execucao_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._processo_em_execucao)


_processo_fase_financeiro_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._processo_fase_financeiro)


# =============================================================================
# 2 - Queries de filtragem
# =============================================================================

_filtrar_em_execucao_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_em_execucao)


_filtrar_entrada_execucao_RJ_no_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_entrada_execucao_no_periodo)


_filtrar_saida_no_periodo_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_saida_no_periodo)


_filtrar_saida_incontroverso_no_periodo_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_saida_incontroverso_no_periodo)


_normalizar_materia = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._normalizar_materia)


_primeiro_valor_preenchido_rj = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._primeiro_valor_preenchido)


group_alvaras_expedidos_por_dia_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_alvaras_expedidos_por_dia)


_SUBFASES_ALVARA_EXPEDIDO = _familia._SUBFASES_ALVARA_EXPEDIDO


list_processos_alvara_expedido_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.list_processos_alvara_expedido)


_normalizar_subfase = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._normalizar_subfase)


_normalizar_comarca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._normalizar_comarca)


filter_execucao_RJ_por_materia = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filter_execucao_por_materia)


filter_execucao_RJ_por_subfase = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filter_execucao_por_subfase)


_SEM_ANO_AJUIZAMENTO_EXEC_RJ = _familia._SEM_ANO_AJUIZAMENTO_EXEC


filter_execucao_RJ_por_ano_ajuizamento = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filter_execucao_por_ano_ajuizamento)


filter_execucao_RJ_por_uf = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filter_execucao_por_uf)


get_opcoes_uf_execucao_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_uf_execucao)


filter_execucao_RJ_por_comarca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filter_execucao_por_comarca)


get_opcoes_comarca_execucao_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_comarca_execucao)


get_opcoes_materia_execucao_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_materia_execucao)


get_opcoes_subfase_execucao_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_subfase_execucao)


# =============================================================================
# 3 - Totais
# =============================================================================

get_total_execucao_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_execucao)


get_total_entrada_execucao_RJ_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_entrada_execucao_periodo)


get_total_saida_execucao_RJ_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_saida_execucao_periodo)


get_estoque_final_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_estoque_final)


get_tre = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_tre)


get_tre_execucao_RJ_dax = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_tre_execucao_dax)


# =============================================================================
# 4 - Valores monetários
# =============================================================================

get_valor_causa_total_execucao_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_total_execucao)


get_detalhe_valor_execucao_vazio_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_detalhe_valor_execucao_vazio)


get_total_valor_execucao_vazio_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_valor_execucao_vazio)


get_valor_honorarios_total_execucao_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_honorarios_total_execucao)


get_valor_em_execucao_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_em_execucao)


get_valor_remanescente_em_execucao_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_remanescente_em_execucao)


get_valor_execucao_saida_periodo_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_execucao_saida_periodo)


get_valor_incontroverso_saida_periodo_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_incontroverso_saida_periodo)


get_total_incontroverso_saida_periodo_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_incontroverso_saida_periodo)


_somar_campos_ted_rj = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._somar_campos_ted)


get_valor_ted_saida_execucao_RJ_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_ted_saida_execucao_periodo)


get_taxa_recuperacao_execucao_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_taxa_recuperacao_execucao)


# =============================================================================
# 5 - Agrupamentos
# =============================================================================

group_valor_saida_execucao_RJ_por_mes = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_valor_saida_execucao_por_mes)


group_valor_execucao_saida_periodo_RJ_por_mes = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_valor_execucao_saida_periodo_por_mes)


group_valor_remanescente_por_mes_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_valor_remanescente_por_mes)


group_quantidade_saida_execucao_RJ_por_mes = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_quantidade_saida_execucao_por_mes)


group_quantidade_entrada_execucao_RJ_por_mes = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_quantidade_entrada_execucao_por_mes)


group_valor_entrada_execucao_RJ_por_mes = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_valor_entrada_execucao_por_mes)


group_execucao_RJ_por_subfase = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_por_subfase)


_uf_por_comarca_rj = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._uf_por_comarca)


group_execucao_RJ_por_comarca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_por_comarca)


group_valor_execucao_RJ_por_comarca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_valor_execucao_por_comarca)


group_valor_execucao_RJ_por_subfase = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_valor_execucao_por_subfase)


group_execucao_RJ_por_materia = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_por_materia)


group_valor_execucao_RJ_por_materia = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_valor_execucao_por_materia)


group_execucao_RJ_por_ano_ajuizamento = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_por_ano_ajuizamento)


# =============================================================================
# 6 - Análise temporal
# =============================================================================

_extrair_duracoes_dias_rj = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._extrair_duracoes_dias)


get_media_tempo_execucao_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_media_tempo_execucao)


get_mediana_tempo_execucao_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_mediana_tempo_execucao)


get_media_tempo_execucao_RJ_por_mes = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_media_tempo_execucao_por_mes)


_classificar_faixa_ultima_movimentacao_rj = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._classificar_faixa_ultima_movimentacao)


group_execucao_RJ_por_faixa_ultima_movimentacao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_por_faixa_ultima_movimentacao)


# =============================================================================
# 7 - Atividades no período (agendamentos do setor Execução RJ)
# =============================================================================

_STATUS_INATIVO_EXEC_RJ = _familia._STATUS_INATIVO_EXEC

_STATUS_EM_ANDAMENTO_EXEC_RJ = _familia._STATUS_EM_ANDAMENTO_EXEC

_STATUS_ENCERRADO_EXEC_RJ = _familia._STATUS_ENCERRADO_EXEC

_STATUS_FILTRO_EXEC_RJ = _familia._STATUS_FILTRO_EXEC

_SITUACOES_FILTRO_EXEC_RJ = _familia._SITUACOES_FILTRO_EXEC

SITUACOES_VALIDAS_EXECUCAO_RJ = _familia.SITUACOES_VALIDAS_EXECUCAO

_STATUS_DEMANDAS_FUNCIONARIO_EXEC_RJ = _familia._STATUS_DEMANDAS_FUNCIONARIO_EXEC

_SLUG_POR_STATUS_EXEC_RJ = _familia._SLUG_POR_STATUS_EXEC

_SEM_ATIVIDADE_EXEC_RJ = _familia._SEM_ATIVIDADE_EXEC

_SEM_FUNCIONARIO_EXEC_RJ = _familia._SEM_FUNCIONARIO_EXEC

_STATUS_CUMPRIDO_EXEC_RJ = _familia._STATUS_CUMPRIDO_EXEC

_COL_FUNCIONARIO_ATRIBUIDO_EXEC_RJ = _familia._COL_FUNCIONARIO_ATRIBUIDO_EXEC

_COL_FUNCIONARIO_ENCERRAMENTO_EXEC_RJ = _familia._COL_FUNCIONARIO_ENCERRAMENTO_EXEC

_COL_ID_USUARIO_ENCERRAMENTO_EXEC_RJ = _familia._COL_ID_USUARIO_ENCERRAMENTO_EXEC

# Reutiliza helpers de data já definidos no módulo
_ag_to_date = _familia._ag_to_date

_ag_data_no_periodo = _familia._ag_data_no_periodo


_nome_em_conjunto_exec_rj = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._nome_em_conjunto_exec)


_get_ag_status_rj = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_status)


_get_ag_data_criacao_rj = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_data_criacao)


_get_ag_data_conclusao_rj = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_data_conclusao)


_get_ag_prazo_rj = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_prazo)


_get_ag_processo_id_rj = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_processo_id)


_get_ag_numero_processo_rj = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_numero_processo)


_get_ag_valor_sentenca_rj = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_valor_sentenca)


_get_ag_valor_acordao_rj = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_valor_acordao)


_get_ag_atividade_nome_rj = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_atividade_nome)


_get_ag_funcionario_atribuido_rj = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_funcionario_atribuido)


_get_ag_funcionario_encerramento_rj = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_funcionario_encerramento)


# V2: como estas atividades são lidas e quais status contam (app/analyses/common/atividades.py).
_ATIVIDADES = atividades.Leitor(
    criacao=_get_ag_data_criacao_rj,
    conclusao=_get_ag_data_conclusao_rj,
    prazo=_get_ag_prazo_rj,
    status=_get_ag_status_rj,
    funcionario_encerramento=_get_ag_funcionario_encerramento_rj,
)
_STATUS_ATIVIDADES = _familia._STATUS_ATIVIDADES


_get_ag_funcionario_nome_rj = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_funcionario_nome)


_incluir_na_lista_exec_rj = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._incluir_na_lista_exec)


_classificar_situacao_exec_rj = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._classificar_situacao_exec)


_filtrar_ag_encerrados_no_periodo_rj = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_ag_encerrados_no_periodo)


def get_kpis_atividades_execucao_RJ(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, int]:
    """KPIs de agendamentos do setor Execução RJ no período."""
    ref = ref_date or date.today()
    total = em_andamento = vencidas = vencem_hoje = concluidas = 0
    total_criadas = criadas_em_andamento = 0
    abertas = 0

    for row in agendamentos:
        criacao = _get_ag_data_criacao_rj(row)
        conclusao = _get_ag_data_conclusao_rj(row)
        status = _get_ag_status_rj(row) or ""
        prazo = _get_ag_prazo_rj(row)
        ativo = status not in _STATUS_INATIVO_EXEC_RJ
        criada_periodo = _ag_data_no_periodo(criacao, from_date, to_date)

        # "Abertas": tudo atualmente em aberto, independente do período (card
        # unificado "Em andamento" da Confecção CS) — mesmo critério do NG.
        if ativo:
            abertas += 1

        # "Criadas": tudo que chegou no período, mesmo já concluído; só exclui Cancelado.
        if criada_periodo and status != "Cancelado":
            total_criadas += 1
            if status not in _STATUS_ENCERRADO_EXEC_RJ:
                criadas_em_andamento += 1

        if criada_periodo and ativo:
            total += 1
            if status in _STATUS_EM_ANDAMENTO_EXEC_RJ:
                em_andamento += 1

        if ativo and prazo is not None:
            if prazo < ref:
                vencidas += 1
            elif prazo == ref:
                vencem_hoje += 1

        if status in _STATUS_ENCERRADO_EXEC_RJ:
            if _ag_data_no_periodo(conclusao, from_date, to_date):
                concluidas += 1

    return {
        "total_atividades_execucao_RJ": total,
        "atividades_execucao_em_andamento_RJ": em_andamento,
        "atividades_execucao_vencidas_RJ": vencidas,
        "atividades_execucao_vencem_hoje_RJ": vencem_hoje,
        "atividades_execucao_concluidas_RJ": concluidas,
        "total_atividades_criadas_execucao_RJ": total_criadas,
        "atividades_criadas_em_andamento_execucao_RJ": criadas_em_andamento,
        "atividades_execucao_abertas_RJ": abertas,
    }


get_media_mensal_atividades_execucao_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_media_mensal_atividades_execucao)


group_execucao_processos_por_atividade_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_processos_por_atividade)


group_atividades_ativas_criadas_por_atividade_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_atividades_ativas_criadas_por_atividade)


group_atividades_criadas_por_atividade_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_atividades_criadas_por_atividade)


group_atividades_ativas_por_prazo_por_atividade_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_atividades_ativas_por_prazo_por_atividade)


group_execucao_demandas_por_funcionario_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_demandas_por_funcionario)


_SEM_FUNCIONARIO_ENCERRAMENTO_EXEC_RJ = _familia._SEM_FUNCIONARIO_ENCERRAMENTO_EXEC


group_execucao_demandas_por_funcionario_completo_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_demandas_por_funcionario_completo)


def group_taxa_conclusao_por_funcionario_RJ(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Taxa de conclusão por colaborador ATRIBUÍDO — RJ, espelho de
    :func:`group_taxa_conclusao_por_funcionario_NG`: ``percent`` = concluídas no
    período ÷ (concluídas + abertas atualmente) do próprio colaborador.
    """
    concluidas: dict[str, int] = defaultdict(int)
    abertas: dict[str, int] = defaultdict(int)
    for row in agendamentos:
        funcionario = _get_ag_funcionario_atribuido_rj(row)
        status = _get_ag_status_rj(row) or ""
        if status in _STATUS_ENCERRADO_EXEC_RJ:
            conclusao = _get_ag_data_conclusao_rj(row)
            if _ag_data_no_periodo(conclusao, from_date, to_date):
                concluidas[funcionario] += 1
        elif status not in _STATUS_INATIVO_EXEC_RJ:
            abertas[funcionario] += 1

    itens: list[dict[str, Any]] = []
    for nome in dict.fromkeys([*concluidas, *abertas]):  # V2: na ordem dos dados (com set, a ordem dos empates mudava a cada vez que a API subia)
        c = concluidas.get(nome, 0)
        a = abertas.get(nome, 0)
        total = c + a
        if total == 0:
            continue
        itens.append({
            "name": nome,
            "encerrado_cumprido": c,
            "abertas": a,
            "total": total,
            "percent": round(100.0 * c / total, 1),
        })
    return sorted(itens, key=lambda x: int(x["total"]), reverse=True)


_ATIVIDADES_FLUXO_CS_1G_RJ = _familia._ATIVIDADES_FLUXO_CS_1G

_ATIVIDADES_FLUXO_CS_2G_RJ = _familia._ATIVIDADES_FLUXO_CS_2G
# Atividade antiga sem grau no nome: vai numa linha própria (decisão do negócio, out/2026 —
# inferir o grau pelo acórdão errava ~43% dos 1G no NG).
_ATIVIDADES_FLUXO_CS_SEM_GRAU_RJ = frozenset({"Elaborar Cumprimento de Sentença".casefold()})
_FLUXO_CS_SEM_GRAU_LABEL_RJ = "CS (sem grau)"
_JANELA_FLUXO_CS_DIAS_RJ = _familia._JANELA_FLUXO_CS_DIAS


def _entradas_por_fluxo_cs_RJ(
    execucao: list[dict[str, Any]],
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[tuple[dict[str, Any], date, str]]:
    """
    ``(processo, DATA_EXECUCAO, fluxo)`` de cada entrada na Execução Condenação no período
    (sem período = histórico completo), com o fluxo da Confecção CS pela regra de
    :func:`group_entrada_execucao_por_fluxo_cs_por_mes_RJ` — ou ``"Outros"`` quando a
    entrada não veio da CS. Base do gráfico de fluxo e da taxa de atualização.
    """
    cs_por_processo: dict[int, list[tuple[date, int, str]]] = defaultdict(list)
    for row in agendamentos:
        status = _get_ag_status_rj(row)
        if status == _STATUS_CUMPRIDO_EXEC_RJ:
            prioridade = 0
        elif status == "Cancelado":
            prioridade = 1
        else:
            continue
        nome = _get_ag_atividade_nome_rj(row).casefold()
        if nome in _ATIVIDADES_FLUXO_CS_1G_RJ:
            grau = "1G"
        elif nome in _ATIVIDADES_FLUXO_CS_2G_RJ:
            grau = "2G"
        elif nome in _ATIVIDADES_FLUXO_CS_SEM_GRAU_RJ:
            grau = _FLUXO_CS_SEM_GRAU_LABEL_RJ
        else:
            continue
        pid = _to_int(_get_ag_processo_id_rj(row))
        conclusao = _get_ag_data_conclusao_rj(row)
        if pid is None or conclusao is None:
            continue
        cs_por_processo[pid].append((conclusao, prioridade, grau))

    resultado: list[tuple[dict[str, Any], date, str]] = []
    for p in _filtrar_entrada_execucao_RJ_no_periodo(execucao, from_date, to_date):
        data_exe = _get_data_execucao_RJ(p)
        pid = _to_int(p.get("id") or p.get("ID"))
        if data_exe is None:
            continue
        candidatos = [
            (abs((conclusao - data_exe).days), prioridade, grau)
            for conclusao, prioridade, grau in cs_por_processo.get(pid, ())
            if abs((conclusao - data_exe).days) <= _JANELA_FLUXO_CS_DIAS_RJ
        ]
        resultado.append((p, data_exe, min(candidatos)[2] if candidatos else "Outros"))
    return resultado


def get_taxa_atualizacao_execucao_RJ(
    execucao: list[dict[str, Any]],
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ano: Optional[int] = None,
) -> dict[str, Any]:
    """
    Taxa de atualização: quanto o valor cresceu da decisão até a Execução, nas entradas da
    Condenação que vieram da Confecção CS (fluxo de :func:`_entradas_por_fluxo_cs_RJ`).
    1G compara ``VALOR_SENTENCA`` com ``VALOR_EXECUCAO``; 2G compara ``VALOR_ACORDAO`` com
    ``VALOR_EXECUCAO``. Taxa = (Σ execução − Σ decisão) ÷ Σ decisão × 100, agregada por fluxo.

    - ``linhas``/``total``: entradas no período; sem um dos dois valores, a entrada fica fora
      da conta e vai para ``sem_valor_processos`` (número do processo e o que falta).
    - ``por_mes``: a mesma taxa mês a mês (mês da ``DATA_EXECUCAO``) do ano ``ano``
      (padrão: ano atual), independente do período.
    """
    campos = {"1G": ("VALOR_SENTENCA", "Sentença"), "2G": ("VALOR_ACORDAO", "Acórdão")}

    def _novo() -> dict[str, Any]:
        return {"quantidade": 0, "sem_valor": 0, "valor_decisao": 0.0, "valor_execucao": 0.0}

    def _valores(p: dict[str, Any], fluxo: str) -> tuple[float, float]:
        decisao_raw = p.get(campos[fluxo][0])
        execucao_raw = p.get("VALOR_EXECUCAO")
        decisao = _converter_valor(decisao_raw) if decisao_raw not in (None, "") else 0.0
        valor_execucao = _converter_valor(execucao_raw) if execucao_raw not in (None, "") else 0.0
        return decisao, valor_execucao

    def _linha(fluxo: str, r: dict[str, Any]) -> dict[str, Any]:
        aumento = r["valor_execucao"] - r["valor_decisao"]
        return {
            "fluxo": fluxo,
            "quantidade": r["quantidade"],
            "sem_valor": r["sem_valor"],
            "valor_decisao": round(r["valor_decisao"], 2),
            "valor_execucao": round(r["valor_execucao"], 2),
            "aumento": round(aumento, 2),
            "taxa": round(100.0 * aumento / r["valor_decisao"], 2) if r["valor_decisao"] else None,
        }

    def _taxa(r: dict[str, Any]) -> Optional[float]:
        if not r["valor_decisao"]:
            return None
        return round(100.0 * (r["valor_execucao"] - r["valor_decisao"]) / r["valor_decisao"], 2)

    resumo = {fluxo: _novo() for fluxo in campos}
    sem_valor_processos: list[dict[str, Any]] = []
    for p, data_exe, fluxo in _entradas_por_fluxo_cs_RJ(execucao, agendamentos, from_date, to_date):
        if fluxo not in campos:
            continue
        decisao, valor_execucao = _valores(p, fluxo)
        if not decisao or not valor_execucao:
            resumo[fluxo]["sem_valor"] += 1
            faltando = [nome for nome, ok in ((campos[fluxo][1], decisao), ("Execução", valor_execucao)) if not ok]
            sem_valor_processos.append({
                "numero_processo": str(p.get("NUMERO_PROCESSO") or "").strip() or None,
                "fluxo": fluxo,
                "data_entrada": data_exe.isoformat(),
                "faltando": faltando,
            })
            continue
        resumo[fluxo]["quantidade"] += 1
        resumo[fluxo]["valor_decisao"] += decisao
        resumo[fluxo]["valor_execucao"] += valor_execucao

    ano_ref = ano or date.today().year
    meses: dict[int, dict[str, dict[str, Any]]] = {}
    for p, data_exe, fluxo in _entradas_por_fluxo_cs_RJ(execucao, agendamentos):
        if fluxo not in campos or data_exe.year != ano_ref:
            continue
        decisao, valor_execucao = _valores(p, fluxo)
        if not decisao or not valor_execucao:
            continue
        mes = meses.setdefault(data_exe.month, {"1G": _novo(), "2G": _novo(), "Total": _novo()})
        for chave in (fluxo, "Total"):
            mes[chave]["quantidade"] += 1
            mes[chave]["valor_decisao"] += decisao
            mes[chave]["valor_execucao"] += valor_execucao
    por_mes = [
        {
            "mes": m,
            "name": f"{_MONTH_NAMES[m - 1]} {ano_ref}",
            "1G": _taxa(meses[m]["1G"]),
            "2G": _taxa(meses[m]["2G"]),
            "Total": _taxa(meses[m]["Total"]),
            "quantidade": meses[m]["Total"]["quantidade"],
            # Valor da decisão do mês: sentença (1G) e acórdão (2G) — linhas do gráfico do modal.
            "valor_sentenca": round(meses[m]["1G"]["valor_decisao"], 2),
            "valor_acordao": round(meses[m]["2G"]["valor_decisao"], 2),
        }
        for m in sorted(meses)
    ]

    total = {
        k: sum(r[k] for r in resumo.values())
        for k in ("quantidade", "sem_valor", "valor_decisao", "valor_execucao")
    }
    return {
        "linhas": [_linha(fluxo, r) for fluxo, r in resumo.items()],
        "total": _linha("Total", total),
        "sem_valor_processos": sorted(sem_valor_processos, key=lambda x: x["data_entrada"], reverse=True),
        "ano": ano_ref,
        "por_mes": por_mes,
    }


def group_entrada_execucao_por_fluxo_cs_por_mes_RJ(
    execucao: list[dict[str, Any]],
    agendamentos: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Espelho de :func:`group_entrada_execucao_por_fluxo_cs_por_mes_NG` — entradas da
    Execução Condenação por mês que vieram da Confecção CS, em ``"1G"``, ``"2G"`` e
    ``"CS (sem grau)"`` (atividade antiga "Elaborar Cumprimento de Sentença").
    Conta CS "Encerrado Cumprido" ou "Cancelado" com encerramento a até 30 dias da
    entrada; vale a mais próxima, e no empate a Cumprida.
    """
    grouped: dict[str, dict[str, Any]] = {}
    for p, data_exe, grau in _entradas_por_fluxo_cs_RJ(execucao, agendamentos):
        month_key = f"{data_exe.year}-{data_exe.month:02d}"
        if month_key not in grouped:
            grouped[month_key] = {
                "name": f"{_MONTH_NAMES[data_exe.month - 1]} {data_exe.year}",
                "1G": 0,
                "2G": 0,
                _FLUXO_CS_SEM_GRAU_LABEL_RJ: 0,
                "Outros": 0,
            }
        # Sem CS por perto: a entrada veio por outro caminho — "Outros" faz a soma das
        # linhas bater com o total de entradas da Condenação (card "Quantidade de entrada").
        grouped[month_key][grau] += 1

    return [grouped[k] for k in sorted(grouped)]


group_execucao_resolvidos_por_dia_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_resolvidos_por_dia)


get_media_execucao_resolvidos_por_funcionario_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_media_execucao_resolvidos_por_funcionario)


group_valor_recuperado_por_funcionario_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_valor_recuperado_por_funcionario)


list_execucao_atividades_periodo_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.list_execucao_atividades_periodo)


get_opcoes_filtros_execucao_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_filtros_execucao)


_agendamento_match_filtros_exec_rj = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._agendamento_match_filtros_exec)


filtrar_agendamentos_execucao_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_agendamentos_execucao)


# ---------------------------------------------------------------------------
# Análise por Prazo — RJ (mesmas 5 métricas, mas usando PRAZO como eixo
# temporal em vez de DATA_HORA_CRIACAO/DATA_HORA_CONCLUSAO).
# ---------------------------------------------------------------------------

_incluir_na_lista_por_prazo_exec_rj = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._incluir_na_lista_por_prazo_exec)


_classificar_situacao_por_prazo_exec_rj = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._classificar_situacao_por_prazo_exec)


def get_kpis_execucao_por_prazo_RJ(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, int]:
    """KPIs de agendamentos do setor Execução RJ usando PRAZO como eixo temporal."""
    ref = ref_date or date.today()
    total = em_andamento = vencidas = vencem_hoje = concluidas = 0

    for row in agendamentos:
        prazo = _get_ag_prazo_rj(row)
        status = _get_ag_status_rj(row) or ""
        ativo = status not in _STATUS_INATIVO_EXEC_RJ
        prazo_no_periodo = _ag_data_no_periodo(prazo, from_date, to_date)

        if not prazo_no_periodo:
            continue

        if ativo:
            total += 1
            if status in _STATUS_EM_ANDAMENTO_EXEC_RJ:
                em_andamento += 1
            if prazo is not None and prazo < ref:
                vencidas += 1
            if prazo is not None and prazo == ref:
                vencem_hoje += 1
        elif status in _STATUS_ENCERRADO_EXEC_RJ:
            concluidas += 1

    return {
        "total_por_prazo_execucao_RJ": total,
        "por_prazo_em_andamento_execucao_RJ": em_andamento,
        "por_prazo_vencidas_execucao_RJ": vencidas,
        "por_prazo_vencem_hoje_execucao_RJ": vencem_hoje,
        "por_prazo_concluidas_execucao_RJ": concluidas,
    }


group_execucao_processos_por_atividade_por_prazo_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_processos_por_atividade_por_prazo)


group_execucao_demandas_por_funcionario_por_prazo_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_demandas_por_funcionario_por_prazo)


group_execucao_demandas_por_funcionario_por_prazo_completo_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_demandas_por_funcionario_por_prazo_completo)


def list_execucao_atividades_abertas_RJ(
    agendamentos: list[dict[str, Any]],
    *,
    ref_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Agendamentos atualmente abertos do setor Execução RJ, independente do período —
    modal do card "Em andamento" da Confecção CS (espelho de
    :func:`list_execucao_atividades_abertas_NG`).
    """
    ref = ref_date or date.today()
    itens: list[dict[str, Any]] = []

    for row in agendamentos:
        status = _get_ag_status_rj(row) or ""
        if status in _STATUS_INATIVO_EXEC_RJ:
            continue
        ag_id = _to_int(row.get("id") or row.get("ID"))
        if ag_id is None:
            continue
        prazo = _get_ag_prazo_rj(row)
        criacao = _get_ag_data_criacao_rj(row)
        setor = str(row.get("SETOR") or row.get("setor") or "EXECUÇÃO").strip().upper()
        atividade = _get_ag_atividade_nome_rj(row)
        pessoa_setor = (
            f"{setor} - {atividade}"
            if atividade and atividade != _SEM_ATIVIDADE_EXEC_RJ
            else setor
        )
        descricao_raw = row.get("DESCRICAO") or row.get("descricao")
        descricao = str(descricao_raw).strip().upper() if descricao_raw else "—"
        operacao = str(row.get("OPERACAO") or row.get("operacao") or "").strip()

        itens.append({
            "id": ag_id,
            "status": status,
            "descricao": descricao,
            "pessoa_setor": pessoa_setor,
            "funcionario": _get_ag_funcionario_nome_rj(row),
            "funcionario_atribuido": _get_ag_funcionario_atribuido_rj(row),
            "funcionario_encerramento": None,
            "atividade": atividade,
            "prazo": prazo.isoformat() if prazo else None,
            "criado_em": criacao.isoformat() if criacao else None,
            "concluido_em": None,
            "operacao": operacao,
            "encerrado_pelo_responsavel": None,
            "numero_processo": _get_ag_numero_processo_rj(row),
            "valor_sentenca": _get_ag_valor_sentenca_rj(row),
            "valor_acordao": _get_ag_valor_acordao_rj(row),
            "em_andamento": status in _STATUS_EM_ANDAMENTO_EXEC_RJ,
            "vencida": prazo is not None and prazo < ref,
            "vence_hoje": prazo is not None and prazo == ref,
            "concluida": False,
        })

    def _sort_key(item: dict[str, Any]) -> tuple[int, str, int]:
        prazo_raw = item.get("prazo")
        prazo_missing = 0 if prazo_raw else 1
        return (prazo_missing, str(prazo_raw or ""), int(item.get("id") or 0))

    return sorted(itens, key=_sort_key)


list_execucao_atividades_por_prazo_periodo_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.list_execucao_atividades_por_prazo_periodo)


get_opcoes_filtros_execucao_por_prazo_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_filtros_execucao_por_prazo)


group_execucao_resolvidos_por_dia_por_prazo_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_resolvidos_por_dia_por_prazo)


get_media_execucao_resolvidos_por_funcionario_por_prazo_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_media_execucao_resolvidos_por_funcionario_por_prazo)


# ---------------------------------------------------------------------------
# Motivo de "Encerrado Não Cumprido" — RJ
# ---------------------------------------------------------------------------

_get_ag_motivo_encaminhamento_itens_rj = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_motivo_encaminhamento_itens)


group_execucao_nao_cumprido_por_motivo_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_nao_cumprido_por_motivo)


# ---------------------------------------------------------------------------
# Detalhamento de atrasos (vencidas por dias de atraso) — RJ
# ---------------------------------------------------------------------------

_ATRASO_MAX_BUCKET_RJ = _familia._ATRASO_MAX_BUCKET

_BUCKET_META_RJ = _familia._BUCKET_META


get_atrasos_detalhamento_execucao_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_atrasos_detalhamento_execucao)

# =============================================================================
# X - Diligências (subconjunto de agendamentos do setor EXECUÇÃO)
# =============================================================================

_eh_diligencia_rj = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._eh_diligencia)


filtrar_agendamentos_diligencia_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_agendamentos_diligencia)


get_total_diligencias_execucao_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_diligencias_execucao)


group_execucao_diligencias_por_processo_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_diligencias_por_processo)


_eh_diligencia_expedicao_alvara_rj = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._eh_diligencia_expedicao_alvara)


filtrar_agendamentos_diligencia_expedicao_alvara_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_agendamentos_diligencia_expedicao_alvara)


get_kpis_diligencias_expedicao_alvara_execucao_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_kpis_diligencias_expedicao_alvara_execucao)


_diligencias_expedicao_alvara_cumpridas_rj = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._diligencias_expedicao_alvara_cumpridas)


list_processos_diligencia_expedicao_alvara_cumprida_execucao_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.list_processos_diligencia_expedicao_alvara_cumprida_execucao)


_TIPOS_VALIDOS_DILIGENCIA_RJ = _familia._TIPOS_VALIDOS_DILIGENCIA


filtrar_agendamentos_diligencia_por_tipo_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_agendamentos_diligencia_por_tipo)


filtrar_agendamentos_diligencia_por_colaborador_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_agendamentos_diligencia_por_colaborador)


group_estoque_execucao_RJ_por_mes = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_estoque_execucao_por_mes)


filtrar_saida_execucao_export_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_saida_execucao_export)


anotar_saida_execucao_export_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.anotar_saida_execucao_export)
