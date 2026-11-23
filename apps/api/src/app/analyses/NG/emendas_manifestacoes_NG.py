# Atividades no período — Setor Manifestação (Emendas e Manifestações) — Escritório NG

from __future__ import annotations

from app.analyses.common import unidade as _unidade  # V2: valores da unidade (common/unidade.py)
from app.analyses.familias import emendas_manifestacoes as _familia  # V2: código único da família (familias/emendas_manifestacoes.py)
from collections import defaultdict
from contextvars import ContextVar  # V2: _dilacao_extra_ctx
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Callable, Optional

from app.analyses.common import conversao  # V2: conversões dos valores do banco num módulo só
from app.analyses.common import periodo  # V2: período e variação vs período anterior num módulo só
from app.analyses.common import atividades  # V2: regras das atividades num módulo só
from app.utils import parse_date_from_db, resolver_periodo_comparativo

# V2: os valores desta unidade para a família, lidos ao vivo deste módulo (common/unidade.py).
_VALORES_UNIDADE = _unidade.ValoresDoModulo(globals(), {"_ATIVIDADES_DILACAO": "_ATIVIDADES_DILACAO"})

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

SITUACOES_VALIDAS_EMENDAS_MANIFESTACOES_NG = _familia.SITUACOES_VALIDAS_EMENDAS_MANIFESTACOES

_STATUS_DEMANDAS_FUNCIONARIO = _familia._STATUS_DEMANDAS_FUNCIONARIO

_SLUG_POR_STATUS = _familia._SLUG_POR_STATUS

_SEM_ATIVIDADE = _familia._SEM_ATIVIDADE

_SEM_FUNCIONARIO = _familia._SEM_FUNCIONARIO

# Classificação do comissionamento (definida pelo usuário em 2026-10-02): a ÚNICA
# atividade do setor MANIFESTAÇÃO que NÃO comissiona é "ANÁLISE DE MANIFESTAÇÃO" — todas
# as outras comissionam. Por isso a regra é por exclusão (não lista fechada): o catálogo do
# setor cresce com frequência (Manifestação Simples/Específica/Provas, Conexão/Aditamento,
# Alegações Finais, Pedido de Providências...) e atividade nova já entra na comissão.
# "ELABORAR MANIFESTAÇÃO" é o nome antigo de "ANÁLISE DE MANIFESTAÇÃO" (renomeada no
# catálogo em 2026-07), mantido na exclusão por segurança. Não confundir com
# "ELABORAR MANIFESTAÇÃO - PEDIDO DE PROVIDÊNCIAS", que é outra atividade e comissiona.
_ATIVIDADES_NAO_COMISSIONAVEIS = _familia._ATIVIDADES_NAO_COMISSIONAVEIS

# Atividade que conta como "Dilação" para o comissionamento (R$ 0,50)
_ATIVIDADES_DILACAO: frozenset[str] = frozenset({
    "ELABORAR DILAÇÃO",
})


# V2 (19/11/2026): atividades que contam como Dilação além de _ATIVIDADES_DILACAO, ligadas pela casca só no RJ
# (app/dashboards/emendas_manifestacoes.py), que usa este cálculo do NG e também pede dilação como
# "MANIFESTAR DILAÇÃO DE PRAZO". Vazio (o padrão) = o cálculo da v1, sem mudança.
_dilacao_extra_ctx = _familia._dilacao_extra_ctx


_is_atividade_dilacao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._is_atividade_dilacao)


_is_atividade_manifestacao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._is_atividade_manifestacao)


_COL_FUNCIONARIO_ATRIBUIDO = _familia._COL_FUNCIONARIO_ATRIBUIDO

_COL_FUNCIONARIO_ENCERRAMENTO = _familia._COL_FUNCIONARIO_ENCERRAMENTO

_COL_ID_USUARIO_ENCERRAMENTO = _familia._COL_ID_USUARIO_ENCERRAMENTO


# =============================================================================
# Utilitários
# =============================================================================

_to_int = _familia._to_int


_to_date = _familia._to_date


_data_no_periodo = _familia._data_no_periodo


