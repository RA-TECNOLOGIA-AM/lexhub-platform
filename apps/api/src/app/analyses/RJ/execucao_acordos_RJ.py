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
# - População: dentro do universo RJ (ID_ESCRITORIO=27), processos na fase de
#              Acordo (ID_FASE=30) com etiqueta "Acordo" OU `acordo_fechado`
#              preenchido.

from __future__ import annotations

import json
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from app.utils import parse_date_from_db
from app.analyses.execucao_estoque_mensal import estoque_por_mes, indice_mes


# =============================================================================
# Constantes
# =============================================================================

ID_FASE_ACORDO = 30
ID_ESCRITORIO = 27

_COL_ID_ESCRITORIO = "ID_ESCRITORIO"

_MONTH_NAMES = (
    "jan", "fev", "mar", "abr", "mai", "jun",
    "jul", "ago", "set", "out", "nov", "dez",
)


# =============================================================================
# 1 - Helpers internos
# =============================================================================

def _to_date(value: Any) -> Optional[date]:
    """Converte um valor bruto do banco para ``date``, ou ``None`` se inválido."""
    if not value:
        return None
    parsed = parse_date_from_db(value)
    if isinstance(parsed, datetime):
        return parsed.date()
    if isinstance(parsed, date):
        return parsed
    return None


def _get_data_acordo_fechado(item: dict[str, Any]) -> Optional[date]:
    return _to_date(item.get("DATA_ACORDO_FECHADO") or item.get("data_acordo_fechado"))


def _get_data_pagamento_acordo(item: dict[str, Any]) -> Optional[date]:
    return _to_date(item.get("DATA_PAGAMENTO_ACORDO") or item.get("data_pagamento_acordo"))


def _get_data_distribuicao(item: dict[str, Any]) -> Optional[date]:
    return _to_date(item.get("DATA_DISTRIBUICAO") or item.get("data_distribuicao"))


def _get_data_execucao_RJ(item: dict[str, Any]) -> Optional[date]:
    return _to_date(item.get("DATA_EXECUCAO") or item.get("data_execucao"))


def _data_no_periodo(
    d: Optional[date],
    from_date: Optional[date],
    to_date: Optional[date],
) -> bool:
    """Verifica se ``d`` está dentro do intervalo [from_date, to_date]."""
    if d is None:
        return False
    if from_date and to_date:
        return from_date <= d <= to_date
    if from_date:
        return d >= from_date
    if to_date:
        return d <= to_date
    return True


def _converter_valor(valor: Any) -> float:
    """
    Converte qualquer representação de valor monetário para ``float``.
    Retorna ``0.0`` em caso de falha ou valor ausente.
    """
    if valor is None:
        return 0.0
    try:
        if isinstance(valor, Decimal):
            return float(valor)
        if isinstance(valor, (int, float)):
            return float(valor)
        if isinstance(valor, str):
            limpo = valor.strip().replace(",", ".")
            limpo = "".join(c for c in limpo if c.isdigit() or c == ".")
            return float(limpo) if limpo else 0.0
        return float(str(valor).replace(",", "."))
    except (ValueError, TypeError, AttributeError):
        return 0.0


def _to_int(value: Any) -> Optional[int]:
    """Converte valores numéricos do banco para ``int`` quando possível."""
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


# =============================================================================
# 2 - Base e filtragem
# =============================================================================

def _tem_etiqueta_ou_acordo_fechado(item: dict[str, Any]) -> bool:
    """
    Critério de recorte "é execução de acordo": etiqueta "Acordo" aplicada ao
    processo (``TEM_ETIQUETA_ACORDO``) OU ``DATA_ACORDO_FECHADO`` preenchida.
    """
    if bool(item.get("TEM_ETIQUETA_ACORDO")):
        return True
    return _get_data_acordo_fechado(item) is not None


def _processo_na_fase_acordo(item: dict[str, Any]) -> bool:
    """Retorna True se o processo pertence à fase de Acordo."""
    id_fase = item.get("ID_FASE")
    return id_fase is not None and int(id_fase) == ID_FASE_ACORDO


