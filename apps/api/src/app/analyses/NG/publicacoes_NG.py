# Análises do dashboard de publicações (LexFlow) — NG

from __future__ import annotations

from app.analyses.familias import publicacoes as _familia  # V2: código único da família (app/analyses/familias/publicacoes.py)
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from statistics import mean
from typing import Any, Callable, Dict, List, Literal, Optional, Union

from app.analyses.common import conversao  # V2: conversões dos valores do banco num módulo só
from app.analyses.common import tempo  # V2: média/mediana de tempo num módulo só
from app.utils import parse_date_from_db


# -----------------------------------------------------------------------------
# Constantes — nomes de colunas do banco
# -----------------------------------------------------------------------------

_COL_DISPONIBILIZACAO = _familia._COL_DISPONIBILIZACAO

_COL_CONCLUSAO = _familia._COL_CONCLUSAO

_COL_STATUS = _familia._COL_STATUS

_COL_LEITOR = _familia._COL_LEITOR

_COL_RESPONSAVEL = _familia._COL_RESPONSAVEL

_COL_MATERIA = _familia._COL_MATERIA

_COL_DOCUMENTO = _familia._COL_DOCUMENTO

_COL_TRIBUNAL = _familia._COL_TRIBUNAL

_COL_ORGAO = _familia._COL_ORGAO

_COL_COMARCA = _familia._COL_COMARCA

_COL_ID_PROCESSO = _familia._COL_ID_PROCESSO

_COL_DATA_LEITURA = _familia._COL_DATA_LEITURA

# Colunas dos agendamentos (query agendamentos_todos_setores_NG).
_COL_AG_PROCESSO_ID = _familia._COL_AG_PROCESSO_ID

_COL_AG_DATA_CRIACAO = _familia._COL_AG_DATA_CRIACAO

_COL_AG_ATIVIDADE = _familia._COL_AG_ATIVIDADE

_COL_AG_SETOR = _familia._COL_AG_SETOR

# Status elegíveis para a métrica de publicações pendentes no dashboard NG.
_STATUS_PENDENTE_METRICA_NG = _familia._STATUS_PENDENTE_METRICA


# -----------------------------------------------------------------------------
# Helpers internos
# -----------------------------------------------------------------------------

_col = _familia._col


_to_date = _familia._to_date


_get_date = _familia._get_date


_status_normalizado = _familia._status_normalizado


_is_cumprido = _familia._is_cumprido


_is_somente_visualizada = _familia._is_somente_visualizada


_conta_como_pendente_publicacao_NG = _familia._conta_como_pendente_publicacao


_in_interval = _familia._in_interval


_formatar_nome = _familia._formatar_nome


_rotulo_leitor = _familia._rotulo_leitor


_label_caixa_alta = _familia._label_caixa_alta


_rotulo_materia_NG = _familia._rotulo_materia


_rotulo_documento_NG = _familia._rotulo_documento


_rotulo_tribunal_NG = _familia._rotulo_tribunal


_rotulo_orgao_NG = _familia._rotulo_orgao


_normalizar_filtro_dimensao_NG = _familia._normalizar_filtro_dimensao


_cumprida_mesmo_dia = _familia._cumprida_mesmo_dia


_agrupar_por_rotulo = _familia._agrupar_por_rotulo


_filtrar_por_rotulo = _familia._filtrar_por_rotulo


# -----------------------------------------------------------------------------
# Filtros por leitor e por dimensão
# -----------------------------------------------------------------------------

filter_publicacoes_por_leitor_NG = _familia.filter_publicacoes_por_leitor


filter_publicacoes_por_materia_NG = _familia.filter_publicacoes_por_materia


filter_publicacoes_por_documento_NG = _familia.filter_publicacoes_por_documento


filter_publicacoes_por_tribunal_NG = _familia.filter_publicacoes_por_tribunal


filter_publicacoes_por_orgao_NG = _familia.filter_publicacoes_por_orgao


# -----------------------------------------------------------------------------
# 1 - Funções que vão nos cartões de informações do dashboard
# -----------------------------------------------------------------------------

get_publicacoes_recebidas_periodo_NG = _familia.get_publicacoes_recebidas_periodo


filter_publicacoes_recebidas_no_periodo_NG = _familia.filter_publicacoes_recebidas_no_periodo


filter_publicacoes_tratadas_no_periodo_NG = _familia.filter_publicacoes_tratadas_no_periodo


get_publicacoes_tratadas_periodo_NG = _familia.get_publicacoes_tratadas_periodo


