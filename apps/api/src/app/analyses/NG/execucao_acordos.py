# Funções de análises do setor de Execução de Acordos (NG)
#
# Mirror de app/analyses/NG/execucao.py: estoque/fluxo/valor + seção Atividades
# (agendamentos do setor 'ACORDOS - %', em vez de 'EXECUÇÃO - %').
#
# Diferenças de domínio em relação a Execução (condenação):
# - Entrada:  DATA_EXECUCAO (coluna `execucao`) — não DATA_ACORDO_FECHADO.
#             `acordo_fechado` nem sempre é preenchida no LEXFLOW mesmo quando o
#             processo já tem execução, valor de alçada final e situação
#             definidos, o que subcontava entradas reais; DATA_EXECUCAO é o
#             campo confiável. `acordo_fechado`/etiqueta "Acordo" continuam
#             sendo o critério de população (ver `_tem_etiqueta_ou_acordo_fechado`).
# - Saída:    DATA_PAGAMENTO_ACORDO (coluna `pagamento_acordo`), não
#             GREATEST(transito_julgado, encerramento) na fase Financeiro.
# - Valor:    VALOR_ALCADA_FINAL (coluna `valor_alcada_final`), não VALOR_EXECUCAO.
# - População: dentro do universo NG (ID_ESCRITORIO=20), processos na fase de
#              Acordo (ID_FASE=30) com etiqueta "Acordo" OU `acordo_fechado`
#              preenchido.

from __future__ import annotations

from app.analyses.common import unidade as _unidade  # V2: valores da unidade (common/unidade.py)
from app.analyses.familias import execucao_acordos as _familia  # V2: código único da família (familias/execucao_acordos.py)
import json
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

ID_FASE_ACORDO = _familia.ID_FASE_ACORDO
ID_ESCRITORIO = 20

_COL_ID_ESCRITORIO = _familia._COL_ID_ESCRITORIO

_MONTH_NAMES = _familia._MONTH_NAMES


# =============================================================================
# 1 - Helpers internos
# =============================================================================

_to_date = _familia._to_date


_get_data_acordo_fechado = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_data_acordo_fechado)


_get_data_pagamento_acordo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_data_pagamento_acordo)


_get_data_distribuicao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_data_distribuicao)


_get_data_execucao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_data_execucao)


_data_no_periodo = _familia._data_no_periodo


_converter_valor = _familia._converter_valor


_to_int = _familia._to_int


# =============================================================================
# 2 - Base e filtragem
# =============================================================================

_tem_etiqueta_ou_acordo_fechado = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._tem_etiqueta_ou_acordo_fechado)


_processo_na_fase_acordo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._processo_na_fase_acordo)


_base_execucao_acordos = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._base_execucao_acordos)


_filtrar_em_execucao_acordos = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_em_execucao_acordos)


group_alvaras_expedidos_acordos_por_dia_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_alvaras_expedidos_acordos_por_dia)


_SUBFASE_ALVARA_EXPEDIDO_ACORDO = _familia._SUBFASE_ALVARA_EXPEDIDO_ACORDO


list_processos_alvara_expedido_acordos_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.list_processos_alvara_expedido_acordos)


_get_valor_alcada_final = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_valor_alcada_final)


_tem_etiqueta_acordo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._tem_etiqueta_acordo)


_filtrar_entrada_execucao_acordos_no_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_entrada_execucao_acordos_no_periodo)


_filtrar_saida_execucao_acordos_no_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_saida_execucao_acordos_no_periodo)


_normalizar_materia = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._normalizar_materia)


_normalizar_subfase = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._normalizar_subfase)


_normalizar_subfase_lista = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._normalizar_subfase_lista)


filter_execucao_acordos_por_materia = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filter_execucao_acordos_por_materia)


filter_execucao_acordos_por_subfase = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filter_execucao_acordos_por_subfase)


filter_execucao_acordos_por_uf = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filter_execucao_acordos_por_uf)


_normalizar_comarca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._normalizar_comarca)


filter_execucao_acordos_por_comarca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filter_execucao_acordos_por_comarca)


get_opcoes_comarca_execucao_acordos = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_comarca_execucao_acordos)


get_opcoes_materia_execucao_acordos = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_materia_execucao_acordos)


get_opcoes_subfase_execucao_acordos = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_subfase_execucao_acordos)


group_execucao_acordos_por_comarca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_acordos_por_comarca)


_uf_por_comarca_acordos = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._uf_por_comarca_acordos)


group_valor_execucao_acordos_por_comarca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_valor_execucao_acordos_por_comarca)


filter_execucao_acordos_por_processo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filter_execucao_acordos_por_processo)


get_opcoes_uf_execucao_acordos = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_uf_execucao_acordos)