_nome_em_conjunto_filtro = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._nome_em_conjunto_filtro)


# =============================================================================
# Getters de campos dos agendamentos
# =============================================================================

_get_status = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_status)


_get_data_criacao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_data_criacao)


_get_data_conclusao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_data_conclusao)


_get_prazo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_prazo)


_get_processo_id = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_processo_id)


_get_numero_processo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_numero_processo)


_get_uf = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_uf)


_get_atividade_nome = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_atividade_nome)


_get_funcionario_atribuido = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_funcionario_atribuido)


_get_funcionario_encerramento = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_funcionario_encerramento)


# V2: como estas atividades são lidas e quais status contam (app/analyses/common/atividades.py).
_ATIVIDADES = _familia._ATIVIDADES

_STATUS_ATIVIDADES = _familia._STATUS_ATIVIDADES


_get_funcionario_nome = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_funcionario_nome)


# =============================================================================
# Filtros de período
# =============================================================================

_filtrar_criados_no_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_criados_no_periodo)


_filtrar_encerrados_no_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_encerrados_no_periodo)


_incluir_na_lista_tarefas = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._incluir_na_lista_tarefas)


_classificar_situacao_tarefa = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._classificar_situacao_tarefa)


# =============================================================================
# KPIs
# =============================================================================

get_kpis_atividades_emendas_manifestacoes_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_kpis_atividades_emendas_manifestacoes)


# =============================================================================
# Histórico de concluídas (mensal e diário)
# =============================================================================

_MONTH_NAMES = _familia._MONTH_NAMES


group_emendas_manifestacoes_concluidas_por_mes_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_emendas_manifestacoes_concluidas_por_mes)


group_emendas_manifestacoes_concluidas_por_dia_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_emendas_manifestacoes_concluidas_por_dia)


get_emendas_manifestacoes_concluidas_por_dia_por_funcionario_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_emendas_manifestacoes_concluidas_por_dia_por_funcionario)


_media_concluidas_por_funcionario = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._media_concluidas_por_funcionario)


get_media_emendas_manifestacoes_concluidas_por_funcionario_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_media_emendas_manifestacoes_concluidas_por_funcionario)


# =============================================================================
# Gráfico: processos distintos por atividade
# =============================================================================

group_emendas_manifestacoes_processos_por_atividade_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_emendas_manifestacoes_processos_por_atividade)


# =============================================================================
# Gráfico: demandas encerradas por funcionário
# =============================================================================

group_emendas_manifestacoes_demandas_por_funcionario_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_emendas_manifestacoes_demandas_por_funcionario)


# =============================================================================
# Gráfico (por prazo): processos distintos por atividade
# =============================================================================

group_emendas_manifestacoes_processos_por_atividade_por_prazo_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_emendas_manifestacoes_processos_por_atividade_por_prazo)


# =============================================================================
# Gráfico (por prazo): demandas encerradas por funcionário
# =============================================================================

group_emendas_manifestacoes_demandas_por_funcionario_por_prazo_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_emendas_manifestacoes_demandas_por_funcionario_por_prazo)


# =============================================================================
# Lista de tarefas
# =============================================================================

list_emendas_manifestacoes_atividades_periodo_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.list_emendas_manifestacoes_atividades_periodo)


# =============================================================================
# Opções de filtros
# =============================================================================

get_opcoes_filtros_emendas_manifestacoes_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_filtros_emendas_manifestacoes)


# =============================================================================
# Filtros cumulativos
# =============================================================================

EmendasManifestacoesAtividadesFiltrosNG = _familia.EmendasManifestacoesAtividadesFiltros


_agendamento_match_filtros = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._agendamento_match_filtros)


filtrar_agendamentos_emendas_manifestacoes_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_agendamentos_emendas_manifestacoes)


# =============================================================================
# Análise por Prazo — helpers internos
# =============================================================================

_incluir_na_lista_por_prazo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._incluir_na_lista_por_prazo)


_classificar_situacao_por_prazo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._classificar_situacao_por_prazo)


# =============================================================================
# KPIs por Prazo
# =============================================================================

