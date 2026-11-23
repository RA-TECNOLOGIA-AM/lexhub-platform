# Atividades no período — Setor Pendência — Escritório NG

from __future__ import annotations

from app.analyses.familias import pendencias_intermediarias as _familia  # V2: código único da família (familias/pendencias_intermediarias.py)
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Callable, Optional

from app.analyses.common import periodo  # V2: período e variação vs período anterior num módulo só
from app.analyses.common import conversao  # V2: conversões dos valores do banco num módulo só
from app.analyses.common import atividades  # V2: regras das atividades num módulo só
from app.utils import parse_date_from_db

# =============================================================================
# Constantes
# =============================================================================

# Inativos: excluídos de Total, Vencidas e Vencem hoje (alinhado com dashboard analítico)
_STATUS_INATIVO = _familia._STATUS_INATIVO
# Em andamento: subset ativo com fluxo explícito de progresso
_STATUS_EM_ANDAMENTO = _familia._STATUS_EM_ANDAMENTO

_STATUS_ENCERRADO = _familia._STATUS_ENCERRADO

_STATUS_FILTRO_TAREFAS = _familia._STATUS_FILTRO_TAREFAS

_SITUACOES_FILTRO_TAREFAS = _familia._SITUACOES_FILTRO_TAREFAS

SITUACOES_VALIDAS_INTERMEDIARIAS_NG = _familia.SITUACOES_VALIDAS_INTERMEDIARIAS

_STATUS_DEMANDAS_FUNCIONARIO = _familia._STATUS_DEMANDAS_FUNCIONARIO

_SLUG_POR_STATUS = _familia._SLUG_POR_STATUS

_SEM_ATIVIDADE = _familia._SEM_ATIVIDADE

_SEM_FUNCIONARIO = _familia._SEM_FUNCIONARIO

# No NG, toda atividade do setor PENDÊNCIA encerrada como "Encerrado Não Cumprido"
# agenda dilação de prazo, com a única exceção de "SANAR PENDÊNCIA 1G" (regra
# confirmada pelo usuário) — diferente da LA, que usa uma lista fixa de atividades
# elegíveis. Hoje só existe "SOLICITAR DOCS COM CLIENTE" além da excluída, mas a
# regra é por exclusão para já cobrir novas atividades que passem a existir no setor.
_ATIVIDADE_SEM_DILACAO_NG = _familia._ATIVIDADE_SEM_DILACAO

_COL_FUNCIONARIO_ATRIBUIDO = _familia._COL_FUNCIONARIO_ATRIBUIDO

_COL_FUNCIONARIO_ENCERRAMENTO = _familia._COL_FUNCIONARIO_ENCERRAMENTO

_COL_ID_USUARIO_ENCERRAMENTO = _familia._COL_ID_USUARIO_ENCERRAMENTO


# =============================================================================
# Utilitários
# =============================================================================

_to_int = _familia._to_int


_to_date = _familia._to_date


_data_no_periodo = _familia._data_no_periodo


_nome_em_conjunto_filtro = _familia._nome_em_conjunto_filtro


# =============================================================================
# Getters de campos dos agendamentos
# =============================================================================

_get_status = _familia._get_status


_get_data_criacao = _familia._get_data_criacao


_get_data_conclusao = _familia._get_data_conclusao


_get_prazo = _familia._get_prazo


_get_processo_id = _familia._get_processo_id


_get_atividade_nome = _familia._get_atividade_nome


_get_funcionario_atribuido = _familia._get_funcionario_atribuido


_get_funcionario_encerramento = _familia._get_funcionario_encerramento


# V2: como estas atividades são lidas e quais status contam (app/analyses/common/atividades.py).
_ATIVIDADES = _familia._ATIVIDADES

_STATUS_ATIVIDADES = _familia._STATUS_ATIVIDADES


_get_funcionario_nome = _familia._get_funcionario_nome


# =============================================================================
# Filtros de período
# =============================================================================

_filtrar_criados_no_periodo = _familia._filtrar_criados_no_periodo


_filtrar_encerrados_no_periodo = _familia._filtrar_encerrados_no_periodo


_incluir_na_lista_tarefas = _familia._incluir_na_lista_tarefas


_classificar_situacao_tarefa = _familia._classificar_situacao_tarefa


# =============================================================================
# KPIs
# =============================================================================

get_kpis_atividades_intermediarias_NG = _familia.get_kpis_atividades_intermediarias


# =============================================================================
# Histórico de concluídas (mensal e diário)
# =============================================================================

