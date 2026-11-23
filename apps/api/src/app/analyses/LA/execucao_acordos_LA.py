# Funções de análises do setor de Execução de Acordos (LA)
#
# Mirror de app/analyses/LA/execucao.py: estoque/fluxo/valor + seção Atividades
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
# - População: dentro do universo LA (ID_ESCRITORIO=21), processos na fase de
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
ID_ESCRITORIO = 21

_COL_ID_ESCRITORIO = _familia._COL_ID_ESCRITORIO

_MONTH_NAMES = _familia._MONTH_NAMES


# =============================================================================
# 1 - Helpers internos
# =============================================================================

_to_date = _familia._to_date


_get_data_acordo_fechado = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_data_acordo_fechado)


_get_data_pagamento_acordo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_data_pagamento_acordo)


_get_data_distribuicao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_data_distribuicao)


_get_data_execucao_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_data_execucao)


_data_no_periodo = _familia._data_no_periodo


_converter_valor = _familia._converter_valor


_to_int = _familia._to_int


# =============================================================================
# 2 - Base e filtragem
# =============================================================================

_tem_etiqueta_ou_acordo_fechado = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._tem_etiqueta_ou_acordo_fechado)


_processo_na_fase_acordo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._processo_na_fase_acordo)


_base_execucao_acordos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._base_execucao_acordos)


_filtrar_em_execucao_acordos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_em_execucao_acordos)


group_alvaras_expedidos_acordos_por_dia_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_alvaras_expedidos_acordos_por_dia)


_SUBFASE_ALVARA_EXPEDIDO_ACORDO = _familia._SUBFASE_ALVARA_EXPEDIDO_ACORDO


list_processos_alvara_expedido_acordos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.list_processos_alvara_expedido_acordos)


_get_valor_alcada_final = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_valor_alcada_final)


_tem_etiqueta_acordo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._tem_etiqueta_acordo)


_filtrar_entrada_execucao_acordos_LA_no_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_entrada_execucao_acordos_no_periodo)


_filtrar_saida_execucao_acordos_LA_no_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_saida_execucao_acordos_no_periodo)


_normalizar_materia = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._normalizar_materia)


_normalizar_subfase = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._normalizar_subfase)


filter_execucao_acordos_LA_por_materia = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filter_execucao_acordos_por_materia)


def filter_execucao_acordos_LA_por_subfase(
    execucao: list[dict[str, Any]],
    subfase: Optional[Any] = None,
) -> list[dict[str, Any]]:
    # Aceita um valor único ou uma lista (seleção múltipla no filtro da página).
    valores = subfase if isinstance(subfase, (list, tuple, set)) else [subfase]
    alvos = {_normalizar_subfase(v) for v in valores if v is not None and str(v).strip()}
    if not alvos:
        return _base_execucao_acordos_LA(execucao)
    return [
        p for p in _base_execucao_acordos_LA(execucao)
        if _normalizar_subfase(p.get("SUBFASE")) in alvos
    ]


filter_execucao_acordos_LA_por_uf = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filter_execucao_acordos_por_uf)


_normalizar_comarca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._normalizar_comarca)


filter_execucao_acordos_LA_por_comarca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filter_execucao_acordos_por_comarca)


get_opcoes_comarca_execucao_acordos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_comarca_execucao_acordos)


get_opcoes_materia_execucao_acordos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_materia_execucao_acordos)


get_opcoes_subfase_execucao_acordos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_subfase_execucao_acordos)


