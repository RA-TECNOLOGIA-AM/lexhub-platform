# Funções de análises do setor de Execução

from __future__ import annotations

from app.analyses.common import unidade as _unidade  # V2: valores da unidade (common/unidade.py)
from app.analyses.familias import execucao as _familia  # V2: código único da família (familias/execucao.py)
import json
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
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
ID_ESCRITORIO = 21
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


_get_data_distribuicao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_data_distribuicao)


_data_no_periodo = _familia._data_no_periodo


_converter_valor = _familia._converter_valor


_to_int = _familia._to_int


_base_execucao_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._base_execucao)


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


group_alvaras_expedidos_por_dia_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_alvaras_expedidos_por_dia)


_SUBFASES_ALVARA_EXPEDIDO = _familia._SUBFASES_ALVARA_EXPEDIDO


list_processos_alvara_expedido_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.list_processos_alvara_expedido)


_normalizar_subfase = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._normalizar_subfase)


_normalizar_comarca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._normalizar_comarca)


filter_execucao_LA_por_materia = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filter_execucao_por_materia)


filter_execucao_LA_por_subfase = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filter_execucao_por_subfase)


filter_execucao_LA_por_uf = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filter_execucao_por_uf)


get_opcoes_uf_execucao_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_uf_execucao)


filter_execucao_LA_por_comarca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filter_execucao_por_comarca)


get_opcoes_comarca_execucao_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_comarca_execucao)


get_opcoes_materia_execucao_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_materia_execucao)


get_opcoes_subfase_execucao_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_subfase_execucao)


_SEM_ANO_AJUIZAMENTO_EXEC = _familia._SEM_ANO_AJUIZAMENTO_EXEC


filter_execucao_LA_por_ano_ajuizamento = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filter_execucao_por_ano_ajuizamento)


# =============================================================================
# 3 - Totais
# =============================================================================

get_total_execucao_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_execucao)


get_total_entrada_execucao_periodo_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_entrada_execucao_periodo)


get_total_saida_execucao_periodo_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_saida_execucao_periodo)


get_estoque_final_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_estoque_final)


get_tre_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_tre)


get_tre_execucao_dax_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_tre_execucao_dax)


# =============================================================================
# 4 - Valores monetários
# =============================================================================

get_valor_causa_total_execucao_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_causa_total_execucao)


get_detalhe_valor_execucao_vazio_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_detalhe_valor_execucao_vazio)


get_total_valor_execucao_vazio_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_valor_execucao_vazio)

get_valor_honorarios_total_execucao_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_honorarios_total_execucao)

def get_valor_em_execucao_LA(execucao: list[dict[str, Any]]) -> float:
    """
    Soma de VALOR_EXECUCAO de todos os processos em Execução (``execucao`` já
    vem filtrado por DATA_EXECUCAO no período pelo chamador — ver
    :func:`_filtrar_em_execucao`).

    Valor cheio, mesmo quando já houve compensação parcial do alvará do
    incontroverso — ver :func:`get_valor_remanescente_em_execucao_LA` para o
    valor ainda em aberto (linha secundária "Valor Remanescente" do card).
    """
    total = 0.0
    for p in _filtrar_em_execucao(execucao):
        valor = _get_valor_execucao(p)
        if valor is not None:
            total += _converter_valor(valor)
    return total


get_valor_remanescente_em_execucao_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_remanescente_em_execucao)


get_valor_execucao_saida_periodo_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_execucao_saida_periodo)


get_valor_incontroverso_saida_periodo_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_incontroverso_saida_periodo)


get_total_incontroverso_saida_periodo_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_total_incontroverso_saida_periodo)


_somar_campos_ted = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._somar_campos_ted)


get_valor_ted_saida_execucao_periodo_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_valor_ted_saida_execucao_periodo)


get_taxa_recuperacao_execucao_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_taxa_recuperacao_execucao)


# =============================================================================
# 5 - Agrupamentos
# =============================================================================

group_valor_saida_execucao_por_mes_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_valor_saida_execucao_por_mes)


group_valor_execucao_saida_periodo_por_mes_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_valor_execucao_saida_periodo_por_mes)


group_valor_remanescente_por_mes_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_valor_remanescente_por_mes)


group_quantidade_saida_execucao_por_mes_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_quantidade_saida_execucao_por_mes)


