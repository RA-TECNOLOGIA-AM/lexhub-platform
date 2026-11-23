# Dashboard Julgados Acórdãos — Escritório NG (id_escritorio_assinante = 20)
#
# A query `julgados` (queries.py) é compartilhada entre escritórios, sem filtro
# de escritório no SQL. O recorte para NG é feito aqui via `_base_julgados_NG`,
# para permitir reuso do mesmo dado por outros escritórios (LA, etc.) no futuro.
#
# Espelha `julgados_sentenca.py` (1º Grau), trocando ``DATA_SENTENCA`` por
# ``DATA_ACORDAO``, ``ID_1G``/``JUIZ_1G`` por ``ID_2G``/``RELATOR_2G`` — mesma
# query (`julgados`), mesmos processos, eixo temporal e status de 2º grau.

from __future__ import annotations

from app.analyses.common import unidade as _unidade  # V2: valores da unidade (common/unidade.py)
from app.analyses.familias import julgados_acordao as _familia  # V2: código único da família (familias/julgados_acordao.py)
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

_COL_ID_2G = _familia._COL_ID_2G

_COL_STATUS_2G = _familia._COL_STATUS_2G

_COL_DATA_ACORDAO = _familia._COL_DATA_ACORDAO

_COL_DATA_AJUIZAMENTO = _familia._COL_DATA_AJUIZAMENTO

_COL_RELATOR_2G = _familia._COL_RELATOR_2G

_COL_MATERIA = _familia._COL_MATERIA

_COL_COMPETENCIA = _familia._COL_COMPETENCIA

_COL_COMARCA = _familia._COL_COMARCA

_COL_UF = _familia._COL_UF

_COL_MOTIVO_STATUS_2G = _familia._COL_MOTIVO_STATUS_2G

_COL_VALOR_CAUSA_ACORDAO = _familia._COL_VALOR_CAUSA_ACORDAO

_SEM_MATERIA = _familia._SEM_MATERIA

_SEM_COMPETENCIA = _familia._SEM_COMPETENCIA

_SEM_COMARCA = _familia._SEM_COMARCA

_SEM_MOTIVO_EXTINCAO = _familia._SEM_MOTIVO_EXTINCAO

_SEM_ANO_AJUIZAMENTO = _familia._SEM_ANO_AJUIZAMENTO

_MONTH_NAMES = _familia._MONTH_NAMES

_RESULTADO_FAV = _familia._RESULTADO_FAV

_RESULTADO_DES = _familia._RESULTADO_DES

_RESULTADO_OUTROS = _familia._RESULTADO_OUTROS

# Mérito 2G (esquema novo, ``acordao_merito_segundo_grau`` — ver
# ``app.analyses.common.matriz_julgamento``). ACORDO HOMOLOGADO não tem mais
# equivalente de mérito (eixo próprio, fora de escopo) — processos só com esse
# status antigo deixam de contar como "Procedentes" e passam a cair em "Não
# classificados". SENTENÇA ANULADA (id novo 8) também não é procedente/
# improcedente/extinto — continua em "Não classificados", agora corretamente
# (antes dependia do ID antigo 22 não estar em nenhum dos 3 conjuntos).
_IDS_2G_PROCEDENTE = _familia._IDS_2G_PROCEDENTE

_IDS_2G_IMPROCEDENTE = _familia._IDS_2G_IMPROCEDENTE

_IDS_2G_EXTINTO = _familia._IDS_2G_EXTINTO


# =============================================================================
# Utilitários
# =============================================================================

_to_int = _familia._to_int


_to_date = _familia._to_date


_data_no_periodo = _familia._data_no_periodo


_get_id_2g = _familia._get_id_2g


_get_data_acordao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_data_acordao)


_get_data_sentenca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_data_sentenca)


_get_data_embargos_acordao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_data_embargos_acordao)


_get_resultado_embargos_acordao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_resultado_embargos_acordao)


_get_data_ajuizamento = _familia._get_data_ajuizamento


_get_ano_ajuizamento = _familia._get_ano_ajuizamento


_to_float = _familia._to_float


_get_valor_causa_acordao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_valor_causa_acordao)