# =============================================================================
# 3 - Totais
# =============================================================================

get_total_execucao_acordos = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_execucao_acordos)


get_total_entrada_execucao_acordos_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_entrada_execucao_acordos_periodo)


get_total_saida_execucao_acordos_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_saida_execucao_acordos_periodo)


get_estoque_final_execucao_acordos = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_estoque_final_execucao_acordos)


get_tre = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_tre)


get_tre_execucao_acordos_dax = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_tre_execucao_acordos_dax)


# =============================================================================
# 4 - Valores monetários
# =============================================================================

get_valor_alcada_final_total_execucao_acordos = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_alcada_final_total_execucao_acordos)


get_detalhe_valor_alcada_final_vazio = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_detalhe_valor_alcada_final_vazio)


get_total_valor_alcada_final_vazio = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_valor_alcada_final_vazio)


get_valor_ted_saida_execucao_acordos_NG_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_ted_saida_execucao_acordos_periodo)


get_valor_saida_execucao_acordos_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_saida_execucao_acordos_periodo)


get_valor_entrada_execucao_acordos_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_entrada_execucao_acordos_periodo)


# =============================================================================
# 5 - Agrupamentos
# =============================================================================

group_valor_saida_execucao_acordos_por_mes = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_valor_saida_execucao_acordos_por_mes)


group_quantidade_saida_execucao_acordos_por_mes = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_quantidade_saida_execucao_acordos_por_mes)


group_quantidade_entrada_execucao_acordos_por_mes = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_quantidade_entrada_execucao_acordos_por_mes)


group_valor_entrada_execucao_acordos_por_mes = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_valor_entrada_execucao_acordos_por_mes)


group_execucao_acordos_por_subfase = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_acordos_por_subfase)


group_valor_execucao_acordos_por_subfase = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_valor_execucao_acordos_por_subfase)


group_execucao_acordos_por_materia = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_acordos_por_materia)


group_valor_execucao_acordos_por_materia = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_valor_execucao_acordos_por_materia)


SEM_ANO_AJUIZAMENTO = _familia.SEM_ANO_AJUIZAMENTO


group_execucao_acordos_por_ano_ajuizamento = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_acordos_por_ano_ajuizamento)


filter_execucao_acordos_por_ano_ajuizamento = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filter_execucao_acordos_por_ano_ajuizamento)


SEM_CLASSIFICACAO_JUDICIAL = _familia.SEM_CLASSIFICACAO_JUDICIAL


_classificar_judicial_extrajudicial = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._classificar_judicial_extrajudicial)


group_execucao_acordos_por_tipo_acao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_acordos_por_tipo_acao)


filter_execucao_acordos_por_tipo_acao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filter_execucao_acordos_por_tipo_acao)


SEM_CLASSIFICACAO_SENTENCA = _familia.SEM_CLASSIFICACAO_SENTENCA


_classificar_pre_pos_sentenca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._classificar_pre_pos_sentenca)


group_execucao_acordos_por_sentenca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_acordos_por_sentenca)


filter_execucao_acordos_por_sentenca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filter_execucao_acordos_por_sentenca)


# =============================================================================
# 6 - Análise temporal
# =============================================================================

_extrair_duracoes_dias = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._extrair_duracoes_dias)


get_media_tempo_execucao_acordos = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_media_tempo_execucao_acordos)


get_mediana_tempo_execucao_acordos = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_mediana_tempo_execucao_acordos)


get_media_tempo_execucao_acordos_por_mes = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_media_tempo_execucao_acordos_por_mes)


# =============================================================================
# 7 - Fechamento de Acordo (negociação, ainda fora da Execução de Acordos)
# =============================================================================
#
# Processos que ainda estão negociando o acordo, antes de terem DATA_ACORDO_FECHADO
# preenchida (portanto fora da população de Execução de Acordos). Marcamos o início
# da negociação por duas vias, já que a automação de vinculação (PROPOSTA ENVIADA/
# PROPOSTA RECEBIDA → INÍCIO DA NEGOCIAÇÃO) é recente e não cobre retroativamente
# processos que já estavam negociando antes dela existir:
#
# 1. Vinculação cumprida: agendamento do setor ACORDOS para a atividade "PROPOSTA
#    ENVIADA" ou "PROPOSTA RECEBIDA" (qualquer variante, ex. "(1G)") com status
#    "Encerrado Cumprido" — DATA_HORA_CONCLUSAO é a data de início da negociação.
# 2. Subfase atual do processo já em uma das subfases de fechamento de acordo.

_SUBFASES_FECHAMENTO_ACORDO = _familia._SUBFASES_FECHAMENTO_ACORDO