group_quantidade_entrada_execucao_por_mes_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_quantidade_entrada_execucao_por_mes)


group_valor_entrada_execucao_por_mes_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_valor_entrada_execucao_por_mes)


group_execucao_por_subfase_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_por_subfase)


def group_execucao_por_comarca_LA(
    execucao: list[dict[str, Any]],
    *,
    criterio: str = "total",
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Agrupa processos em Execução por COMARCA, conforme ``criterio``:

    - "total": estoque atual em Execução (ID_FASE == 12, situação Ativo),
      sem filtro de período — :func:`_filtrar_em_execucao`.
    - "entrada": processos com DATA_EXECUCAO no período — :func:`_filtrar_entrada_execucao_no_periodo`.
    - "saida": processos com DATA_COMPENSACAO_ALVARA no período — :func:`_filtrar_saida_no_periodo`.

    Cada item traz, além da quantidade (``value``): a soma do VALOR_EXECUCAO
    (``valor_execucao``) e o tempo médio em dias entre DATA_EXECUCAO e
    DATA_COMPENSACAO_ALVARA (``tempo_medio_dias``, ``None`` quando nenhum processo
    da comarca tem as duas datas preenchidas) — mesmo par de campos de
    :func:`~app.analyses.NG.execucao.group_execucao_por_comarca`.

    ``tempo_medio_dias`` é fixo por comarca e **não muda com o ``criterio``** — é
    calculado sobre o universo histórico completo da comarca (:func:`_base_execucao_LA`,
    todo processo com as duas datas preenchidas, independente da fase atual ou do
    período), para servir de referência estável de "quanto tempo um processo dessa
    comarca costuma levar para sair da Execução". Só ``value``/``valor_execucao``
    respeitam o ``criterio`` selecionado.

    Retorna lista ordenada de forma decrescente por quantidade.
    """
    if criterio == "entrada":
        base = _filtrar_entrada_execucao_no_periodo(execucao, from_date, to_date)
    elif criterio == "saida":
        base = _filtrar_saida_no_periodo(execucao, from_date, to_date)
    else:
        base = _filtrar_em_execucao(execucao)

    por_comarca = tempo.duracoes_por_grupo(
        _base_execucao_LA(execucao), _get_data_execucao, _get_data_compensacao_alvara, lambda p, _saida: _normalizar_comarca(p.get("COMARCA"))
    )
    tempo_medio_por_comarca = {name: tempo.media(dias) for name, dias in por_comarca.items()}

    grupos: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for p in base:
        grupos[_normalizar_comarca(p.get("COMARCA"))].append(p)

    itens: list[dict[str, Any]] = []
    for name, rows in grupos.items():
        valor_total = 0.0
        for p in rows:
            valor = _get_valor_execucao(p)
            if valor is not None:
                valor_total += _converter_valor(valor)
        itens.append({
            "name": name,
            "value": len(rows),
            "valor_execucao": round(valor_total, 2),
            "tempo_medio_dias": tempo_medio_por_comarca.get(name),
        })

    return sorted(itens, key=lambda x: x["value"], reverse=True)


def group_valor_execucao_por_comarca_LA(
    execucao: list[dict[str, Any]],
    *,
    criterio: str = "total",
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Agrupa o valor dos processos em Execução por COMARCA, conforme ``criterio``
    (mesmo recorte de :func:`group_execucao_por_comarca_LA`, mas somando valor
    em vez de contar):

    - "total": VALOR_EXECUCAO em aberto (:func:`_get_valor_execucao_em_aberto`)
      do estoque atual — mesmo critério de :func:`group_valor_execucao_por_subfase_LA`.
    - "entrada": VALOR_EXECUCAO cheio dos processos com DATA_EXECUCAO no período.
    - "saida": VALOR_EXECUCAO em aberto dos processos com DATA_COMPENSACAO_ALVARA
      no período — não inclui o valor incontroverso compensado separadamente
      (ver :func:`get_valor_incontroverso_saida_periodo_LA`), diferente do
      card "Valor saída Execução".

    Retorna lista de ``{"name": comarca, "value": valor}``, ordenada de forma
    decrescente por valor.
    """
    if criterio == "entrada":
        base = _filtrar_entrada_execucao_no_periodo(execucao, from_date, to_date)
        get_valor = _get_valor_execucao
    elif criterio == "saida":
        base = _filtrar_saida_no_periodo(execucao, from_date, to_date)
        get_valor = _get_valor_execucao_em_aberto
    else:
        base = _filtrar_em_execucao(execucao)
        get_valor = _get_valor_execucao_em_aberto

    totais: defaultdict[str, float] = defaultdict(float)
    for p in base:
        valor = get_valor(p)
        if valor is not None:
            totais[_normalizar_comarca(p.get("COMARCA"))] += _converter_valor(valor)

    return sorted(
        [{"name": name, "value": float(value)} for name, value in totais.items()],
        key=lambda x: x["value"],
        reverse=True,
    )


group_valor_execucao_por_subfase_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_valor_execucao_por_subfase)


