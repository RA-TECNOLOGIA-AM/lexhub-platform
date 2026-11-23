# Dashboard Julgados — Escritório NG (id_escritorio_assinante = 20)
#
# A query `julgados` (queries.py) é compartilhada entre escritórios, sem filtro
# de escritório no SQL. O recorte para NG é feito aqui via `_base_julgados_NG`,
# para permitir reuso do mesmo dado por outros escritórios (LA, etc.) no futuro.

from __future__ import annotations

from app.analyses.common import unidade as _unidade  # V2: valores da unidade (common/unidade.py)
from app.analyses.familias import julgados_sentenca as _familia  # V2: código único da família (familias/julgados_sentenca.py)
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Optional

from app.analyses.common import julgados  # V2: leitores e agrupamentos dos Julgados num módulo só
from app.analyses.common import conversao  # V2: conversões dos valores do banco num módulo só
from app.analyses.common import periodo  # V2: período e variação vs período anterior num módulo só
from app.analyses.common import memo  # V2: cache por pedido (a mesma conta uma vez por pedido)
from app.analyses.common import tempo  # V2: média/mediana de tempo num módulo só
from app.utils import parse_date_from_db, resolver_periodo_comparativo
from app.analyses.common import matriz_julgamento as mj
from app.analyses.common.julgados_agravo import eh_processo_agravo, numero_processo

# V2: os valores desta unidade para a família, lidos ao vivo deste módulo (common/unidade.py).
_VALORES_UNIDADE = _unidade.ValoresDoModulo(globals(), {"ID_ESCRITORIO": "ID_ESCRITORIO_NG"})

# =============================================================================
# Constantes
# =============================================================================

ID_ESCRITORIO_NG = 20

_COL_ID_ESCRITORIO = _familia._COL_ID_ESCRITORIO

_COL_ID_1G = _familia._COL_ID_1G

_COL_STATUS_1G = _familia._COL_STATUS_1G

_COL_STATUS_2G = _familia._COL_STATUS_2G

_COL_DATA_AJUIZAMENTO = _familia._COL_DATA_AJUIZAMENTO

_COL_DATA_SENTENCA = _familia._COL_DATA_SENTENCA

_COL_JUIZ_1G = _familia._COL_JUIZ_1G

_COL_MATERIA = _familia._COL_MATERIA

_COL_COMPETENCIA = _familia._COL_COMPETENCIA

_COL_COMARCA = _familia._COL_COMARCA

_COL_UF = _familia._COL_UF

_COL_MOTIVO_STATUS_1G = _familia._COL_MOTIVO_STATUS_1G

_COL_VALOR_CAUSA_SENTENCA = _familia._COL_VALOR_CAUSA_SENTENCA

_SEM_MATERIA = _familia._SEM_MATERIA

_SEM_COMPETENCIA = _familia._SEM_COMPETENCIA

_SEM_COMARCA = _familia._SEM_COMARCA

_SEM_MOTIVO_EXTINCAO = _familia._SEM_MOTIVO_EXTINCAO

_SEM_ANO_AJUIZAMENTO = _familia._SEM_ANO_AJUIZAMENTO

_MONTH_NAMES = _familia._MONTH_NAMES

_RESULTADO_FAV = _familia._RESULTADO_FAV

_RESULTADO_DES = _familia._RESULTADO_DES

_RESULTADO_OUTROS = _familia._RESULTADO_OUTROS

# Mérito 1G (esquema novo, ``sentenca_merito_primeiro_grau`` — ver
# ``app.analyses.common.matriz_julgamento``). ACORDO HOMOLOGADO não tem mais
# equivalente de mérito (eixo próprio, fora de escopo) — processos só com esse
# status antigo deixam de contar como "Procedentes" nesta migração.
_IDS_1G_PROCEDENTE = _familia._IDS_1G_PROCEDENTE

_IDS_1G_IMPROCEDENTE = _familia._IDS_1G_IMPROCEDENTE

_IDS_1G_EXTINTO = _familia._IDS_1G_EXTINTO


# =============================================================================
# Utilitários
# =============================================================================

_to_int = _familia._to_int


_to_date = _familia._to_date


