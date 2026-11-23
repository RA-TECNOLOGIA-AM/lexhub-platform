"""
Análises do controle de processos (LexFlow) — escritório Nicolas Gomes (ID_ESCRITORIO=20).

Este módulo trabalha em cima do payload retornado pela query `controle_processo`
definida em `app/queries.py` e assume que o dado de entrada é uma lista de dicts
(linhas do banco já serializadas), como nos demais módulos de `app/analyses`.
"""

from __future__ import annotations

from app.analyses.common import unidade as _unidade  # V2: valores da unidade (common/unidade.py)
from app.analyses.familias import controle_processo as _familia  # V2: código único da família (familias/controle_processo.py)
import re
import unicodedata
from collections import defaultdict
from contextvars import ContextVar  # V2: _escritorio_ctx
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.analyses.common import periodo  # V2: período e variação vs período anterior num módulo só
from app.analyses.common import memo  # V2: cache por pedido (a mesma conta uma vez por pedido)
from app.analyses.common import tempo  # V2: média/mediana de tempo num módulo só
from app.utils import ordem_mes  # V2: séries mês a mês em ordem cronológica
from app.utils import parse_date_from_db, parse_datetime_from_db, resolver_periodo_comparativo
from app.analyses.common import matriz_julgamento as mj


_ID_ESCRITORIO_NG = _familia._ID_ESCRITORIO

# V2 (19/11/2026): o escritório da base, trocado pela casca só no Controle de Processos do RJ (escritório 27), que a
# v1 não tem e usa este cálculo do NG (app/dashboards/controle_processos.py). Padrão: 20 (o cálculo da v1, sem
# mudança; o Recursal do RJ continua marcando as linhas dele como 20 para usar estas funções).
_escritorio_ctx: ContextVar[int] = ContextVar("escritorio_controle_processo_ng", default=_ID_ESCRITORIO_NG)

# LexFlow `fase.id` — alinhado ao cadastro do banco (controle_processo)
_ID_FASE_INICIAL_NG = _familia._ID_FASE_INICIAL

_ID_FASE_RECURSAL_NG = _familia._ID_FASE_RECURSAL

_ID_FASE_EXECUCAO_NG = _familia._ID_FASE_EXECUCAO

_ID_FASE_TRANSITO_JULGADO = _familia._ID_FASE_TRANSITO_JULGADO

_ID_FASE_ARQUVADO_IMPROCEDENTE = _familia._ID_FASE_ARQUVADO_IMPROCEDENTE

_ID_FASE_ARQUVADO_PROCEDENTE = _familia._ID_FASE_ARQUVADO_PROCEDENTE

# Extintos com/sem mérito (1G e 2G) e taxa de provimento agora usam a Matriz de
# Julgamento (``app.analyses.common.matriz_julgamento``), que resolve o mérito a
# partir das colunas novas (``id_sentenca_merito_grau1``/``id_acordao_merito_grau2``)
# com fallback nos status antigos por nome — ver ``_get_id_merito_1g``/``_get_id_merito_2g``.

_COL_ID_ESCRITORIO = _familia._COL_ID_ESCRITORIO
# Query `controle_processo`: p.uf AS "UF"
_COL_UF = _familia._COL_UF
# Query `controle_processo`: p.id_situacao AS "ID_SITUACAO" — LexFlow ``public.situacao``
_COL_ID_SITUACAO = _familia._COL_ID_SITUACAO
# public.situacao: 1=ATIVO, 2=ARQUIVADO, 6=SUSPENSO/SOBRESTADO. A query já restringe a (1, 6).
_ID_SITUACAO_ATIVO_NG = _familia._ID_SITUACAO_ATIVO

_ID_SITUACAO_SUSPENSO_SOBRESTADO_NG = _familia._ID_SITUACAO_SUSPENSO_SOBRESTADO
# Query `controle_processo`: p.id_status_grau1 AS "ID_1G"
_COL_ID_1G = _familia._COL_ID_1G
# Query `controle_processo`: spg.nome AS "STATUS_1G"
_COL_STATUS_1G = _familia._COL_STATUS_1G
# Query `controle_processo`: p.id_status_grau2 AS "ID_2G"
_COL_ID_2G = _familia._COL_ID_2G
# Query `controle_processo`: ssg.nome AS "STATUS_2G"
_COL_STATUS_2G = _familia._COL_STATUS_2G

