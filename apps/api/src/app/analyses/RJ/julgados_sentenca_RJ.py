# Dashboard Julgados Sentenças — Escritório RJ / LAADV RJ (id_escritorio_assinante = 27)
#
# Réplica de `LA/julgados_sentenca_LA.py` (06/11/2026): mesma lógica e regras (inclusive
# exclusão de agravos), só troca o escritório 21 -> 27.
#
# A query `julgados` (queries.py) é compartilhada entre escritórios, sem filtro
# de escritório no SQL. O recorte para RJ é feito aqui via `_base_julgados_RJ`,
# mesma query e joins usados pelo módulo NG (`julgados_sentenca.py`).

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
_VALORES_UNIDADE = _unidade.ValoresDoModulo(globals(), {"ID_ESCRITORIO": "ID_ESCRITORIO_RJ"})

# =============================================================================
# Constantes
# =============================================================================

ID_ESCRITORIO_RJ = 27

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

CATEGORIAS_1G_VALIDAS_JULGADOS_RJ = _familia.CATEGORIAS_1G_VALIDAS_JULGADOS

_RESULTADO_PARA_CATEGORIA = _familia._RESULTADO_PARA_CATEGORIA


_get_categoria_1g_julgados = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_categoria_1g_julgados)


_valor_em_conjunto_filtro_julgados = _familia._valor_em_conjunto_filtro_julgados


JulgadosSentencaFiltrosRJ = _familia.JulgadosSentencaFiltros


_sentenca_match_filtros_julgados_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._sentenca_match_filtros_julgados)


filtrar_sentencas_julgados_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_sentencas_julgados)


# =============================================================================
# Base por escritório
# =============================================================================

_base_julgados_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._base_julgados)


_filtrar_sentenca_no_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_sentenca_no_periodo)


_filtrar_embargos_sentenca_no_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_embargos_sentenca_no_periodo)


_contar_sentenca_por_categoria = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._contar_sentenca_por_categoria)


# =============================================================================
# KPIs de Sentença (1º Grau)
# =============================================================================

_tempo_medio_dias_sentenca_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._tempo_medio_dias_sentenca)


_valor_causa_sentencas_procedentes_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._valor_causa_sentencas_procedentes)


_contar_sentenca_embargados_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._contar_sentenca_embargados)


_contar_sentenca_revertidos_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._contar_sentenca_revertidos)


_tempo_medio_dias_embargos_sentenca_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._tempo_medio_dias_embargos_sentenca)


def get_kpis_sentenca_julgados_RJ(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> dict[str, int]:
    """
    KPIs de sentenças (1º Grau) do escritório RJ no período (eixo: DATA_SENTENCA).

    - **Total**: processos com sentença proferida no período.
    - **Procedentes**: ``ID_1G`` em qualquer variação de procedência (total ou
      parcial, com ou sem proveito econômico).
    - **Improcedentes**: somente ``ID_1G`` = IMPROCEDENTE.
    - **Extintos**: ``ID_1G`` = extinção sem mérito.
    - **Tempo médio (dias)**: média entre DATA_AJUIZAMENTO e DATA_SENTENCA.
    - **Valor das sentenças procedentes**: soma de VALOR_CAUSA_SENTENCA só das procedentes.
    """
    base = _base_julgados_RJ(processos)
    return {
        "julgados_sentenca_total_RJ": _contar_sentenca_por_categoria(base, from_date, to_date, None),
        "julgados_sentenca_procedentes_RJ": _contar_sentenca_por_categoria(base, from_date, to_date, _IDS_1G_PROCEDENTE),
        "julgados_sentenca_improcedentes_RJ": _contar_sentenca_por_categoria(base, from_date, to_date, _IDS_1G_IMPROCEDENTE),
        "julgados_sentenca_extintos_RJ": _contar_sentenca_por_categoria(base, from_date, to_date, _IDS_1G_EXTINTO),
        "julgados_sentenca_tempo_medio_dias_RJ": _tempo_medio_dias_sentenca_RJ(base, from_date, to_date),
        "julgados_sentenca_embargos_tempo_medio_dias_RJ": _tempo_medio_dias_embargos_sentenca_RJ(base, from_date, to_date),
        "julgados_sentenca_valor_procedentes_RJ": _valor_causa_sentencas_procedentes_RJ(base, from_date, to_date),
        "julgados_sentenca_embargados_RJ": _contar_sentenca_embargados_RJ(base, from_date, to_date),
        "julgados_sentenca_revertidos_RJ": _contar_sentenca_revertidos_RJ(base, from_date, to_date),
    }


# =============================================================================
# Comparativos (mesmo padrão de analyses/NG/comercial_geral.py)
# =============================================================================

_resolver_periodos_comparativo_julgados_RJ = _familia._resolver_periodos_comparativo_julgados


_comparativo_variacao_percentual_julgados_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._comparativo_variacao_percentual_julgados)


