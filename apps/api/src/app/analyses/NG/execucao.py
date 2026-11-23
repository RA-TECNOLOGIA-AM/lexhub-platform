# Funções de análises do setor de Execução

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
ID_ESCRITORIO = 20
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


_get_data_execucao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_data_execucao)


_get_data_compensacao_alvara = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_data_compensacao_alvara)


_get_data_compensacao_alvara_incontroverso = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_data_compensacao_alvara_incontroverso)


_normalizar_titulo_extra = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._normalizar_titulo_extra)


_campos_extras = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._campos_extras)


_eventos_incontroverso = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._eventos_incontroverso)


_get_data_encerramento = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_data_encerramento)


_get_ultima_movimentacao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ultima_movimentacao)


_get_data_distribuicao_ng = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_data_distribuicao)


_data_no_periodo = _familia._data_no_periodo


_converter_valor = _familia._converter_valor


_to_int = _familia._to_int


_base_execucao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._base_execucao)


_get_valor_execucao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_valor_execucao)


_get_valor_ted = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_valor_ted)


_get_valor_incontroverso = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_valor_incontroverso)


_get_valor_remanescente = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_valor_remanescente)


_get_valor_execucao_em_aberto = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_valor_execucao_em_aberto)


_get_valor_honorarios = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_valor_honorarios)


_processo_em_execucao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._processo_em_execucao)


_processo_fase_financeiro = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._processo_fase_financeiro)


# =============================================================================
# 2 - Queries de filtragem
# =============================================================================

_filtrar_em_execucao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_em_execucao)


_filtrar_por_data_execucao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_por_data_execucao)


_filtrar_entrada_execucao_no_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_entrada_execucao_no_periodo)


_filtrar_saida_no_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_saida_no_periodo)


_filtrar_saida_incontroverso_no_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_saida_incontroverso_no_periodo)


_normalizar_materia = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._normalizar_materia)


_primeiro_valor_preenchido = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._primeiro_valor_preenchido)


group_alvaras_expedidos_por_dia_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_alvaras_expedidos_por_dia)


_SUBFASES_ALVARA_EXPEDIDO = _familia._SUBFASES_ALVARA_EXPEDIDO


list_processos_alvara_expedido_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.list_processos_alvara_expedido)


_normalizar_subfase = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._normalizar_subfase)


_normalizar_comarca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._normalizar_comarca)


filter_execucao_por_materia = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filter_execucao_por_materia)


filter_execucao_por_subfase = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filter_execucao_por_subfase)


_SEM_ANO_AJUIZAMENTO_EXEC = _familia._SEM_ANO_AJUIZAMENTO_EXEC


filter_execucao_por_ano_ajuizamento = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filter_execucao_por_ano_ajuizamento)


filter_execucao_por_uf = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filter_execucao_por_uf)


get_opcoes_uf_execucao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_uf_execucao)


filter_execucao_por_comarca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filter_execucao_por_comarca)


get_opcoes_comarca_execucao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_comarca_execucao)


get_opcoes_materia_execucao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_materia_execucao)


get_opcoes_subfase_execucao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_subfase_execucao)


# =============================================================================
# 3 - Totais
# =============================================================================

get_total_execucao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_execucao)


get_total_entrada_execucao_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_entrada_execucao_periodo)


get_total_saida_execucao_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_saida_execucao_periodo)


get_estoque_final = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_estoque_final)


get_tre = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_tre)


get_tre_execucao_dax = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_tre_execucao_dax)


# =============================================================================
# 4 - Valores monetários
# =============================================================================

get_valor_causa_total_execucao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_total_execucao)


get_detalhe_valor_execucao_vazio = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_detalhe_valor_execucao_vazio)


get_total_valor_execucao_vazio = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_valor_execucao_vazio)

get_valor_honorarios_total_execucao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_honorarios_total_execucao)

get_valor_em_execucao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_em_execucao)


get_valor_remanescente_em_execucao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_remanescente_em_execucao)


get_valor_execucao_saida_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_execucao_saida_periodo)


get_valor_incontroverso_saida_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_incontroverso_saida_periodo)