def group_execucao_acordos_LA_por_comarca(
    execucao: list[dict[str, Any]],
    *,
    criterio: str = "total",
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Agrupa processos em Execução de Acordos por COMARCA, conforme ``criterio``:

    - "total": estoque atual (fase ACORDO), sem filtro de período —
      :func:`_filtrar_em_execucao_acordos_LA`.
    - "entrada": processos com etiqueta "Acordo" e DATA_EXECUCAO no período —
      :func:`_filtrar_entrada_execucao_acordos_LA_no_periodo`.
    - "saida": processos com DATA_PAGAMENTO_ACORDO no período —
      :func:`_filtrar_saida_execucao_acordos_LA_no_periodo`.

    Cada item traz, além da quantidade (``value``): a soma do VALOR_ALCADA_FINAL
    (``valor_execucao``) e o tempo médio em dias entre DATA_EXECUCAO e
    DATA_PAGAMENTO_ACORDO (``tempo_medio_dias``, ``None`` quando nenhum processo
    da comarca tem as duas datas preenchidas).

    ``tempo_medio_dias`` é fixo por comarca e **não muda com o ``criterio``** — é
    calculado sobre o universo histórico completo da comarca
    (:func:`_base_execucao_acordos_LA`, todo acordo com as duas datas preenchidas,
    independente da fase atual ou do período), para servir de referência estável
    de "quanto tempo um acordo dessa comarca costuma levar para ser pago". Só
    ``value``/``valor_execucao`` respeitam o ``criterio`` selecionado.

    Retorna lista ordenada de forma decrescente por quantidade.
    """
    if criterio == "entrada":
        base = _filtrar_entrada_execucao_acordos_LA_no_periodo(execucao, from_date, to_date)
    elif criterio == "saida":
        base = _filtrar_saida_execucao_acordos_LA_no_periodo(execucao, from_date, to_date)
    else:
        base = _filtrar_em_execucao_acordos_LA(execucao)

    por_comarca = tempo.duracoes_por_grupo(
        _base_execucao_acordos_LA(execucao), _get_data_execucao_LA, _get_data_pagamento_acordo, lambda p, _saida: _normalizar_comarca(p.get("COMARCA"))
    )
    tempo_medio_por_comarca = {name: tempo.media(dias) for name, dias in por_comarca.items()}

    grupos: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for p in base:
        grupos[_normalizar_comarca(p.get("COMARCA"))].append(p)

    itens: list[dict[str, Any]] = []
    for name, rows in grupos.items():
        valor_total = 0.0
        for p in rows:
            valor = _get_valor_alcada_final(p)
            if valor is not None:
                valor_total += _converter_valor(valor)
        itens.append({
            "name": name,
            "value": len(rows),
            "valor_execucao": round(valor_total, 2),
            "tempo_medio_dias": tempo_medio_por_comarca.get(name),
        })

    return sorted(itens, key=lambda x: x["value"], reverse=True)


def group_valor_execucao_acordos_LA_por_comarca(
    execucao: list[dict[str, Any]],
    *,
    criterio: str = "total",
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Agrupa o valor dos acordos em Execução por COMARCA, conforme ``criterio``
    (mesmo recorte de :func:`group_execucao_acordos_LA_por_comarca`, mas somando
    VALOR_ALCADA_FINAL em vez de contar).

    Retorna lista de ``{"name": comarca, "value": valor}``, ordenada de forma
    decrescente por valor.
    """
    if criterio == "entrada":
        base = _filtrar_entrada_execucao_acordos_LA_no_periodo(execucao, from_date, to_date)
    elif criterio == "saida":
        base = _filtrar_saida_execucao_acordos_LA_no_periodo(execucao, from_date, to_date)
    else:
        base = _filtrar_em_execucao_acordos_LA(execucao)

    totais: defaultdict[str, float] = defaultdict(float)
    for p in base:
        valor = _get_valor_alcada_final(p)
        if valor is not None:
            totais[_normalizar_comarca(p.get("COMARCA"))] += _converter_valor(valor)

    return sorted(
        [{"name": name, "value": float(value)} for name, value in totais.items()],
        key=lambda x: x["value"],
        reverse=True,
    )


filter_execucao_acordos_LA_por_processo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filter_execucao_acordos_por_processo)


get_opcoes_uf_execucao_acordos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_uf_execucao_acordos)


# =============================================================================
# 3 - Totais
# =============================================================================

get_total_execucao_acordos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_execucao_acordos)


get_total_entrada_execucao_acordos_LA_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_entrada_execucao_acordos_periodo)


get_total_saida_execucao_acordos_LA_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_saida_execucao_acordos_periodo)


get_estoque_final_execucao_acordos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_estoque_final_execucao_acordos)


get_tre = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_tre)


get_tre_execucao_acordos_LA_dax = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_tre_execucao_acordos_dax)