_normalizar_nome_relator = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._normalizar_nome_relator)


_get_relator_2g = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_relator_2g)


_get_materia = _familia._get_materia


_get_competencia = _familia._get_competencia


_get_comarca = _familia._get_comarca


_get_uf = _familia._get_uf


_get_motivo_extincao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_motivo_extincao)


_iniciais_nome = _familia._iniciais_nome


_classificar_resultado_2g_julgados = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._classificar_resultado_2g_julgados)


# =============================================================================
# Filtros interativos cumulativos (matéria, relator, comarca, competência, categoria, UF)
# =============================================================================

CATEGORIA_PROCEDENTE = _familia.CATEGORIA_PROCEDENTE

CATEGORIA_IMPROCEDENTE = _familia.CATEGORIA_IMPROCEDENTE

CATEGORIA_EXTINTO = _familia.CATEGORIA_EXTINTO

CATEGORIAS_2G_VALIDAS_JULGADOS_NG = _familia.CATEGORIAS_2G_VALIDAS_JULGADOS

_RESULTADO_PARA_CATEGORIA = _familia._RESULTADO_PARA_CATEGORIA


_get_categoria_2g_julgados = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_categoria_2g_julgados)


_valor_em_conjunto_filtro_julgados = _familia._valor_em_conjunto_filtro_julgados


JulgadosAcordaoFiltros = _familia.JulgadosAcordaoFiltros


_acordao_match_filtros_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._acordao_match_filtros_julgados)


filtrar_acordaos_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_acordaos_julgados)


# =============================================================================
# Base por escritório
# =============================================================================

_base_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._base_julgados)


_filtrar_acordao_no_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_acordao_no_periodo)


_filtrar_embargos_acordao_no_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_embargos_acordao_no_periodo)


_contar_acordao_por_categoria = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._contar_acordao_por_categoria)


# =============================================================================
# KPIs de Acórdão (2º Grau)
# =============================================================================

_contar_acordao_nao_classificados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._contar_acordao_nao_classificados)


_valor_acordao_acordaos_procedentes_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._valor_acordao_acordaos_procedentes)


_valor_causa_acordaos_procedentes_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._valor_causa_acordaos_procedentes)


_contar_acordao_embargados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._contar_acordao_embargados)


_contar_acordao_revertidos_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._contar_acordao_revertidos)


_tempo_medio_dias_acordao_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._tempo_medio_dias_acordao)


_tempo_medio_dias_embargos_acordao_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._tempo_medio_dias_embargos_acordao)


get_kpis_acordao_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_kpis_acordao_julgados)


# =============================================================================
# Comparativos (mesmo padrão de analyses/NG/comercial_geral.py)
# =============================================================================

_resolver_periodos_comparativo_julgados_NG = _familia._resolver_periodos_comparativo_julgados


_comparativo_variacao_percentual_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._comparativo_variacao_percentual_julgados)


_comparativo_variacao_percentual_nao_classificados_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._comparativo_variacao_percentual_nao_classificados_julgados)


_comparativo_variacao_percentual_valor_fixado_acordao_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._comparativo_variacao_percentual_valor_fixado_acordao_julgados)


_comparativo_variacao_percentual_valor_acordao_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._comparativo_variacao_percentual_valor_acordao_julgados)


_comparativo_variacao_percentual_embargados_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._comparativo_variacao_percentual_embargados_julgados)


_comparativo_variacao_percentual_revertidos_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._comparativo_variacao_percentual_revertidos_julgados)


_comparativo_variacao_percentual_tempo_medio_acordao_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._comparativo_variacao_percentual_tempo_medio_acordao_julgados)


get_comparativos_acordao_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_comparativos_acordao_julgados)


# =============================================================================
# Ranking de relatores (2G): Procedentes / Improcedentes / Extintos
# =============================================================================

get_ranking_relatores_acordao_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_ranking_relatores_acordao_julgados)


# =============================================================================
# Distribuição por matéria / competência / comarca
# =============================================================================

_agrupar_por_campo = _familia._agrupar_por_campo


_group_acordao_por_campo_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._group_acordao_por_campo_julgados)