_STATUS_CUMPRIDO_PROPOSTA_ACORDO = _familia._STATUS_CUMPRIDO_PROPOSTA_ACORDO


_tem_subfase_fechamento_acordo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._tem_subfase_fechamento_acordo)


_get_numero_processo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_numero_processo)


get_total_processos_fechamento_acordo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_processos_fechamento_acordo)


_processos_fechamento_acordo_por_subfase = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._processos_fechamento_acordo_por_subfase)


group_fechamento_acordo_por_subfase = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_fechamento_acordo_por_subfase)


group_valor_fechamento_acordo_por_subfase = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_valor_fechamento_acordo_por_subfase)


# =============================================================================
# 6 - Lista de execuções de acordo (tabela)
# =============================================================================

_montar_linhas_execucao_acordos_lista = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._montar_linhas_execucao_acordos_lista)


list_execucao_acordos_lista_entrada = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.list_execucao_acordos_lista_entrada)


list_execucao_acordos_lista_saida = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.list_execucao_acordos_lista_saida)


list_execucao_acordos_lista_total = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.list_execucao_acordos_lista_total)


# =============================================================================
# 7 - Atividades (agendamentos) da Execução de Acordos NG
# =============================================================================
#
# Mirror mecânico da seção Atividades de app/analyses/NG/execucao.py, restrita
# ao setor 'ACORDOS - %' de vw_dashboard_agendamentos_detalhados (em vez de
# 'EXECUÇÃO - %'). A lógica de agendamento (status/prazo/situação/filtros) é
# genérica — não depende do domínio Execução vs Acordo — só o nome das
# funções/chaves de stats muda (sufixo "_acordos" antes do "_NG" final) para
# não colidir com os nomes já usados por execucao.py quando ambos os módulos
# são importados no mesmo dashboard_routes.py.
#
# NÃO inclui group_valor_recuperado_por_funcionario_NG (valor recuperado por
# funcionário): métrica em espera no frontend original (comentada, "não
# adicionar ainda") e sem campo equivalente óbvio de "valor recuperado" no
# domínio de Acordo — omitida por ora, igual ao módulo original.

_STATUS_INATIVO_EXEC = _familia._STATUS_INATIVO_EXEC

_STATUS_EM_ANDAMENTO_EXEC = _familia._STATUS_EM_ANDAMENTO_EXEC

_STATUS_ENCERRADO_EXEC = _familia._STATUS_ENCERRADO_EXEC

_STATUS_FILTRO_EXEC = _familia._STATUS_FILTRO_EXEC

_SITUACOES_FILTRO_EXEC_NG = _familia._SITUACOES_FILTRO_EXEC

SITUACOES_VALIDAS_EXECUCAO_NG = _familia.SITUACOES_VALIDAS_EXECUCAO

# `filtros.situacoes` chega com os ids de `_SITUACOES_FILTRO_EXEC_NG` (plural:
# "vencidas"/"vencem_hoje"/"concluidas"), mas `_classificar_situacao_exec_ng`
# devolve chaves no singular ("vencida"/"vence_hoje"/"concluida") — mesmo
# formato de `RecursalAtividadeTarefaRow`, que não pode mudar. Tradução
# necessária para o filtro de situação (usado por `_agendamento_match_filtros_exec_ng`)
# realmente casar com os flags.
_SITUACAO_ID_PARA_FLAG_NG = _familia._SITUACAO_ID_PARA_FLAG

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


get_kpis_atividades_execucao_acordos_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_kpis_atividades_execucao_acordos)


get_media_mensal_atividades_execucao_acordos_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_media_mensal_atividades_execucao_acordos)


group_execucao_processos_por_atividade_acordos_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_processos_por_atividade_acordos)


group_atividades_ativas_criadas_por_atividade_acordos_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_atividades_ativas_criadas_por_atividade_acordos)


group_atividades_ativas_por_prazo_por_atividade_acordos_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_atividades_ativas_por_prazo_por_atividade_acordos)


group_execucao_demandas_por_funcionario_acordos_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_demandas_por_funcionario_acordos)


_SEM_FUNCIONARIO_ENCERRAMENTO_EXEC_NG = _familia._SEM_FUNCIONARIO_ENCERRAMENTO_EXEC


group_execucao_demandas_por_funcionario_completo_acordos_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_demandas_por_funcionario_completo_acordos)


group_execucao_resolvidos_por_dia_acordos_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_resolvidos_por_dia_acordos)


get_media_execucao_resolvidos_por_funcionario_acordos_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_media_execucao_resolvidos_por_funcionario_acordos)


list_execucao_atividades_periodo_acordos_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.list_execucao_atividades_periodo_acordos)


get_opcoes_filtros_execucao_acordos_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_filtros_execucao_acordos)


