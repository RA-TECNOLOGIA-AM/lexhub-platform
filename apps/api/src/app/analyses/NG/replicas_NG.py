# Atividades no período — Setor Réplica — Escritório NG
#
# Réplica de analyses/LA/replicas_LA.py. Diferenças do NG:
# - setor no LexFlow é "RÉPLICA" (singular) e tem 3 atividades: ELABORAR RÉPLICA,
#   RÉPLICA CANCELADA e VERIFICAR CONTESTAÇÃO (o LA só tem ELABORAR RÉPLICA);
# - a taxa de procedência só considera processos com ELABORAR RÉPLICA (réplica de
#   fato apresentada);
# - sem comissionamento (decisão do usuário, 05/10/2026).

from __future__ import annotations

from app.analyses.familias import replicas as _familia  # V2: código único da família (familias/replicas.py)
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
# Em andamento: qualquer status ativo (ainda não encerrado/cancelado)
_STATUS_EM_ANDAMENTO = _familia._STATUS_EM_ANDAMENTO

_STATUS_ENCERRADO = _familia._STATUS_ENCERRADO

_STATUS_FILTRO_TAREFAS = _familia._STATUS_FILTRO_TAREFAS

_SITUACOES_FILTRO_TAREFAS = _familia._SITUACOES_FILTRO_TAREFAS

SITUACOES_VALIDAS_REPLICAS_NG = _familia.SITUACOES_VALIDAS_REPLICAS

_STATUS_DEMANDAS_FUNCIONARIO = _familia._STATUS_DEMANDAS_FUNCIONARIO

_SLUG_POR_STATUS = _familia._SLUG_POR_STATUS

_SEM_ATIVIDADE = _familia._SEM_ATIVIDADE

_SEM_FUNCIONARIO = _familia._SEM_FUNCIONARIO

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

get_kpis_atividades_replicas_NG = _familia.get_kpis_atividades_replicas


# =============================================================================
# Histórico de concluídas (mensal e diário)
# =============================================================================

_MONTH_NAMES = _familia._MONTH_NAMES


group_replicas_concluidas_por_mes_NG = _familia.group_replicas_concluidas_por_mes


group_replicas_concluidas_por_dia_NG = _familia.group_replicas_concluidas_por_dia


get_replicas_concluidas_por_dia_por_funcionario_NG = _familia.get_replicas_concluidas_por_dia_por_funcionario


_media_concluidas_por_funcionario = _familia._media_concluidas_por_funcionario


get_media_replicas_concluidas_por_funcionario_NG = _familia.get_media_replicas_concluidas_por_funcionario


# =============================================================================
# Gráfico: processos distintos por atividade
# =============================================================================

group_replicas_processos_por_atividade_NG = _familia.group_replicas_processos_por_atividade


# =============================================================================
# Gráfico: demandas encerradas por funcionário
# =============================================================================

group_replicas_demandas_por_funcionario_NG = _familia.group_replicas_demandas_por_funcionario


# =============================================================================
# Gráfico (por prazo): processos distintos por atividade
# =============================================================================

group_replicas_processos_por_atividade_por_prazo_NG = _familia.group_replicas_processos_por_atividade_por_prazo


# =============================================================================
# Gráfico (por prazo): demandas encerradas por funcionário
# =============================================================================

group_replicas_demandas_por_funcionario_por_prazo_NG = _familia.group_replicas_demandas_por_funcionario_por_prazo


# =============================================================================
# Lista de tarefas
# =============================================================================

list_replicas_atividades_periodo_NG = _familia.list_replicas_atividades_periodo


# =============================================================================
# Opções de filtros
# =============================================================================

get_opcoes_filtros_replicas_NG = _familia.get_opcoes_filtros_replicas


# =============================================================================
# Filtros cumulativos
# =============================================================================

ReplicasAtividadesFiltrosNG = _familia.ReplicasAtividadesFiltros


_agendamento_match_filtros = _familia._agendamento_match_filtros


filtrar_agendamentos_replicas_NG = _familia.filtrar_agendamentos_replicas


# =============================================================================
# Análise por Prazo — helpers internos
# =============================================================================

_incluir_na_lista_por_prazo = _familia._incluir_na_lista_por_prazo


_classificar_situacao_por_prazo = _familia._classificar_situacao_por_prazo


# =============================================================================
# KPIs por Prazo
# =============================================================================

get_kpis_replicas_por_prazo_NG = _familia.get_kpis_replicas_por_prazo


# =============================================================================
# Histórico de concluídas por Prazo (mensal e diário)
# =============================================================================

_filtrar_encerrados_com_prazo_no_periodo = _familia._filtrar_encerrados_com_prazo_no_periodo


group_replicas_concluidas_por_prazo_por_mes_NG = _familia.group_replicas_concluidas_por_prazo_por_mes


group_replicas_concluidas_por_prazo_por_dia_NG = _familia.group_replicas_concluidas_por_prazo_por_dia


get_replicas_concluidas_por_prazo_por_dia_por_funcionario_NG = _familia.get_replicas_concluidas_por_prazo_por_dia_por_funcionario


get_media_replicas_concluidas_por_prazo_por_funcionario_NG = _familia.get_media_replicas_concluidas_por_prazo_por_funcionario


# =============================================================================
# Lista de tarefas por Prazo
# =============================================================================

list_replicas_por_prazo_NG = _familia.list_replicas_por_prazo


# =============================================================================
# Opções de filtros por Prazo
# =============================================================================

get_opcoes_filtros_replicas_por_prazo_NG = _familia.get_opcoes_filtros_replicas_por_prazo


# =============================================================================
# Filtros cumulativos por Prazo
# =============================================================================

_agendamento_match_filtros_por_prazo = _familia._agendamento_match_filtros_por_prazo


filtrar_agendamentos_replicas_por_prazo_NG = _familia.filtrar_agendamentos_replicas_por_prazo


# =============================================================================
# Taxa de procedência (1G) dos processos com Réplica apresentada
# =============================================================================
#
# Considerados "procedentes" os status de 1G (tabela public.status_primeiro_grau)
# que representam ganho de causa, com ou sem proveito econômico, total ou parcial:
#   20 PROCEDENTE COM PROVEITO ECONÔMICO
#   21 PARCIALMENTE PROCEDENTE COM PROVEITO ECONÔMICO
#   22 PROCEDENTE SEM PROVEITO ECONÔMICO
#   23 PARCIALMENTE PROCEDENTE SEM PROVEITO ECONÔMICO

_IDS_1G_PROCEDENTE_REPLICAS = _familia._IDS_1G_PROCEDENTE_REPLICAS

# Só esta atividade representa réplica apresentada; RÉPLICA CANCELADA e
# VERIFICAR CONTESTAÇÃO ficam fora do universo da taxa.
_ATIVIDADE_REPLICA_APRESENTADA_NG = _familia._ATIVIDADE_REPLICA_APRESENTADA
# V2 (decisão de 19/11/2026): no NG a atividade foi dividida em ELABORAR RÉPLICA SIMPLES e ELABORAR RÉPLICA
# ESPECÍFICA, e o nome exato acima não casava com nenhuma (a taxa ficava sempre zerada, também na v1). As três
# contam como réplica apresentada; ANÁLISE DE VIABILIDADE e RÉPLICA CANCELADA continuam fora. O RJ (que usa este
# cálculo) só tem ELABORAR RÉPLICA.
_ATIVIDADES_REPLICA_APRESENTADA_NG = _familia._ATIVIDADES_REPLICA_APRESENTADA


get_replicas_taxa_procedencia_NG = _familia.get_replicas_taxa_procedencia