def group_execucao_por_materia_LA(execucao: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Agrupa os processos em Execução por matéria."""
    contagem: defaultdict[str, int] = defaultdict(int)

    for p in _filtrar_em_execucao(execucao):
        contagem[_normalizar_materia(p.get("MATERIA"))] += 1

    return sorted(
        [{"name": name, "value": int(qtd)} for name, qtd in contagem.items()],
        key=lambda x: x["value"],
        reverse=True,
    )


def group_valor_execucao_por_materia_LA(execucao: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Agrupa o valor ainda em aberto (:func:`_get_valor_execucao_em_aberto`) dos
    processos em Execução por matéria — bate com o KPI "Valor Total em execução"
    (:func:`get_valor_causa_total_execucao_LA`).

    Mesmo critério de filtragem de :func:`group_execucao_por_materia_LA` — a
    "entrada no período" resulta de o chamador passar a lista já restrita por
    ``DATA_EXECUCAO`` (parâmetro ``execucao`` do builder), assim como ocorre
    hoje para ``execucao_por_materia_LA``.
    """
    totais: defaultdict[str, float] = defaultdict(float)

    for p in _filtrar_em_execucao(execucao):
        valor = _get_valor_execucao_em_aberto(p)
        if valor is not None:
            totais[_normalizar_materia(p.get("MATERIA"))] += _converter_valor(valor)

    return sorted(
        [{"name": name, "value": float(value)} for name, value in totais.items()],
        key=lambda x: x["value"],
        reverse=True,
    )


def group_execucao_por_ano_ajuizamento_LA(execucao: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Agrupa os processos em Execução pelo ano de ajuizamento (DATA_DISTRIBUICAO).

    Cada item traz a quantidade (``value``) e a soma do valor (``valor_causa``,
    :func:`_get_valor_execucao_em_aberto` — bate com "Valor Total em execução")
    dos processos daquele ano. Mesmo critério de filtragem de
    :func:`group_execucao_por_materia_LA` — quando `execucao` já vem restrito
    por ``DATA_EXECUCAO`` no período selecionado, representa o "ano de
    ajuizamento das entradas".
    """
    contagem: defaultdict[str, int] = defaultdict(int)
    valores: defaultdict[str, float] = defaultdict(float)

    for p in _filtrar_em_execucao(execucao):
        data_distribuicao = _get_data_distribuicao(p)
        ano = str(data_distribuicao.year) if data_distribuicao else _SEM_ANO_AJUIZAMENTO_EXEC
        contagem[ano] += 1
        valor = _get_valor_execucao_em_aberto(p)
        if valor is not None:
            valores[ano] += _converter_valor(valor)

    return sorted(
        [
            {"name": name, "value": int(value), "valor_causa": float(valores.get(name, 0.0))}
            for name, value in contagem.items()
        ],
        key=lambda x: x["name"],
    )


# =============================================================================
# 6 - Análise temporal
# =============================================================================

_extrair_duracoes_dias = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._extrair_duracoes_dias)


get_media_tempo_execucao_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_media_tempo_execucao)


get_mediana_tempo_execucao_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_mediana_tempo_execucao)


get_media_tempo_execucao_por_mes_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_media_tempo_execucao_por_mes)


_classificar_faixa_ultima_movimentacao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._classificar_faixa_ultima_movimentacao)


group_execucao_por_faixa_ultima_movimentacao_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_por_faixa_ultima_movimentacao)


# =============================================================================
# 7 - Atividades no período (agendamentos do setor Execução)
# =============================================================================

_STATUS_INATIVO_EXEC = _familia._STATUS_INATIVO_EXEC

_STATUS_EM_ANDAMENTO_EXEC = _familia._STATUS_EM_ANDAMENTO_EXEC

_STATUS_ENCERRADO_EXEC = _familia._STATUS_ENCERRADO_EXEC

_STATUS_FILTRO_EXEC = _familia._STATUS_FILTRO_EXEC

_SITUACOES_FILTRO_EXEC = _familia._SITUACOES_FILTRO_EXEC

SITUACOES_VALIDAS_EXECUCAO = _familia.SITUACOES_VALIDAS_EXECUCAO

_STATUS_DEMANDAS_FUNCIONARIO_EXEC = _familia._STATUS_DEMANDAS_FUNCIONARIO_EXEC

_SLUG_POR_STATUS_EXEC = _familia._SLUG_POR_STATUS_EXEC

_SEM_ATIVIDADE_EXEC = _familia._SEM_ATIVIDADE_EXEC

_SEM_FUNCIONARIO_EXEC = _familia._SEM_FUNCIONARIO_EXEC

_STATUS_CUMPRIDO_EXEC = _familia._STATUS_CUMPRIDO_EXEC

_COL_FUNCIONARIO_ATRIBUIDO_EXEC = _familia._COL_FUNCIONARIO_ATRIBUIDO_EXEC

_COL_FUNCIONARIO_ENCERRAMENTO_EXEC = _familia._COL_FUNCIONARIO_ENCERRAMENTO_EXEC

_COL_ID_USUARIO_ENCERRAMENTO_EXEC = _familia._COL_ID_USUARIO_ENCERRAMENTO_EXEC


_ag_to_date = _familia._ag_to_date


_ag_data_no_periodo = _familia._ag_data_no_periodo


_nome_em_conjunto_exec = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._nome_em_conjunto_exec)


_get_ag_status = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_status)


_get_ag_data_criacao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_data_criacao)


_get_ag_data_conclusao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_data_conclusao)


_get_ag_prazo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_prazo)


_get_ag_processo_id = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_processo_id)


_get_ag_numero_processo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_numero_processo)


_get_ag_valor_sentenca = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_valor_sentenca)


_get_ag_valor_acordao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_valor_acordao)


_get_ag_atividade_nome = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_atividade_nome)


_get_ag_funcionario_atribuido = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_funcionario_atribuido)


_get_ag_funcionario_encerramento = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_funcionario_encerramento)


# V2: como estas atividades são lidas e quais status contam (app/analyses/common/atividades.py).
_ATIVIDADES = atividades.Leitor(
    criacao=_get_ag_data_criacao,
    conclusao=_get_ag_data_conclusao,
    prazo=_get_ag_prazo,
    status=_get_ag_status,
    funcionario_encerramento=_get_ag_funcionario_encerramento,
)
_STATUS_ATIVIDADES = _familia._STATUS_ATIVIDADES


_get_ag_funcionario_nome = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_funcionario_nome)


_incluir_na_lista_exec = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._incluir_na_lista_exec)


_classificar_situacao_exec = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._classificar_situacao_exec)


_filtrar_ag_encerrados_no_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_ag_encerrados_no_periodo)


def get_kpis_atividades_execucao_LA(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, int]:
    """KPIs de agendamentos do setor Execução no período."""
    ref = ref_date or date.today()
    total = em_andamento = vencidas = vencem_hoje = concluidas = 0
    total_criadas = criadas_em_andamento = 0
    abertas = 0

    for row in agendamentos:
        criacao = _get_ag_data_criacao(row)
        conclusao = _get_ag_data_conclusao(row)
        status = _get_ag_status(row) or ""
        prazo = _get_ag_prazo(row)
        ativo = status not in _STATUS_INATIVO_EXEC
        criada_periodo = _ag_data_no_periodo(criacao, from_date, to_date)

        # "Abertas": todas as atividades atualmente em aberto (não concluídas/
        # canceladas), independente de quando foram criadas ou do período
        # selecionado — engloba tanto as "em andamento" quanto as "represadas"
        # (vencidas/vencem hoje), que são um subconjunto dela. Usada no card
        # unificado "Em andamento" da Confecção CS (substitui os antigos
        # cards separados "Em andamento", restrito ao período, e "Represados").
        if ativo:
            abertas += 1

        if criada_periodo and ativo:
            total += 1
            if status in _STATUS_EM_ANDAMENTO_EXEC:
                em_andamento += 1

        # Variante "criadas": conta tudo que chegou no período, mesmo já
        # concluído (Cumprido/Não Cumprido) — só exclui Cancelado (cancelado
        # antes mesmo de começar). Usada no card "Total de atividades" do
        # painel Confecção CS do Execução Estratégico Geral; "em andamento"
        # aqui é o que o card "Total de atividades" media antes dessa
        # distinção existir (criado no período e ainda não concluído).
        if criada_periodo and status != "Cancelado":
            total_criadas += 1
            if status not in _STATUS_ENCERRADO_EXEC:
                criadas_em_andamento += 1

        if ativo and prazo is not None:
            if prazo < ref:
                vencidas += 1
            elif prazo == ref:
                vencem_hoje += 1

        if status in _STATUS_ENCERRADO_EXEC:
            if _ag_data_no_periodo(conclusao, from_date, to_date):
                concluidas += 1

    return {
        "total_atividades_execucao_LA": total,
        "atividades_execucao_em_andamento_LA": em_andamento,
        "atividades_execucao_vencidas_LA": vencidas,
        "atividades_execucao_vencem_hoje_LA": vencem_hoje,
        "atividades_execucao_concluidas_LA": concluidas,
        "total_atividades_criadas_execucao_LA": total_criadas,
        "atividades_criadas_em_andamento_execucao_LA": criadas_em_andamento,
        "atividades_execucao_abertas_LA": abertas,
    }


get_media_mensal_atividades_execucao_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_media_mensal_atividades_execucao)


group_execucao_processos_por_atividade_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_processos_por_atividade)


group_atividades_ativas_criadas_por_atividade_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_atividades_ativas_criadas_por_atividade)


group_atividades_criadas_por_atividade_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_atividades_criadas_por_atividade)


group_atividades_ativas_por_prazo_por_atividade_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_atividades_ativas_por_prazo_por_atividade)


group_execucao_demandas_por_funcionario_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_demandas_por_funcionario)


_SEM_FUNCIONARIO_ENCERRAMENTO_EXEC = _familia._SEM_FUNCIONARIO_ENCERRAMENTO_EXEC


group_execucao_demandas_por_funcionario_completo_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_demandas_por_funcionario_completo)


group_taxa_conclusao_por_funcionario_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_taxa_conclusao_por_funcionario)


_ATIVIDADES_FLUXO_CS_1G_LA = _familia._ATIVIDADES_FLUXO_CS_1G

_ATIVIDADES_FLUXO_CS_2G_LA = _familia._ATIVIDADES_FLUXO_CS_2G
# Atividade antiga sem grau no nome: vai numa linha própria (decisão do negócio, out/2026 —
# inferir o grau pelo acórdão errava ~43% dos 1G no NG).
_ATIVIDADES_FLUXO_CS_SEM_GRAU_LA = frozenset({"Elaborar Cumprimento de Sentença".casefold()})
_FLUXO_CS_SEM_GRAU_LABEL_LA = "CS (sem grau)"
_JANELA_FLUXO_CS_DIAS_LA = _familia._JANELA_FLUXO_CS_DIAS


def _entradas_por_fluxo_cs_LA(
    execucao: list[dict[str, Any]],
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[tuple[dict[str, Any], date, str]]:
    """
    ``(processo, DATA_EXECUCAO, fluxo)`` de cada entrada na Execução Condenação no período
    (sem período = histórico completo), com o fluxo da Confecção CS pela regra de
    :func:`group_entrada_execucao_por_fluxo_cs_por_mes_LA` — ou ``"Outros"`` quando a
    entrada não veio da CS. Base do gráfico de fluxo e da taxa de atualização.
    """
    cs_por_processo: dict[int, list[tuple[date, int, str]]] = defaultdict(list)
    for row in agendamentos:
        status = _get_ag_status(row)
        if status == _STATUS_CUMPRIDO_EXEC:
            prioridade = 0
        elif status == "Cancelado":
            prioridade = 1
        else:
            continue
        nome = _get_ag_atividade_nome(row).casefold()
        if nome in _ATIVIDADES_FLUXO_CS_1G_LA:
            grau = "1G"
        elif nome in _ATIVIDADES_FLUXO_CS_2G_LA:
            grau = "2G"
        elif nome in _ATIVIDADES_FLUXO_CS_SEM_GRAU_LA:
            grau = _FLUXO_CS_SEM_GRAU_LABEL_LA
        else:
            continue
        pid = _to_int(_get_ag_processo_id(row))
        conclusao = _get_ag_data_conclusao(row)
        if pid is None or conclusao is None:
            continue
        cs_por_processo[pid].append((conclusao, prioridade, grau))

    resultado: list[tuple[dict[str, Any], date, str]] = []
    for p in _filtrar_entrada_execucao_no_periodo(execucao, from_date, to_date):
        data_exe = _get_data_execucao(p)
        pid = _to_int(p.get("id") or p.get("ID"))
        if data_exe is None:
            continue
        candidatos = [
            (abs((conclusao - data_exe).days), prioridade, grau)
            for conclusao, prioridade, grau in cs_por_processo.get(pid, ())
            if abs((conclusao - data_exe).days) <= _JANELA_FLUXO_CS_DIAS_LA
        ]
        resultado.append((p, data_exe, min(candidatos)[2] if candidatos else "Outros"))
    return resultado


def get_taxa_atualizacao_execucao_LA(
    execucao: list[dict[str, Any]],
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ano: Optional[int] = None,
) -> dict[str, Any]:
    """
    Taxa de atualização: quanto o valor cresceu da decisão até a Execução, nas entradas da
    Condenação que vieram da Confecção CS (fluxo de :func:`_entradas_por_fluxo_cs_LA`).
    1G compara ``VALOR_SENTENCA`` com ``VALOR_EXECUCAO``; 2G compara ``VALOR_ACORDAO`` com
    ``VALOR_EXECUCAO``. Taxa = (Σ execução − Σ decisão) ÷ Σ decisão × 100, agregada por fluxo.

    - ``linhas``/``total``: entradas no período; sem um dos dois valores, a entrada fica fora
      da conta e vai para ``sem_valor_processos`` (número do processo e o que falta).
    - ``por_mes``: a mesma taxa mês a mês (mês da ``DATA_EXECUCAO``) do ano ``ano``
      (padrão: ano atual), independente do período.
    """
    campos = {"1G": ("VALOR_SENTENCA", "Sentença"), "2G": ("VALOR_ACORDAO", "Acórdão")}

    def _novo() -> dict[str, Any]:
        return {"quantidade": 0, "sem_valor": 0, "valor_decisao": 0.0, "valor_execucao": 0.0}

    def _valores(p: dict[str, Any], fluxo: str) -> tuple[float, float]:
        decisao_raw = p.get(campos[fluxo][0])
        execucao_raw = p.get("VALOR_EXECUCAO")
        decisao = _converter_valor(decisao_raw) if decisao_raw not in (None, "") else 0.0
        valor_execucao = _converter_valor(execucao_raw) if execucao_raw not in (None, "") else 0.0
        return decisao, valor_execucao

    def _linha(fluxo: str, r: dict[str, Any]) -> dict[str, Any]:
        aumento = r["valor_execucao"] - r["valor_decisao"]
        return {
            "fluxo": fluxo,
            "quantidade": r["quantidade"],
            "sem_valor": r["sem_valor"],
            "valor_decisao": round(r["valor_decisao"], 2),
            "valor_execucao": round(r["valor_execucao"], 2),
            "aumento": round(aumento, 2),
            "taxa": round(100.0 * aumento / r["valor_decisao"], 2) if r["valor_decisao"] else None,
        }

    def _taxa(r: dict[str, Any]) -> Optional[float]:
        if not r["valor_decisao"]:
            return None
        return round(100.0 * (r["valor_execucao"] - r["valor_decisao"]) / r["valor_decisao"], 2)

    resumo = {fluxo: _novo() for fluxo in campos}
    sem_valor_processos: list[dict[str, Any]] = []
    for p, data_exe, fluxo in _entradas_por_fluxo_cs_LA(execucao, agendamentos, from_date, to_date):
        if fluxo not in campos:
            continue
        decisao, valor_execucao = _valores(p, fluxo)
        if not decisao or not valor_execucao:
            resumo[fluxo]["sem_valor"] += 1
            faltando = [nome for nome, ok in ((campos[fluxo][1], decisao), ("Execução", valor_execucao)) if not ok]
            sem_valor_processos.append({
                "numero_processo": str(p.get("NUMERO_PROCESSO") or "").strip() or None,
                "fluxo": fluxo,
                "data_entrada": data_exe.isoformat(),
                "faltando": faltando,
            })
            continue
        resumo[fluxo]["quantidade"] += 1
        resumo[fluxo]["valor_decisao"] += decisao
        resumo[fluxo]["valor_execucao"] += valor_execucao

    ano_ref = ano or date.today().year
    meses: dict[int, dict[str, dict[str, Any]]] = {}
    for p, data_exe, fluxo in _entradas_por_fluxo_cs_LA(execucao, agendamentos):
        if fluxo not in campos or data_exe.year != ano_ref:
            continue
        decisao, valor_execucao = _valores(p, fluxo)
        if not decisao or not valor_execucao:
            continue
        mes = meses.setdefault(data_exe.month, {"1G": _novo(), "2G": _novo(), "Total": _novo()})
        for chave in (fluxo, "Total"):
            mes[chave]["quantidade"] += 1
            mes[chave]["valor_decisao"] += decisao
            mes[chave]["valor_execucao"] += valor_execucao
    por_mes = [
        {
            "mes": m,
            "name": f"{_MONTH_NAMES[m - 1]} {ano_ref}",
            "1G": _taxa(meses[m]["1G"]),
            "2G": _taxa(meses[m]["2G"]),
            "Total": _taxa(meses[m]["Total"]),
            "quantidade": meses[m]["Total"]["quantidade"],
            # Valor da decisão do mês: sentença (1G) e acórdão (2G) — linhas do gráfico do modal.
            "valor_sentenca": round(meses[m]["1G"]["valor_decisao"], 2),
            "valor_acordao": round(meses[m]["2G"]["valor_decisao"], 2),
        }
        for m in sorted(meses)
    ]

    total = {
        k: sum(r[k] for r in resumo.values())
        for k in ("quantidade", "sem_valor", "valor_decisao", "valor_execucao")
    }
    return {
        "linhas": [_linha(fluxo, r) for fluxo, r in resumo.items()],
        "total": _linha("Total", total),
        "sem_valor_processos": sorted(sem_valor_processos, key=lambda x: x["data_entrada"], reverse=True),
        "ano": ano_ref,
        "por_mes": por_mes,
    }


def group_entrada_execucao_por_fluxo_cs_por_mes_LA(
    execucao: list[dict[str, Any]],
    agendamentos: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Espelho de :func:`group_entrada_execucao_por_fluxo_cs_por_mes_NG` — entradas da
    Execução Condenação por mês que vieram da Confecção CS, em ``"1G"``, ``"2G"`` e
    ``"CS (sem grau)"`` (atividade antiga "Elaborar Cumprimento de Sentença").
    Conta CS "Encerrado Cumprido" ou "Cancelado" com encerramento a até 30 dias da
    entrada; vale a mais próxima, e no empate a Cumprida.
    """
    grouped: dict[str, dict[str, Any]] = {}
    for p, data_exe, grau in _entradas_por_fluxo_cs_LA(execucao, agendamentos):
        month_key = f"{data_exe.year}-{data_exe.month:02d}"
        if month_key not in grouped:
            grouped[month_key] = {
                "name": f"{_MONTH_NAMES[data_exe.month - 1]} {data_exe.year}",
                "1G": 0,
                "2G": 0,
                _FLUXO_CS_SEM_GRAU_LABEL_LA: 0,
                "Outros": 0,
            }
        # Sem CS por perto: a entrada veio por outro caminho — "Outros" faz a soma das
        # linhas bater com o total de entradas da Condenação (card "Quantidade de entrada").
        grouped[month_key][grau] += 1

    return [grouped[k] for k in sorted(grouped)]


group_execucao_resolvidos_por_dia_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_resolvidos_por_dia)


get_media_execucao_resolvidos_por_funcionario_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_media_execucao_resolvidos_por_funcionario)