# =============================================================================
# 4 - Valores monetários
# =============================================================================

get_valor_alcada_final_total_execucao_acordos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_alcada_final_total_execucao_acordos)


get_detalhe_valor_alcada_final_vazio_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_detalhe_valor_alcada_final_vazio)


get_total_valor_alcada_final_vazio_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_valor_alcada_final_vazio)


get_valor_ted_saida_execucao_acordos_LA_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_ted_saida_execucao_acordos_periodo)


get_valor_saida_execucao_acordos_LA_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_saida_execucao_acordos_periodo)


get_valor_entrada_execucao_acordos_LA_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_entrada_execucao_acordos_periodo)


# =============================================================================
# 5 - Agrupamentos
# =============================================================================

group_valor_saida_execucao_acordos_LA_por_mes = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_valor_saida_execucao_acordos_por_mes)


group_quantidade_saida_execucao_acordos_LA_por_mes = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_quantidade_saida_execucao_acordos_por_mes)


group_quantidade_entrada_execucao_acordos_LA_por_mes = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_quantidade_entrada_execucao_acordos_por_mes)


group_valor_entrada_execucao_acordos_LA_por_mes = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_valor_entrada_execucao_acordos_por_mes)


group_execucao_acordos_LA_por_subfase = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_acordos_por_subfase)


group_valor_execucao_acordos_LA_por_subfase = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_valor_execucao_acordos_por_subfase)


group_execucao_acordos_LA_por_materia = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_acordos_por_materia)


group_valor_execucao_acordos_LA_por_materia = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_valor_execucao_acordos_por_materia)


SEM_ANO_AJUIZAMENTO = _familia.SEM_ANO_AJUIZAMENTO


group_execucao_acordos_LA_por_ano_ajuizamento = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_acordos_por_ano_ajuizamento)


filter_execucao_acordos_LA_por_ano_ajuizamento = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filter_execucao_acordos_por_ano_ajuizamento)


SEM_CLASSIFICACAO_JUDICIAL = _familia.SEM_CLASSIFICACAO_JUDICIAL


_classificar_judicial_extrajudicial = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._classificar_judicial_extrajudicial)


group_execucao_acordos_LA_por_tipo_acao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_acordos_por_tipo_acao)


filter_execucao_acordos_LA_por_tipo_acao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filter_execucao_acordos_por_tipo_acao)


SEM_CLASSIFICACAO_SENTENCA = _familia.SEM_CLASSIFICACAO_SENTENCA


_classificar_pre_pos_sentenca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._classificar_pre_pos_sentenca)


group_execucao_acordos_LA_por_sentenca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_acordos_por_sentenca)


filter_execucao_acordos_LA_por_sentenca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filter_execucao_acordos_por_sentenca)


# =============================================================================
# 6 - Análise temporal
# =============================================================================

_extrair_duracoes_dias = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._extrair_duracoes_dias)


get_media_tempo_execucao_acordos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_media_tempo_execucao_acordos)


get_mediana_tempo_execucao_acordos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_mediana_tempo_execucao_acordos)


get_media_tempo_execucao_acordos_LA_por_mes = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_media_tempo_execucao_acordos_por_mes)


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


get_total_processos_fechamento_acordo_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_processos_fechamento_acordo)


_processos_fechamento_acordo_por_subfase = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._processos_fechamento_acordo_por_subfase)


group_fechamento_acordo_por_subfase_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_fechamento_acordo_por_subfase)


group_valor_fechamento_acordo_por_subfase_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_valor_fechamento_acordo_por_subfase)


# =============================================================================
# 6 - Lista de execuções de acordo (tabela)
# =============================================================================

_montar_linhas_execucao_acordos_LA_lista = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._montar_linhas_execucao_acordos_lista)


list_execucao_acordos_LA_lista_entrada = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.list_execucao_acordos_lista_entrada)


list_execucao_acordos_LA_lista_saida = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.list_execucao_acordos_lista_saida)


list_execucao_acordos_LA_lista_total = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.list_execucao_acordos_lista_total)


# =============================================================================
# 7 - Atividades (agendamentos) da Execução de Acordos LA
# =============================================================================
#
# Mirror mecânico da seção Atividades de app/analyses/LA/execucao.py, restrita
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