_agendamento_match_filtros_exec_ng = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._agendamento_match_filtros_exec)


filtrar_agendamentos_execucao_acordos_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_agendamentos_execucao_acordos)


# ---------------------------------------------------------------------------
# Análise por Prazo — NG (mesmas 5 métricas, mas usando PRAZO como eixo
# temporal em vez de DATA_HORA_CRIACAO/DATA_HORA_CONCLUSAO). Mesmo padrão de
# analyses/LA/pendencias_intermediarias_LA.py.
# ---------------------------------------------------------------------------

_incluir_na_lista_por_prazo_exec_ng = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._incluir_na_lista_por_prazo_exec)


_classificar_situacao_por_prazo_exec_ng = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._classificar_situacao_por_prazo_exec)


get_kpis_execucao_por_prazo_acordos_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_kpis_execucao_por_prazo_acordos)


group_execucao_processos_por_atividade_por_prazo_acordos_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_processos_por_atividade_por_prazo_acordos)


group_execucao_demandas_por_funcionario_por_prazo_acordos_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_demandas_por_funcionario_por_prazo_acordos)


group_execucao_demandas_por_funcionario_por_prazo_completo_acordos_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_demandas_por_funcionario_por_prazo_completo_acordos)


list_execucao_atividades_por_prazo_periodo_acordos_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.list_execucao_atividades_por_prazo_periodo_acordos)


get_opcoes_filtros_execucao_por_prazo_acordos_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_filtros_execucao_por_prazo_acordos)


group_execucao_resolvidos_por_dia_por_prazo_acordos_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_resolvidos_por_dia_por_prazo_acordos)


get_media_execucao_resolvidos_por_funcionario_por_prazo_acordos_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_media_execucao_resolvidos_por_funcionario_por_prazo_acordos)


# ---------------------------------------------------------------------------
# Motivo de "Encerrado Não Cumprido" — NG
# ---------------------------------------------------------------------------

_get_ag_motivo_encaminhamento_itens_ng = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_motivo_encaminhamento_itens)


group_execucao_nao_cumprido_por_motivo_acordos_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_nao_cumprido_por_motivo_acordos)


# ---------------------------------------------------------------------------
# Detalhamento de atrasos (vencidas por dias de atraso) — NG
# ---------------------------------------------------------------------------

_ATRASO_MAX_BUCKET_NG = _familia._ATRASO_MAX_BUCKET

_BUCKET_META_NG = _familia._BUCKET_META


get_atrasos_detalhamento_execucao_acordos_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_atrasos_detalhamento_execucao_acordos)


# =============================================================================
# 8 - Diligências (subconjunto de agendamentos do setor ACORDOS)
# =============================================================================
#
# Diligência é um tipo de agendamento dentro do setor ACORDOS (ex.: "DILIGÊNCIA
# PARA HOMOLOGAÇÃO + REMESSA 2", "DILIGÊNCIA PARA EXPEDIÇÃO DE ALVARÁ DE ACORDO
# JUDICIAL 1"), identificado pelo nome da atividade conter "DILIG". Um mesmo
# processo pode ter a diligência agendada mais de uma vez ao longo do tempo.

_eh_diligencia_acordos_ng = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._eh_diligencia_acordos)


filtrar_agendamentos_diligencia_acordos_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_agendamentos_diligencia_acordos)


get_total_diligencias_execucao_acordos_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_diligencias_execucao_acordos)


group_execucao_acordos_diligencias_por_processo_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_acordos_diligencias_por_processo)


_eh_diligencia_expedicao_alvara_acordos_ng = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._eh_diligencia_expedicao_alvara_acordos)


filtrar_agendamentos_diligencia_expedicao_alvara_acordos_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_agendamentos_diligencia_expedicao_alvara_acordos)


get_kpis_diligencias_expedicao_alvara_acordos_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_kpis_diligencias_expedicao_alvara_acordos)


_diligencias_expedicao_alvara_cumpridas_acordos_ng = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._diligencias_expedicao_alvara_cumpridas_acordos)


list_processos_diligencia_expedicao_alvara_cumprida_acordos_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.list_processos_diligencia_expedicao_alvara_cumprida_acordos)


_TIPOS_VALIDOS_DILIGENCIA_ACORDOS_NG = _familia._TIPOS_VALIDOS_DILIGENCIA_ACORDOS


filtrar_agendamentos_diligencia_por_tipo_acordos_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_agendamentos_diligencia_por_tipo_acordos)


filtrar_agendamentos_diligencia_por_colaborador_acordos_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_agendamentos_diligencia_por_colaborador_acordos)


group_estoque_execucao_acordos_por_mes = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_estoque_execucao_acordos_por_mes)