get_total_incontroverso_saida_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_incontroverso_saida_periodo)


filtrar_saida_execucao_export = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_saida_execucao_export)


anotar_saida_execucao_export = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.anotar_saida_execucao_export)


_somar_campos_ted = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._somar_campos_ted)


get_valor_ted_saida_execucao_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_ted_saida_execucao_periodo)


get_taxa_recuperacao_execucao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_taxa_recuperacao_execucao)


# =============================================================================
# 5 - Agrupamentos
# =============================================================================

group_valor_saida_execucao_por_mes = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_valor_saida_execucao_por_mes)


group_valor_execucao_saida_periodo_por_mes = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_valor_execucao_saida_periodo_por_mes)


group_valor_remanescente_por_mes = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_valor_remanescente_por_mes)


group_quantidade_saida_execucao_por_mes = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_quantidade_saida_execucao_por_mes)


group_quantidade_entrada_execucao_por_mes = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_quantidade_entrada_execucao_por_mes)


group_valor_entrada_execucao_por_mes = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_valor_entrada_execucao_por_mes)


group_execucao_por_subfase = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_por_subfase)


group_execucao_por_comarca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_por_comarca)


_uf_por_comarca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._uf_por_comarca)


group_valor_execucao_por_comarca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_valor_execucao_por_comarca)


group_valor_execucao_por_subfase = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_valor_execucao_por_subfase)


group_execucao_por_materia = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_por_materia)


group_valor_execucao_por_materia = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_valor_execucao_por_materia)


group_execucao_por_ano_ajuizamento_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_por_ano_ajuizamento)


# =============================================================================
# 6 - Análise temporal
# =============================================================================

_extrair_duracoes_dias = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._extrair_duracoes_dias)


get_media_tempo_execucao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_media_tempo_execucao)


get_mediana_tempo_execucao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_mediana_tempo_execucao)


get_media_tempo_execucao_por_mes = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_media_tempo_execucao_por_mes)


_classificar_faixa_ultima_movimentacao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._classificar_faixa_ultima_movimentacao)


group_execucao_por_faixa_ultima_movimentacao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_por_faixa_ultima_movimentacao)


# =============================================================================
# 7 - Atividades no período (agendamentos do setor Execução NG)
# =============================================================================

_STATUS_INATIVO_EXEC = _familia._STATUS_INATIVO_EXEC

_STATUS_EM_ANDAMENTO_EXEC = _familia._STATUS_EM_ANDAMENTO_EXEC

_STATUS_ENCERRADO_EXEC = _familia._STATUS_ENCERRADO_EXEC

_STATUS_FILTRO_EXEC = _familia._STATUS_FILTRO_EXEC

_SITUACOES_FILTRO_EXEC_NG = _familia._SITUACOES_FILTRO_EXEC

SITUACOES_VALIDAS_EXECUCAO_NG = _familia.SITUACOES_VALIDAS_EXECUCAO

_STATUS_DEMANDAS_FUNCIONARIO_EXEC_NG = _familia._STATUS_DEMANDAS_FUNCIONARIO_EXEC

_SLUG_POR_STATUS_EXEC_NG = _familia._SLUG_POR_STATUS_EXEC

_SEM_ATIVIDADE_EXEC = _familia._SEM_ATIVIDADE_EXEC

_SEM_FUNCIONARIO_EXEC = _familia._SEM_FUNCIONARIO_EXEC

_STATUS_CUMPRIDO_EXEC = _familia._STATUS_CUMPRIDO_EXEC

_COL_FUNCIONARIO_ATRIBUIDO_EXEC = _familia._COL_FUNCIONARIO_ATRIBUIDO_EXEC

_COL_FUNCIONARIO_ENCERRAMENTO_EXEC = _familia._COL_FUNCIONARIO_ENCERRAMENTO_EXEC

_COL_ID_USUARIO_ENCERRAMENTO_EXEC = _familia._COL_ID_USUARIO_ENCERRAMENTO_EXEC

# Reutiliza helpers de data já definidos no módulo
_ag_to_date = _familia._ag_to_date