_SITUACOES_FILTRO_EXEC_LA = _familia._SITUACOES_FILTRO_EXEC

SITUACOES_VALIDAS_EXECUCAO_LA = _familia.SITUACOES_VALIDAS_EXECUCAO

# `filtros.situacoes` chega com os ids de `_SITUACOES_FILTRO_EXEC_LA` (plural:
# "vencidas"/"vencem_hoje"/"concluidas"), mas `_classificar_situacao_exec_la`
# devolve chaves no singular ("vencida"/"vence_hoje"/"concluida") — mesmo
# formato de `RecursalAtividadeTarefaRow`, que não pode mudar. Tradução
# necessária para o filtro de situação (usado por `_agendamento_match_filtros_exec_la`)
# realmente casar com os flags.
_SITUACAO_ID_PARA_FLAG_LA = _familia._SITUACAO_ID_PARA_FLAG

_STATUS_DEMANDAS_FUNCIONARIO_EXEC_LA = _familia._STATUS_DEMANDAS_FUNCIONARIO_EXEC

_SLUG_POR_STATUS_EXEC_LA = _familia._SLUG_POR_STATUS_EXEC

_SEM_ATIVIDADE_EXEC = _familia._SEM_ATIVIDADE_EXEC

_SEM_FUNCIONARIO_EXEC = _familia._SEM_FUNCIONARIO_EXEC

_STATUS_CUMPRIDO_EXEC = _familia._STATUS_CUMPRIDO_EXEC

_COL_FUNCIONARIO_ATRIBUIDO_EXEC = _familia._COL_FUNCIONARIO_ATRIBUIDO_EXEC

_COL_FUNCIONARIO_ENCERRAMENTO_EXEC = _familia._COL_FUNCIONARIO_ENCERRAMENTO_EXEC

_COL_ID_USUARIO_ENCERRAMENTO_EXEC = _familia._COL_ID_USUARIO_ENCERRAMENTO_EXEC

# Reutiliza helpers de data já definidos no módulo
_ag_to_date = _familia._ag_to_date

_ag_data_no_periodo = _familia._ag_data_no_periodo


_nome_em_conjunto_exec_la = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._nome_em_conjunto_exec)


_get_ag_status_la = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_status)


_get_ag_data_criacao_la = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_data_criacao)


_get_ag_data_conclusao_la = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_data_conclusao)


_get_ag_prazo_la = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_prazo)


_get_ag_processo_id_la = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_processo_id)


_get_ag_atividade_nome_la = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_atividade_nome)


_get_ag_funcionario_atribuido_la = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_funcionario_atribuido)


_get_ag_funcionario_encerramento_la = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_funcionario_encerramento)


# V2: como estas atividades são lidas e quais status contam (app/analyses/common/atividades.py).
_ATIVIDADES = atividades.Leitor(
    criacao=_get_ag_data_criacao_la,
    conclusao=_get_ag_data_conclusao_la,
    prazo=_get_ag_prazo_la,
    status=_get_ag_status_la,
    funcionario_encerramento=_get_ag_funcionario_encerramento_la,
)
_STATUS_ATIVIDADES = _familia._STATUS_ATIVIDADES


_get_ag_funcionario_nome_la = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_funcionario_nome)


_incluir_na_lista_exec_la = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._incluir_na_lista_exec)


_classificar_situacao_exec_la = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._classificar_situacao_exec)


_filtrar_ag_encerrados_no_periodo_la = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_ag_encerrados_no_periodo)