resolve_dia_referencia_fim_periodo_NG = _familia.resolve_dia_referencia_fim_periodo


get_publicacoes_tratadas_no_dia_NG = _familia.get_publicacoes_tratadas_no_dia


get_publicacoes_recebidas_no_dia_NG = _familia.get_publicacoes_recebidas_no_dia


get_publicacoes_cumpridas_mesmo_dia_chegada_no_dia_NG = _familia.get_publicacoes_cumpridas_mesmo_dia_chegada_no_dia


get_publicacoes_com_data_disponibilizacao_NG = _familia.get_publicacoes_com_data_disponibilizacao


get_publicacoes_cumpridas_mesmo_dia_chegada_NG = _familia.get_publicacoes_cumpridas_mesmo_dia_chegada


get_pct_tratadas_mesmo_dia_publicacoes_NG = _familia.get_pct_tratadas_mesmo_dia_publicacoes


get_publicacoes_pendentes_NG = _familia.get_publicacoes_pendentes


get_media_tempo_tratamento_publicacoes_NG = _familia.get_media_tempo_tratamento_publicacoes


get_publicacoes_pendentes_zeradas_no_periodo_NG = _familia.get_publicacoes_pendentes_zeradas_no_periodo


group_publicacoes_recebidas_por_dia_NG = _familia.group_publicacoes_recebidas_por_dia


group_publicacoes_tratadas_por_dia_NG = _familia.group_publicacoes_tratadas_por_dia


group_publicacoes_visualizadas_por_dia_NG = _familia.group_publicacoes_visualizadas_por_dia


# -----------------------------------------------------------------------------
# 2 - Agrupando dados para os gráficos
# -----------------------------------------------------------------------------

group_publicacoes_por_tribunal_NG = _familia.group_publicacoes_por_tribunal


group_publicacoes_por_tipo_documento_NG = _familia.group_publicacoes_por_tipo_documento


group_publicacoes_por_materia_NG = _familia.group_publicacoes_por_materia


group_publicacoes_por_orgao_NG = _familia.group_publicacoes_por_orgao


group_publicacoes_por_comarca_NG = _familia.group_publicacoes_por_comarca


# -----------------------------------------------------------------------------
# 3 - Funções por Funcionário (Leitor e Responsável)
# -----------------------------------------------------------------------------

group_publicacoes_cumprido_por_leitor_NG = _familia.group_publicacoes_cumprido_por_leitor


group_publicacoes_pendentes_por_leitor_NG = _familia.group_publicacoes_pendentes_por_leitor


group_publicacoes_pendentes_por_dias_atraso_NG = _familia.group_publicacoes_pendentes_por_dias_atraso


# -----------------------------------------------------------------------------
# 4 - Agendamento criado após a finalização da publicação (qualquer setor)
# -----------------------------------------------------------------------------

_agendamentos_por_processo_NG = _familia._agendamentos_por_processo


_agendamento_apos_finalizacao_NG = _familia._agendamento_apos_finalizacao


build_publicacoes_agendamento_apos_finalizacao_NG = _familia.build_publicacoes_agendamento_apos_finalizacao


filter_publicacoes_por_atividade_agendamento_NG = _familia.filter_publicacoes_por_atividade_agendamento


filter_publicacoes_por_setor_agendamento_NG = _familia.filter_publicacoes_por_setor_agendamento


filter_publicacoes_por_status_agendamento_NG = _familia.filter_publicacoes_por_status_agendamento


# -----------------------------------------------------------------------------
# 5 - Lista de publicações (tabela "Lista de tarefas" do dashboard)
# -----------------------------------------------------------------------------

_status_agendamento_amigavel_NG = _familia._status_agendamento_amigavel


_agendamento_mais_recente_apos_finalizacao_NG = _familia._agendamento_mais_recente_apos_finalizacao


list_publicacoes_NG = _familia.list_publicacoes


# -----------------------------------------------------------------------------
# 6 - Comissionamento por funcionário (leitor)
# -----------------------------------------------------------------------------

# Valores unitários do modelo de cálculo (item 6 do documento de comissionamento):
# certa = lida corretamente e com agendamento correto; errada = lida e com agendamento errado.
_VALOR_UNITARIO_CERTA_NG = _familia._VALOR_UNITARIO_CERTA

_VALOR_UNITARIO_ERRADA_NG = _familia._VALOR_UNITARIO_ERRADA


get_publicacoes_comissionamento_por_funcionario_NG = _familia.get_publicacoes_comissionamento_por_funcionario