_COL_ID_FASE = _familia._COL_ID_FASE

_COL_FASE = _familia._COL_FASE

_COL_SUBFASE = _familia._COL_SUBFASE
# Query `controle_processo`: p.valor_causa as "VALOR_DE_CAUSA" — única fonte de valor monetário
# usada neste módulo (mesmo em cartões de sentença/acórdão/execução, que antes usavam colunas
# próprias como VALOR_CAUSA_SENTENCA/VALOR_CAUSA_ACORDO/VALOR_CAUSA_EXECUCAO).
_COL_VALOR_CAUSA = _familia._COL_VALOR_CAUSA
# Exceção: painel "Extintos · 2º Grau" do Recursal usa especificamente o valor de causa do
# acórdão (não o valor de causa inicial), a pedido do escritório — ver funções
# ``*_valor_acordao_NG`` mais abaixo. Controle de Processos continua em ``_COL_VALOR_CAUSA``.
_COL_VALOR_CAUSA_ACORDO = _familia._COL_VALOR_CAUSA_ACORDO
# CTE `fases_log` na query `controle_processo`
_COL_DT_ENTRADA_INICIAL = _familia._COL_DT_ENTRADA_INICIAL

_COL_DT_SAIDA_INICIAL = _familia._COL_DT_SAIDA_INICIAL

_COL_DT_ENTRADA_RECURSAL = _familia._COL_DT_ENTRADA_RECURSAL

_COL_DT_SAIDA_RECURSAL = _familia._COL_DT_SAIDA_RECURSAL

_COL_DT_ENTRADA_EXECUCAO = _familia._COL_DT_ENTRADA_EXECUCAO

_COL_DT_SAIDA_EXECUCAO = _familia._COL_DT_SAIDA_EXECUCAO
# Flags derivadas de ``log_fase_processual`` na query ``controle_processo`` (CTE ``fases_log``)
_COL_LOG_TEVE_SUBFASE_INICIAL_INDEFERIDA = _familia._COL_LOG_TEVE_SUBFASE_INICIAL_INDEFERIDA

_COL_LOG_TEVE_SUBFASE_RECURSO_NAO_PROVIDO = _familia._COL_LOG_TEVE_SUBFASE_RECURSO_NAO_PROVIDO

# Data “real” de entrada na fase inicial (melhor proxy para início do fluxo)
_COL_DATA_AJUIZAMENTO = _familia._COL_DATA_AJUIZAMENTO
# Query `controle_processo`: p.sentenca AS "DATA_SENTENCA"
_COL_DATA_SENTENCA = _familia._COL_DATA_SENTENCA
# Query `controle_processo`: p.acordao_data AS "DATA_ACORDAO"
_COL_DATA_ACORDAO = _familia._COL_DATA_ACORDAO
# Query `controle_processo`: p.transito_julgado AS "DATA_TRANSITO_JULGADO"
_COL_DATA_TRANSITO_JULGADO = _familia._COL_DATA_TRANSITO_JULGADO

_SEM_FASE = _familia._SEM_FASE

_SEM_SUBFASE = _familia._SEM_SUBFASE

_MONTH_NAMES_NG = _familia._MONTH_NAMES


_col = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia._col)


_normalizar_chave_fase_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia._normalizar_chave_fase)


_rotulo_fase_grafico_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia._rotulo_fase_grafico)


_rotulo_subfase_grafico_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia._rotulo_subfase_grafico)


_truthy_flag_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia._truthy_flag)


_to_int = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia._to_int)


_converter_valor_causa = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia._converter_valor_causa)


_parse_data_controle_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia._parse_data_controle)


_parse_datetime_controle_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia._parse_datetime_controle)


_data_sentenca_no_intervalo_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia._data_sentenca_no_intervalo)


_data_acordao_no_intervalo_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia._data_acordao_no_intervalo)


_data_transito_julgado_no_intervalo_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia._data_transito_julgado_no_intervalo)


_col_data_no_intervalo_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia._col_data_no_intervalo)


_duracao_dias_entrada_saida_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia._duracao_dias_entrada_saida)


_duracoes_permanencia_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia._duracoes_permanencia)


_media_dias_permanencia_setor_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia._media_dias_permanencia_setor)


_mediana_dias_permanencia_setor_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia._mediana_dias_permanencia_setor)