def get_kpis_atividades_execucao_acordos_LA(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, int]:
    """KPIs de agendamentos do setor Execução LA no período."""
    ref = ref_date or date.today()
    total = em_andamento = vencidas = vencem_hoje = concluidas = 0

    for row in agendamentos:
        criacao = _get_ag_data_criacao_la(row)
        conclusao = _get_ag_data_conclusao_la(row)
        status = _get_ag_status_la(row) or ""
        prazo = _get_ag_prazo_la(row)
        ativo = status not in _STATUS_INATIVO_EXEC

        if _ag_data_no_periodo(criacao, from_date, to_date) and ativo:
            total += 1
            if status in _STATUS_EM_ANDAMENTO_EXEC:
                em_andamento += 1

        if ativo and prazo is not None:
            if prazo < ref:
                vencidas += 1
            elif prazo == ref:
                vencem_hoje += 1

        if status in _STATUS_ENCERRADO_EXEC:
            if _ag_data_no_periodo(conclusao, from_date, to_date):
                concluidas += 1

    return {
        "total_atividades_execucao_acordos_LA": total,
        "atividades_execucao_em_andamento_acordos_LA": em_andamento,
        "atividades_execucao_vencidas_acordos_LA": vencidas,
        "atividades_execucao_vencem_hoje_acordos_LA": vencem_hoje,
        "atividades_execucao_concluidas_acordos_LA": concluidas,
    }


get_media_mensal_atividades_execucao_acordos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_media_mensal_atividades_execucao_acordos)


group_execucao_processos_por_atividade_acordos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_processos_por_atividade_acordos)


group_atividades_ativas_criadas_por_atividade_acordos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_atividades_ativas_criadas_por_atividade_acordos)


group_atividades_ativas_por_prazo_por_atividade_acordos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_atividades_ativas_por_prazo_por_atividade_acordos)


group_execucao_demandas_por_funcionario_acordos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_demandas_por_funcionario_acordos)


_SEM_FUNCIONARIO_ENCERRAMENTO_EXEC_LA = _familia._SEM_FUNCIONARIO_ENCERRAMENTO_EXEC


group_execucao_demandas_por_funcionario_completo_acordos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_demandas_por_funcionario_completo_acordos)


group_execucao_resolvidos_por_dia_acordos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_resolvidos_por_dia_acordos)


get_media_execucao_resolvidos_por_funcionario_acordos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_media_execucao_resolvidos_por_funcionario_acordos)


list_execucao_atividades_periodo_acordos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.list_execucao_atividades_periodo_acordos)


get_opcoes_filtros_execucao_acordos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_filtros_execucao_acordos)


_agendamento_match_filtros_exec_la = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._agendamento_match_filtros_exec)


filtrar_agendamentos_execucao_acordos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_agendamentos_execucao_acordos)


# ---------------------------------------------------------------------------
# Análise por Prazo — LA (mesmas 5 métricas, mas usando PRAZO como eixo
# temporal em vez de DATA_HORA_CRIACAO/DATA_HORA_CONCLUSAO). Mesmo padrão de
# analyses/LA/pendencias_intermediarias_LA.py.
# ---------------------------------------------------------------------------

_incluir_na_lista_por_prazo_exec_la = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._incluir_na_lista_por_prazo_exec)


_classificar_situacao_por_prazo_exec_la = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._classificar_situacao_por_prazo_exec)


def get_kpis_execucao_por_prazo_acordos_LA(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, int]:
    """
    KPIs de agendamentos do setor Execução LA usando PRAZO como eixo temporal.

    - Total: ativas com prazo no período (exclui Cancelado, Concluído, Encerrado*)
    - Em andamento: status Iniciado, Reaberto ou Encaminhado com prazo no período
    - Vencidas: ativas com prazo no período anterior a hoje
    - Vencem hoje: ativas com prazo = hoje no período
    - Concluídas: encerradas com prazo no período (contagem separada do Total)
    """
    ref = ref_date or date.today()
    total = em_andamento = vencidas = vencem_hoje = concluidas = 0

    for row in agendamentos:
        prazo = _get_ag_prazo_la(row)
        status = _get_ag_status_la(row) or ""
        ativo = status not in _STATUS_INATIVO_EXEC
        prazo_no_periodo = _ag_data_no_periodo(prazo, from_date, to_date)

        if not prazo_no_periodo:
            continue

        if ativo:
            total += 1
            if status in _STATUS_EM_ANDAMENTO_EXEC:
                em_andamento += 1
            if prazo is not None and prazo < ref:
                vencidas += 1
            if prazo is not None and prazo == ref:
                vencem_hoje += 1
        elif status in _STATUS_ENCERRADO_EXEC:
            concluidas += 1

    return {
        "total_por_prazo_execucao_acordos_LA": total,
        "por_prazo_em_andamento_execucao_acordos_LA": em_andamento,
        "por_prazo_vencidas_execucao_acordos_LA": vencidas,
        "por_prazo_vencem_hoje_execucao_acordos_LA": vencem_hoje,
        "por_prazo_concluidas_execucao_acordos_LA": concluidas,
    }