group_valor_recuperado_por_funcionario_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_valor_recuperado_por_funcionario)


list_execucao_atividades_periodo_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.list_execucao_atividades_periodo)


list_execucao_atividades_abertas_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.list_execucao_atividades_abertas)


get_opcoes_filtros_execucao_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_filtros_execucao)


@dataclass(frozen=True)
class ExecucaoAtividadesFiltros:
    """Filtros cumulativos (AND) sobre agendamentos do setor Execução."""

    funcionarios: frozenset[str] | None = None
    atividades: frozenset[str] | None = None
    status: frozenset[str] | None = None
    situacoes: frozenset[str] | None = None

    def ativo(self) -> bool:
        return bool(self.funcionarios or self.atividades or self.status or self.situacoes)


def _agendamento_match_filtros_exec(
    row: dict[str, Any],
    filtros: ExecucaoAtividadesFiltros,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> bool:
    if filtros.funcionarios is not None:
        funcionario = _get_ag_funcionario_nome(row)
        if not _nome_em_conjunto_exec(funcionario, filtros.funcionarios):
            return False
    if filtros.atividades is not None:
        atividade = _get_ag_atividade_nome(row)
        if not _nome_em_conjunto_exec(atividade, filtros.atividades):
            return False
    if filtros.status is not None:
        status = (_get_ag_status(row) or "—").strip()
        if not _nome_em_conjunto_exec(status, filtros.status):
            return False
    if filtros.situacoes is not None:
        flags = _classificar_situacao_exec(row, from_date, to_date, ref_date=ref_date)
        if not any(flags.get(sid) for sid in filtros.situacoes):
            return False
    return True


def filtrar_agendamentos_execucao_LA(
    agendamentos: list[dict[str, Any]],
    filtros: ExecucaoAtividadesFiltros | None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Restringe agendamentos aos filtros cumulativos."""
    if filtros is None or not filtros.ativo():
        return agendamentos
    return [
        row for row in agendamentos
        if _agendamento_match_filtros_exec(row, filtros, from_date, to_date, ref_date=ref_date)
    ]


# ---------------------------------------------------------------------------
# Análise por Prazo — LA (mesmas 5 métricas, mas usando PRAZO como eixo
# temporal em vez de DATA_HORA_CRIACAO/DATA_HORA_CONCLUSAO). Mesmo padrão de
# analyses/LA/pendencias_intermediarias_LA.py.
# ---------------------------------------------------------------------------

_incluir_na_lista_por_prazo_exec = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._incluir_na_lista_por_prazo_exec)


_classificar_situacao_por_prazo_exec = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._classificar_situacao_por_prazo_exec)


def get_kpis_execucao_por_prazo_LA(
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
        prazo = _get_ag_prazo(row)
        status = _get_ag_status(row) or ""
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
        "total_por_prazo_execucao_LA": total,
        "por_prazo_em_andamento_execucao_LA": em_andamento,
        "por_prazo_vencidas_execucao_LA": vencidas,
        "por_prazo_vencem_hoje_execucao_LA": vencem_hoje,
        "por_prazo_concluidas_execucao_LA": concluidas,
    }


group_execucao_processos_por_atividade_por_prazo_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_processos_por_atividade_por_prazo)


group_execucao_demandas_por_funcionario_por_prazo_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_demandas_por_funcionario_por_prazo)


group_execucao_demandas_por_funcionario_por_prazo_completo_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_demandas_por_funcionario_por_prazo_completo)


list_execucao_atividades_por_prazo_periodo_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.list_execucao_atividades_por_prazo_periodo)


get_opcoes_filtros_execucao_por_prazo_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_opcoes_filtros_execucao_por_prazo)


group_execucao_resolvidos_por_dia_por_prazo_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_resolvidos_por_dia_por_prazo)


get_media_execucao_resolvidos_por_funcionario_por_prazo_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_media_execucao_resolvidos_por_funcionario_por_prazo)


# ---------------------------------------------------------------------------
# Motivo de "Encerrado Não Cumprido" — LA
# ---------------------------------------------------------------------------

_get_ag_motivo_encaminhamento_itens = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_ag_motivo_encaminhamento_itens)


group_execucao_nao_cumprido_por_motivo_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_execucao_nao_cumprido_por_motivo)


# ---------------------------------------------------------------------------
# Detalhamento de atrasos (vencidas por dias de atraso)
# ---------------------------------------------------------------------------

_ATRASO_MAX_BUCKET = _familia._ATRASO_MAX_BUCKET

_BUCKET_META = _familia._BUCKET_META


get_atrasos_detalhamento_execucao_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_atrasos_detalhamento_execucao)

group_estoque_execucao_por_mes_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_estoque_execucao_por_mes)


filtrar_saida_execucao_export_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.filtrar_saida_execucao_export)


anotar_saida_execucao_export_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.anotar_saida_execucao_export)