_comparativo_variacao_percentual_tempo_medio_sentenca_julgados_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._comparativo_variacao_percentual_tempo_medio_sentenca_julgados)


_comparativo_variacao_percentual_valor_sentenca_julgados_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._comparativo_variacao_percentual_valor_sentenca_julgados)


_comparativo_variacao_percentual_embargados_julgados_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._comparativo_variacao_percentual_embargados_julgados)


_comparativo_variacao_percentual_revertidos_julgados_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._comparativo_variacao_percentual_revertidos_julgados)


def get_comparativos_sentenca_julgados_RJ(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> dict[str, float]:
    """Variação % de cada card de Sentença vs período anterior de mesma duração."""
    base = _base_julgados_RJ(processos)
    return {
        "comparativo_julgados_sentenca_total_RJ": _comparativo_variacao_percentual_julgados_RJ(
            base, from_date, to_date, None
        ),
        "comparativo_julgados_sentenca_procedentes_RJ": _comparativo_variacao_percentual_julgados_RJ(
            base, from_date, to_date, _IDS_1G_PROCEDENTE
        ),
        "comparativo_julgados_sentenca_improcedentes_RJ": _comparativo_variacao_percentual_julgados_RJ(
            base, from_date, to_date, _IDS_1G_IMPROCEDENTE
        ),
        "comparativo_julgados_sentenca_extintos_RJ": _comparativo_variacao_percentual_julgados_RJ(
            base, from_date, to_date, _IDS_1G_EXTINTO
        ),
        "comparativo_julgados_sentenca_tempo_medio_dias_RJ": _comparativo_variacao_percentual_tempo_medio_sentenca_julgados_RJ(
            base, from_date, to_date
        ),
        "comparativo_julgados_sentenca_valor_procedentes_RJ": _comparativo_variacao_percentual_valor_sentenca_julgados_RJ(
            base, from_date, to_date
        ),
        "comparativo_julgados_sentenca_embargados_RJ": _comparativo_variacao_percentual_embargados_julgados_RJ(
            base, from_date, to_date
        ),
        "comparativo_julgados_sentenca_revertidos_RJ": _comparativo_variacao_percentual_revertidos_julgados_RJ(
            base, from_date, to_date
        ),
    }


# =============================================================================
# Ranking de juízes (1G): Procedentes / Improcedentes / Extintos
# =============================================================================

get_ranking_juizes_sentenca_julgados_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_ranking_juizes_sentenca_julgados)


# =============================================================================
# Distribuição por matéria / competência / comarca
# =============================================================================

_agrupar_por_campo = _familia._agrupar_por_campo


_group_sentenca_por_campo_julgados_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._group_sentenca_por_campo_julgados)


group_sentenca_por_materia_julgados_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_sentenca_por_materia_julgados)


group_sentenca_por_competencia_julgados_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_sentenca_por_competencia_julgados)


group_sentenca_por_comarca_julgados_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_sentenca_por_comarca_julgados)


_sentencas_extintas_no_escopo_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._sentencas_extintas_no_escopo)


group_sentenca_por_motivo_extincao_julgados_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_sentenca_por_motivo_extincao_julgados)


_uf_por_comarca_julgados_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._uf_por_comarca_julgados)


_tempo_medio_dias_por_comarca_julgados_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._tempo_medio_dias_por_comarca_julgados)


group_sentenca_extintas_por_comarca_julgados_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_sentenca_extintas_por_comarca_julgados)


get_ranking_juizes_extincao_julgados_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_ranking_juizes_extincao_julgados)


get_extincao_totais_julgados_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_extincao_totais_julgados)


get_total_sentencas_julgados_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_sentencas_julgados)


get_extincao_revertida_2g_julgados_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_extincao_revertida_2g_julgados)


# =============================================================================
# Estudo das Improcedências (11/11/2026) — mesma montagem do "Estudos de Extinção",
# trocando a categoria para improcedente (``_IDS_1G_IMPROCEDENTE``). Escopo igual:
# sem ``from_date``/``to_date`` = estoque (toda a base sentenciada); com datas = entrada.
# =============================================================================