group_execucao_processos_por_atividade_por_prazo_acordos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_processos_por_atividade_por_prazo_acordos)


group_execucao_demandas_por_funcionario_por_prazo_acordos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_demandas_por_funcionario_por_prazo_acordos)


group_execucao_demandas_por_funcionario_por_prazo_completo_acordos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_demandas_por_funcionario_por_prazo_completo_acordos)


list_execucao_atividades_por_prazo_periodo_acordos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.list_execucao_atividades_por_prazo_periodo_acordos)


get_opcoes_filtros_execucao_por_prazo_acordos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_filtros_execucao_por_prazo_acordos)


group_execucao_resolvidos_por_dia_por_prazo_acordos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_resolvidos_por_dia_por_prazo_acordos)


get_media_execucao_resolvidos_por_funcionario_por_prazo_acordos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_media_execucao_resolvidos_por_funcionario_por_prazo_acordos)


# ---------------------------------------------------------------------------
# Motivo de "Encerrado Não Cumprido" — LA
# ---------------------------------------------------------------------------

_get_ag_motivo_encaminhamento_itens_la = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_motivo_encaminhamento_itens)


group_execucao_nao_cumprido_por_motivo_acordos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_nao_cumprido_por_motivo_acordos)


# ---------------------------------------------------------------------------
# Detalhamento de atrasos (vencidas por dias de atraso) — LA
# ---------------------------------------------------------------------------

_ATRASO_MAX_BUCKET_LA = _familia._ATRASO_MAX_BUCKET

_BUCKET_META_LA = _familia._BUCKET_META


get_atrasos_detalhamento_execucao_acordos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_atrasos_detalhamento_execucao_acordos)


# =============================================================================
# 8 - Diligências (subconjunto de agendamentos do setor ACORDOS)
# =============================================================================
#
# Diligência é um tipo de agendamento dentro do setor ACORDOS (ex.: "DILIGÊNCIA
# PARA HOMOLOGAÇÃO + REMESSA 2", "DILIGÊNCIA PARA EXPEDIÇÃO DE ALVARÁ DE ACORDO
# JUDICIAL 1"), identificado pelo nome da atividade conter "DILIG". Um mesmo
# processo pode ter a diligência agendada mais de uma vez ao longo do tempo.

_eh_diligencia_acordos_la = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._eh_diligencia_acordos)


filtrar_agendamentos_diligencia_acordos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_agendamentos_diligencia_acordos)


get_total_diligencias_execucao_acordos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_diligencias_execucao_acordos)


group_execucao_acordos_diligencias_por_processo_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_acordos_diligencias_por_processo)


_eh_diligencia_expedicao_alvara_acordos_la = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._eh_diligencia_expedicao_alvara_acordos)


filtrar_agendamentos_diligencia_expedicao_alvara_acordos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_agendamentos_diligencia_expedicao_alvara_acordos)


get_kpis_diligencias_expedicao_alvara_acordos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_kpis_diligencias_expedicao_alvara_acordos)


_diligencias_expedicao_alvara_cumpridas_acordos_la = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._diligencias_expedicao_alvara_cumpridas_acordos)


list_processos_diligencia_expedicao_alvara_cumprida_acordos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.list_processos_diligencia_expedicao_alvara_cumprida_acordos)


_TIPOS_VALIDOS_DILIGENCIA_ACORDOS_LA = _familia._TIPOS_VALIDOS_DILIGENCIA_ACORDOS


filtrar_agendamentos_diligencia_por_tipo_acordos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_agendamentos_diligencia_por_tipo_acordos)


filtrar_agendamentos_diligencia_por_colaborador_acordos_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_agendamentos_diligencia_por_colaborador_acordos)


group_estoque_execucao_acordos_por_mes_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_estoque_execucao_acordos_por_mes)