_ag_data_no_periodo = _familia._ag_data_no_periodo


_nome_em_conjunto_exec_ng = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._nome_em_conjunto_exec)


_get_ag_status_ng = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_status)


_get_ag_data_criacao_ng = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_data_criacao)


_get_ag_data_conclusao_ng = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_data_conclusao)


_get_ag_prazo_ng = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_prazo)


_get_ag_processo_id_ng = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_processo_id)


_get_ag_numero_processo_ng = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_numero_processo)


_get_ag_valor_sentenca_ng = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_valor_sentenca)


_get_ag_valor_acordao_ng = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_valor_acordao)


_get_ag_atividade_nome_ng = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_atividade_nome)


_get_ag_funcionario_atribuido_ng = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_funcionario_atribuido)


_get_ag_funcionario_encerramento_ng = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_funcionario_encerramento)


# V2: como estas atividades são lidas e quais status contam (app/analyses/common/atividades.py).
_ATIVIDADES = atividades.Leitor(
    criacao=_get_ag_data_criacao_ng,
    conclusao=_get_ag_data_conclusao_ng,
    prazo=_get_ag_prazo_ng,
    status=_get_ag_status_ng,
    funcionario_encerramento=_get_ag_funcionario_encerramento_ng,
)
_STATUS_ATIVIDADES = _familia._STATUS_ATIVIDADES


_get_ag_funcionario_nome_ng = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_funcionario_nome)


_incluir_na_lista_exec_ng = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._incluir_na_lista_exec)


_classificar_situacao_exec_ng = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._classificar_situacao_exec)


_filtrar_ag_encerrados_no_periodo_ng = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_ag_encerrados_no_periodo)


get_kpis_atividades_execucao_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_kpis_atividades_execucao)


get_media_mensal_atividades_execucao_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_media_mensal_atividades_execucao)


group_execucao_processos_por_atividade_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_processos_por_atividade)


group_atividades_ativas_criadas_por_atividade_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_atividades_ativas_criadas_por_atividade)


group_atividades_criadas_por_atividade_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_atividades_criadas_por_atividade)


group_atividades_ativas_por_prazo_por_atividade_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_atividades_ativas_por_prazo_por_atividade)


group_execucao_demandas_por_funcionario_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_demandas_por_funcionario)


_SEM_FUNCIONARIO_ENCERRAMENTO_EXEC_NG = _familia._SEM_FUNCIONARIO_ENCERRAMENTO_EXEC


group_execucao_demandas_por_funcionario_completo_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_demandas_por_funcionario_completo)


group_taxa_conclusao_por_funcionario_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_taxa_conclusao_por_funcionario)


_ATIVIDADES_FLUXO_CS_1G_NG = _familia._ATIVIDADES_FLUXO_CS_1G

_ATIVIDADES_FLUXO_CS_2G_NG = _familia._ATIVIDADES_FLUXO_CS_2G
# Concluir a CS é o que marca a entrada (93% no mesmo dia, out/2026); a janela absorve
# pequenos desvios sem atribuir à CS entradas antigas de processos que já estavam na Execução.
_JANELA_FLUXO_CS_DIAS = _familia._JANELA_FLUXO_CS_DIAS


_entradas_por_fluxo_cs_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._entradas_por_fluxo_cs)


get_taxa_atualizacao_execucao_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_taxa_atualizacao_execucao)


group_entrada_execucao_por_fluxo_cs_por_mes_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_entrada_execucao_por_fluxo_cs_por_mes)


group_execucao_resolvidos_por_dia_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_resolvidos_por_dia)


get_media_execucao_resolvidos_por_funcionario_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_media_execucao_resolvidos_por_funcionario)


group_valor_recuperado_por_funcionario_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_valor_recuperado_por_funcionario)


list_execucao_atividades_periodo_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.list_execucao_atividades_periodo)


list_execucao_atividades_abertas_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.list_execucao_atividades_abertas)


get_opcoes_filtros_execucao_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_filtros_execucao)


_agendamento_match_filtros_exec_ng = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._agendamento_match_filtros_exec)