def _base_execucao_acordos_RJ(execucao: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Universo histórico de Execução de Acordos LA: ``ID_ESCRITORIO == 20``, com
    etiqueta "Acordo" ou ``acordo_fechado`` preenchido, deduplicado por
    ``NUMERO_PROCESSO`` — SEM exigir que o processo ainda esteja na fase de
    Acordo hoje.

    Inclui processos já arquivados (ex.: arquivado por procedência) que já
    entraram/saíram da Execução de Acordos em algum momento. Use esta base para
    métricas de fluxo histórico (entrada/saída por período, por mês); para o
    estoque atual, use :func:`_filtrar_em_execucao_acordos_RJ`.
    """
    base: list[dict[str, Any]] = []
    vistos: set[Any] = set()
    for item in execucao:
        id_escritorio = item.get(_COL_ID_ESCRITORIO) or item.get("id_escritorio")
        if _to_int(id_escritorio) != ID_ESCRITORIO:
            continue
        if not _tem_etiqueta_ou_acordo_fechado(item):
            continue
        chave = item.get("NUMERO_PROCESSO") or item.get("id") or item.get("ID")
        if chave is not None:
            if chave in vistos:
                continue
            vistos.add(chave)
        base.append(item)
    return base


def _filtrar_em_execucao_acordos_RJ(execucao: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Retorna somente os processos ainda na fase de Acordo hoje (``ID_FASE == 30``),
    dentro do universo histórico de :func:`_base_execucao_acordos_RJ`.

    Use para métricas de estoque atual (total em execução, valor total, rankings
    por matéria/subfase, etc.) — não para fluxo histórico de entrada/saída.
    """
    return [e for e in _base_execucao_acordos_RJ(execucao) if _processo_na_fase_acordo(e)]



def group_alvaras_expedidos_acordos_por_dia_RJ(execucao: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Alvarás de acordo expedidos por dia (histórico completo, :func:`_base_execucao_acordos_RJ`) —
    ``DATA_EXPEDICAO_ALVARA_ACORDO``, valor ``VALOR_ALVARA`` (senão ``VALOR_ALCADA_FINAL``).
    Mesmo formato de :func:`group_alvaras_expedidos_por_dia_RJ` da Condenação.
    """
    por_dia: dict[str, dict[str, Any]] = {}
    for p in _base_execucao_acordos_RJ(execucao):
        dia = _to_date(p.get("DATA_EXPEDICAO_ALVARA_ACORDO"))
        if dia is None:
            continue
        valor = 0.0
        for campo in ("VALOR_ALVARA", "VALOR_ALCADA_FINAL"):
            raw = p.get(campo)
            if raw is None or (isinstance(raw, str) and not raw.strip()):
                continue
            convertido = _converter_valor(raw)
            if convertido:
                valor = convertido
                break
        chave = dia.isoformat()
        item = por_dia.setdefault(chave, {"data": chave, "quantidade": 0, "valor": 0.0})
        item["quantidade"] += 1
        item["valor"] += valor
    return [
        {**por_dia[k], "valor": round(por_dia[k]["valor"], 2)}
        for k in sorted(por_dia)
    ]


_SUBFASE_ALVARA_EXPEDIDO_ACORDO = "ALVARÁ EXPEDIDO ACORDO"


def list_processos_alvara_expedido_acordos_RJ(
    execucao: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Processos ainda na fase Acordo (estoque atual, :func:`_filtrar_em_execucao_acordos_RJ`) com subfase
    "ALVARÁ EXPEDIDO ACORDO" — mesmo formato de linha da lista da Condenação, com
    ``origem="Acordo"``. Data: ``DATA_EXPEDICAO_ALVARA_ACORDO``; valor: ``VALOR_ALVARA``,
    senão ``VALOR_ALCADA_FINAL`` (zero conta como vazio).
    """
    itens: list[dict[str, Any]] = []
    for p in _filtrar_em_execucao_acordos_RJ(execucao):
        if _normalizar_subfase(p.get("SUBFASE")).casefold() != _SUBFASE_ALVARA_EXPEDIDO_ACORDO.casefold():
            continue
        valor_alvara = None
        for campo in ("VALOR_ALVARA", "VALOR_ALCADA_FINAL"):
            raw = p.get(campo)
            if raw is None or (isinstance(raw, str) and not raw.strip()):
                continue
            valor = _converter_valor(raw)
            if valor:
                valor_alvara = valor
                break
        data_expedicao = _to_date(p.get("DATA_EXPEDICAO_ALVARA_ACORDO"))
        itens.append({
            "id": _to_int(p.get("id") or p.get("ID")),
            "origem": "Acordo",
            "numero_processo": str(p.get("NUMERO_PROCESSO") or "").strip() or None,
            "subfase": _normalizar_subfase(p.get("SUBFASE")),
            "materia": _normalizar_materia(p.get("MATERIA")),
            "data_expedicao_alvara": data_expedicao.isoformat() if data_expedicao else None,
            "tipo_alvara": "Acordo",
            "data_expedicao_alvara_incontroverso": None,
            "valor_alvara": valor_alvara,
            "valor_alvara_incontroverso": None,
        })
    return sorted(itens, key=lambda x: x["data_expedicao_alvara"] or "", reverse=True)


def _get_valor_alcada_final(item: dict[str, Any]) -> Optional[Any]:
    """Retorna o valor bruto de VALOR_ALCADA_FINAL, ou ``None`` se ausente/vazio."""
    raw = item.get("VALOR_ALCADA_FINAL")
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None
    return raw


def _tem_etiqueta_acordo(item: dict[str, Any]) -> bool:
    """Etiqueta "Acordo" aplicada ao processo no LEXFLOW (``TEM_ETIQUETA_ACORDO``)."""
    return bool(item.get("TEM_ETIQUETA_ACORDO"))


def _filtrar_entrada_execucao_acordos_RJ_no_periodo(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Processos com a etiqueta "Acordo" aplicada no LEXFLOW cuja ``DATA_EXECUCAO``
    está no período informado. Deduplicado por NUMERO_PROCESSO.

    Não usa ID_FASE nem DATA_ACORDO_FECHADO como critério de população aqui:
    a fase do processo pode mudar depois (ex.: acordo pago e arquivado, ou
    movido para outra fase) e a entrada seria perdida se exigíssemos uma fase
    específica; e DATA_ACORDO_FECHADO nem sempre é preenchida no LEXFLOW mesmo
    quando o processo já tem execução e valor de alçada final definidos. A
    etiqueta é o marcador estável de que o processo é uma execução de acordo.
    """
    vistos: set[Any] = set()
    filtrados: list[dict[str, Any]] = []
    for item in execucao:
        id_escritorio = item.get(_COL_ID_ESCRITORIO) or item.get("id_escritorio")
        if _to_int(id_escritorio) != ID_ESCRITORIO:
            continue
        if not _tem_etiqueta_acordo(item):
            continue
        if not _data_no_periodo(_get_data_execucao_RJ(item), from_date, to_date):
            continue
        chave = _get_numero_processo(item)
        if chave is not None:
            if chave in vistos:
                continue
            vistos.add(chave)
        filtrados.append(item)
    return filtrados


def _filtrar_saida_execucao_acordos_RJ_no_periodo(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Processos com ``DATA_PAGAMENTO_ACORDO`` preenchida cuja data está no período informado."""
    return [
        item for item in _base_execucao_acordos_RJ(execucao)
        if _data_no_periodo(_get_data_pagamento_acordo(item), from_date, to_date)
    ]


def _normalizar_materia(raw: Any) -> str:
    """Extrai a matéria: apenas a parte antes do ' - '."""
    if raw is None or raw == "":
        return "Sem materia"
    s = str(raw).strip()
    if " - " in s:
        s = s.split(" - ", 1)[0].strip()
    return s if s else "Sem materia"


def _normalizar_subfase(raw: Any) -> str:
    if raw is None or raw == "":
        return "Sem subfase"
    s = str(raw).strip()
    return s if s else "Sem subfase"


def filter_execucao_acordos_RJ_por_materia(
    execucao: list[dict[str, Any]],
    materia: Optional[Any] = None,
) -> list[dict[str, Any]]:
    # Aceita um valor único ou uma lista (seleção múltipla no filtro da página).
    valores = materia if isinstance(materia, (list, tuple, set)) else [materia]
    alvos = {_normalizar_materia(v) for v in valores if v is not None and str(v).strip()}
    if not alvos:
        return _base_execucao_acordos_RJ(execucao)
    return [
        p for p in _base_execucao_acordos_RJ(execucao)
        if _normalizar_materia(p.get("MATERIA")) in alvos
    ]


def filter_execucao_acordos_RJ_por_subfase(
    execucao: list[dict[str, Any]],
    subfase: Optional[Any] = None,
) -> list[dict[str, Any]]:
    # Aceita um valor único ou uma lista (seleção múltipla no filtro da página).
    valores = subfase if isinstance(subfase, (list, tuple, set)) else [subfase]
    alvos = {_normalizar_subfase(v) for v in valores if v is not None and str(v).strip()}
    if not alvos:
        return _base_execucao_acordos_RJ(execucao)
    return [
        p for p in _base_execucao_acordos_RJ(execucao)
        if _normalizar_subfase(p.get("SUBFASE")) in alvos
    ]


def filter_execucao_acordos_RJ_por_uf(
    execucao: list[dict[str, Any]],
    ufs: Optional[list[str]] = None,
) -> list[dict[str, Any]]:
    """Sem UFs informadas, não filtra. Caso contrário, mantém só as UFs selecionadas."""
    base = _base_execucao_acordos_RJ(execucao)
    alvo = {str(u).strip().upper() for u in ufs if str(u).strip()} if ufs else set()
    if not alvo:
        return base
    return [p for p in base if str(p.get("UF") or "").strip().upper() in alvo]


def _normalizar_comarca(raw: Any) -> str:
    if raw is None or raw == "":
        return "Sem comarca"
    s = str(raw).strip()
    return s if s else "Sem comarca"


def filter_execucao_acordos_RJ_por_comarca(
    execucao: list[dict[str, Any]],
    comarcas: Optional[list[str]] = None,
) -> list[dict[str, Any]]:
    """Sem comarcas informadas, não filtra. Caso contrário, mantém só as comarcas selecionadas."""
    base = _base_execucao_acordos_RJ(execucao)
    alvo = {_normalizar_comarca(c) for c in comarcas if str(c).strip()} if comarcas else set()
    if not alvo:
        return base
    return [p for p in base if _normalizar_comarca(p.get("COMARCA")) in alvo]


def get_opcoes_comarca_execucao_acordos_RJ(execucao: list[dict[str, Any]]) -> list[str]:
    """Comarcas distintas (não vazias) presentes na base de Execução de Acordos, em ordem alfabética."""
    comarcas = {
        _normalizar_comarca(p.get("COMARCA"))
        for p in _base_execucao_acordos_RJ(execucao)
    }
    comarcas.discard("Sem comarca")
    return sorted(comarcas)


def get_opcoes_materia_execucao_acordos_RJ(execucao: list[dict[str, Any]]) -> list[str]:
    """Matérias distintas (não vazias) presentes na base de Execução de Acordos LA, em ordem alfabética."""
    materias = {
        _normalizar_materia(p.get("MATERIA"))
        for p in _base_execucao_acordos_RJ(execucao)
    }
    materias.discard("Sem materia")
    return sorted(materias)


def get_opcoes_subfase_execucao_acordos_RJ(execucao: list[dict[str, Any]]) -> list[str]:
    """Subfases distintas (não vazias) presentes na base de Execução de Acordos LA, em ordem alfabética."""
    subfases = {
        _normalizar_subfase(p.get("SUBFASE"))
        for p in _base_execucao_acordos_RJ(execucao)
    }
    subfases.discard("Sem subfase")
    return sorted(subfases)


def group_execucao_acordos_RJ_por_comarca(
    execucao: list[dict[str, Any]],
    *,
    criterio: str = "total",
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Agrupa processos em Execução de Acordos por COMARCA, conforme ``criterio``:

    - "total": estoque atual (fase ACORDO), sem filtro de período —
      :func:`_filtrar_em_execucao_acordos_RJ`.
    - "entrada": processos com etiqueta "Acordo" e DATA_EXECUCAO no período —
      :func:`_filtrar_entrada_execucao_acordos_RJ_no_periodo`.
    - "saida": processos com DATA_PAGAMENTO_ACORDO no período —
      :func:`_filtrar_saida_execucao_acordos_RJ_no_periodo`.

    Cada item traz, além da quantidade (``value``): a soma do VALOR_ALCADA_FINAL
    (``valor_execucao``) e o tempo médio em dias entre DATA_EXECUCAO e
    DATA_PAGAMENTO_ACORDO (``tempo_medio_dias``, ``None`` quando nenhum processo
    da comarca tem as duas datas preenchidas).

    ``tempo_medio_dias`` é fixo por comarca e **não muda com o ``criterio``** — é
    calculado sobre o universo histórico completo da comarca
    (:func:`_base_execucao_acordos_RJ`, todo acordo com as duas datas preenchidas,
    independente da fase atual ou do período), para servir de referência estável
    de "quanto tempo um acordo dessa comarca costuma levar para ser pago". Só
    ``value``/``valor_execucao`` respeitam o ``criterio`` selecionado.

    Retorna lista ordenada de forma decrescente por quantidade.
    """
    if criterio == "entrada":
        base = _filtrar_entrada_execucao_acordos_RJ_no_periodo(execucao, from_date, to_date)
    elif criterio == "saida":
        base = _filtrar_saida_execucao_acordos_RJ_no_periodo(execucao, from_date, to_date)
    else:
        base = _filtrar_em_execucao_acordos_RJ(execucao)

    duracoes_por_comarca: defaultdict[str, list[float]] = defaultdict(list)
    for p in _base_execucao_acordos_RJ(execucao):
        entrada = _get_data_execucao_RJ(p)
        saida = _get_data_pagamento_acordo(p)
        if entrada and saida:
            dias = (saida - entrada).days
            if dias > 0:
                duracoes_por_comarca[_normalizar_comarca(p.get("COMARCA"))].append(float(dias))
    tempo_medio_por_comarca = {
        name: round(sum(duracoes) / len(duracoes), 2)
        for name, duracoes in duracoes_por_comarca.items()
    }

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


def group_valor_execucao_acordos_RJ_por_comarca(
    execucao: list[dict[str, Any]],
    *,
    criterio: str = "total",
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Agrupa o valor dos acordos em Execução por COMARCA, conforme ``criterio``
    (mesmo recorte de :func:`group_execucao_acordos_RJ_por_comarca`, mas somando
    VALOR_ALCADA_FINAL em vez de contar).

    Retorna lista de ``{"name": comarca, "value": valor}``, ordenada de forma
    decrescente por valor.
    """
    if criterio == "entrada":
        base = _filtrar_entrada_execucao_acordos_RJ_no_periodo(execucao, from_date, to_date)
    elif criterio == "saida":
        base = _filtrar_saida_execucao_acordos_RJ_no_periodo(execucao, from_date, to_date)
    else:
        base = _filtrar_em_execucao_acordos_RJ(execucao)

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


def filter_execucao_acordos_RJ_por_processo(
    execucao: list[dict[str, Any]],
    numero_processo: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Filtra por um único NUMERO_PROCESSO (igual ao `name` usado nos gráficos
    por processo, ex.: "Processos com mais Diligências")."""
    if numero_processo is None or not str(numero_processo).strip():
        return _base_execucao_acordos_RJ(execucao)
    alvo = str(numero_processo).strip()
    return [
        p for p in _base_execucao_acordos_RJ(execucao)
        if str(p.get("NUMERO_PROCESSO") or "").strip() == alvo
    ]


def get_opcoes_uf_execucao_acordos_RJ(execucao: list[dict[str, Any]]) -> list[str]:
    """UFs distintas (não vazias) presentes na base de Execução de Acordos, em ordem alfabética."""
    ufs = {
        str(p.get("UF") or "").strip().upper()
        for p in _base_execucao_acordos_RJ(execucao)
    }
    ufs.discard("")
    return sorted(ufs)


# =============================================================================
# 3 - Totais
# =============================================================================

def get_total_execucao_acordos_RJ(execucao: list[dict[str, Any]]) -> int:
    """Retorna o total de processos atualmente em Execução de Acordos."""
    return len(_filtrar_em_execucao_acordos_RJ(execucao))


def get_total_entrada_execucao_acordos_RJ_periodo(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """Quantidade de acordos com entrada na execução no período (``DATA_EXECUCAO`` no intervalo)."""
    return len(_filtrar_entrada_execucao_acordos_RJ_no_periodo(execucao, from_date, to_date))


def get_total_saida_execucao_acordos_RJ_periodo(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """Quantidade de acordos pagos no período (``DATA_PAGAMENTO_ACORDO`` no intervalo)."""
    return len(_filtrar_saida_execucao_acordos_RJ_no_periodo(execucao, from_date, to_date))


def get_estoque_final_execucao_acordos_RJ(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    execucao_fluxos_periodo: Optional[list[dict[str, Any]]] = None,
) -> int:
    """
    Estoque final calculado: ``(total em Execução de Acordos − entradas no período)
    + saídas no período``.
    """
    fluxos = execucao_fluxos_periodo if execucao_fluxos_periodo is not None else execucao
    resultado_subtracao = (
        get_total_execucao_acordos_RJ(execucao)
        - get_total_entrada_execucao_acordos_RJ_periodo(fluxos, from_date, to_date)
    )
    return resultado_subtracao + get_total_saida_execucao_acordos_RJ_periodo(
        fluxos, from_date, to_date
    )


def get_tre(estoque_inicial: int, estoque_final: int) -> float:
    """TRE: ``DIVIDE((Estoque_Inicial − Estoque_Final) × 100, Estoque_Final, 0)``."""
    if estoque_final == 0:
        return 0.0
    diferenca = float(estoque_inicial) - float(estoque_final)
    return (diferenca * 100.0) / float(estoque_final)


def get_tre_execucao_acordos_RJ_dax(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    execucao_fluxos_periodo: Optional[list[dict[str, Any]]] = None,
) -> float:
    inicial = get_total_execucao_acordos_RJ(execucao)
    final = get_estoque_final_execucao_acordos_RJ(
        execucao,
        from_date,
        to_date,
        execucao_fluxos_periodo=execucao_fluxos_periodo,
    )
    return get_tre(inicial, final)


# =============================================================================
# 4 - Valores monetários
# =============================================================================

def get_valor_alcada_final_total_execucao_acordos_RJ(execucao: list[dict[str, Any]]) -> float:
    """Soma de VALOR_ALCADA_FINAL de todos os processos em Execução de Acordos."""
    total = 0.0
    for p in _filtrar_em_execucao_acordos_RJ(execucao):
        valor = _get_valor_alcada_final(p)
        if valor is not None:
            total += _converter_valor(valor)
    return total


def get_detalhe_valor_alcada_final_vazio_RJ(execucao: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Processos em Execução de Acordos com VALOR_ALCADA_FINAL ausente/vazio —
    número do processo + campo faltando (alimenta o alerta clicável do dashboard)."""
    return [
        {
            "numero_processo": str(p.get("NUMERO_PROCESSO") or p.get("id") or p.get("ID") or ""),
            "campo": "Valor de Alçada Final",
        }
        for p in _filtrar_em_execucao_acordos_RJ(execucao)
        if _get_valor_alcada_final(p) is None
    ]


def get_total_valor_alcada_final_vazio_RJ(execucao: list[dict[str, Any]]) -> int:
    """Quantidade de processos em Execução de Acordos com VALOR_ALCADA_FINAL ausente/vazio."""
    return len(get_detalhe_valor_alcada_final_vazio_RJ(execucao))


def get_valor_ted_saida_execucao_acordos_RJ_periodo(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """Soma de ``VALOR_TED`` (+ ``VALOR_TED_2``/``VALOR_TED_3``) dos acordos pagos (DATA_PAGAMENTO_ACORDO) no período — mesmo
    recorte de :func:`get_valor_saida_execucao_acordos_RJ_periodo`; soma com o TED da Condenação no card "Valor saída Execução"."""
    total = 0.0
    for p in _filtrar_saida_execucao_acordos_RJ_no_periodo(execucao, from_date, to_date):
        for campo in ("VALOR_TED", "VALOR_TED_2", "VALOR_TED_3"):
            raw = p.get(campo)
            if raw is None or (isinstance(raw, str) and not raw.strip()):
                continue
            total += _converter_valor(raw)
    return total


def get_valor_saida_execucao_acordos_RJ_periodo(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """Soma de VALOR_ALCADA_FINAL dos acordos pagos (DATA_PAGAMENTO_ACORDO) no período."""
    total = 0.0
    for p in _filtrar_saida_execucao_acordos_RJ_no_periodo(execucao, from_date, to_date):
        valor = _get_valor_alcada_final(p)
        if valor is not None:
            total += _converter_valor(valor)
    return total


def get_valor_entrada_execucao_acordos_RJ_periodo(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """
    Soma de VALOR_ALCADA_FINAL dos acordos com entrada na execução
    (DATA_EXECUCAO) no período — histórico completo, inclui processos já
    arquivados depois de entrarem na Execução de Acordos (ex.: arquivado por
    procedência).
    """
    total = 0.0
    for p in _filtrar_entrada_execucao_acordos_RJ_no_periodo(execucao, from_date, to_date):
        valor = _get_valor_alcada_final(p)
        if valor is not None:
            total += _converter_valor(valor)
    return total


# =============================================================================
# 5 - Agrupamentos
# =============================================================================

def group_valor_saida_execucao_acordos_RJ_por_mes(
    execucao: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Agrupa a soma de VALOR_ALCADA_FINAL dos acordos pagos, por mês (histórico completo)."""
    saidas = _filtrar_saida_execucao_acordos_RJ_no_periodo(execucao)
    grouped: dict[str, dict[str, Any]] = {}

    for p in saidas:
        try:
            data_saida = _get_data_pagamento_acordo(p)
            if not data_saida:
                continue

            month_key = f"{data_saida.year}-{data_saida.month:02d}"

            if month_key not in grouped:
                month_name = f"{_MONTH_NAMES[data_saida.month - 1]} {data_saida.year}"
                grouped[month_key] = {"name": month_name, "value": 0.0}

            valor = _get_valor_alcada_final(p)
            if valor is not None:
                grouped[month_key]["value"] += _converter_valor(valor)

        except (ValueError, AttributeError, TypeError):
            continue

    return [
        {**item, "value": round(item["value"], 2)}
        for item in sorted(grouped.values(), key=lambda x: x["name"])
    ]


def group_quantidade_saida_execucao_acordos_RJ_por_mes(
    execucao: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Agrupa a quantidade de acordos pagos, por mês (histórico completo)."""
    saidas = _filtrar_saida_execucao_acordos_RJ_no_periodo(execucao)
    grouped: dict[str, dict[str, Any]] = {}

    for p in saidas:
        try:
            data_saida = _get_data_pagamento_acordo(p)
            if not data_saida:
                continue

            month_key = f"{data_saida.year}-{data_saida.month:02d}"

            if month_key not in grouped:
                month_name = f"{_MONTH_NAMES[data_saida.month - 1]} {data_saida.year}"
                grouped[month_key] = {"name": month_name, "value": 0}

            grouped[month_key]["value"] += 1

        except (ValueError, AttributeError, TypeError):
            continue

    return [item for item in sorted(grouped.values(), key=lambda x: x["name"])]


def group_quantidade_entrada_execucao_acordos_RJ_por_mes(
    execucao: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Agrupa a quantidade de acordos com entrada na execução, por mês (histórico completo)."""
    entradas = _filtrar_entrada_execucao_acordos_RJ_no_periodo(execucao)
    grouped: dict[str, dict[str, Any]] = {}

    for p in entradas:
        try:
            data_entrada = _get_data_execucao_RJ(p)
            if not data_entrada:
                continue

            month_key = f"{data_entrada.year}-{data_entrada.month:02d}"

            if month_key not in grouped:
                month_name = f"{_MONTH_NAMES[data_entrada.month - 1]} {data_entrada.year}"
                grouped[month_key] = {"name": month_name, "value": 0}

            grouped[month_key]["value"] += 1

        except (ValueError, AttributeError, TypeError):
            continue

    return [item for item in sorted(grouped.values(), key=lambda x: x["name"])]


def group_valor_entrada_execucao_acordos_RJ_por_mes(
    execucao: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Agrupa a soma de VALOR_ALCADA_FINAL dos acordos com entrada na execução, por mês (histórico completo)."""
    entradas = _filtrar_entrada_execucao_acordos_RJ_no_periodo(execucao)
    grouped: dict[str, dict[str, Any]] = {}

    for p in entradas:
        try:
            data_entrada = _get_data_execucao_RJ(p)
            if not data_entrada:
                continue

            month_key = f"{data_entrada.year}-{data_entrada.month:02d}"

            if month_key not in grouped:
                month_name = f"{_MONTH_NAMES[data_entrada.month - 1]} {data_entrada.year}"
                grouped[month_key] = {"name": month_name, "value": 0.0}

            valor = _get_valor_alcada_final(p)
            if valor is not None:
                grouped[month_key]["value"] += _converter_valor(valor)

        except (ValueError, AttributeError, TypeError):
            continue

    return [
        {**item, "value": round(item["value"], 2)}
        for item in sorted(grouped.values(), key=lambda x: x["name"])
    ]


def group_execucao_acordos_RJ_por_subfase(execucao: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Agrupa os processos em Execução de Acordos por SUBFASE."""
    contagem: defaultdict[str, int] = defaultdict(int)

    for p in _filtrar_em_execucao_acordos_RJ(execucao):
        contagem[_normalizar_subfase(p.get("SUBFASE"))] += 1

    return sorted(
        [{"name": name, "value": int(value)} for name, value in contagem.items()],
        key=lambda x: x["value"],
        reverse=True,
    )


def group_valor_execucao_acordos_RJ_por_subfase(execucao: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Agrupa o VALOR_ALCADA_FINAL dos processos em Execução de Acordos por SUBFASE."""
    totais: defaultdict[str, float] = defaultdict(float)

    for p in _filtrar_em_execucao_acordos_RJ(execucao):
        valor = _get_valor_alcada_final(p)
        if valor is not None:
            totais[_normalizar_subfase(p.get("SUBFASE"))] += _converter_valor(valor)

    return sorted(
        [{"name": name, "value": float(value)} for name, value in totais.items()],
        key=lambda x: x["value"],
        reverse=True,
    )


def group_execucao_acordos_RJ_por_materia(
    execucao: list[dict[str, Any]],
    *,
    restringir_fase_atual: bool = False,
) -> list[dict[str, Any]]:
    """
    Agrupa os processos em Execução de Acordos por matéria.

    Por padrão usa :func:`_base_execucao_acordos_RJ` (sem exigir ``ID_FASE == 30``
    atual), para bater com :func:`get_total_entrada_execucao_acordos_RJ_periodo` quando
    ``execucao`` já vem filtrado por período (modo "Qtd Entrada" do front) — um
    acordo que entrou no período mas já saiu da fase Acordo (ex.: pago e arquivado)
    não pode sumir daqui, senão a soma por matéria fica menor que o KPI de entrada.

    Passe ``restringir_fase_atual=True`` para o modo "Total" (estoque atual, sem
    filtro de período) — aí a soma por matéria precisa bater com
    :func:`get_total_execucao_acordos_RJ`, que exige ``ID_FASE == 30`` atual.
    """
    base = (
        _filtrar_em_execucao_acordos_RJ(execucao)
        if restringir_fase_atual
        else _base_execucao_acordos_RJ(execucao)
    )
    contagem: defaultdict[str, int] = defaultdict(int)

    for p in base:
        contagem[_normalizar_materia(p.get("MATERIA"))] += 1

    return sorted(
        [{"name": name, "value": int(qtd)} for name, qtd in contagem.items()],
        key=lambda x: x["value"],
        reverse=True,
    )


def group_valor_execucao_acordos_RJ_por_materia(
    execucao: list[dict[str, Any]],
    *,
    restringir_fase_atual: bool = False,
) -> list[dict[str, Any]]:
    """
    Agrupa o VALOR_ALCADA_FINAL dos processos em Execução de Acordos por matéria.

    Mesmo critério de :func:`group_execucao_acordos_RJ_por_materia` — ver docstring lá
    para o motivo de ``restringir_fase_atual``.
    """
    base = (
        _filtrar_em_execucao_acordos_RJ(execucao)
        if restringir_fase_atual
        else _base_execucao_acordos_RJ(execucao)
    )
    totais: defaultdict[str, float] = defaultdict(float)

    for p in base:
        valor = _get_valor_alcada_final(p)
        if valor is not None:
            totais[_normalizar_materia(p.get("MATERIA"))] += _converter_valor(valor)

    return sorted(
        [{"name": name, "value": float(value)} for name, value in totais.items()],
        key=lambda x: x["value"],
        reverse=True,
    )


SEM_ANO_AJUIZAMENTO = "Sem data de ajuizamento"


def group_execucao_acordos_RJ_por_ano_ajuizamento(
    execucao: list[dict[str, Any]],
    *,
    restringir_fase_atual: bool = False,
) -> list[dict[str, Any]]:
    """
    Agrupa os processos em Execução de Acordos pelo ano de ajuizamento (DATA_DISTRIBUICAO).

    Cada item traz a quantidade (``value``) e a soma do VALOR_ALCADA_FINAL (``valor_causa``)
    dos processos daquele ano. Mesmo critério/motivo de ``restringir_fase_atual`` de
    :func:`group_execucao_acordos_RJ_por_materia`.
    """
    contagem: defaultdict[str, int] = defaultdict(int)
    valores: defaultdict[str, float] = defaultdict(float)

    base = (
        _filtrar_em_execucao_acordos_RJ(execucao)
        if restringir_fase_atual
        else _base_execucao_acordos_RJ(execucao)
    )
    for p in base:
        data_distribuicao = _get_data_distribuicao(p)
        ano = str(data_distribuicao.year) if data_distribuicao else SEM_ANO_AJUIZAMENTO
        contagem[ano] += 1
        valor = _get_valor_alcada_final(p)
        if valor is not None:
            valores[ano] += _converter_valor(valor)

    return sorted(
        [
            {"name": name, "value": int(value), "valor_causa": float(valores.get(name, 0.0))}
            for name, value in contagem.items()
        ],
        key=lambda x: x["name"],
    )


def filter_execucao_acordos_RJ_por_ano_ajuizamento(
    execucao: list[dict[str, Any]],
    ano_ajuizamento: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Filtra pelo ano de ajuizamento (DATA_DISTRIBUICAO), ou por `SEM_ANO_AJUIZAMENTO`."""
    base = _base_execucao_acordos_RJ(execucao)
    alvo = str(ano_ajuizamento).strip() if ano_ajuizamento else ""
    if not alvo:
        return base
    return [
        p
        for p in base
        if (
            str(d.year) if (d := _get_data_distribuicao(p)) else SEM_ANO_AJUIZAMENTO
        )
        == alvo
    ]


SEM_CLASSIFICACAO_JUDICIAL = "Sem classificação"


def _classificar_judicial_extrajudicial(item: dict[str, Any]) -> str:
    """
    Classifica o processo como "Judicial" ou "Extrajudicial" a partir das
    etiquetas "JUDICIAL"/"EXTRAJUDICIAL" aplicadas a ele no LEXFLOW.
    """
    if bool(item.get("TEM_ETIQUETA_JUDICIAL")):
        return "Judicial"
    if bool(item.get("TEM_ETIQUETA_EXTRAJUDICIAL")):
        return "Extrajudicial"
    return SEM_CLASSIFICACAO_JUDICIAL


def group_execucao_acordos_RJ_por_tipo_acao(execucao: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Agrupa os processos em Execução de Acordos por Judicial/Extrajudicial (etiquetas)."""
    contagem: defaultdict[str, int] = defaultdict(int)

    for p in _filtrar_em_execucao_acordos_RJ(execucao):
        contagem[_classificar_judicial_extrajudicial(p)] += 1

    return sorted(
        [{"name": name, "value": int(value)} for name, value in contagem.items()],
        key=lambda x: x["value"],
        reverse=True,
    )


def filter_execucao_acordos_RJ_por_tipo_acao(
    execucao: list[dict[str, Any]],
    tipo_acao: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Filtra pela classificação Judicial/Extrajudicial/Sem classificação (etiquetas)."""
    if tipo_acao is None or not str(tipo_acao).strip():
        return _base_execucao_acordos_RJ(execucao)
    alvo = str(tipo_acao).strip()
    return [
        p for p in _base_execucao_acordos_RJ(execucao)
        if _classificar_judicial_extrajudicial(p) == alvo
    ]


SEM_CLASSIFICACAO_SENTENCA = "Sem classificação"


def _classificar_pre_pos_sentenca(item: dict[str, Any]) -> str:
    """
    Classifica o processo como "Pré-Sentença" ou "Pós-Sentença" a partir das
    etiquetas "PRÉ-SENTENÇA"/"PÓS-SENTENÇA" aplicadas a ele no LEXFLOW.
    """
    if bool(item.get("TEM_ETIQUETA_PRE_SENTENCA")):
        return "Pré-Sentença"
    if bool(item.get("TEM_ETIQUETA_POS_SENTENCA")):
        return "Pós-Sentença"
    return SEM_CLASSIFICACAO_SENTENCA


def group_execucao_acordos_RJ_por_sentenca(execucao: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Agrupa os processos em Execução de Acordos por Pré/Pós-Sentença (etiquetas)."""
    contagem: defaultdict[str, int] = defaultdict(int)

    for p in _filtrar_em_execucao_acordos_RJ(execucao):
        contagem[_classificar_pre_pos_sentenca(p)] += 1

    return sorted(
        [{"name": name, "value": int(value)} for name, value in contagem.items()],
        key=lambda x: x["value"],
        reverse=True,
    )


def filter_execucao_acordos_RJ_por_sentenca(
    execucao: list[dict[str, Any]],
    sentenca: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Filtra pela classificação Pré-Sentença/Pós-Sentença/Sem classificação (etiquetas)."""
    if sentenca is None or not str(sentenca).strip():
        return _base_execucao_acordos_RJ(execucao)
    alvo = str(sentenca).strip()
    return [
        p for p in _base_execucao_acordos_RJ(execucao)
        if _classificar_pre_pos_sentenca(p) == alvo
    ]


# =============================================================================
# 6 - Análise temporal
# =============================================================================

def _extrair_duracoes_dias(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[float]:
    """
    Calcula a duração em dias (DATA_PAGAMENTO_ACORDO - DATA_EXECUCAO) por processo,
    amostrada pelos processos cuja SAÍDA (DATA_PAGAMENTO_ACORDO) caiu no período
    informado (não pela entrada) — mesmo critério de `_media_dias_permanencia_setor_NG`
    em `controle_processo_NG.py`. Sem período informado, não restringe (histórico completo).

    Usa a base histórica (`_base_execucao_acordos_RJ`), SEM exigir que o processo ainda
    esteja na fase de Acordo hoje: é comum um acordo ser pago e, em seguida, arquivado
    (ex.: arquivado por procedência) — esse processo já saiu da fase 30, mas o pagamento
    é real e deve contar no tempo médio/mediana.
    """
    duracoes: list[float] = []

    for p in _base_execucao_acordos_RJ(execucao):
        try:
            saida = _get_data_pagamento_acordo(p)
            if not _data_no_periodo(saida, from_date, to_date):
                continue

            entrada = _get_data_execucao_RJ(p)
            if not entrada or not saida:
                continue

            dias = (saida - entrada).days
            if dias > 0:
                duracoes.append(float(dias))

        except (ValueError, AttributeError, TypeError):
            continue

    return duracoes


def get_media_tempo_execucao_acordos_RJ(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """Tempo médio (em dias) entre DATA_EXECUCAO e DATA_PAGAMENTO_ACORDO, amostrado pela saída no período."""
    duracoes = _extrair_duracoes_dias(execucao, from_date, to_date)
    if not duracoes:
        return 0.0
    return round(sum(duracoes) / len(duracoes), 2)


def get_mediana_tempo_execucao_acordos_RJ(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """Mediana do tempo (em dias) entre DATA_EXECUCAO e DATA_PAGAMENTO_ACORDO, amostrada pela saída no período."""
    duracoes = sorted(_extrair_duracoes_dias(execucao, from_date, to_date))
    n = len(duracoes)

    if not n:
        return 0.0

    meio = n // 2
    if n % 2 == 1:
        return round(duracoes[meio], 2)
    return round((duracoes[meio - 1] + duracoes[meio]) / 2.0, 2)


def get_media_tempo_execucao_acordos_RJ_por_mes(execucao: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Série mensal (todo o histórico) da média de dias entre DATA_EXECUCAO e
    DATA_PAGAMENTO_ACORDO, agrupada pelo mês/ano da SAÍDA (DATA_PAGAMENTO_ACORDO) —
    mesmo critério de `_extrair_duracoes_dias`, quebrado mês a mês para acompanhar a
    tendência do tempo médio ao longo do tempo.
    """
    grouped: dict[str, dict[str, Any]] = {}

    for p in _base_execucao_acordos_RJ(execucao):
        try:
            saida = _get_data_pagamento_acordo(p)
            entrada = _get_data_execucao_RJ(p)
            if not entrada or not saida:
                continue

            dias = (saida - entrada).days
            if dias <= 0:
                continue

            month_key = f"{saida.year}-{saida.month:02d}"
            if month_key not in grouped:
                month_name = f"{_MONTH_NAMES[saida.month - 1]} {saida.year}"
                grouped[month_key] = {"name": month_name, "total": 0.0, "count": 0}
            grouped[month_key]["total"] += float(dias)
            grouped[month_key]["count"] += 1

        except (ValueError, AttributeError, TypeError):
            continue

    result = [
        {"name": v["name"], "value": round(v["total"] / v["count"], 2)}
        for v in grouped.values()
        if v["count"] > 0
    ]
    return sorted(result, key=lambda x: x["name"])


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

_SUBFASES_FECHAMENTO_ACORDO = frozenset({
    "ACORDO FECHADO",
    "ACORDO CANCELADO",
    "AG. PROTOCOLO DA MINUTA DE ACORDO",
    "MINUTA DE ACORDO PROTOCOLADA",
    "ACORDO EM NEGOCIAÇÃO",
})

_STATUS_CUMPRIDO_PROPOSTA_ACORDO = "Encerrado Cumprido"


def _tem_subfase_fechamento_acordo(item: dict[str, Any]) -> bool:
    return str(item.get("SUBFASE") or "").strip().upper() in _SUBFASES_FECHAMENTO_ACORDO


def _get_numero_processo(item: dict[str, Any]) -> Optional[Any]:
    return item.get("NUMERO_PROCESSO") or item.get("numero_processo")


def get_total_processos_fechamento_acordo_RJ(
    processos: list[dict[str, Any]],
    agendamentos_proposta: list[dict[str, Any]],
) -> int:
    """
    Total de processos LA que já entraram no funil de negociação/fechamento de
    acordo: processos cuja SUBFASE atual é uma das subfases de fechamento de
    acordo, OU que já tiveram uma vinculação PROPOSTA ENVIADA/PROPOSTA RECEBIDA
    marcada como cumprida (início da negociação) — o que vier primeiro.

    Deduplicado por NUMERO_PROCESSO, para não contar duas vezes um processo que
    satisfaz os dois critérios.
    """
    numeros: set[Any] = set()

    for p in processos:
        id_escritorio = p.get(_COL_ID_ESCRITORIO) or p.get("id_escritorio")
        if _to_int(id_escritorio) != ID_ESCRITORIO:
            continue
        if not _tem_subfase_fechamento_acordo(p):
            continue
        chave = _get_numero_processo(p)
        if chave is not None:
            numeros.add(chave)

    for a in agendamentos_proposta:
        status = str(a.get("STATUS") or "").strip()
        if status != _STATUS_CUMPRIDO_PROPOSTA_ACORDO:
            continue
        chave = _get_numero_processo(a)
        if chave is not None:
            numeros.add(chave)

    return len(numeros)


def _processos_fechamento_acordo_por_subfase(
    processos: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Base deduplicada (por NUMERO_PROCESSO) dos processos LA atualmente em uma das
    subfases de fechamento de acordo.
    """
    vistos: set[Any] = set()
    base: list[dict[str, Any]] = []
    for p in processos:
        id_escritorio = p.get(_COL_ID_ESCRITORIO) or p.get("id_escritorio")
        if _to_int(id_escritorio) != ID_ESCRITORIO:
            continue
        if not _tem_subfase_fechamento_acordo(p):
            continue
        chave = _get_numero_processo(p)
        if chave is not None:
            if chave in vistos:
                continue
            vistos.add(chave)
        base.append(p)
    return base


def group_fechamento_acordo_por_subfase_RJ(processos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Agrupa (contagem) os processos de Fechamento de Acordo por subfase."""
    contagem: defaultdict[str, int] = defaultdict(int)
    for p in _processos_fechamento_acordo_por_subfase(processos):
        contagem[str(p.get("SUBFASE") or "").strip().upper()] += 1

    return sorted(
        [{"name": name, "value": int(value)} for name, value in contagem.items()],
        key=lambda x: x["value"],
        reverse=True,
    )


def group_valor_fechamento_acordo_por_subfase_RJ(processos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Agrupa (soma de VALOR_ALCADA_FINAL) os processos de Fechamento de Acordo por subfase."""
    totais: defaultdict[str, float] = defaultdict(float)
    for p in _processos_fechamento_acordo_por_subfase(processos):
        valor = _get_valor_alcada_final(p)
        if valor is not None:
            totais[str(p.get("SUBFASE") or "").strip().upper()] += _converter_valor(valor)

    return sorted(
        [{"name": name, "value": float(value)} for name, value in totais.items()],
        key=lambda x: x["value"],
        reverse=True,
    )


# =============================================================================
# 6 - Lista de execuções de acordo (tabela)
# =============================================================================

def _montar_linhas_execucao_acordos_RJ_lista(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Converte processos brutos nas linhas da tabela: nº processo, UF, data da
    execução, valor de alçada final e subfase. Ordenado por data da execução
    (mais recente primeiro); processos sem data ficam no final."""
    itens: list[dict[str, Any]] = []
    for row in rows:
        data_execucao = _get_data_execucao_RJ(row)
        valor = _get_valor_alcada_final(row)
        itens.append({
            "id": _to_int(row.get("ID") or row.get("id")),
            "numero_processo": str(_get_numero_processo(row) or "").strip() or "—",
            "uf": str(row.get("UF") or "").strip().upper() or "—",
            "data_execucao": data_execucao.isoformat() if data_execucao else None,
            "valor_execucao": _converter_valor(valor) if valor is not None else None,
            "subfase": _normalizar_subfase(row.get("SUBFASE")),
        })

    com_data = sorted(
        (i for i in itens if i["data_execucao"]),
        key=lambda i: i["data_execucao"],
        reverse=True,
    )
    sem_data = [i for i in itens if not i["data_execucao"]]
    return com_data + sem_data


def list_execucao_acordos_RJ_lista_entrada(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Lista de acordos com entrada na Execução de Acordos no período (mesmo
    critério de :func:`_filtrar_entrada_execucao_acordos_RJ_no_periodo`)."""
    return _montar_linhas_execucao_acordos_RJ_lista(
        _filtrar_entrada_execucao_acordos_RJ_no_periodo(execucao, from_date, to_date)
    )


def list_execucao_acordos_RJ_lista_saida(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Lista de acordos pagos no período (mesmo critério de
    :func:`_filtrar_saida_execucao_acordos_RJ_no_periodo`)."""
    return _montar_linhas_execucao_acordos_RJ_lista(
        _filtrar_saida_execucao_acordos_RJ_no_periodo(execucao, from_date, to_date)
    )


def list_execucao_acordos_RJ_lista_total(execucao: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Lista do total atual em Execução de Acordos (mesmo critério de
    :func:`_filtrar_em_execucao_acordos_RJ`), sem filtro de período."""
    return _montar_linhas_execucao_acordos_RJ_lista(_filtrar_em_execucao_acordos_RJ(execucao))


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

_STATUS_INATIVO_EXEC = frozenset({
    "Encerrado Cumprido", "Encerrado Não Cumprido", "Cancelado", "Concluído",
})
_STATUS_EM_ANDAMENTO_EXEC = frozenset({"Iniciado", "Reaberto"})
_STATUS_ENCERRADO_EXEC = frozenset({"Encerrado Cumprido", "Encerrado Não Cumprido"})

_STATUS_FILTRO_EXEC: tuple[str, ...] = (
    "Recebido", "Visualizado", "Iniciado", "Reaberto", "Encaminhado",
    "Encerrado Cumprido", "Encerrado Não Cumprido", "Cancelado",
)

_SITUACOES_FILTRO_EXEC_RJ: tuple[tuple[str, str], ...] = (
    ("em_andamento", "Em andamento"),
    ("vencidas", "Vencidas"),
    ("vencem_hoje", "Vencem hoje"),
    ("concluidas", "Concluídas"),
)

SITUACOES_VALIDAS_EXECUCAO_RJ = frozenset(sid for sid, _ in _SITUACOES_FILTRO_EXEC_RJ)

# `filtros.situacoes` chega com os ids de `_SITUACOES_FILTRO_EXEC_RJ` (plural:
# "vencidas"/"vencem_hoje"/"concluidas"), mas `_classificar_situacao_exec_rj`
# devolve chaves no singular ("vencida"/"vence_hoje"/"concluida") — mesmo
# formato de `RecursalAtividadeTarefaRow`, que não pode mudar. Tradução
# necessária para o filtro de situação (usado por `_agendamento_match_filtros_exec_rj`)
# realmente casar com os flags.
_SITUACAO_ID_PARA_FLAG_RJ: dict[str, str] = {
    "vencidas": "vencida",
    "vencem_hoje": "vence_hoje",
    "concluidas": "concluida",
}

_STATUS_DEMANDAS_FUNCIONARIO_EXEC_RJ: tuple[tuple[str, str], ...] = (
    ("encerrado_nao_cumprido", "Encerrado Não Cumprido"),
    ("encerrado_cumprido", "Encerrado Cumprido"),
)
_SLUG_POR_STATUS_EXEC_RJ: dict[str, str] = {
    label: slug for slug, label in _STATUS_DEMANDAS_FUNCIONARIO_EXEC_RJ
}

_SEM_ATIVIDADE_EXEC = "Sem atividade"
_SEM_FUNCIONARIO_EXEC = "Sem funcionário"
_STATUS_CUMPRIDO_EXEC = "Encerrado Cumprido"

_COL_FUNCIONARIO_ATRIBUIDO_EXEC = "FUNCIONARIO_ATRIBUIDO"
_COL_FUNCIONARIO_ENCERRAMENTO_EXEC = "FUNCIONARIO_ENCERRAMENTO"
_COL_ID_USUARIO_ENCERRAMENTO_EXEC = "ID_USUARIO_ENCERRAMENTO"

# Reutiliza helpers de data já definidos no módulo
_ag_to_date = _to_date
_ag_data_no_periodo = _data_no_periodo


def _nome_em_conjunto_exec_rj(nome: str, conjunto: frozenset[str] | None) -> bool:
    if not conjunto:
        return True
    chave = nome.casefold()
    return any(chave == x.casefold() for x in conjunto)


def _get_ag_status_rj(item: dict[str, Any]) -> str | None:
    raw = item.get("STATUS") or item.get("status")
    if raw is None or not str(raw).strip():
        return None
    return str(raw).strip()


def _get_ag_data_criacao_rj(item: dict[str, Any]) -> Optional[date]:
    return _ag_to_date(item.get("DATA_HORA_CRIACAO") or item.get("data_hora_criacao"))


def _get_ag_data_conclusao_rj(item: dict[str, Any]) -> Optional[date]:
    return _ag_to_date(item.get("DATA_HORA_CONCLUSAO") or item.get("data_hora_conclusao"))


def _get_ag_prazo_rj(item: dict[str, Any]) -> Optional[date]:
    return _ag_to_date(item.get("PRAZO") or item.get("prazo"))


def _get_ag_processo_id_rj(item: dict[str, Any]) -> Any | None:
    return item.get("processo_id") or item.get("PROCESSO_ID")


def _get_ag_atividade_nome_rj(item: dict[str, Any]) -> str:
    raw = item.get("ATIVIDADE") or item.get("atividade")
    if raw is None or not str(raw).strip():
        return _SEM_ATIVIDADE_EXEC
    return str(raw).strip()


def _get_ag_funcionario_atribuido_rj(item: dict[str, Any]) -> str:
    raw = (
        item.get(_COL_FUNCIONARIO_ATRIBUIDO_EXEC)
        or item.get("FUNCIONARIO")
        or item.get("funcionario")
    )
    if raw is None or not str(raw).strip():
        return _SEM_FUNCIONARIO_EXEC
    return str(raw).strip()


def _get_ag_funcionario_encerramento_rj(item: dict[str, Any]) -> str | None:
    uid = item.get(_COL_ID_USUARIO_ENCERRAMENTO_EXEC) or item.get("id_usuario_encerramento")
    if uid is None or (isinstance(uid, str) and not str(uid).strip()):
        return None
    raw = item.get(_COL_FUNCIONARIO_ENCERRAMENTO_EXEC) or item.get("funcionario_encerramento")
    if raw is not None and str(raw).strip():
        return str(raw).strip()
    return None


def _get_ag_funcionario_nome_rj(item: dict[str, Any]) -> str:
    status = _get_ag_status_rj(item) or ""
    if status in _STATUS_ENCERRADO_EXEC:
        encerrador = _get_ag_funcionario_encerramento_rj(item)
        if encerrador:
            return encerrador
    return _get_ag_funcionario_atribuido_rj(item)


def _incluir_na_lista_exec_rj(
    row: dict[str, Any],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> bool:
    criacao = _get_ag_data_criacao_rj(row)
    conclusao = _get_ag_data_conclusao_rj(row)
    status = _get_ag_status_rj(row) or ""
    prazo = _get_ag_prazo_rj(row)
    ref = ref_date or date.today()
    if _ag_data_no_periodo(criacao, from_date, to_date):
        return True
    if status in _STATUS_ENCERRADO_EXEC:
        return _ag_data_no_periodo(conclusao, from_date, to_date)
    if status not in _STATUS_INATIVO_EXEC and prazo is not None and prazo <= ref:
        return True
    return False


def _classificar_situacao_exec_rj(
    row: dict[str, Any],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, bool]:
    ref = ref_date or date.today()
    criacao = _get_ag_data_criacao_rj(row)
    conclusao = _get_ag_data_conclusao_rj(row)
    status = _get_ag_status_rj(row) or ""
    prazo = _get_ag_prazo_rj(row)
    criada_periodo = _ag_data_no_periodo(criacao, from_date, to_date)
    ativo = status not in _STATUS_INATIVO_EXEC
    em_andamento = status in _STATUS_EM_ANDAMENTO_EXEC and criada_periodo
    vencida = ativo and prazo is not None and prazo < ref
    vence_hoje = ativo and prazo is not None and prazo == ref
    concluida = (
        status in _STATUS_ENCERRADO_EXEC
        and _ag_data_no_periodo(conclusao, from_date, to_date)
    )
    return {
        "em_andamento": em_andamento,
        "vencida": vencida,
        "vence_hoje": vence_hoje,
        "concluida": concluida,
    }


def _filtrar_ag_encerrados_no_periodo_rj(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    exigir_encerrador: bool = False,
) -> list[dict[str, Any]]:
    resultado = []
    for row in agendamentos:
        status = _get_ag_status_rj(row) or ""
        if status not in _STATUS_ENCERRADO_EXEC:
            continue
        if exigir_encerrador and _get_ag_funcionario_encerramento_rj(row) is None:
            continue
        conclusao = _get_ag_data_conclusao_rj(row)
        if _ag_data_no_periodo(conclusao, from_date, to_date):
            resultado.append(row)
    return resultado


def get_kpis_atividades_execucao_acordos_RJ(
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
        criacao = _get_ag_data_criacao_rj(row)
        conclusao = _get_ag_data_conclusao_rj(row)
        status = _get_ag_status_rj(row) or ""
        prazo = _get_ag_prazo_rj(row)
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
        "total_atividades_execucao_acordos_RJ": total,
        "atividades_execucao_em_andamento_acordos_RJ": em_andamento,
        "atividades_execucao_vencidas_acordos_RJ": vencidas,
        "atividades_execucao_vencem_hoje_acordos_RJ": vencem_hoje,
        "atividades_execucao_concluidas_acordos_RJ": concluidas,
    }


def get_media_mensal_atividades_execucao_acordos_RJ(agendamentos: list[dict[str, Any]]) -> float:
    """
    Média mensal de agendamentos criados (DATA_HORA_CRIACAO), considerando o
    histórico completo da lista informada (independente do período selecionado).

    Usado para medir o ritmo médio de entrada de uma atividade específica (ex.:
    "Elaborar Cumprimento de Sentença"), a partir de `agendamentos` já restrito
    por :func:`filtrar_agendamentos_execucao_acordos_RJ`.
    """
    meses: defaultdict[str, int] = defaultdict(int)
    for row in agendamentos:
        criacao = _get_ag_data_criacao_rj(row)
        if criacao is None:
            continue
        meses[f"{criacao.year}-{criacao.month:02d}"] += 1
    if not meses:
        return 0.0
    total = sum(meses.values())
    return round(total / len(meses), 2)


def group_execucao_processos_por_atividade_acordos_RJ(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Processos distintos por atividade (agendamentos criados no período) — LA."""
    base = [
        row for row in agendamentos
        if _ag_data_no_periodo(_get_ag_data_criacao_rj(row), from_date, to_date)
    ]
    grouped: dict[str, set[Any]] = defaultdict(set)
    for row in base:
        pid = _get_ag_processo_id_rj(row)
        if pid is None:
            continue
        grouped[_get_ag_atividade_nome_rj(row)].add(pid)

    total = float(sum(len(v) for v in grouped.values()))
    itens: list[dict[str, Any]] = []
    for nome, processos in grouped.items():
        qtd = len(processos)
        itens.append({
            "name": nome,
            "value": float(qtd),
            "percent": round(100.0 * float(qtd) / total, 1) if total > 0 else 0.0,
        })
    return sorted(itens, key=lambda x: float(x["value"]), reverse=True)


def group_atividades_ativas_criadas_por_atividade_acordos_RJ(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Quantidade de agendamentos ATIVOS (status fora de `_STATUS_INATIVO_EXEC`)
    criados no período, agrupados por atividade.

    Mesmo critério de contagem do card "Total de atividades"
    (:func:`get_kpis_atividades_execucao_acordos_RJ`), porém quebrado por nome da
    atividade — ao contrário de :func:`group_execucao_processos_por_atividade_acordos_RJ`,
    que conta processos distintos (não agendamentos) e não filtra por status.
    """
    contagem: defaultdict[str, int] = defaultdict(int)
    for row in agendamentos:
        status = _get_ag_status_rj(row) or ""
        if status in _STATUS_INATIVO_EXEC:
            continue
        criacao = _get_ag_data_criacao_rj(row)
        if not _ag_data_no_periodo(criacao, from_date, to_date):
            continue
        contagem[_get_ag_atividade_nome_rj(row)] += 1

    total = float(sum(contagem.values()))
    itens = [
        {
            "name": nome,
            "value": float(qtd),
            "percent": round(100.0 * float(qtd) / total, 1) if total > 0 else 0.0,
        }
        for nome, qtd in contagem.items()
    ]
    return sorted(itens, key=lambda x: float(x["value"]), reverse=True)


def group_atividades_ativas_por_prazo_por_atividade_acordos_RJ(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Quantidade de agendamentos ATIVOS com PRAZO no período, agrupados por
    atividade.

    Mesmo critério de contagem do "Total" na visão "Por prazo"
    (:func:`get_kpis_execucao_por_prazo_acordos_RJ`), porém quebrado por nome da
    atividade.
    """
    contagem: defaultdict[str, int] = defaultdict(int)
    for row in agendamentos:
        status = _get_ag_status_rj(row) or ""
        if status in _STATUS_INATIVO_EXEC:
            continue
        prazo = _get_ag_prazo_rj(row)
        if not _ag_data_no_periodo(prazo, from_date, to_date):
            continue
        contagem[_get_ag_atividade_nome_rj(row)] += 1

    total = float(sum(contagem.values()))
    itens = [
        {
            "name": nome,
            "value": float(qtd),
            "percent": round(100.0 * float(qtd) / total, 1) if total > 0 else 0.0,
        }
        for nome, qtd in contagem.items()
    ]
    return sorted(itens, key=lambda x: float(x["value"]), reverse=True)


def group_execucao_demandas_por_funcionario_acordos_RJ(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Demandas encerradas por funcionário (Cumprido / Não Cumprido) no período — LA."""
    base = _filtrar_ag_encerrados_no_periodo_rj(
        agendamentos, from_date, to_date, exigir_encerrador=True
    )
    grouped: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in base:
        funcionario = _get_ag_funcionario_encerramento_rj(row)
        if not funcionario:
            continue
        status = _get_ag_status_rj(row) or ""
        slug = _SLUG_POR_STATUS_EXEC_RJ.get(status)
        if slug is None:
            continue
        grouped[funcionario][slug] += 1

    itens: list[dict[str, Any]] = []
    for nome, contagens in grouped.items():
        item: dict[str, Any] = {"name": nome}
        total = 0
        for slug, _ in _STATUS_DEMANDAS_FUNCIONARIO_EXEC_RJ:
            valor = int(contagens.get(slug, 0))
            item[slug] = valor
            total += valor
        item["total"] = total
        if total > 0:
            itens.append(item)
    return sorted(itens, key=lambda x: int(x["total"]), reverse=True)


_SEM_FUNCIONARIO_ENCERRAMENTO_EXEC_RJ = "Sem funcionário identificado"


def group_execucao_demandas_por_funcionario_completo_acordos_RJ(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Demandas encerradas por funcionário (Cumprido / Não Cumprido) no período —
    LA, incluindo uma linha "Sem funcionário identificado" para agendamentos
    encerrados sem usuário de encerramento registrado.

    Ao contrário de :func:`group_execucao_demandas_por_funcionario_acordos_RJ` (que
    descarta esses agendamentos), a soma deste resultado sempre bate com
    ``atividades_execucao_concluidas_acordos_RJ`` (:func:`get_kpis_atividades_execucao_acordos_RJ`).
    """
    base = _filtrar_ag_encerrados_no_periodo_rj(agendamentos, from_date, to_date)
    grouped: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in base:
        funcionario = _get_ag_funcionario_encerramento_rj(row) or _SEM_FUNCIONARIO_ENCERRAMENTO_EXEC_RJ
        status = _get_ag_status_rj(row) or ""
        slug = _SLUG_POR_STATUS_EXEC_RJ.get(status)
        if slug is None:
            continue
        grouped[funcionario][slug] += 1

    itens: list[dict[str, Any]] = []
    for nome, contagens in grouped.items():
        item: dict[str, Any] = {"name": nome}
        total = 0
        for slug, _ in _STATUS_DEMANDAS_FUNCIONARIO_EXEC_RJ:
            valor = int(contagens.get(slug, 0))
            item[slug] = valor
            total += valor
        item["total"] = total
        if total > 0:
            itens.append(item)
    return sorted(itens, key=lambda x: int(x["total"]), reverse=True)


def group_execucao_resolvidos_por_dia_acordos_RJ(
    agendamentos: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Produção diária: quantidade de atividades "Encerrado Cumprido" por dia de
    conclusão (DATA_HORA_CONCLUSAO), histórico completo — LA. O filtro por
    período (calendário do dashboard) é aplicado no frontend, como em
    :func:`group_resolvidos_por_dia` do domínio OrgDoc.
    """
    grouped: dict[str, int] = defaultdict(int)
    for row in agendamentos:
        if _get_ag_status_rj(row) != _STATUS_CUMPRIDO_EXEC:
            continue
        conclusao = _get_ag_data_conclusao_rj(row)
        if conclusao is None:
            continue
        grouped[conclusao.strftime("%Y-%m-%d")] += 1

    return [
        {"name": dia, "value": count}
        for dia, count in sorted(grouped.items(), key=lambda x: x[0])
    ]


def get_media_execucao_resolvidos_por_funcionario_acordos_RJ(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Média de atividades "Encerrado Cumprido" por funcionário no período — LA.

    Média = total de atividades cumpridas ÷ número de dias distintos com
    conclusão no período (mesmo critério de
    :func:`get_media_resolvidos_por_funcionario` do domínio OrgDoc).
    """
    grouped: dict[str, dict[str, Any]] = defaultdict(lambda: {"total": 0, "dias": set()})
    for row in agendamentos:
        if _get_ag_status_rj(row) != _STATUS_CUMPRIDO_EXEC:
            continue
        conclusao = _get_ag_data_conclusao_rj(row)
        if conclusao is None or not _ag_data_no_periodo(conclusao, from_date, to_date):
            continue
        funcionario = _get_ag_funcionario_encerramento_rj(row)
        if not funcionario:
            continue
        grouped[funcionario]["total"] += 1
        grouped[funcionario]["dias"].add(conclusao)

    itens: list[dict[str, Any]] = []
    for nome, info in grouped.items():
        dias = len(info["dias"])
        if dias == 0:
            continue
        itens.append({"name": nome, "value": round(info["total"] / dias, 2)})
    return sorted(itens, key=lambda x: x["value"], reverse=True)



def list_execucao_atividades_periodo_acordos_RJ(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Lista de agendamentos do setor Execução LA para a tabela de tarefas."""
    ref = ref_date or date.today()
    itens: list[dict[str, Any]] = []

    for row in agendamentos:
        if not _incluir_na_lista_exec_rj(row, from_date, to_date, ref_date=ref):
            continue
        ag_id = _to_int(row.get("id") or row.get("ID"))
        if ag_id is None:
            continue
        status = _get_ag_status_rj(row) or "—"
        prazo = _get_ag_prazo_rj(row)
        criacao = _get_ag_data_criacao_rj(row)
        situacao = _classificar_situacao_exec_rj(row, from_date, to_date, ref_date=ref)
        funcionario_atrib = _get_ag_funcionario_atribuido_rj(row)
        funcionario_enc = _get_ag_funcionario_encerramento_rj(row)
        encerrado_pelo_responsavel: bool | None = None
        if status in _STATUS_ENCERRADO_EXEC and funcionario_enc is not None:
            encerrado_pelo_responsavel = (
                funcionario_enc.strip().lower() == funcionario_atrib.strip().lower()
            )
        setor = str(row.get("SETOR") or row.get("setor") or "EXECUÇÃO").strip().upper()
        atividade = _get_ag_atividade_nome_rj(row)
        pessoa_setor = (
            f"{setor} - {atividade}"
            if atividade and atividade != _SEM_ATIVIDADE_EXEC
            else setor
        )
        descricao_raw = row.get("DESCRICAO") or row.get("descricao")
        descricao = str(descricao_raw).strip().upper() if descricao_raw else "—"
        operacao = str(row.get("OPERACAO") or row.get("operacao") or "").strip()

        itens.append({
            "id": ag_id,
            "status": status,
            "descricao": descricao,
            "pessoa_setor": pessoa_setor,
            "funcionario": _get_ag_funcionario_nome_rj(row),
            "funcionario_atribuido": funcionario_atrib,
            "funcionario_encerramento": funcionario_enc,
            "atividade": atividade,
            "prazo": prazo.isoformat() if prazo else None,
            "criado_em": criacao.isoformat() if criacao else None,
            "operacao": operacao,
            "encerrado_pelo_responsavel": encerrado_pelo_responsavel,
            **situacao,
        })

    def _sort_key(item: dict[str, Any]) -> tuple[int, str, int]:
        prazo_raw = item.get("prazo")
        prazo_missing = 0 if prazo_raw else 1
        return (prazo_missing, str(prazo_raw or ""), int(item.get("id") or 0))

    return sorted(itens, key=_sort_key)


def get_opcoes_filtros_execucao_acordos_RJ(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, Any]:
    """Opções de filtros da lista de tarefas — LA."""
    rows = list_execucao_atividades_periodo_acordos_RJ(
        agendamentos, from_date=from_date, to_date=to_date, ref_date=ref_date
    )
    funcionarios: set[str] = set()
    atividades: set[str] = set()
    status_vistos: set[str] = set()

    for row in rows:
        funcionarios.add(str(row.get("funcionario") or _SEM_FUNCIONARIO_EXEC))
        atividade = str(row.get("atividade") or "").strip()
        if atividade and atividade != _SEM_ATIVIDADE_EXEC:
            atividades.add(atividade)
        status = str(row.get("status") or "").strip()
        if status and status != "—":
            status_vistos.add(status)

    status_ordenados: list[str] = []
    for label in _STATUS_FILTRO_EXEC:
        if label in status_vistos:
            status_ordenados.append(label)
    for label in sorted(status_vistos - set(status_ordenados), key=lambda x: x.casefold()):
        status_ordenados.append(label)

    return {
        "funcionarios": sorted(funcionarios, key=lambda x: x.casefold()),
        "atividades": sorted(atividades, key=lambda x: x.casefold()),
        "status": status_ordenados,
        "situacoes": [
            {"id": sid, "label": label} for sid, label in _SITUACOES_FILTRO_EXEC_RJ
        ],
    }


def _agendamento_match_filtros_exec_rj(
    row: dict[str, Any],
    filtros: Any,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> bool:
    if filtros.funcionarios is not None:
        funcionario = _get_ag_funcionario_nome_rj(row)
        if not _nome_em_conjunto_exec_rj(funcionario, filtros.funcionarios):
            return False
    if filtros.atividades is not None:
        atividade = _get_ag_atividade_nome_rj(row)
        if not _nome_em_conjunto_exec_rj(atividade, filtros.atividades):
            return False
    if filtros.status is not None:
        status = (_get_ag_status_rj(row) or "—").strip()
        if not _nome_em_conjunto_exec_rj(status, filtros.status):
            return False
    if filtros.situacoes is not None:
        flags = _classificar_situacao_exec_rj(row, from_date, to_date, ref_date=ref_date)
        if not any(flags.get(_SITUACAO_ID_PARA_FLAG_RJ.get(sid, sid)) for sid in filtros.situacoes):
            return False
    return True


def filtrar_agendamentos_execucao_acordos_RJ(
    agendamentos: list[dict[str, Any]],
    filtros: Any,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Restringe agendamentos LA aos filtros cumulativos."""
    if filtros is None or not filtros.ativo():
        return agendamentos
    return [
        row for row in agendamentos
        if _agendamento_match_filtros_exec_rj(row, filtros, from_date, to_date, ref_date=ref_date)
    ]


# ---------------------------------------------------------------------------
# Análise por Prazo — LA (mesmas 5 métricas, mas usando PRAZO como eixo
# temporal em vez de DATA_HORA_CRIACAO/DATA_HORA_CONCLUSAO). Mesmo padrão de
# analyses/LA/pendencias_intermediarias_RJ.py.
# ---------------------------------------------------------------------------

def _incluir_na_lista_por_prazo_exec_rj(
    row: dict[str, Any],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> bool:
    prazo = _get_ag_prazo_rj(row)
    return _ag_data_no_periodo(prazo, from_date, to_date)


def _classificar_situacao_por_prazo_exec_rj(
    row: dict[str, Any],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, bool]:
    ref = ref_date or date.today()
    prazo = _get_ag_prazo_rj(row)
    status = _get_ag_status_rj(row) or ""
    ativo = status not in _STATUS_INATIVO_EXEC
    prazo_no_periodo = _ag_data_no_periodo(prazo, from_date, to_date)
    em_andamento = status in _STATUS_EM_ANDAMENTO_EXEC and prazo_no_periodo
    vencida = ativo and prazo_no_periodo and prazo is not None and prazo < ref
    vence_hoje = ativo and prazo_no_periodo and prazo is not None and prazo == ref
    concluida = status in _STATUS_ENCERRADO_EXEC and prazo_no_periodo
    return {
        "em_andamento": em_andamento,
        "vencida": vencida,
        "vence_hoje": vence_hoje,
        "concluida": concluida,
    }


def get_kpis_execucao_por_prazo_acordos_RJ(
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
        prazo = _get_ag_prazo_rj(row)
        status = _get_ag_status_rj(row) or ""
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
        "total_por_prazo_execucao_acordos_RJ": total,
        "por_prazo_em_andamento_execucao_acordos_RJ": em_andamento,
        "por_prazo_vencidas_execucao_acordos_RJ": vencidas,
        "por_prazo_vencem_hoje_execucao_acordos_RJ": vencem_hoje,
        "por_prazo_concluidas_execucao_acordos_RJ": concluidas,
    }


def group_execucao_processos_por_atividade_por_prazo_acordos_RJ(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Processos distintos por atividade (agendamentos com prazo no período) — LA."""
    base = [
        row for row in agendamentos
        if _ag_data_no_periodo(_get_ag_prazo_rj(row), from_date, to_date)
    ]
    grouped: dict[str, set[Any]] = defaultdict(set)
    for row in base:
        pid = _get_ag_processo_id_rj(row)
        if pid is None:
            continue
        grouped[_get_ag_atividade_nome_rj(row)].add(pid)

    total = float(sum(len(v) for v in grouped.values()))
    itens: list[dict[str, Any]] = []
    for nome, processos in grouped.items():
        qtd = len(processos)
        itens.append({
            "name": nome,
            "value": float(qtd),
            "percent": round(100.0 * float(qtd) / total, 1) if total > 0 else 0.0,
        })
    return sorted(itens, key=lambda x: float(x["value"]), reverse=True)


def group_execucao_demandas_por_funcionario_por_prazo_acordos_RJ(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Demandas encerradas por funcionário (Cumprido / Não Cumprido), com PRAZO no período — LA."""
    base = [
        row for row in agendamentos
        if (_get_ag_status_rj(row) or "") in _STATUS_ENCERRADO_EXEC
        and _ag_data_no_periodo(_get_ag_prazo_rj(row), from_date, to_date)
        and _get_ag_funcionario_encerramento_rj(row) is not None
    ]
    grouped: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in base:
        funcionario = _get_ag_funcionario_encerramento_rj(row)
        if not funcionario:
            continue
        status = _get_ag_status_rj(row) or ""
        slug = _SLUG_POR_STATUS_EXEC_RJ.get(status)
        if slug is None:
            continue
        grouped[funcionario][slug] += 1

    itens: list[dict[str, Any]] = []
    for nome, contagens in grouped.items():
        item: dict[str, Any] = {"name": nome}
        total = 0
        for slug, _ in _STATUS_DEMANDAS_FUNCIONARIO_EXEC_RJ:
            valor = int(contagens.get(slug, 0))
            item[slug] = valor
            total += valor
        item["total"] = total
        if total > 0:
            itens.append(item)
    return sorted(itens, key=lambda x: int(x["total"]), reverse=True)


def group_execucao_demandas_por_funcionario_por_prazo_completo_acordos_RJ(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Demandas encerradas por funcionário (Cumprido / Não Cumprido), com PRAZO no
    período — LA, incluindo uma linha "Sem funcionário identificado" para
    agendamentos encerrados sem usuário de encerramento registrado.

    Ao contrário de :func:`group_execucao_demandas_por_funcionario_por_prazo_acordos_RJ`
    (que descarta esses agendamentos), a soma deste resultado sempre bate com
    ``por_prazo_concluidas_execucao_acordos_RJ`` (:func:`get_kpis_execucao_por_prazo_acordos_RJ`).
    """
    base = [
        row for row in agendamentos
        if (_get_ag_status_rj(row) or "") in _STATUS_ENCERRADO_EXEC
        and _ag_data_no_periodo(_get_ag_prazo_rj(row), from_date, to_date)
    ]
    grouped: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in base:
        funcionario = _get_ag_funcionario_encerramento_rj(row) or _SEM_FUNCIONARIO_ENCERRAMENTO_EXEC_RJ
        status = _get_ag_status_rj(row) or ""
        slug = _SLUG_POR_STATUS_EXEC_RJ.get(status)
        if slug is None:
            continue
        grouped[funcionario][slug] += 1

    itens: list[dict[str, Any]] = []
    for nome, contagens in grouped.items():
        item: dict[str, Any] = {"name": nome}
        total = 0
        for slug, _ in _STATUS_DEMANDAS_FUNCIONARIO_EXEC_RJ:
            valor = int(contagens.get(slug, 0))
            item[slug] = valor
            total += valor
        item["total"] = total
        if total > 0:
            itens.append(item)
    return sorted(itens, key=lambda x: int(x["total"]), reverse=True)


def list_execucao_atividades_por_prazo_periodo_acordos_RJ(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Lista de agendamentos do setor Execução LA filtrados pelo PRAZO para a tabela de tarefas."""
    ref = ref_date or date.today()
    itens: list[dict[str, Any]] = []

    for row in agendamentos:
        if not _incluir_na_lista_por_prazo_exec_rj(row, from_date, to_date, ref_date=ref):
            continue
        ag_id = _to_int(row.get("id") or row.get("ID"))
        if ag_id is None:
            continue
        status = _get_ag_status_rj(row) or "—"
        prazo = _get_ag_prazo_rj(row)
        criacao = _get_ag_data_criacao_rj(row)
        situacao = _classificar_situacao_por_prazo_exec_rj(row, from_date, to_date, ref_date=ref)
        funcionario_atrib = _get_ag_funcionario_atribuido_rj(row)
        funcionario_enc = _get_ag_funcionario_encerramento_rj(row)
        encerrado_pelo_responsavel: bool | None = None
        if status in _STATUS_ENCERRADO_EXEC and funcionario_enc is not None:
            encerrado_pelo_responsavel = (
                funcionario_enc.strip().lower() == funcionario_atrib.strip().lower()
            )
        setor = str(row.get("SETOR") or row.get("setor") or "EXECUÇÃO").strip().upper()
        atividade = _get_ag_atividade_nome_rj(row)
        pessoa_setor = (
            f"{setor} - {atividade}"
            if atividade and atividade != _SEM_ATIVIDADE_EXEC
            else setor
        )
        descricao_raw = row.get("DESCRICAO") or row.get("descricao")
        descricao = str(descricao_raw).strip().upper() if descricao_raw else "—"
        operacao = str(row.get("OPERACAO") or row.get("operacao") or "").strip()

        itens.append({
            "id": ag_id,
            "status": status,
            "descricao": descricao,
            "pessoa_setor": pessoa_setor,
            "funcionario": _get_ag_funcionario_nome_rj(row),
            "funcionario_atribuido": funcionario_atrib,
            "funcionario_encerramento": funcionario_enc,
            "atividade": atividade,
            "prazo": prazo.isoformat() if prazo else None,
            "criado_em": criacao.isoformat() if criacao else None,
            "operacao": operacao,
            "encerrado_pelo_responsavel": encerrado_pelo_responsavel,
            **situacao,
        })

    def _sort_key(item: dict[str, Any]) -> tuple[int, str, int]:
        prazo_raw = item.get("prazo")
        prazo_missing = 0 if prazo_raw else 1
        return (prazo_missing, str(prazo_raw or ""), int(item.get("id") or 0))

    return sorted(itens, key=_sort_key)


def get_opcoes_filtros_execucao_por_prazo_acordos_RJ(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, Any]:
    """Opções de filtros da lista por prazo — LA."""
    rows = list_execucao_atividades_por_prazo_periodo_acordos_RJ(
        agendamentos, from_date=from_date, to_date=to_date, ref_date=ref_date
    )
    funcionarios: set[str] = set()
    atividades: set[str] = set()
    status_vistos: set[str] = set()

    for row in rows:
        funcionarios.add(str(row.get("funcionario") or _SEM_FUNCIONARIO_EXEC))
        atividade = str(row.get("atividade") or "").strip()
        if atividade and atividade != _SEM_ATIVIDADE_EXEC:
            atividades.add(atividade)
        status = str(row.get("status") or "").strip()
        if status and status != "—":
            status_vistos.add(status)

    status_ordenados: list[str] = []
    for label in _STATUS_FILTRO_EXEC:
        if label in status_vistos:
            status_ordenados.append(label)
    for label in sorted(status_vistos - set(status_ordenados), key=lambda x: x.casefold()):
        status_ordenados.append(label)

    return {
        "funcionarios": sorted(funcionarios, key=lambda x: x.casefold()),
        "atividades": sorted(atividades, key=lambda x: x.casefold()),
        "status": status_ordenados,
        "situacoes": [
            {"id": sid, "label": label} for sid, label in _SITUACOES_FILTRO_EXEC_RJ
        ],
    }


def group_execucao_resolvidos_por_dia_por_prazo_acordos_RJ(
    agendamentos: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Produção diária (por prazo): quantidade de atividades "Encerrado Cumprido"
    por dia de PRAZO, histórico completo — LA.
    """
    grouped: dict[str, int] = defaultdict(int)
    for row in agendamentos:
        if _get_ag_status_rj(row) != _STATUS_CUMPRIDO_EXEC:
            continue
        prazo = _get_ag_prazo_rj(row)
        if prazo is None:
            continue
        grouped[prazo.strftime("%Y-%m-%d")] += 1

    return [
        {"name": dia, "value": count}
        for dia, count in sorted(grouped.items(), key=lambda x: x[0])
    ]


def get_media_execucao_resolvidos_por_funcionario_por_prazo_acordos_RJ(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Média de atividades "Encerrado Cumprido" por funcionário no período,
    usando PRAZO como eixo temporal — LA.
    """
    grouped: dict[str, dict[str, Any]] = defaultdict(lambda: {"total": 0, "dias": set()})
    for row in agendamentos:
        if _get_ag_status_rj(row) != _STATUS_CUMPRIDO_EXEC:
            continue
        prazo = _get_ag_prazo_rj(row)
        if prazo is None or not _ag_data_no_periodo(prazo, from_date, to_date):
            continue
        funcionario = _get_ag_funcionario_encerramento_rj(row)
        if not funcionario:
            continue
        grouped[funcionario]["total"] += 1
        grouped[funcionario]["dias"].add(prazo)

    itens: list[dict[str, Any]] = []
    for nome, info in grouped.items():
        dias = len(info["dias"])
        if dias == 0:
            continue
        itens.append({"name": nome, "value": round(info["total"] / dias, 2)})
    return sorted(itens, key=lambda x: x["value"], reverse=True)


# ---------------------------------------------------------------------------
# Motivo de "Encerrado Não Cumprido" — LA
# ---------------------------------------------------------------------------

def _get_ag_motivo_encaminhamento_itens_rj(item: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Lê e faz parse de MOTIVO_ENCAMINHAMENTO (jsonb serializado como texto,
    formato ``{"itens": [{"motivo": "...", ...}, ...]}``).
    """
    raw = item.get("MOTIVO_ENCAMINHAMENTO") or item.get("motivo_encaminhamento")
    if not raw:
        return []
    try:
        parsed = json.loads(raw) if isinstance(raw, str) else raw
    except (TypeError, ValueError):
        return []
    if not isinstance(parsed, dict):
        return []
    itens = parsed.get("itens")
    return itens if isinstance(itens, list) else []


def group_execucao_nao_cumprido_por_motivo_acordos_RJ(
    agendamentos: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Agrupa as atividades "Encerrado Não Cumprido" pelo motivo registrado no
    encaminhamento (MOTIVO_ENCAMINHAMENTO), histórico completo — LA.

    Ignora agendamentos sem motivo registrado (campo pode não estar
    preenchido dependendo de como a atividade foi encerrada no LEXFLOW).
    """
    grouped: dict[str, int] = defaultdict(int)
    for row in agendamentos:
        if _get_ag_status_rj(row) != "Encerrado Não Cumprido":
            continue
        for it in _get_ag_motivo_encaminhamento_itens_rj(row):
            motivo = str(it.get("motivo") or "").strip()
            if not motivo:
                continue
            grouped[motivo] += 1

    total = float(sum(grouped.values()))
    itens: list[dict[str, Any]] = [
        {
            "name": motivo,
            "value": float(qtd),
            "percent": round(100.0 * float(qtd) / total, 1) if total > 0 else 0.0,
        }
        for motivo, qtd in grouped.items()
    ]
    return sorted(itens, key=lambda x: float(x["value"]), reverse=True)


# ---------------------------------------------------------------------------
# Detalhamento de atrasos (vencidas por dias de atraso) — LA
# ---------------------------------------------------------------------------

_ATRASO_MAX_BUCKET_RJ = 6

_BUCKET_META_RJ: dict[int, tuple[str, str]] = {
    1: ("1 dia",          "Venceu ontem"),
    2: ("2 dias",         "Há 2 dias de atraso"),
    3: ("3 dias",         "Há 3 dias de atraso"),
    4: ("4 dias",         "Há 4 dias de atraso"),
    5: ("5 dias",         "Há 5 dias de atraso"),
    6: ("6 dias ou mais", "Atraso prolongado"),
}


def get_atrasos_detalhamento_execucao_acordos_RJ(
    agendamentos: list[dict[str, Any]],
    *,
    ref_date: Optional[date] = None,
) -> dict[str, Any]:
    """Detalhamento de agendamentos vencidos por dias de atraso (1–5 e 6+) — LA."""
    ref = ref_date or date.today()
    counts: dict[int, int] = {d: 0 for d in range(1, _ATRASO_MAX_BUCKET_RJ + 1)}

    for row in agendamentos:
        status = _get_ag_status_rj(row) or ""
        if status in _STATUS_INATIVO_EXEC:
            continue
        prazo = _get_ag_prazo_rj(row)
        if prazo is None or prazo >= ref:
            continue
        dias = (ref - prazo).days
        bucket = min(dias, _ATRASO_MAX_BUCKET_RJ)
        counts[bucket] += 1

    total = sum(counts.values())

    buckets = []
    for dias in range(1, _ATRASO_MAX_BUCKET_RJ + 1):
        count = counts[dias]
        pct = round(100.0 * count / total, 1) if total > 0 else 0.0
        label, descricao = _BUCKET_META_RJ[dias]
        buckets.append({
            "dias": dias,
            "label": label,
            "descricao": descricao,
            "count": count,
            "pct": pct,
        })

    return {"total": total, "buckets": buckets}


# =============================================================================
# 8 - Diligências (subconjunto de agendamentos do setor ACORDOS)
# =============================================================================
#
# Diligência é um tipo de agendamento dentro do setor ACORDOS (ex.: "DILIGÊNCIA
# PARA HOMOLOGAÇÃO + REMESSA 2", "DILIGÊNCIA PARA EXPEDIÇÃO DE ALVARÁ DE ACORDO
# JUDICIAL 1"), identificado pelo nome da atividade conter "DILIG". Um mesmo
# processo pode ter a diligência agendada mais de uma vez ao longo do tempo.

def _eh_diligencia_acordos_rj(item: dict[str, Any]) -> bool:
    atividade = str(item.get("ATIVIDADE") or item.get("atividade") or "").upper()
    return "DILIG" in atividade


def filtrar_agendamentos_diligencia_acordos_RJ(
    agendamentos: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Restringe agendamentos do setor ACORDOS aos que são diligência."""
    return [row for row in agendamentos if _eh_diligencia_acordos_rj(row)]


def get_total_diligencias_execucao_acordos_RJ(
    agendamentos_diligencia: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """Total de agendamentos de diligência criados no período."""
    return sum(
        1 for row in agendamentos_diligencia
        if _ag_data_no_periodo(_get_ag_data_criacao_rj(row), from_date, to_date)
    )


def group_execucao_acordos_diligencias_por_processo_RJ(
    agendamentos_diligencia: list[dict[str, Any]],
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Quantidade de agendamentos de diligência por processo, no período informado
    (DATA_HORA_CRIACAO), com o valor de alçada final do processo (``valor_execucao``).
    Um processo pode aparecer com quantidade > 1 quando a diligência foi feita
    mais de uma vez nele.
    """
    contagem: defaultdict[Any, int] = defaultdict(int)
    for row in agendamentos_diligencia:
        if not _ag_data_no_periodo(_get_ag_data_criacao_rj(row), from_date, to_date):
            continue
        pid = _get_ag_processo_id_rj(row)
        if pid is None:
            continue
        contagem[pid] += 1

    numero_por_id: dict[Any, str] = {}
    valor_por_id: dict[Any, float] = {}
    for p in processos:
        pid = p.get("id") or p.get("ID")
        numero = p.get("NUMERO_PROCESSO")
        if pid is not None and numero:
            numero_por_id[pid] = str(numero)
        valor = p.get("VALOR_ALCADA_FINAL")
        if pid is not None and valor is not None:
            try:
                valor_por_id[pid] = float(valor)
            except (TypeError, ValueError):
                pass

    itens = [
        {
            "name": numero_por_id[pid],
            "value": int(qtd),
            "valor_execucao": valor_por_id.get(pid),
        }
        for pid, qtd in contagem.items()
        if pid in numero_por_id
    ]
    return sorted(itens, key=lambda x: x["value"], reverse=True)


def _eh_diligencia_expedicao_alvara_acordos_rj(item: dict[str, Any]) -> bool:
    atividade = str(item.get("ATIVIDADE") or item.get("atividade") or "").upper()
    return "EXPEDIÇÃO DE ALVARÁ" in atividade


def filtrar_agendamentos_diligencia_expedicao_alvara_acordos_RJ(
    agendamentos_diligencia: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Restringe agendamentos de diligência aos de expedição de alvará (ex.:
    "DILIGÊNCIA PARA EXPEDIÇÃO DE ALVARÁ DE ACORDO JUDICIAL 1/2", "DILIGÊNCIA
    PARA EXPEDIÇÃO DE ALVARÁ + HOMOLOGAÇÃO 1/2")."""
    return [
        row for row in agendamentos_diligencia
        if _eh_diligencia_expedicao_alvara_acordos_rj(row)
    ]


def get_kpis_diligencias_expedicao_alvara_acordos_RJ(
    agendamentos_expedicao_alvara: list[dict[str, Any]],
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    colaborador: Optional[str] = None,
) -> dict[str, Any]:
    """
    KPIs das diligências de expedição de alvará (subconjunto de diligências):
    - total: agendamentos criados no período;
    - cumpridas: agendamentos encerrados como "Encerrado Cumprido" no período;
    - valor: soma do VALOR_ALCADA_FINAL dos processos com diligência de
      expedição de alvará cumprida no período (deduplicado por processo, para
      não somar duas vezes o mesmo processo caso tenha mais de uma diligência
      cumprida).

    ``colaborador``, quando informado (clique no ranking por colaborador),
    restringe os 3 números a apenas as diligências encerradas por essa pessoa.
    """
    agendamentos_expedicao_alvara = filtrar_agendamentos_diligencia_por_colaborador_acordos_RJ(
        agendamentos_expedicao_alvara, colaborador
    )
    total = sum(
        1 for row in agendamentos_expedicao_alvara
        if _ag_data_no_periodo(_get_ag_data_criacao_rj(row), from_date, to_date)
    )

    cumpridas_rows, processos_cumpridos = _diligencias_expedicao_alvara_cumpridas_acordos_rj(
        agendamentos_expedicao_alvara, from_date, to_date
    )

    valor_por_id: dict[Any, float] = {}
    for p in processos:
        pid = p.get("id") or p.get("ID")
        valor = p.get("VALOR_ALCADA_FINAL")
        if pid is not None and valor is not None:
            try:
                valor_por_id[pid] = float(valor)
            except (TypeError, ValueError):
                pass

    valor = sum(valor_por_id.get(pid, 0.0) for pid in processos_cumpridos)

    return {"total": total, "cumpridas": len(cumpridas_rows), "valor": valor}


def _diligencias_expedicao_alvara_cumpridas_acordos_rj(
    agendamentos_expedicao_alvara: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> tuple[list[dict[str, Any]], set[Any]]:
    """Agendamentos de expedição de alvará cumpridos no período, e o conjunto
    (deduplicado) de processo_id correspondentes."""
    cumpridas_rows = [
        row for row in _filtrar_ag_encerrados_no_periodo_rj(
            agendamentos_expedicao_alvara, from_date, to_date
        )
        if _get_ag_status_rj(row) == _STATUS_CUMPRIDO_EXEC
    ]
    processos_cumpridos: set[Any] = {
        pid for row in cumpridas_rows
        if (pid := _get_ag_processo_id_rj(row)) is not None
    }
    return cumpridas_rows, processos_cumpridos


def list_processos_diligencia_expedicao_alvara_cumprida_acordos_RJ(
    agendamentos_expedicao_alvara: list[dict[str, Any]],
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    colaborador: Optional[str] = None,
) -> list[dict[str, Any]]:
    """
    Lista os processos que compõem o valor do card "Valor Realizado (Alvará)":
    processos com pelo menos uma diligência de expedição de alvará cumprida no
    período — mesma população/deduplicação de
    :func:`get_kpis_diligencias_expedicao_alvara_acordos_RJ`.

    ``colaborador``, quando informado, restringe aos processos cuja diligência
    de expedição de alvará foi cumprida por essa pessoa.
    """
    agendamentos_expedicao_alvara = filtrar_agendamentos_diligencia_por_colaborador_acordos_RJ(
        agendamentos_expedicao_alvara, colaborador
    )
    _, processos_cumpridos = _diligencias_expedicao_alvara_cumpridas_acordos_rj(
        agendamentos_expedicao_alvara, from_date, to_date
    )
    if not processos_cumpridos:
        return []

    processo_por_id: dict[Any, dict[str, Any]] = {}
    for p in processos:
        pid = p.get("id") or p.get("ID")
        if pid is not None:
            processo_por_id[pid] = p

    itens: list[dict[str, Any]] = []
    for pid in processos_cumpridos:
        p = processo_por_id.get(pid)
        if p is None:
            continue
        valor = _get_valor_alcada_final(p)
        data_execucao = _get_data_execucao_RJ(p)
        itens.append({
            "numero_processo": str(_get_numero_processo(p) or "").strip() or "—",
            "uf": str(p.get("UF") or "").strip().upper() or "—",
            "data_execucao": data_execucao.isoformat() if data_execucao else None,
            "valor_execucao": _converter_valor(valor) if valor is not None else None,
            "subfase": _normalizar_subfase(p.get("SUBFASE")),
        })
    return sorted(itens, key=lambda x: (x["valor_execucao"] or 0), reverse=True)


_TIPOS_VALIDOS_DILIGENCIA_ACORDOS_RJ = ("expedicao_alvara", "expedicao_alvara_cumprida")


def filtrar_agendamentos_diligencia_por_tipo_acordos_RJ(
    agendamentos_diligencia: list[dict[str, Any]],
    tipo: Optional[str] = None,
) -> list[dict[str, Any]]:
    """
    Filtra diligências pelo card clicado na seção Diligências:
    - "expedicao_alvara": só diligências de expedição de alvará (qualquer status);
    - "expedicao_alvara_cumprida": só as de expedição de alvará com status
      "Encerrado Cumprido";
    - None/outro valor: não filtra.
    """
    if tipo not in _TIPOS_VALIDOS_DILIGENCIA_ACORDOS_RJ:
        return agendamentos_diligencia
    base = filtrar_agendamentos_diligencia_expedicao_alvara_acordos_RJ(agendamentos_diligencia)
    if tipo == "expedicao_alvara_cumprida":
        base = [row for row in base if _get_ag_status_rj(row) == _STATUS_CUMPRIDO_EXEC]
    return base


def filtrar_agendamentos_diligencia_por_colaborador_acordos_RJ(
    agendamentos_diligencia: list[dict[str, Any]],
    colaborador: Optional[str] = None,
) -> list[dict[str, Any]]:
    """
    Filtra diligências pelo colaborador clicado no ranking (mesmo critério de
    agrupamento de :func:`group_execucao_demandas_por_funcionario_acordos_RJ`:
    quem encerrou a diligência).
    """
    if colaborador is None or not str(colaborador).strip():
        return agendamentos_diligencia
    alvo = str(colaborador).strip()
    return [
        row for row in agendamentos_diligencia
        if (_get_ag_funcionario_encerramento_rj(row) or "").strip() == alvo
    ]


def group_estoque_execucao_acordos_por_mes_RJ(
    execucao: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Estoque em Execução de Acordos ao fim de cada mês: (quantidade, valor de
    alçada final) — base do "Ticket Médio Total" mês a mês.

    Reconstrução histórica: o processo conta do mês de ``DATA_EXECUCAO`` até o
    mês anterior ao de ``DATA_PAGAMENTO_ACORDO``; sem pagamento, só conta se
    ainda está na fase de Acordo hoje (mesmo critério do card "Total em
    Execução").
    """
    intervalos = []
    for p in _base_execucao_acordos_RJ(execucao):
        entrada = _get_data_execucao_RJ(p)
        if entrada is None:
            continue
        saida = _get_data_pagamento_acordo(p)
        if saida is None and not _processo_na_fase_acordo(p):
            continue
        intervalos.append((
            indice_mes(entrada),
            indice_mes(saida) if saida is not None else None,
            True,
            _converter_valor(_get_valor_alcada_final(p)),
        ))
    return estoque_por_mes(intervalos, _MONTH_NAMES)