get_kpis_emendas_manifestacoes_por_prazo_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_kpis_emendas_manifestacoes_por_prazo)


# =============================================================================
# Histórico de concluídas por Prazo (mensal e diário)
# =============================================================================

_filtrar_encerrados_com_prazo_no_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_encerrados_com_prazo_no_periodo)


group_emendas_manifestacoes_concluidas_por_prazo_por_mes_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_emendas_manifestacoes_concluidas_por_prazo_por_mes)


group_emendas_manifestacoes_concluidas_por_prazo_por_dia_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_emendas_manifestacoes_concluidas_por_prazo_por_dia)


get_emendas_manifestacoes_concluidas_por_prazo_por_dia_por_funcionario_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_emendas_manifestacoes_concluidas_por_prazo_por_dia_por_funcionario)


get_media_emendas_manifestacoes_concluidas_por_prazo_por_funcionario_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_media_emendas_manifestacoes_concluidas_por_prazo_por_funcionario)


# =============================================================================
# Lista de tarefas por Prazo
# =============================================================================

list_emendas_manifestacoes_por_prazo_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.list_emendas_manifestacoes_por_prazo)


# =============================================================================
# Opções de filtros por Prazo
# =============================================================================

get_opcoes_filtros_emendas_manifestacoes_por_prazo_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_filtros_emendas_manifestacoes_por_prazo)


# =============================================================================
# Filtros cumulativos por Prazo
# =============================================================================

_agendamento_match_filtros_por_prazo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._agendamento_match_filtros_por_prazo)


filtrar_agendamentos_emendas_manifestacoes_por_prazo_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_agendamentos_emendas_manifestacoes_por_prazo)


# =============================================================================
# Comissionamento
# =============================================================================
#
# Regras (definidas pelo usuário em 2026-07 para o escritório NG — diferente da
# LA, que usa faixas 85%/97%): NG não tem faixa de comissionamento. Toda
# Manifestação produzida vale R$ 1,00 e toda Dilação vale R$ 0,50, sem gatilho
# mínimo de agenda cumprida — o valor é fixo e sempre aplicado.
#
# "Agenda do mês" (agenda_percentual) continua calculada e exposta como métrica
# informativa de aderência ao prazo (PRAZO no período; Cancelado/Concluído não
# entram), mas não influencia mais o valor da comissão.
#
# As peças (Manifestação/Dilação) só contam quando o resultado foi "Encerrado
# Cumprido" (Não Cumprido conta para a agenda, mas não é peça remunerada),
# usando o PRAZO no período como eixo temporal (mesma base da agenda) — não a
# DATA_HORA_CONCLUSAO (mesma lógica validada para a LA, ver
# analyses/LA/emendas_manifestacoes_LA.py).

_VALOR_MANIFESTACAO_NG = _familia._VALOR_MANIFESTACAO

_VALOR_DILACAO_NG = _familia._VALOR_DILACAO


_agenda_cumprida_funcionario_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._agenda_cumprida_funcionario)


get_emendas_manifestacoes_comissionamento_por_funcionario_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_emendas_manifestacoes_comissionamento_por_funcionario)


# =============================================================================
# Comparativos (mesmo padrão de analyses/NG/comercial_geral.py)
# =============================================================================

_resolver_periodos_comparativo_emendas_manifestacoes_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._resolver_periodos_comparativo_emendas_manifestacoes)


_qtd_pecas_produzidas_emendas_manifestacoes_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._qtd_pecas_produzidas_emendas_manifestacoes)


_comparativo_variacao_percentual_emendas_manifestacoes_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._comparativo_variacao_percentual_emendas_manifestacoes)


get_comparativo_qtd_manifestacoes_emendas_manifestacoes_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_comparativo_qtd_manifestacoes_emendas_manifestacoes)


get_comparativo_qtd_dilacoes_emendas_manifestacoes_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_comparativo_qtd_dilacoes_emendas_manifestacoes)


# =============================================================================
# UF — opções de filtro
# =============================================================================

get_opcoes_uf_emendas_manifestacoes_NG = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_uf_emendas_manifestacoes)