group_acordao_por_materia_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_acordao_por_materia_julgados)


group_acordao_por_competencia_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_acordao_por_competencia_julgados)


group_acordao_por_comarca_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_acordao_por_comarca_julgados)


group_acordao_por_motivo_extincao_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_acordao_por_motivo_extincao_julgados)


# =============================================================================
# Estudo das Improcedências — Acórdão (11/11/2026). Mesma montagem do estudo da
# Sentença: estoque (sem ``from_date``/``to_date``) ou entrada (``DATA_ACORDAO``
# no período); comarca (qtd + valor de causa inicial + UF + tempo médio), motivo
# informado no 2G, ranking de relatores e quantos subiram ao STJ/STF (subfase).
# =============================================================================

_acordaos_improcedentes_no_escopo_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._acordaos_improcedentes_no_escopo)


_uf_por_comarca_julgados_acordao_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._uf_por_comarca_julgados_acordao)


_tempo_medio_dias_por_comarca_acordao_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._tempo_medio_dias_por_comarca_acordao)


group_acordao_improcedentes_por_comarca_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_acordao_improcedentes_por_comarca_julgados)


group_acordao_por_motivo_improcedencia_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_acordao_por_motivo_improcedencia_julgados)


get_ranking_relatores_improcedencia_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_ranking_relatores_improcedencia_julgados)


get_improcedencia_acordao_totais_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_improcedencia_acordao_totais_julgados)


# Subfases (``status_processual``) de subida ao tribunal superior no NG.
ID_SUBFASE_RECURSO_ESPECIAL_STJ = _familia.ID_SUBFASE_RECURSO_ESPECIAL_STJ

ID_SUBFASE_RECURSO_EXTRAORDINARIO_STF = _familia.ID_SUBFASE_RECURSO_EXTRAORDINARIO_STF


_tribunal_superior_por_subfase = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._tribunal_superior_por_subfase)


get_improcedencia_acordao_tribunal_superior_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_improcedencia_acordao_tribunal_superior_julgados)


get_total_acordaos_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_acordaos_julgados)


group_acordao_por_ano_ajuizamento_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_acordao_por_ano_ajuizamento_julgados)


group_acordao_embargos_resultado_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_acordao_embargos_resultado_julgados)


# =============================================================================
# Histórico de acórdãos por mês e categoria — sem filtro de data, para o
# gráfico "Acórdãos mês a mês" (uma série por categoria; ano filtrado no front)
# =============================================================================

_group_acordao_por_mes_categoria_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._group_acordao_por_mes_categoria)


group_julgados_acordao_procedentes_por_mes_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_julgados_acordao_procedentes_por_mes)


group_julgados_acordao_improcedentes_por_mes_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_julgados_acordao_improcedentes_por_mes)


group_julgados_acordao_extintos_por_mes_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_julgados_acordao_extintos_por_mes)


# =============================================================================
# Opções de UF (para o filtro ao lado do seletor de período)
# =============================================================================

get_opcoes_uf_julgados_acordao_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_uf_julgados_acordao)


# =============================================================================
# Acórdãos com campos vazios (relator / matéria / comarca / competência / UF)
# =============================================================================

_IDS_MERITO_COM_PE = _familia._IDS_MERITO_COM_PE


_falta_valor_pe_acordao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._falta_valor_pe_acordao)


_merito_sem_data_acordao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._merito_sem_data_acordao)


_data_sem_merito_acordao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._data_sem_merito_acordao)


get_julgados_acordao_campos_vazios_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_julgados_acordao_campos_vazios)


get_julgados_acordao_dados_faltando_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_julgados_acordao_dados_faltando)


# =============================================================================
# Lista de acórdãos (tabela): Nº processo, fase, subfase, status 2G, UF, relator, data
# =============================================================================

_get_fase = _familia._get_fase


_get_subfase = _familia._get_subfase


_get_status_2g = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_status_2g)


_get_status_embargos_acordao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_status_embargos_acordao)


_get_numero_processo = _familia._get_numero_processo


list_acordaos_julgados_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.list_acordaos_julgados)