_MONTH_NAMES = _familia._MONTH_NAMES


group_intermediarias_concluidas_por_mes_NG = _familia.group_intermediarias_concluidas_por_mes


group_intermediarias_concluidas_por_dia_NG = _familia.group_intermediarias_concluidas_por_dia


get_intermediarias_concluidas_por_dia_por_funcionario_NG = _familia.get_intermediarias_concluidas_por_dia_por_funcionario


_media_concluidas_por_funcionario = _familia._media_concluidas_por_funcionario


get_media_intermediarias_concluidas_por_funcionario_NG = _familia.get_media_intermediarias_concluidas_por_funcionario


# =============================================================================
# Gráfico: processos distintos por atividade
# =============================================================================

group_intermediarias_processos_por_atividade_NG = _familia.group_intermediarias_processos_por_atividade


# =============================================================================
# Gráfico: demandas encerradas por funcionário
# =============================================================================

group_intermediarias_demandas_por_funcionario_NG = _familia.group_intermediarias_demandas_por_funcionario


# =============================================================================
# Gráfico (por prazo): processos distintos por atividade
# =============================================================================

group_intermediarias_processos_por_atividade_por_prazo_NG = _familia.group_intermediarias_processos_por_atividade_por_prazo


# =============================================================================
# Gráfico (por prazo): demandas encerradas por funcionário
# =============================================================================

group_intermediarias_demandas_por_funcionario_por_prazo_NG = _familia.group_intermediarias_demandas_por_funcionario_por_prazo


# =============================================================================
# Lista de tarefas
# =============================================================================

list_intermediarias_atividades_periodo_NG = _familia.list_intermediarias_atividades_periodo


# =============================================================================
# Opções de filtros
# =============================================================================

get_opcoes_filtros_intermediarias_NG = _familia.get_opcoes_filtros_intermediarias


# =============================================================================
# Filtros cumulativos
# =============================================================================

IntermediariasAtividadesFiltrosNG = _familia.IntermediariasAtividadesFiltros


_agendamento_match_filtros = _familia._agendamento_match_filtros


filtrar_agendamentos_intermediarias_NG = _familia.filtrar_agendamentos_intermediarias


# =============================================================================
# Análise por Prazo — helpers internos
# =============================================================================

_incluir_na_lista_por_prazo = _familia._incluir_na_lista_por_prazo


_classificar_situacao_por_prazo = _familia._classificar_situacao_por_prazo


# =============================================================================
# Dilações
# =============================================================================

_solicitar_docs_nao_cumprido_por_processo = _familia._solicitar_docs_nao_cumprido_por_processo


get_dilacoes_intermediarias_NG = _familia.get_dilacoes_intermediarias


get_dilacoes_intermediarias_por_funcionario_NG = _familia.get_dilacoes_intermediarias_por_funcionario


# =============================================================================
# KPIs por Prazo
# =============================================================================

get_kpis_intermediarias_por_prazo_NG = _familia.get_kpis_intermediarias_por_prazo


# =============================================================================
# Histórico de concluídas por Prazo (mensal e diário)
# =============================================================================

_filtrar_encerrados_com_prazo_no_periodo = _familia._filtrar_encerrados_com_prazo_no_periodo


group_intermediarias_concluidas_por_prazo_por_mes_NG = _familia.group_intermediarias_concluidas_por_prazo_por_mes


group_intermediarias_concluidas_por_prazo_por_dia_NG = _familia.group_intermediarias_concluidas_por_prazo_por_dia


get_intermediarias_concluidas_por_prazo_por_dia_por_funcionario_NG = _familia.get_intermediarias_concluidas_por_prazo_por_dia_por_funcionario


get_media_intermediarias_concluidas_por_prazo_por_funcionario_NG = _familia.get_media_intermediarias_concluidas_por_prazo_por_funcionario


# =============================================================================
# Lista de tarefas por Prazo
# =============================================================================

list_intermediarias_por_prazo_NG = _familia.list_intermediarias_por_prazo


# =============================================================================
# Opções de filtros por Prazo
# =============================================================================

get_opcoes_filtros_intermediarias_por_prazo_NG = _familia.get_opcoes_filtros_intermediarias_por_prazo


# =============================================================================
# Filtros cumulativos por Prazo
# =============================================================================

_agendamento_match_filtros_por_prazo = _familia._agendamento_match_filtros_por_prazo


filtrar_agendamentos_intermediarias_por_prazo_NG = _familia.filtrar_agendamentos_intermediarias_por_prazo