# -----------------------------------------------------------------------------
# 1 - Função auxiliar base (todas as outras devem partir daqui)
# -----------------------------------------------------------------------------
_base_controle_processo_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia._base_controle_processo)


_filtrar_controle_processo_por_id_fase_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia._filtrar_controle_processo_por_id_fase)


_filtrar_controle_processo_log_inicial_indeferida_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia._filtrar_controle_processo_log_inicial_indeferida)


_filtrar_controle_processo_log_recursal_nao_provido_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia._filtrar_controle_processo_log_recursal_nao_provido)


_filtrar_controle_processo_fase_transito_julgado_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia._filtrar_controle_processo_fase_transito_julgado)


_get_id_merito_1g = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia._get_id_merito_1g)


_get_id_merito_2g = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia._get_id_merito_2g)


_filtrar_extintos_com_merito_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia._filtrar_extintos_com_merito)


_filtrar_extintos_com_merito_2g_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia._filtrar_extintos_com_merito_2g)


_filtrar_extintos_sem_merito_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia._filtrar_extintos_sem_merito)


_filtrar_extintos_sem_merito_2g_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia._filtrar_extintos_sem_merito_2g)


# -----------------------------------------------------------------------------
# 2 - Totais gerais
# -----------------------------------------------------------------------------
get_total_controle_processo_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_total_controle_processo)


get_valor_causa_total_controle_processo_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_valor_causa_total_controle_processo)


get_total_controle_processo_fase_inicial_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_total_controle_processo_fase_inicial)


get_total_controle_processo_log_inicial_indeferida_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_total_controle_processo_log_inicial_indeferida)


get_valor_causa_total_controle_processo_log_inicial_indeferida_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_valor_causa_total_controle_processo_log_inicial_indeferida)


get_total_controle_processo_log_recursal_nao_provido_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_total_controle_processo_log_recursal_nao_provido)


get_valor_causa_total_controle_processo_log_recursal_nao_provido_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_valor_causa_total_controle_processo_log_recursal_nao_provido)


get_valor_causa_total_controle_processo_fase_inicial_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_valor_causa_total_controle_processo_fase_inicial)


get_total_controle_processo_fase_recursal_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_total_controle_processo_fase_recursal)


get_valor_causa_total_controle_processo_fase_recursal_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_valor_causa_total_controle_processo_fase_recursal)


get_total_controle_processo_fase_execucao_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_total_controle_processo_fase_execucao)


get_valor_causa_execucao_total_controle_processo_fase_execucao_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_valor_causa_execucao_total_controle_processo_fase_execucao)


get_total_controle_processo_fase_arquivado_procedente_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_total_controle_processo_fase_arquivado_procedente)


get_valor_causa_total_controle_processo_fase_arquivado_procedente_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_valor_causa_total_controle_processo_fase_arquivado_procedente)


get_total_controle_processo_fase_arquivado_improcedente_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_total_controle_processo_fase_arquivado_improcedente)


get_valor_causa_total_controle_processo_fase_arquivado_improcedente_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_valor_causa_total_controle_processo_fase_arquivado_improcedente)


get_total_controle_processo_fase_transito_julgado_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_total_controle_processo_fase_transito_julgado)


get_valor_causa_total_controle_processo_fase_transito_julgado_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_valor_causa_total_controle_processo_fase_transito_julgado)


get_total_extintos_com_merito_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_total_extintos_com_merito)


get_valor_causa_total_extintos_com_merito_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_valor_causa_total_extintos_com_merito)


get_extintos_com_merito_por_tipo_sentenca_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_extintos_com_merito_por_tipo_sentenca)


get_total_extintos_com_merito_2g_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_total_extintos_com_merito_2g)


get_valor_causa_total_extintos_com_merito_2g_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_valor_causa_total_extintos_com_merito_2g)


get_valor_causa_acordao_total_extintos_com_merito_2g_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_valor_causa_acordao_total_extintos_com_merito_2g)


get_extintos_com_merito_2g_por_tipo_sentenca_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_extintos_com_merito_2g_por_tipo_sentenca)


get_extintos_com_merito_2g_por_tipo_sentenca_valor_acordao_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_extintos_com_merito_2g_por_tipo_sentenca_valor_acordao)


get_total_extintos_sem_merito_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_total_extintos_sem_merito)