filtrar_agendamentos_execucao_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_agendamentos_execucao)


# ---------------------------------------------------------------------------
# Análise por Prazo — NG (mesmas 5 métricas, mas usando PRAZO como eixo
# temporal em vez de DATA_HORA_CRIACAO/DATA_HORA_CONCLUSAO). Mesmo padrão de
# analyses/LA/pendencias_intermediarias_LA.py.
# ---------------------------------------------------------------------------

_incluir_na_lista_por_prazo_exec_ng = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._incluir_na_lista_por_prazo_exec)


_classificar_situacao_por_prazo_exec_ng = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._classificar_situacao_por_prazo_exec)


get_kpis_execucao_por_prazo_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_kpis_execucao_por_prazo)


group_execucao_processos_por_atividade_por_prazo_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_processos_por_atividade_por_prazo)


group_execucao_demandas_por_funcionario_por_prazo_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_demandas_por_funcionario_por_prazo)


group_execucao_demandas_por_funcionario_por_prazo_completo_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_demandas_por_funcionario_por_prazo_completo)


list_execucao_atividades_por_prazo_periodo_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.list_execucao_atividades_por_prazo_periodo)


get_opcoes_filtros_execucao_por_prazo_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_filtros_execucao_por_prazo)


group_execucao_resolvidos_por_dia_por_prazo_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_resolvidos_por_dia_por_prazo)


get_media_execucao_resolvidos_por_funcionario_por_prazo_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_media_execucao_resolvidos_por_funcionario_por_prazo)


# ---------------------------------------------------------------------------
# Motivo de "Encerrado Não Cumprido" — NG
# ---------------------------------------------------------------------------

_get_ag_motivo_encaminhamento_itens_ng = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_motivo_encaminhamento_itens)


group_execucao_nao_cumprido_por_motivo_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_nao_cumprido_por_motivo)


# ---------------------------------------------------------------------------
# Detalhamento de atrasos (vencidas por dias de atraso) — NG
# ---------------------------------------------------------------------------

_ATRASO_MAX_BUCKET_NG = _familia._ATRASO_MAX_BUCKET

_BUCKET_META_NG = _familia._BUCKET_META


get_atrasos_detalhamento_execucao_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_atrasos_detalhamento_execucao)

# =============================================================================
# X - Diligências (subconjunto de agendamentos do setor EXECUÇÃO)
# =============================================================================
#
# Diligência é um tipo de agendamento dentro do setor EXECUÇÃO (ex.: "DILIGÊNCIA
# CUMPRIMENTO DE SENTENÇA", "DILIGÊNCIA PARA EXPEDIÇÃO DE ALVARÁ"), identificado pelo nome da atividade conter "DILIG". Um mesmo
# processo pode ter a diligência agendada mais de uma vez ao longo do tempo.

_eh_diligencia_ng = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._eh_diligencia)


filtrar_agendamentos_diligencia_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_agendamentos_diligencia)


get_total_diligencias_execucao_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_diligencias_execucao)


group_execucao_diligencias_por_processo_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_diligencias_por_processo)


_eh_diligencia_expedicao_alvara_ng = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._eh_diligencia_expedicao_alvara)


filtrar_agendamentos_diligencia_expedicao_alvara_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_agendamentos_diligencia_expedicao_alvara)


get_kpis_diligencias_expedicao_alvara_execucao_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_kpis_diligencias_expedicao_alvara_execucao)


_diligencias_expedicao_alvara_cumpridas_ng = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._diligencias_expedicao_alvara_cumpridas)


list_processos_diligencia_expedicao_alvara_cumprida_execucao_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.list_processos_diligencia_expedicao_alvara_cumprida_execucao)


_TIPOS_VALIDOS_DILIGENCIA_NG = _familia._TIPOS_VALIDOS_DILIGENCIA


filtrar_agendamentos_diligencia_por_tipo_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_agendamentos_diligencia_por_tipo)


filtrar_agendamentos_diligencia_por_colaborador_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_agendamentos_diligencia_por_colaborador)


group_estoque_execucao_por_mes = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_estoque_execucao_por_mes)