_sentencas_improcedentes_no_escopo_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._sentencas_improcedentes_no_escopo)


group_sentenca_por_motivo_improcedencia_julgados_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_sentenca_por_motivo_improcedencia_julgados)


group_sentenca_improcedentes_por_comarca_julgados_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_sentenca_improcedentes_por_comarca_julgados)


get_ranking_juizes_improcedencia_julgados_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_ranking_juizes_improcedencia_julgados)


get_improcedencia_totais_julgados_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_improcedencia_totais_julgados)


get_improcedencia_revertida_2g_julgados_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_improcedencia_revertida_2g_julgados)


group_sentenca_por_ano_ajuizamento_julgados_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_sentenca_por_ano_ajuizamento_julgados)


group_sentenca_embargos_resultado_julgados_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_sentenca_embargos_resultado_julgados)


# =============================================================================
# Histórico de sentenças por mês e categoria — sem filtro de data, para o
# gráfico "Sentenças mês a mês" (uma série por categoria; ano filtrado no front)
# =============================================================================

_group_sentenca_por_mes_categoria_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._group_sentenca_por_mes_categoria)


group_julgados_sentenca_procedentes_por_mes_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_julgados_sentenca_procedentes_por_mes)


group_julgados_sentenca_improcedentes_por_mes_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_julgados_sentenca_improcedentes_por_mes)


group_julgados_sentenca_extintos_por_mes_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_julgados_sentenca_extintos_por_mes)


# =============================================================================
# Opções de UF (para o filtro ao lado do seletor de período)
# =============================================================================

get_opcoes_uf_julgados_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_uf_julgados)


get_opcoes_comarca_julgados_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_comarca_julgados)


# =============================================================================
# Sentenças com campos vazios (juiz / matéria / comarca / competência / UF)
# =============================================================================

_IDS_MERITO_COM_PE = _familia._IDS_MERITO_COM_PE


_falta_valor_pe_sentenca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._falta_valor_pe_sentenca)


_merito_sem_data_sentenca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._merito_sem_data_sentenca)


_data_sem_merito_sentenca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._data_sem_merito_sentenca)


def get_julgados_sentenca_campos_vazios_RJ(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> dict[str, int]:
    """Quantidade de sentenças do período sem juiz/matéria/comarca/competência/UF preenchidos."""
    base = _base_julgados_RJ(processos)
    sentencas = _filtrar_sentenca_no_periodo(base, from_date, to_date)

    sem_juiz = sum(1 for row in sentencas if not _get_juiz_1g(row))
    sem_materia = sum(1 for row in sentencas if _get_materia(row) == _SEM_MATERIA)
    sem_comarca = sum(1 for row in sentencas if _get_comarca(row) == _SEM_COMARCA)
    sem_competencia = sum(1 for row in sentencas if _get_competencia(row) == _SEM_COMPETENCIA)
    sem_uf = sum(1 for row in sentencas if not _get_uf(row))
    sem_valor_pe = sum(1 for row in sentencas if _falta_valor_pe_sentenca(row))
    # Fora do eixo de data (10/11/2026): processos que não entram em nenhuma contagem do
    # dashboard por inconsistência entre mérito e data da sentença.
    merito_sem_data = sum(1 for row in base if _merito_sem_data_sentenca(row))
    data_sem_merito = sum(1 for row in base if _data_sem_merito_sentenca(row))

    return {
        "julgados_sentenca_sem_juiz_RJ": sem_juiz,
        "julgados_sentenca_sem_materia_RJ": sem_materia,
        "julgados_sentenca_sem_comarca_RJ": sem_comarca,
        "julgados_sentenca_sem_competencia_RJ": sem_competencia,
        "julgados_sentenca_sem_uf_RJ": sem_uf,
        "julgados_sentenca_sem_valor_pe_RJ": sem_valor_pe,
        "julgados_sentenca_merito_sem_data_RJ": merito_sem_data,
        "julgados_sentenca_data_sem_merito_RJ": data_sem_merito,
    }


get_julgados_sentenca_dados_faltando_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_julgados_sentenca_dados_faltando)


# =============================================================================
# Lista de sentenças (tabela): Nº processo, fase, subfase, status 1G, UF, juiz, data
# =============================================================================

_get_fase = _familia._get_fase


_get_subfase = _familia._get_subfase


_get_status_1g = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_status_1g)


_get_status_embargos_sentenca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_status_embargos_sentenca)


_get_numero_processo = _familia._get_numero_processo


list_sentencas_julgados_RJ = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.list_sentencas_julgados)