_data_no_periodo = _familia._data_no_periodo


_get_id_1g = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_id_1g)


_get_id_2g = _familia._get_id_2g


_get_data_sentenca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_data_sentenca)


_get_data_ajuizamento = _familia._get_data_ajuizamento


_get_data_embargos_sentenca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_data_embargos_sentenca)


_get_resultado_embargos_sentenca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_resultado_embargos_sentenca)


_get_ano_ajuizamento = _familia._get_ano_ajuizamento


_to_float = _familia._to_float


_get_valor_causa_sentenca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_valor_causa_sentenca)


_normalizar_nome_juiz = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._normalizar_nome_juiz)


_get_juiz_1g = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_juiz_1g)


_get_materia = _familia._get_materia


_get_competencia = _familia._get_competencia


_get_comarca = _familia._get_comarca


_get_uf = _familia._get_uf


_get_motivo_extincao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_motivo_extincao)


_iniciais_nome = _familia._iniciais_nome


_classificar_resultado_1g_julgados = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._classificar_resultado_1g_julgados)


# =============================================================================
# Filtros interativos cumulativos (matéria, juiz, comarca, competência, categoria)
# =============================================================================

CATEGORIA_PROCEDENTE = _familia.CATEGORIA_PROCEDENTE

CATEGORIA_IMPROCEDENTE = _familia.CATEGORIA_IMPROCEDENTE

CATEGORIA_EXTINTO = _familia.CATEGORIA_EXTINTO

CATEGORIAS_1G_VALIDAS_JULGADOS_NG = _familia.CATEGORIAS_1G_VALIDAS_JULGADOS

_RESULTADO_PARA_CATEGORIA = _familia._RESULTADO_PARA_CATEGORIA


_get_categoria_1g_julgados = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_categoria_1g_julgados)


_valor_em_conjunto_filtro_julgados = _familia._valor_em_conjunto_filtro_julgados


JulgadosSentencaFiltros = _familia.JulgadosSentencaFiltros


_sentenca_match_filtros_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._sentenca_match_filtros_julgados)


filtrar_sentencas_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_sentencas_julgados)


# =============================================================================
# Base por escritório
# =============================================================================

_base_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._base_julgados)


_filtrar_sentenca_no_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_sentenca_no_periodo)


_filtrar_embargos_sentenca_no_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_embargos_sentenca_no_periodo)


_contar_sentenca_por_categoria = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._contar_sentenca_por_categoria)


# =============================================================================
# KPIs de Sentença (1º Grau)
# =============================================================================

_tempo_medio_dias_sentenca_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._tempo_medio_dias_sentenca)


_valor_causa_sentencas_procedentes_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._valor_causa_sentencas_procedentes)


_contar_sentenca_embargados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._contar_sentenca_embargados)


_contar_sentenca_revertidos_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._contar_sentenca_revertidos)


_tempo_medio_dias_embargos_sentenca_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._tempo_medio_dias_embargos_sentenca)


get_kpis_sentenca_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_kpis_sentenca_julgados)


# =============================================================================
# Comparativos (mesmo padrão de analyses/NG/comercial_geral.py)
# =============================================================================

_resolver_periodos_comparativo_julgados_NG = _familia._resolver_periodos_comparativo_julgados


_comparativo_variacao_percentual_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._comparativo_variacao_percentual_julgados)


_comparativo_variacao_percentual_tempo_medio_sentenca_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._comparativo_variacao_percentual_tempo_medio_sentenca_julgados)


_comparativo_variacao_percentual_valor_sentenca_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._comparativo_variacao_percentual_valor_sentenca_julgados)


_comparativo_variacao_percentual_embargados_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._comparativo_variacao_percentual_embargados_julgados)


_comparativo_variacao_percentual_revertidos_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._comparativo_variacao_percentual_revertidos_julgados)


get_comparativos_sentenca_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_comparativos_sentenca_julgados)


# =============================================================================
# Ranking de juízes (1G): Procedentes / Improcedentes / Extintos
# =============================================================================

get_ranking_juizes_sentenca_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_ranking_juizes_sentenca_julgados)