get_valor_causa_total_extintos_sem_merito_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_valor_causa_total_extintos_sem_merito)


get_total_extintos_sem_merito_2g_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_total_extintos_sem_merito_2g)


get_valor_causa_total_extintos_sem_merito_2g_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_valor_causa_total_extintos_sem_merito_2g)


get_valor_causa_acordao_total_extintos_sem_merito_2g_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_valor_causa_acordao_total_extintos_sem_merito_2g)


# -----------------------------------------------------------------------------
# Taxa de provimento (2º grau)
# -----------------------------------------------------------------------------
_filtrar_acordaos_2g_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia._filtrar_acordaos_2g)


get_total_acordaos_2g_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_total_acordaos_2g)


get_total_decisoes_positivas_taxa_provimento_2g_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_total_decisoes_positivas_taxa_provimento_2g)


get_total_decisoes_improcedentes_taxa_provimento_2g_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_total_decisoes_improcedentes_taxa_provimento_2g)


get_taxa_provimento_2g_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_taxa_provimento_2g)


get_media_tempo_dias_fase_inicial_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_media_tempo_dias_fase_inicial)


get_media_tempo_dias_fase_recursal_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_media_tempo_dias_fase_recursal)


get_media_tempo_dias_fase_execucao_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_media_tempo_dias_fase_execucao)


get_mediana_tempo_dias_fase_inicial_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_mediana_tempo_dias_fase_inicial)


get_mediana_tempo_dias_fase_recursal_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_mediana_tempo_dias_fase_recursal)


get_mediana_tempo_dias_fase_execucao_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_mediana_tempo_dias_fase_execucao)


_comparativo_percentual_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia._comparativo_percentual)


get_comparativo_media_tempo_dias_fase_inicial_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_comparativo_media_tempo_dias_fase_inicial)


get_comparativo_media_tempo_dias_fase_recursal_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_comparativo_media_tempo_dias_fase_recursal)


get_comparativo_media_tempo_dias_fase_execucao_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_comparativo_media_tempo_dias_fase_execucao)


get_comparativo_mediana_tempo_dias_fase_inicial_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_comparativo_mediana_tempo_dias_fase_inicial)


get_comparativo_mediana_tempo_dias_fase_recursal_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_comparativo_mediana_tempo_dias_fase_recursal)


get_comparativo_mediana_tempo_dias_fase_execucao_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_comparativo_mediana_tempo_dias_fase_execucao)


_media_dias_permanencia_setor_por_mes_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia._media_dias_permanencia_setor_por_mes)


get_media_tempo_dias_fase_inicial_por_mes_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_media_tempo_dias_fase_inicial_por_mes)


get_media_tempo_dias_fase_recursal_por_mes_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_media_tempo_dias_fase_recursal_por_mes)


get_media_tempo_dias_fase_execucao_por_mes_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_media_tempo_dias_fase_execucao_por_mes)


# -----------------------------------------------------------------------------
# 3 - Filtros
# -----------------------------------------------------------------------------
filter_controle_processo_por_situacao_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.filter_controle_processo_por_situacao)


get_opcoes_uf_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_opcoes_uf)


filter_controle_processo_com_numero_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.filter_controle_processo_com_numero)


filter_controle_processo_por_uf_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.filter_controle_processo_por_uf)


filter_controle_processo_por_fase_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.filter_controle_processo_por_fase)


# -----------------------------------------------------------------------------
# 4 - Agrupamentos (derivados da base)
# -----------------------------------------------------------------------------
group_controle_processo_por_fase_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.group_controle_processo_por_fase)


group_controle_processo_por_subfase_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.group_controle_processo_por_subfase)


group_controle_processo_por_subfase_na_fase_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.group_controle_processo_por_subfase_na_fase)


# -----------------------------------------------------------------------------
# 5 - Tempo médio por subfase (log_fase_processual)
# -----------------------------------------------------------------------------
_COL_LOG_ID_PROCESSO = _familia._COL_LOG_ID_PROCESSO

_COL_LOG_DATA = _familia._COL_LOG_DATA


_base_log_subfase_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia._base_log_subfase)


_construir_segmentos_subfase_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia._construir_segmentos_subfase)


get_tempo_medio_dias_por_subfase_NG = _unidade.na_unidade_de(_familia._escritorio_ctx, _escritorio_ctx.get, _familia.get_tempo_medio_dias_por_subfase)