# =============================================================================
# Distribuição por matéria / competência / comarca
# =============================================================================

_agrupar_por_campo = _familia._agrupar_por_campo


_group_sentenca_por_campo_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._group_sentenca_por_campo_julgados)


group_sentenca_por_materia_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_sentenca_por_materia_julgados)


group_sentenca_por_competencia_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_sentenca_por_competencia_julgados)


group_sentenca_por_comarca_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_sentenca_por_comarca_julgados)


_sentencas_extintas_no_escopo_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._sentencas_extintas_no_escopo)


group_sentenca_por_motivo_extincao_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_sentenca_por_motivo_extincao_julgados)


_uf_por_comarca_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._uf_por_comarca_julgados)


_tempo_medio_dias_por_comarca_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._tempo_medio_dias_por_comarca_julgados)


group_sentenca_extintas_por_comarca_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_sentenca_extintas_por_comarca_julgados)


get_opcoes_comarca_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_comarca_julgados)


get_ranking_juizes_extincao_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_ranking_juizes_extincao_julgados)


get_extincao_totais_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_extincao_totais_julgados)


get_total_sentencas_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_sentencas_julgados)


get_extincao_revertida_2g_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_extincao_revertida_2g_julgados)


# =============================================================================
# Estudo das Improcedências (11/11/2026) — mesma montagem do "Estudos de Extinção",
# trocando a categoria para improcedente (``_IDS_1G_IMPROCEDENTE``). Escopo igual:
# sem ``from_date``/``to_date`` = estoque (toda a base sentenciada); com datas = entrada.
# =============================================================================

_sentencas_improcedentes_no_escopo_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._sentencas_improcedentes_no_escopo)


group_sentenca_por_motivo_improcedencia_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_sentenca_por_motivo_improcedencia_julgados)


group_sentenca_improcedentes_por_comarca_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_sentenca_improcedentes_por_comarca_julgados)


get_ranking_juizes_improcedencia_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_ranking_juizes_improcedencia_julgados)


get_improcedencia_totais_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_improcedencia_totais_julgados)


get_improcedencia_revertida_2g_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_improcedencia_revertida_2g_julgados)


group_sentenca_por_ano_ajuizamento_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_sentenca_por_ano_ajuizamento_julgados)


group_sentenca_embargos_resultado_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_sentenca_embargos_resultado_julgados)


# =============================================================================
# Histórico de sentenças por mês e categoria — sem filtro de data, para o
# gráfico "Sentenças mês a mês" (uma série por categoria; ano filtrado no front)
# =============================================================================

_group_sentenca_por_mes_categoria_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._group_sentenca_por_mes_categoria)


group_julgados_sentenca_procedentes_por_mes_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_julgados_sentenca_procedentes_por_mes)


group_julgados_sentenca_improcedentes_por_mes_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_julgados_sentenca_improcedentes_por_mes)


group_julgados_sentenca_extintos_por_mes_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_julgados_sentenca_extintos_por_mes)


# =============================================================================
# Opções de UF (para o filtro ao lado do seletor de período)
# =============================================================================

get_opcoes_uf_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_uf_julgados)


# =============================================================================
# Sentenças com campos vazios (juiz / matéria / comarca / competência / UF)
# =============================================================================

_IDS_MERITO_COM_PE = _familia._IDS_MERITO_COM_PE


_falta_valor_pe_sentenca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._falta_valor_pe_sentenca)


_merito_sem_data_sentenca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._merito_sem_data_sentenca)


_data_sem_merito_sentenca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._data_sem_merito_sentenca)


get_julgados_sentenca_campos_vazios_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_julgados_sentenca_campos_vazios)


get_julgados_sentenca_dados_faltando_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_julgados_sentenca_dados_faltando)


# =============================================================================
# Lista de sentenças (tabela): Nº processo, fase, subfase, status 1G, UF, juiz, data
# =============================================================================

_get_fase = _familia._get_fase


_get_subfase = _familia._get_subfase


_get_status_1g = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_status_1g)


_get_status_embargos_sentenca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_status_embargos_sentenca)


_get_numero_processo = _familia._get_numero_processo


list_sentencas_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.list_sentencas_julgados)
