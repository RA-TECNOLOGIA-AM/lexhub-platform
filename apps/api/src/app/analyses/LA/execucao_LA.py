# Funções de análises do setor de Execução

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from app.utils import parse_date_from_db
from app.analyses.execucao_estoque_mensal import estoque_por_mes, indice_mes


# =============================================================================
# Constantes
# =============================================================================

ID_FASE_EXECUCAO = 12
ID_FASE_FINANCEIRO = 26
ID_ESCRITORIO = 21
ID_SITUACAO_ATIVO = 1

_COL_ID_ESCRITORIO = "ID_ESCRITORIO"
_COL_ID_SITUACAO = "ID_SITUACAO"

SEM_DATA_ULTIMA_MOVIMENTACAO = "Sem data de movimentação"

_MONTH_NAMES = (
    "jan", "fev", "mar", "abr", "mai", "jun",
    "jul", "ago", "set", "out", "nov", "dez",
)

_FAIXAS_ULTIMA_MOVIMENTACAO_ORDEM = (
    SEM_DATA_ULTIMA_MOVIMENTACAO,
    "180+ dias",
    "90+ dias",
    "60+ dias",
    "Menos de 30 dias",
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


def _get_data_execucao(item: dict[str, Any]) -> Optional[date]:
    return _to_date(item.get("DATA_EXECUCAO") or item.get("data_execucao"))


def _get_data_compensacao_alvara(item: dict[str, Any]) -> Optional[date]:
    return _to_date(item.get("DATA_COMPENSACAO_ALVARA") or item.get("data_compensacao_alvara"))


def _get_data_compensacao_alvara_incontroverso(item: dict[str, Any]) -> Optional[date]:
    return _to_date(
        item.get("DATA_COMPENSACAO_ALVARA_INCONTROVERSO")
        or item.get("data_compensacao_alvara_incontroverso")
    )


def _get_data_encerramento(item: dict[str, Any]) -> Optional[date]:
    return _to_date(item.get("DATA_ENCERRAMENTO") or item.get("data_encerramento"))


def _get_ultima_movimentacao(item: dict[str, Any]) -> Optional[date]:
    return _to_date(
        item.get("ULTIMA_MOVIMENTACAO")
        or item.get("ultima_movimentacao")
        or item.get("DATA_ULTIMA_MOVIMENTACAO")
    )


def _get_data_distribuicao(item: dict[str, Any]) -> Optional[date]:
    """Data de ajuizamento do processo (coluna DATA_DISTRIBUICAO)."""
    return _to_date(item.get("DATA_DISTRIBUICAO") or item.get("data_distribuicao"))


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


def _base_execucao_LA(execucao: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Base padrão das análises de Execução LA: ID_ESCRITORIO == 21, deduplicado por
    NUMERO_PROCESSO — o identificador único do processo (a mesma NUMERO_PROCESSO pode
    aparecer em mais de uma linha ``processo``, ex.: joins 1:N com tabelas auxiliares
    ou múltiplos registros por processo na origem).
    """
    base: list[dict[str, Any]] = []
    vistos: set[Any] = set()
    for item in execucao:
        id_escritorio = item.get(_COL_ID_ESCRITORIO) or item.get("id_escritorio")
        if _to_int(id_escritorio) != ID_ESCRITORIO:
            continue
        if item.get("TEM_ETIQUETA_ACORDO"):
            continue
        chave = item.get("NUMERO_PROCESSO") or item.get("id") or item.get("ID")
        if chave is not None:
            if chave in vistos:
                continue
            vistos.add(chave)
        base.append(item)
    return base


def _get_valor_execucao(item: dict[str, Any]) -> Optional[Any]:
    """Retorna o valor bruto de VALOR_EXECUCAO, ou ``None`` se ausente/vazio."""
    raw = item.get("VALOR_EXECUCAO")
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None
    return raw


def _get_valor_ted(item: dict[str, Any]) -> Optional[Any]:
    """Retorna o valor bruto de VALOR_TED, ou ``None`` se ausente/vazio."""
    raw = item.get("VALOR_TED")
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None
    return raw


def _get_valor_incontroverso(item: dict[str, Any]) -> Optional[Any]:
    """Retorna o valor bruto de VALOR_INCONTROVERSO, ou ``None`` se ausente/vazio."""
    raw = item.get("VALOR_INCONTROVERSO")
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None
    return raw


def _get_valor_remanescente(item: dict[str, Any]) -> Optional[Any]:
    """Retorna o valor bruto de VALOR_REMANESCENTE, ou ``None`` se ausente/vazio."""
    raw = item.get("VALOR_REMANESCENTE")
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None
    return raw


def _get_valor_execucao_em_aberto(item: dict[str, Any]) -> Optional[Any]:
    """
    Retorna o valor ainda em aberto do processo: VALOR_REMANESCENTE quando já
    houve compensação do alvará do incontroverso (DATA_COMPENSACAO_ALVARA_INCONTROVERSO
    preenchida — a parte incontroversa já caiu e não representa mais valor "em
    execução"), ou VALOR_EXECUCAO cheio caso contrário (processo sem pagamento
    parcial ainda).
    """
    if _get_data_compensacao_alvara_incontroverso(item) is not None:
        return _get_valor_remanescente(item)
    return _get_valor_execucao(item)


def _get_valor_honorarios(item: dict[str, Any]) -> Optional[Any]:
    """
    Retorna o valor bruto de VALOR_HONORARIOS somente para processos na fase
    Financeiro (ID_FASE == 26), ou ``None`` se ausente/vazio.
    """
    if not _processo_fase_financeiro(item):
        return None
    raw = item.get("VALOR_HONORARIOS")
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None
    return raw


def _processo_em_execucao(item: dict[str, Any]) -> bool:
    """
    Retorna True se o processo está atualmente em Execução: fase Execução
    (ID_FASE == 12) e situação Ativo (ID_SITUACAO == 1) — processos arquivados
    ficam retidos na fase Execução até alguém corrigir manualmente a fase no
    LexFlow, e não devem contar no estoque atual.
    """
    id_fase = item.get("ID_FASE")
    if id_fase is None or int(id_fase) != ID_FASE_EXECUCAO:
        return False
    id_situacao = _to_int(item.get(_COL_ID_SITUACAO))
    return id_situacao == ID_SITUACAO_ATIVO


def _processo_fase_financeiro(item: dict[str, Any]) -> bool:
    """Retorna True se o processo está na fase Financeiro."""
    id_fase = item.get("ID_FASE")
    return id_fase is not None and int(id_fase) == ID_FASE_FINANCEIRO


# =============================================================================
# 2 - Queries de filtragem
# =============================================================================

def _filtrar_em_execucao(execucao: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Retorna somente os processos na fase de Execução (ID_FASE == 12)."""
    return [e for e in _base_execucao_LA(execucao) if _processo_em_execucao(e)]


def _filtrar_por_data_execucao(
    execucao: list[dict[str, Any]],
    from_date: date,
    to_date: date,
) -> list[dict[str, Any]]:
    """Filtra processos cujo DATA_EXECUCAO esteja no intervalo [from_date, to_date]."""
    return [
        item for item in _base_execucao_LA(execucao)
        if _data_no_periodo(_get_data_execucao(item), from_date, to_date)
    ]


def _filtrar_entrada_execucao_no_periodo(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Processos com ``DATA_EXECUCAO`` preenchida cuja data está no período informado,
    garantindo unicidade por NUMERO_PROCESSO, o identificador único do processo (mesmo critério de
    :func:`_filtrar_saida_no_periodo`).
    """
    vistos: set[Any] = set()
    filtrados: list[dict[str, Any]] = []

    for item in _base_execucao_LA(execucao):
        data_exe = _get_data_execucao(item)
        if data_exe is None:
            continue
        if not _data_no_periodo(data_exe, from_date, to_date):
            continue

        chave = item.get("NUMERO_PROCESSO") or item.get("id") or item.get("ID")
        if chave is not None:
            if chave in vistos:
                continue
            vistos.add(chave)

        filtrados.append(item)

    return filtrados


def _filtrar_saida_no_periodo(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Retorna processos com ``DATA_COMPENSACAO_ALVARA`` preenchida cuja data
    esteja no período indicado, garantindo unicidade por NUMERO_PROCESSO
    (identificador único do processo).

    Não restringe pela fase atual do processo: processos já compensados
    (pagos) saem da fase Financeiro e ficam arquivados (situação Arquivado,
    fase "Arquivado por Procedência", motivo "Valor Compensado") — por isso o
    histórico de saídas (quantidade e valor) precisa considerar qualquer fase
    atual, olhando somente para a data de compensação do alvará.
    """
    vistos: set[Any] = set()
    filtrados: list[dict[str, Any]] = []

    for item in _base_execucao_LA(execucao):
        data_compensacao = _get_data_compensacao_alvara(item)
        if data_compensacao is None:
            continue
        if not _data_no_periodo(data_compensacao, from_date, to_date):
            continue

        chave = item.get("NUMERO_PROCESSO") or item.get("id") or item.get("ID")
        if chave is not None:
            if chave in vistos:
                continue
            vistos.add(chave)

        filtrados.append(item)

    return filtrados


def _filtrar_saida_incontroverso_no_periodo(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Retorna processos com ``DATA_COMPENSACAO_ALVARA_INCONTROVERSO`` preenchida
    cuja data esteja no período indicado, garantindo unicidade por
    NUMERO_PROCESSO.

    Compensação parcial do alvará: quando o valor de execução é pago em duas
    partes (incontroverso + remanescente), a parte incontroversa "sai" da
    Execução (em valor) assim que é compensada, mesmo que o processo continue
    ativo na fase Execução até a compensação do remanescente.
    """
    vistos: set[Any] = set()
    filtrados: list[dict[str, Any]] = []

    for item in _base_execucao_LA(execucao):
        data_incontroverso = _get_data_compensacao_alvara_incontroverso(item)
        if data_incontroverso is None:
            continue
        if not _data_no_periodo(data_incontroverso, from_date, to_date):
            continue

        chave = item.get("NUMERO_PROCESSO") or item.get("id") or item.get("ID")
        if chave is not None:
            if chave in vistos:
                continue
            vistos.add(chave)

        filtrados.append(item)

    return filtrados


def _normalizar_materia(raw: Any) -> str:
    """Extrai a matéria: apenas a parte antes do ' - '."""
    if raw is None or raw == "":
        return "Sem materia"
    s = str(raw).strip()
    if " - " in s:
        s = s.split(" - ", 1)[0].strip()
    return s if s else "Sem materia"



def _primeiro_valor_preenchido(p: dict[str, Any], *campos: str) -> float:
    """Primeiro campo com valor diferente de zero, ou ``0.0``."""
    for campo in campos:
        raw = p.get(campo)
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            continue
        valor = _converter_valor(raw)
        if valor:
            return valor
    return 0.0


def group_alvaras_expedidos_por_dia_LA(execucao: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Alvarás expedidos por dia (histórico completo, qualquer fase atual) — gráfico mês a mês
    com drill-down por dia da seção Alvarás Expedidos. Cada alvará é um evento na sua data:
    o do incontroverso (``DATA_EXPEDICAO_ALVARA_INCONTROVERSO``, valor
    ``VALOR_ALVARA_INCONTROVERSO`` ou ``VALOR_INCONTROVERSO``) e o total/remanescente
    (``DATA_EXPEDICAO_ALVARA``, valor ``VALOR_ALVARA``; no remanescente, fallback
    ``VALOR_REMANESCENTE``) — mesma lógica da lista de alvarás expedidos.
    """
    por_dia: dict[str, dict[str, Any]] = {}

    def _somar(dia: date, valor: float) -> None:
        chave = dia.isoformat()
        item = por_dia.setdefault(chave, {"data": chave, "quantidade": 0, "valor": 0.0})
        item["quantidade"] += 1
        item["valor"] += valor

    for p in _base_execucao_LA(execucao):
        exp_incontroverso = _to_date(p.get("DATA_EXPEDICAO_ALVARA_INCONTROVERSO"))
        exp_total = _to_date(p.get("DATA_EXPEDICAO_ALVARA"))
        if exp_incontroverso is not None:
            _somar(
                exp_incontroverso,
                _primeiro_valor_preenchido(p, "VALOR_ALVARA_INCONTROVERSO", "VALOR_INCONTROVERSO"),
            )
        if exp_total is not None:
            teve_incontroverso = (
                exp_incontroverso is not None or _get_data_compensacao_alvara_incontroverso(p) is not None
            )
            campos = ("VALOR_ALVARA", "VALOR_REMANESCENTE") if teve_incontroverso else ("VALOR_ALVARA",)
            _somar(exp_total, _primeiro_valor_preenchido(p, *campos))

    return [
        {**por_dia[k], "valor": round(por_dia[k]["valor"], 2)}
        for k in sorted(por_dia)
    ]


_SUBFASE_ALVARA_EXPEDIDO = "ALVARÁ EXPEDIDO"


def list_processos_alvara_expedido_LA(execucao: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Processos atualmente na Execução (mesma base do card "Total em Execução") com subfase
    "ALVARÁ EXPEDIDO" — alvará já expedido, valor ainda por compensar.

    Data e valor com a lógica de incontroverso dos cards da Seção 01: havendo
    ``DATA_EXPEDICAO_ALVARA`` ela vale, como ``"Remanescente"`` se o processo já teve
    incontroverso, senão ``"Total"`` — valor ``VALOR_ALVARA`` (no Remanescente, com
    fallback ``VALOR_REMANESCENTE``); só com ``DATA_EXPEDICAO_ALVARA_INCONTROVERSO``,
    ``"Incontroverso"`` — valor ``VALOR_ALVARA_INCONTROVERSO`` (fallback
    ``VALOR_INCONTROVERSO``). Zero conta como vazio. Ordenado pela expedição mais recente.
    """

    def _valor(p: dict[str, Any], *campos: str) -> Optional[float]:
        for campo in campos:
            raw = p.get(campo)
            if raw is None or (isinstance(raw, str) and not raw.strip()):
                continue
            valor = _converter_valor(raw)
            if valor:
                return valor
        return None

    itens: list[dict[str, Any]] = []
    for p in _filtrar_em_execucao(execucao):
        if _normalizar_subfase(p.get("SUBFASE")).casefold() != _SUBFASE_ALVARA_EXPEDIDO.casefold():
            continue
        exp_total = _to_date(p.get("DATA_EXPEDICAO_ALVARA"))
        exp_incontroverso = _to_date(p.get("DATA_EXPEDICAO_ALVARA_INCONTROVERSO"))
        teve_incontroverso = (
            exp_incontroverso is not None
            or _get_data_compensacao_alvara_incontroverso(p) is not None
        )
        valor_incontroverso = _valor(p, "VALOR_ALVARA_INCONTROVERSO", "VALOR_INCONTROVERSO")
        if exp_total is not None:
            data_expedicao = exp_total
            if teve_incontroverso:
                tipo = "Remanescente"
                valor_alvara = _valor(p, "VALOR_ALVARA", "VALOR_REMANESCENTE")
            else:
                tipo = "Total"
                valor_alvara = _valor(p, "VALOR_ALVARA")
        elif exp_incontroverso is not None:
            data_expedicao = exp_incontroverso
            tipo = "Incontroverso"
            valor_alvara = valor_incontroverso
        else:
            data_expedicao = None
            tipo = None
            valor_alvara = _valor(p, "VALOR_ALVARA")
        itens.append({
            "id": _to_int(p.get("id") or p.get("ID")),
            "origem": "Condenação",
            "numero_processo": str(p.get("NUMERO_PROCESSO") or "").strip() or None,
            "subfase": _normalizar_subfase(p.get("SUBFASE")),
            "materia": _normalizar_materia(p.get("MATERIA")),
            "data_expedicao_alvara": data_expedicao.isoformat() if data_expedicao else None,
            "tipo_alvara": tipo,
            "data_expedicao_alvara_incontroverso": (
                exp_incontroverso.isoformat() if exp_incontroverso else None
            ),
            "valor_alvara": valor_alvara,
            "valor_alvara_incontroverso": valor_incontroverso if tipo == "Remanescente" else None,
        })
    # Mais recente primeiro; sem data ("" no sort) fica por último.
    return sorted(itens, key=lambda x: x["data_expedicao_alvara"] or "", reverse=True)


def _normalizar_subfase(raw: Any) -> str:
    if raw is None or raw == "":
        return "Sem subfase"
    s = str(raw).strip()
    return s if s else "Sem subfase"


def _normalizar_comarca(raw: Any) -> str:
    if raw is None or raw == "":
        return "Sem comarca"
    s = str(raw).strip()
    return s if s else "Sem comarca"


def filter_execucao_LA_por_materia(
    execucao: list[dict[str, Any]],
    materia: Optional[Any] = None,
) -> list[dict[str, Any]]:
    """
    Mesmo critério de :func:`filter_protocolo_LA_por_materia` em ``protocolo_LA``
    (:func:`_normalizar_materia`).
    """
    # Aceita um valor único ou uma lista (seleção múltipla no filtro da página).
    valores = materia if isinstance(materia, (list, tuple, set)) else [materia]
    alvos = {_normalizar_materia(v) for v in valores if v is not None and str(v).strip()}
    if not alvos:
        return _base_execucao_LA(execucao)
    return [
        p for p in _base_execucao_LA(execucao)
        if _normalizar_materia(p.get("MATERIA")) in alvos
    ]


def filter_execucao_LA_por_subfase(
    execucao: list[dict[str, Any]],
    subfase: Optional[Any] = None,
) -> list[dict[str, Any]]:
    # Aceita um valor único ou uma lista (seleção múltipla no filtro da página).
    valores = subfase if isinstance(subfase, (list, tuple, set)) else [subfase]
    alvos = {_normalizar_subfase(v) for v in valores if v is not None and str(v).strip()}
    if not alvos:
        return _base_execucao_LA(execucao)
    return [
        p for p in _base_execucao_LA(execucao)
        if _normalizar_subfase(p.get("SUBFASE")) in alvos
    ]


def filter_execucao_LA_por_uf(
    execucao: list[dict[str, Any]],
    ufs: Optional[list[str]] = None,
) -> list[dict[str, Any]]:
    """Sem UFs informadas, não filtra. Caso contrário, mantém só as UFs selecionadas."""
    base = _base_execucao_LA(execucao)
    alvo = {str(u).strip().upper() for u in ufs if str(u).strip()} if ufs else set()
    if not alvo:
        return base
    return [p for p in base if str(p.get("UF") or "").strip().upper() in alvo]


def get_opcoes_uf_execucao_LA(execucao: list[dict[str, Any]]) -> list[str]:
    """UFs distintas (não vazias) presentes na base de Execução LA, em ordem alfabética."""
    ufs = {
        str(p.get("UF") or "").strip().upper()
        for p in _base_execucao_LA(execucao)
    }
    ufs.discard("")
    return sorted(ufs)


def filter_execucao_LA_por_comarca(
    execucao: list[dict[str, Any]],
    comarcas: Optional[list[str]] = None,
) -> list[dict[str, Any]]:
    """Sem comarcas informadas, não filtra. Caso contrário, mantém só as comarcas selecionadas."""
    base = _base_execucao_LA(execucao)
    alvo = {_normalizar_comarca(c) for c in comarcas if str(c).strip()} if comarcas else set()
    if not alvo:
        return base
    return [p for p in base if _normalizar_comarca(p.get("COMARCA")) in alvo]


def get_opcoes_comarca_execucao_LA(execucao: list[dict[str, Any]]) -> list[str]:
    """Comarcas distintas (não vazias) presentes na base de Execução LA, em ordem alfabética."""
    comarcas = {
        _normalizar_comarca(p.get("COMARCA"))
        for p in _base_execucao_LA(execucao)
    }
    comarcas.discard("Sem comarca")
    return sorted(comarcas)


def get_opcoes_materia_execucao_LA(execucao: list[dict[str, Any]]) -> list[str]:
    """Matérias distintas (não vazias) presentes na base de Execução LA, em ordem alfabética."""
    materias = {
        _normalizar_materia(p.get("MATERIA"))
        for p in _base_execucao_LA(execucao)
    }
    materias.discard("Sem materia")
    return sorted(materias)


def get_opcoes_subfase_execucao_LA(execucao: list[dict[str, Any]]) -> list[str]:
    """Subfases distintas (não vazias) presentes na base de Execução LA, em ordem alfabética."""
    subfases = {
        _normalizar_subfase(p.get("SUBFASE"))
        for p in _base_execucao_LA(execucao)
    }
    subfases.discard("Sem subfase")
    return sorted(subfases)


_SEM_ANO_AJUIZAMENTO_EXEC = "Sem data de ajuizamento"


def filter_execucao_LA_por_ano_ajuizamento(
    execucao: list[dict[str, Any]],
    ano_ajuizamento: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Filtra pelo ano de ajuizamento (DATA_DISTRIBUICAO), ou por `_SEM_ANO_AJUIZAMENTO_EXEC`."""
    alvo = str(ano_ajuizamento).strip() if ano_ajuizamento else ""
    if not alvo:
        return _base_execucao_LA(execucao)
    return [
        p for p in _base_execucao_LA(execucao)
        if (
            str(d.year) if (d := _get_data_distribuicao(p)) else _SEM_ANO_AJUIZAMENTO_EXEC
        )
        == alvo
    ]


# =============================================================================
# 3 - Totais
# =============================================================================

def get_total_execucao_LA(execucao: list[dict[str, Any]]) -> int:
    """Retorna o total de processos atualmente em Execução."""
    return len(_filtrar_em_execucao(execucao))


def get_total_entrada_execucao_periodo_LA(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """
    Quantidade de processos que entraram na Execução no período (``DATA_EXECUCAO``
    dentro do intervalo informado).

    Ignora linhas sem ``DATA_EXECUCAO`` válida.
    """
    return len(_filtrar_entrada_execucao_no_periodo(execucao, from_date, to_date))


def get_total_saida_execucao_periodo_LA(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """
    Retorna a quantidade de processos que saíram da Execução no período.

    Considera processos com ``DATA_COMPENSACAO_ALVARA`` preenchida, cuja data
    esteja no intervalo informado — independente da fase atual (ver
    :func:`_filtrar_saida_no_periodo`).
    """
    return len(_filtrar_saida_no_periodo(execucao, from_date, to_date))


def get_estoque_final_LA(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    execucao_fluxos_periodo: Optional[list[dict[str, Any]]] = None,
) -> int:
    """
    Estoque final **calculado** (equivalente medida-Power BI ``[get_estoque_final_LA]``):

    ``(total em Execução − entradas no período) + saídas no período``.

    Por omissão, ``execucao`` alimenta os três termos. Se ``execucao_fluxos_periodo``
    for informado (ex.: base completa ``all_execucao`` no dashboard), entradas e
    saídas usam essa lista e apenas o total em Execução usa ``execucao``.
    """
    fluxos = execucao_fluxos_periodo if execucao_fluxos_periodo is not None else execucao
    resultado_subtracao = (
        get_total_execucao_LA(execucao)
        - get_total_entrada_execucao_periodo_LA(fluxos, from_date, to_date)
    )
    return resultado_subtracao + get_total_saida_execucao_periodo_LA(
        fluxos, from_date, to_date
    )


def get_tre_LA(estoque_inicial: int, estoque_final: int) -> float:
    """
    TRE segundo o modelo DAX:

    ``DIVIDE((Estoque_Inicial − Estoque_Final) × 100, Estoque_Final, 0)``

    Retorna ``0.0`` se ``estoque_final == 0``.
    Use :func:`get_tre_execucao_dax_LA` quando as medidas forem ``get_total_execucao_LA`` e
    :func:`get_estoque_final_LA`.
    """
    if estoque_final == 0:
        return 0.0
    diferenca = float(estoque_inicial) - float(estoque_final)
    diferenca_2 = diferenca * 100.0
    taxa = diferenca_2 / float(estoque_final)
    return taxa


def get_tre_execucao_dax_LA(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    execucao_fluxos_periodo: Optional[list[dict[str, Any]]] = None,
) -> float:
    """
    Mesma sequência do DAX:

        Estoque_Inicial = ``get_total_execucao_LA(execucao)``
        Estoque_Final = ``get_estoque_final_LA(...)``

    e retorno de :func:`get_tre_LA` sobre esses dois valores.
    """
    inicial = get_total_execucao_LA(execucao)
    final = get_estoque_final_LA(
        execucao,
        from_date,
        to_date,
        execucao_fluxos_periodo=execucao_fluxos_periodo,
    )
    return get_tre_LA(inicial, final)


# =============================================================================
# 4 - Valores monetários
# =============================================================================

def get_valor_causa_total_execucao_LA(execucao: list[dict[str, Any]]) -> float:
    """
    Soma do valor ainda em aberto de todos os processos em Execução —
    card "Valor Total em execução".

    Quando o processo já teve o alvará do incontroverso compensado
    (pagamento parcial), usa VALOR_REMANESCENTE em vez do VALOR_EXECUCAO
    cheio — ver :func:`_get_valor_execucao_em_aberto`: a parte incontroversa
    já caiu (sai pelo card "Valor Incontroverso" no período em que foi
    compensada) e não deve continuar contando aqui.
    """
    total = 0.0
    for p in _filtrar_em_execucao(execucao):
        valor = _get_valor_execucao_em_aberto(p)
        if valor is not None:
            total += _converter_valor(valor)
    return total


def get_detalhe_valor_execucao_vazio_LA(execucao: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Processos em Execução com VALOR_EXECUCAO ausente/vazio — número do processo +
    campo faltando (alimenta o alerta clicável do dashboard)."""
    return [
        {
            "numero_processo": str(p.get("NUMERO_PROCESSO") or p.get("id") or p.get("ID") or ""),
            "campo": "Valor da Execução",
        }
        for p in _filtrar_em_execucao(execucao)
        if _get_valor_execucao(p) is None
    ]


def get_total_valor_execucao_vazio_LA(execucao: list[dict[str, Any]]) -> int:
    """Quantidade de processos em Execução com VALOR_EXECUCAO ausente ou vazio."""
    return len(get_detalhe_valor_execucao_vazio_LA(execucao))

def get_valor_honorarios_total_execucao_LA(execucao: list[dict[str, Any]]) -> float:
    """Soma de VALOR_HONORARIOS dos processos na fase Financeiro (ID_FASE == 26)."""
    total = 0.0
    for p in _base_execucao_LA(execucao):
        valor = _get_valor_honorarios(p)
        if valor is not None:
            total += _converter_valor(valor)
    return total

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


def get_valor_remanescente_em_execucao_LA(execucao: list[dict[str, Any]]) -> float:
    """
    Soma de ``VALOR_REMANESCENTE`` de todos os processos atualmente em
    Execução — card "Valor Remanescente".

    Usa :func:`_filtrar_em_execucao` (estoque atual, mesmo conjunto de
    :func:`get_valor_causa_total_execucao_LA`), não o recorte de entrada no
    período: o remanescente normalmente vem de processos que entraram em
    Execução em períodos anteriores (a compensação do incontroverso costuma
    acontecer bem depois da entrada), então restringir por "entrada no
    período selecionado" esconderia a maior parte do saldo em aberto.

    Só soma o valor já preenchido nessa coluna (processos sem compensação
    parcial do alvará do incontroverso simplesmente não contribuem, sem
    fallback para o VALOR_EXECUCAO cheio).
    """
    total = 0.0
    for p in _filtrar_em_execucao(execucao):
        valor = _get_valor_remanescente(p)
        if valor is not None:
            total += _converter_valor(valor)
    return total


def get_valor_execucao_saida_periodo_LA(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """
    Soma do valor que efetivamente saiu da Execução no período — valor em
    destaque no card "Valor saída Execução".

    Considera processos com ``DATA_COMPENSACAO_ALVARA`` preenchida, cuja data
    esteja no intervalo informado — independente da fase atual (ver
    :func:`_filtrar_saida_no_periodo`) — mais o valor incontroverso compensado
    no período (:func:`get_valor_incontroverso_saida_periodo_LA`), para refletir
    o total que de fato saiu da Execução no período.

    Compensação parcial do alvará: se o processo já teve a parte incontroversa
    compensada em algum momento (ver :func:`_get_valor_execucao_em_aberto`),
    a parcela do remanescente soma só o VALOR_REMANESCENTE — o que de fato
    caiu nesta saída — em vez do VALOR_EXECUCAO cheio; a parte incontroversa
    entra separadamente via :func:`get_valor_incontroverso_saida_periodo_LA`,
    sem risco de contagem duplicada, pois cada uma usa sua própria data de
    compensação (DATA_COMPENSACAO_ALVARA vs. DATA_COMPENSACAO_ALVARA_INCONTROVERSO).
    Processos sem nenhum pagamento parcial (a maioria) continuam somando o
    valor cheio normalmente.
    """
    total = 0.0
    for p in _filtrar_saida_no_periodo(execucao, from_date, to_date):
        valor = _get_valor_execucao_em_aberto(p)
        if valor is not None:
            total += _converter_valor(valor)
    total += get_valor_incontroverso_saida_periodo_LA(execucao, from_date, to_date)
    return total


def get_valor_incontroverso_saida_periodo_LA(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """
    Soma de ``VALOR_INCONTROVERSO`` dos processos com
    ``DATA_COMPENSACAO_ALVARA_INCONTROVERSO`` preenchida no período — linha
    secundária "Valor Incontroverso" do card "Valor saída Execução", exibida
    acima de "Valor TED".

    Compensação parcial do alvará: a parte incontroversa já caiu (foi paga)
    mesmo que o processo continue ativo na fase Execução aguardando a
    compensação do remanescente — ver :func:`_filtrar_saida_incontroverso_no_periodo`.
    """
    total = 0.0
    for p in _filtrar_saida_incontroverso_no_periodo(execucao, from_date, to_date):
        valor = _get_valor_incontroverso(p)
        if valor is not None:
            total += _converter_valor(valor)
    return total


def get_total_incontroverso_saida_periodo_LA(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """
    Quantidade de processos com ``DATA_COMPENSACAO_ALVARA_INCONTROVERSO``
    preenchida no período — linha secundária "Qtd. Incontroverso" do card
    "Quantidade de saída da Execução".

    Exclui processos que já têm ``DATA_COMPENSACAO_ALVARA`` preenchida (o
    remanescente já caiu): esses já contam como saída normal em
    :func:`get_total_saida_execucao_periodo_LA`, então não devem ser contados
    duas vezes aqui — enquanto o remanescente não cai, o processo conta só
    como incontroverso; quando cai, passa a contar só como saída normal.
    """
    return len([
        p for p in _filtrar_saida_incontroverso_no_periodo(execucao, from_date, to_date)
        if _get_data_compensacao_alvara(p) is None
    ])



def _somar_campos_ted(item: dict[str, Any], campos: tuple[str, ...]) -> float:
    total = 0.0
    for campo in campos:
        raw = item.get(campo)
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            continue
        total += _converter_valor(raw)
    return total


def get_valor_ted_saida_execucao_periodo_LA(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """
    Soma do TED que saiu da Execução no período — valor secundário "Valor TED" do card
    "Valor saída Execução", com a mesma lógica de incontroverso do valor de saída:

    - incontroverso compensado no período (``DATA_COMPENSACAO_ALVARA_INCONTROVERSO``):
      soma ``VALOR_TED`` (TED da 1ª compensação);
    - compensação total no período (``DATA_COMPENSACAO_ALVARA``): se o processo já teve
      incontroverso, soma só ``VALOR_TED_2`` + ``VALOR_TED_3`` (TEDs do remanescente —
      o ``VALOR_TED`` já entrou com o incontroverso); senão soma os três.
    """
    total = 0.0
    for p in _filtrar_saida_no_periodo(execucao, from_date, to_date):
        if _get_data_compensacao_alvara_incontroverso(p) is not None:
            total += _somar_campos_ted(p, ("VALOR_TED_2", "VALOR_TED_3"))
        else:
            total += _somar_campos_ted(p, ("VALOR_TED", "VALOR_TED_2", "VALOR_TED_3"))
    for p in _filtrar_saida_incontroverso_no_periodo(execucao, from_date, to_date):
        total += _somar_campos_ted(p, ("VALOR_TED",))
    return total


def get_taxa_recuperacao_execucao_LA(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """
    Taxa de recuperação (%) do que saiu da Execução no período:
    ``Valor TED da saída ÷ Valor de saída × 100``.

    Numerador :func:`get_valor_ted_saida_execucao_periodo_LA` e denominador
    :func:`get_valor_execucao_saida_periodo_LA` — os dois com a mesma lógica de
    incontroverso. Razão agregada, não média por processo; ``0.0`` se o valor
    de saída for zero.
    """
    total_saida = get_valor_execucao_saida_periodo_LA(execucao, from_date, to_date)
    if total_saida == 0:
        return 0.0
    total_ted = get_valor_ted_saida_execucao_periodo_LA(execucao, from_date, to_date)
    return round((total_ted / total_saida) * 100.0, 2)


# =============================================================================
# 5 - Agrupamentos
# =============================================================================

def group_valor_saida_execucao_por_mes_LA(
    execucao: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Agrupa a soma de ``VALOR_TED`` dos processos que saíram da Execução por mês.

    Usa os mesmos critérios de :func:`get_valor_ted_saida_execucao_periodo_LA` e
    :func:`_filtrar_saida_no_periodo` (``DATA_COMPENSACAO_ALVARA``, independente
    da fase atual).
    """
    saidas = _filtrar_saida_no_periodo(execucao)
    grouped: dict[str, dict[str, Any]] = {}

    for p in saidas:
        try:
            data_compensacao = _get_data_compensacao_alvara(p)
            if not data_compensacao:
                continue

            month_key = f"{data_compensacao.year}-{data_compensacao.month:02d}"

            if month_key not in grouped:
                month_name = f"{_MONTH_NAMES[data_compensacao.month - 1]} {data_compensacao.year}"
                grouped[month_key] = {"name": month_name, "value": 0.0}

            valor = _get_valor_ted(p)
            if valor is not None:
                grouped[month_key]["value"] += _converter_valor(valor)

        except (ValueError, AttributeError, TypeError):
            continue

    return [
        {**item, "value": round(item["value"], 2)}
        for item in sorted(grouped.values(), key=lambda x: x["name"])
    ]


def group_valor_execucao_saida_periodo_por_mes_LA(
    execucao: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Agrupa por mês o valor total que saiu da Execução — mesma soma do card
    "Valor saída Execução" (:func:`get_valor_execucao_saida_periodo_LA`) somada
    com o card "Valor Incontroverso" (:func:`get_valor_incontroverso_saida_periodo_LA`),
    mês a mês.

    Dois recortes por mês, somados:
    - Processos com ``DATA_COMPENSACAO_ALVARA`` (final) naquele mês: valor
      ainda em aberto (:func:`_get_valor_execucao_em_aberto` — VALOR_REMANESCENTE
      quando há pagamento parcial, senão VALOR_EXECUCAO cheio).
    - Processos com ``DATA_COMPENSACAO_ALVARA_INCONTROVERSO`` naquele mês:
      VALOR_INCONTROVERSO (mesmo que o processo continue ativo em Execução).

    Histórico completo, independente do filtro de período — alimenta o
    gráfico "Valor Saída Execução Mês a Mês".
    """
    grouped: dict[str, dict[str, Any]] = {}

    for p in _filtrar_saida_no_periodo(execucao):
        try:
            data_compensacao = _get_data_compensacao_alvara(p)
            if not data_compensacao:
                continue

            valor = _get_valor_execucao_em_aberto(p)
            if valor is None:
                continue

            month_key = f"{data_compensacao.year}-{data_compensacao.month:02d}"
            if month_key not in grouped:
                month_name = f"{_MONTH_NAMES[data_compensacao.month - 1]} {data_compensacao.year}"
                grouped[month_key] = {"name": month_name, "value": 0.0}
            grouped[month_key]["value"] += _converter_valor(valor)

        except (ValueError, AttributeError, TypeError):
            continue

    for p in _filtrar_saida_incontroverso_no_periodo(execucao):
        try:
            data_incontroverso = _get_data_compensacao_alvara_incontroverso(p)
            if not data_incontroverso:
                continue

            valor = _get_valor_incontroverso(p)
            if valor is None:
                continue

            month_key = f"{data_incontroverso.year}-{data_incontroverso.month:02d}"
            if month_key not in grouped:
                month_name = f"{_MONTH_NAMES[data_incontroverso.month - 1]} {data_incontroverso.year}"
                grouped[month_key] = {"name": month_name, "value": 0.0}
            grouped[month_key]["value"] += _converter_valor(valor)

        except (ValueError, AttributeError, TypeError):
            continue

    return [
        {**item, "value": round(item["value"], 2)}
        for item in sorted(grouped.values(), key=lambda x: x["name"])
    ]


def group_valor_remanescente_por_mes_LA(
    execucao: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Agrupa a soma de ``VALOR_REMANESCENTE`` por mês de entrada na Execução
    (``DATA_EXECUCAO``) — gráfico de tendência "Valor Remanescente Mês a Mês".

    Usa o mesmo conjunto de processos de :func:`get_valor_remanescente_em_execucao_LA`
    (:func:`_filtrar_em_execucao`, estoque atual): agrupa pelo mês em que o
    processo ENTROU na Execução, não pelo mês em que o incontroverso foi
    compensado — o remanescente pertence ao processo desde a entrada, mesmo
    que a compensação parcial só tenha acontecido bem depois.
    """
    grouped: dict[str, dict[str, Any]] = {}

    for p in _filtrar_em_execucao(execucao):
        try:
            data_exe = _get_data_execucao(p)
            if not data_exe:
                continue

            valor = _get_valor_remanescente(p)
            if valor is None:
                continue

            month_key = f"{data_exe.year}-{data_exe.month:02d}"

            if month_key not in grouped:
                month_name = f"{_MONTH_NAMES[data_exe.month - 1]} {data_exe.year}"
                grouped[month_key] = {"name": month_name, "value": 0.0}

            grouped[month_key]["value"] += _converter_valor(valor)

        except (ValueError, AttributeError, TypeError):
            continue

    return [
        {**item, "value": round(item["value"], 2)}
        for item in sorted(grouped.values(), key=lambda x: x["name"])
    ]


def group_quantidade_saida_execucao_por_mes_LA(
    execucao: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Agrupa a quantidade de processos que saíram da Execução por mês.

    Usa os mesmos critérios de :func:`group_valor_saida_execucao_por_mes_LA` e
    :func:`_filtrar_saida_no_periodo` (``DATA_COMPENSACAO_ALVARA``, independente
    da fase atual), sem filtro de período (histórico completo, para permitir
    seleção de ano no frontend).
    """
    saidas = _filtrar_saida_no_periodo(execucao)
    grouped: dict[str, dict[str, Any]] = {}

    for p in saidas:
        try:
            data_compensacao = _get_data_compensacao_alvara(p)
            if not data_compensacao:
                continue

            month_key = f"{data_compensacao.year}-{data_compensacao.month:02d}"

            if month_key not in grouped:
                month_name = f"{_MONTH_NAMES[data_compensacao.month - 1]} {data_compensacao.year}"
                grouped[month_key] = {"name": month_name, "value": 0}

            grouped[month_key]["value"] += 1

        except (ValueError, AttributeError, TypeError):
            continue

    return [item for item in sorted(grouped.values(), key=lambda x: x["name"])]


def group_quantidade_entrada_execucao_por_mes_LA(
    execucao: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Agrupa a quantidade de processos que entraram na Execução por mês.

    Usa os mesmos critérios de :func:`get_total_entrada_execucao_periodo_LA` e
    :func:`_filtrar_entrada_execucao_no_periodo` (``DATA_EXECUCAO``), sem filtro
    de período (histórico completo, para permitir seleção de ano no frontend).
    """
    entradas = _filtrar_entrada_execucao_no_periodo(execucao)
    grouped: dict[str, dict[str, Any]] = {}

    for p in entradas:
        try:
            data_exe = _get_data_execucao(p)
            if not data_exe:
                continue

            month_key = f"{data_exe.year}-{data_exe.month:02d}"

            if month_key not in grouped:
                month_name = f"{_MONTH_NAMES[data_exe.month - 1]} {data_exe.year}"
                grouped[month_key] = {"name": month_name, "value": 0}

            grouped[month_key]["value"] += 1

        except (ValueError, AttributeError, TypeError):
            continue

    return [item for item in sorted(grouped.values(), key=lambda x: x["name"])]


def group_valor_entrada_execucao_por_mes_LA(
    execucao: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Agrupa a soma de ``VALOR_EXECUCAO`` dos processos que entraram na Execução por mês.

    Usa os mesmos critérios de :func:`group_quantidade_entrada_execucao_por_mes_LA`,
    sem filtro de período (histórico completo, para permitir seleção de ano no frontend).
    """
    entradas = _filtrar_entrada_execucao_no_periodo(execucao)
    grouped: dict[str, dict[str, Any]] = {}

    for p in entradas:
        try:
            data_exe = _get_data_execucao(p)
            if not data_exe:
                continue

            month_key = f"{data_exe.year}-{data_exe.month:02d}"

            if month_key not in grouped:
                month_name = f"{_MONTH_NAMES[data_exe.month - 1]} {data_exe.year}"
                grouped[month_key] = {"name": month_name, "value": 0.0}

            valor = _get_valor_execucao(p)
            if valor is not None:
                grouped[month_key]["value"] += _converter_valor(valor)

        except (ValueError, AttributeError, TypeError):
            continue

    return [
        {**item, "value": round(item["value"], 2)}
        for item in sorted(grouped.values(), key=lambda x: x["name"])
    ]


def group_execucao_por_subfase_LA(execucao: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Agrupa os processos em Execução por SUBFASE.

    Retorna lista de ``{"name": subfase, "value": quantidade}``,
    ordenada de forma decrescente por quantidade.
    """
    contagem: defaultdict[str, int] = defaultdict(int)

    for p in _filtrar_em_execucao(execucao):
        contagem[_normalizar_subfase(p.get("SUBFASE"))] += 1

    return sorted(
        [{"name": name, "value": int(value)} for name, value in contagem.items()],
        key=lambda x: x["value"],
        reverse=True,
    )


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

    duracoes_por_comarca: defaultdict[str, list[float]] = defaultdict(list)
    for p in _base_execucao_LA(execucao):
        entrada = _get_data_execucao(p)
        saida = _get_data_compensacao_alvara(p)
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


def group_valor_execucao_por_subfase_LA(execucao: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Agrupa o valor ainda em aberto (:func:`_get_valor_execucao_em_aberto`) dos
    processos em Execução por SUBFASE — bate com o KPI "Valor Total em execução"
    (:func:`get_valor_causa_total_execucao_LA`).

    Retorna lista de ``{"name": subfase, "value": valor}``,
    ordenada de forma decrescente por valor.
    """
    totais: defaultdict[str, float] = defaultdict(float)

    for p in _filtrar_em_execucao(execucao):
        valor = _get_valor_execucao_em_aberto(p)
        if valor is not None:
            totais[_normalizar_subfase(p.get("SUBFASE"))] += _converter_valor(valor)

    return sorted(
        [{"name": name, "value": float(value)} for name, value in totais.items()],
        key=lambda x: x["value"],
        reverse=True,
    )


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

def _extrair_duracoes_dias(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[float]:
    """
    Calcula a duração em dias (DATA_COMPENSACAO_ALVARA - DATA_EXECUCAO) por
    processo.

    Não restringe pela fase atual (usa :func:`_base_execucao_LA`, não
    :func:`_filtrar_em_execucao`): processos já compensados e arquivados por
    procedência não estão mais em ID_FASE == 12, mas precisam continuar
    entrando no cálculo de tempo médio/mediana de saída.

    Quando `from_date`/`to_date` são informados, amostra pela SAÍDA
    (DATA_COMPENSACAO_ALVARA) dentro do período — não pela DATA_EXECUCAO —
    para bater com o card "Quantidade de saída da Execução" (processos que
    saíram no período, independente de quando entraram).
    """
    duracoes: list[float] = []

    for p in _base_execucao_LA(execucao):
        try:
            saida = _get_data_compensacao_alvara(p)
            if from_date is not None or to_date is not None:
                if not _data_no_periodo(saida, from_date, to_date):
                    continue

            entrada = _get_data_execucao(p)

            if not entrada or not saida:
                continue

            dias = (saida - entrada).days
            if dias > 0:
                duracoes.append(float(dias))

        except (ValueError, AttributeError, TypeError):
            continue

    return duracoes


def get_media_tempo_execucao_LA(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """Tempo médio (em dias) entre DATA_EXECUCAO e DATA_COMPENSACAO_ALVARA, amostrado pela saída no período."""
    duracoes = _extrair_duracoes_dias(execucao, from_date, to_date)
    if not duracoes:
        return 0.0
    return round(sum(duracoes) / len(duracoes), 2)


def get_mediana_tempo_execucao_LA(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """Mediana do tempo (em dias) entre DATA_EXECUCAO e DATA_COMPENSACAO_ALVARA, amostrada pela saída no período."""
    duracoes = sorted(_extrair_duracoes_dias(execucao, from_date, to_date))
    n = len(duracoes)

    if not n:
        return 0.0

    meio = n // 2
    if n % 2 == 1:
        return round(duracoes[meio], 2)
    return round((duracoes[meio - 1] + duracoes[meio]) / 2.0, 2)


def get_media_tempo_execucao_por_mes_LA(execucao: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Série mensal (todo o histórico) da média de dias entre DATA_EXECUCAO e
    DATA_COMPENSACAO_ALVARA, agrupada pelo mês/ano da saída (DATA_COMPENSACAO_ALVARA) —
    mesmo critério de `_extrair_duracoes_dias`, quebrado mês a mês para acompanhar a
    tendência do tempo médio ao longo do tempo.
    """
    grouped: dict[str, dict[str, Any]] = {}

    for p in _base_execucao_LA(execucao):
        try:
            entrada = _get_data_execucao(p)
            saida = _get_data_compensacao_alvara(p)
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


def _classificar_faixa_ultima_movimentacao(dias_desde: int) -> Optional[str]:
    """
    Faixas exclusivas de dias desde a última movimentação.

    - Menos de 30 dias: até 30 dias
    - 60+ dias: 31 a 90 dias
    - 90+ dias: 91 a 180 dias
    - 180+ dias: mais de 180 dias
    """
    if dias_desde <= 30:
        return "Menos de 30 dias"
    if dias_desde <= 90:
        return "60+ dias"
    if dias_desde <= 180:
        return "90+ dias"
    return "180+ dias"


def group_execucao_por_faixa_ultima_movimentacao_LA(
    execucao: list[dict[str, Any]],
    reference_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Conta processos em Execução por faixa exclusiva de dias desde a
    ``ULTIMA_MOVIMENTACAO``, no formato de gráfico (``name`` / ``value``).

    Ordem do eixo X (esquerda → direita): 180+ dias, 90+ dias, 60+ dias,
    Menos de 30 dias, Sem data de ultima movimentação.
    """
    ref = reference_date or date.today()
    contadores = {nome: 0 for nome in _FAIXAS_ULTIMA_MOVIMENTACAO_ORDEM}

    for p in _filtrar_em_execucao(execucao):
        ultima = _get_ultima_movimentacao(p)
        if ultima is None:
            contadores[SEM_DATA_ULTIMA_MOVIMENTACAO] += 1
            continue

        dias_desde = (ref - ultima).days
        if dias_desde < 0:
            continue

        faixa = _classificar_faixa_ultima_movimentacao(dias_desde)
        if faixa is not None:
            contadores[faixa] += 1

    return [
        {"name": nome, "value": int(contadores[nome])}
        for nome in _FAIXAS_ULTIMA_MOVIMENTACAO_ORDEM
    ]


# =============================================================================
# 7 - Atividades no período (agendamentos do setor Execução)
# =============================================================================

_STATUS_INATIVO_EXEC = frozenset({
    "Encerrado Cumprido", "Encerrado Não Cumprido", "Cancelado", "Concluído",
})
_STATUS_EM_ANDAMENTO_EXEC = frozenset({"Iniciado", "Reaberto"})
_STATUS_ENCERRADO_EXEC = frozenset({"Encerrado Cumprido", "Encerrado Não Cumprido"})

_STATUS_FILTRO_EXEC: tuple[str, ...] = (
    "Recebido", "Visualizado", "Iniciado", "Reaberto", "Encaminhado",
    "Encerrado Cumprido", "Encerrado Não Cumprido", "Cancelado",
)

_SITUACOES_FILTRO_EXEC: tuple[tuple[str, str], ...] = (
    ("em_andamento", "Em andamento"),
    ("vencidas", "Vencidas"),
    ("vencem_hoje", "Vencem hoje"),
    ("concluidas", "Concluídas"),
)

SITUACOES_VALIDAS_EXECUCAO = frozenset(sid for sid, _ in _SITUACOES_FILTRO_EXEC)

_STATUS_DEMANDAS_FUNCIONARIO_EXEC: tuple[tuple[str, str], ...] = (
    ("encerrado_nao_cumprido", "Encerrado Não Cumprido"),
    ("encerrado_cumprido", "Encerrado Cumprido"),
)
_SLUG_POR_STATUS_EXEC: dict[str, str] = {
    label: slug for slug, label in _STATUS_DEMANDAS_FUNCIONARIO_EXEC
}

_SEM_ATIVIDADE_EXEC = "Sem atividade"
_SEM_FUNCIONARIO_EXEC = "Sem funcionário"
_STATUS_CUMPRIDO_EXEC = "Encerrado Cumprido"

_COL_FUNCIONARIO_ATRIBUIDO_EXEC = "FUNCIONARIO_ATRIBUIDO"
_COL_FUNCIONARIO_ENCERRAMENTO_EXEC = "FUNCIONARIO_ENCERRAMENTO"
_COL_ID_USUARIO_ENCERRAMENTO_EXEC = "ID_USUARIO_ENCERRAMENTO"


def _ag_to_date(value: Any) -> Optional[date]:
    if not value:
        return None
    parsed = parse_date_from_db(value)
    if isinstance(parsed, datetime):
        return parsed.date()
    if isinstance(parsed, date):
        return parsed
    return None


def _ag_data_no_periodo(
    d: Optional[date],
    from_date: Optional[date],
    to_date: Optional[date],
) -> bool:
    if d is None:
        return False
    if from_date and to_date:
        return from_date <= d <= to_date
    if from_date:
        return d >= from_date
    if to_date:
        return d <= to_date
    return True


def _nome_em_conjunto_exec(nome: str, conjunto: frozenset[str] | None) -> bool:
    if not conjunto:
        return True
    chave = nome.casefold()
    return any(chave == x.casefold() for x in conjunto)


def _get_ag_status(item: dict[str, Any]) -> str | None:
    raw = item.get("STATUS") or item.get("status")
    if raw is None or not str(raw).strip():
        return None
    return str(raw).strip()


def _get_ag_data_criacao(item: dict[str, Any]) -> Optional[date]:
    return _ag_to_date(item.get("DATA_HORA_CRIACAO") or item.get("data_hora_criacao"))


def _get_ag_data_conclusao(item: dict[str, Any]) -> Optional[date]:
    return _ag_to_date(item.get("DATA_HORA_CONCLUSAO") or item.get("data_hora_conclusao"))


def _get_ag_prazo(item: dict[str, Any]) -> Optional[date]:
    return _ag_to_date(item.get("PRAZO") or item.get("prazo"))


def _get_ag_processo_id(item: dict[str, Any]) -> Any | None:
    return item.get("processo_id") or item.get("PROCESSO_ID")


def _get_ag_numero_processo(item: dict[str, Any]) -> Optional[str]:
    raw = item.get("NUMERO_PROCESSO") or item.get("numero_processo")
    if raw is None or not str(raw).strip():
        return None
    return str(raw).strip()


def _get_ag_valor_sentenca(item: dict[str, Any]) -> Optional[float]:
    """Valor da sentença (``processo.valor_causa_vs``), ou ``None`` se ausente/zerado."""
    raw = item.get("VALOR_CAUSA_SENTENCA")
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None
    valor = _converter_valor(raw)
    return valor if valor else None


def _get_ag_valor_acordao(item: dict[str, Any]) -> Optional[float]:
    """Valor do acórdão (``processo.valor_causa_va``), ou ``None`` se ausente/zerado."""
    raw = item.get("VALOR_CAUSA_ACORDO")
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None
    valor = _converter_valor(raw)
    return valor if valor else None


def _get_ag_atividade_nome(item: dict[str, Any]) -> str:
    raw = item.get("ATIVIDADE") or item.get("atividade")
    if raw is None or not str(raw).strip():
        return _SEM_ATIVIDADE_EXEC
    return str(raw).strip()


def _get_ag_funcionario_atribuido(item: dict[str, Any]) -> str:
    raw = (
        item.get(_COL_FUNCIONARIO_ATRIBUIDO_EXEC)
        or item.get("FUNCIONARIO")
        or item.get("funcionario")
    )
    if raw is None or not str(raw).strip():
        return _SEM_FUNCIONARIO_EXEC
    return str(raw).strip()


def _get_ag_funcionario_encerramento(item: dict[str, Any]) -> str | None:
    uid = item.get(_COL_ID_USUARIO_ENCERRAMENTO_EXEC) or item.get("id_usuario_encerramento")
    if uid is None or (isinstance(uid, str) and not str(uid).strip()):
        return None
    raw = item.get(_COL_FUNCIONARIO_ENCERRAMENTO_EXEC) or item.get("funcionario_encerramento")
    if raw is not None and str(raw).strip():
        return str(raw).strip()
    return None


def _get_ag_funcionario_nome(item: dict[str, Any]) -> str:
    status = _get_ag_status(item) or ""
    if status in _STATUS_ENCERRADO_EXEC:
        encerrador = _get_ag_funcionario_encerramento(item)
        if encerrador:
            return encerrador
    return _get_ag_funcionario_atribuido(item)


def _incluir_na_lista_exec(
    row: dict[str, Any],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> bool:
    criacao = _get_ag_data_criacao(row)
    conclusao = _get_ag_data_conclusao(row)
    status = _get_ag_status(row) or ""
    prazo = _get_ag_prazo(row)
    ref = ref_date or date.today()
    if _ag_data_no_periodo(criacao, from_date, to_date):
        return True
    if status in _STATUS_ENCERRADO_EXEC:
        return _ag_data_no_periodo(conclusao, from_date, to_date)
    if status not in _STATUS_INATIVO_EXEC and prazo is not None and prazo <= ref:
        return True
    return False


def _classificar_situacao_exec(
    row: dict[str, Any],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, bool]:
    ref = ref_date or date.today()
    criacao = _get_ag_data_criacao(row)
    conclusao = _get_ag_data_conclusao(row)
    status = _get_ag_status(row) or ""
    prazo = _get_ag_prazo(row)
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


def _filtrar_ag_encerrados_no_periodo(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    exigir_encerrador: bool = False,
) -> list[dict[str, Any]]:
    resultado = []
    for row in agendamentos:
        status = _get_ag_status(row) or ""
        if status not in _STATUS_ENCERRADO_EXEC:
            continue
        if exigir_encerrador and _get_ag_funcionario_encerramento(row) is None:
            continue
        conclusao = _get_ag_data_conclusao(row)
        if _ag_data_no_periodo(conclusao, from_date, to_date):
            resultado.append(row)
    return resultado


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


def get_media_mensal_atividades_execucao_LA(agendamentos: list[dict[str, Any]]) -> float:
    """
    Média mensal de agendamentos criados (DATA_HORA_CRIACAO), considerando o
    histórico completo da lista informada (independente do período selecionado).

    Usado para medir o ritmo médio de entrada de uma atividade específica (ex.:
    "Elaborar Cumprimento de Sentença"), a partir de `agendamentos` já restrito
    por :func:`filtrar_agendamentos_execucao_LA`.
    """
    meses: defaultdict[str, int] = defaultdict(int)
    for row in agendamentos:
        criacao = _get_ag_data_criacao(row)
        if criacao is None:
            continue
        meses[f"{criacao.year}-{criacao.month:02d}"] += 1
    if not meses:
        return 0.0
    total = sum(meses.values())
    return round(total / len(meses), 2)


def group_execucao_processos_por_atividade_LA(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Processos distintos por atividade (agendamentos criados no período)."""
    base = [
        row for row in agendamentos
        if _ag_data_no_periodo(_get_ag_data_criacao(row), from_date, to_date)
    ]
    grouped: dict[str, set[Any]] = defaultdict(set)
    for row in base:
        pid = _get_ag_processo_id(row)
        if pid is None:
            continue
        grouped[_get_ag_atividade_nome(row)].add(pid)

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


def group_atividades_ativas_criadas_por_atividade_LA(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Quantidade de agendamentos ATIVOS (status fora de `_STATUS_INATIVO_EXEC`)
    criados no período, agrupados por atividade.

    Mesmo critério de contagem do card "Total de atividades"
    (:func:`get_kpis_atividades_execucao_LA`), porém quebrado por nome da
    atividade — ao contrário de :func:`group_execucao_processos_por_atividade_LA`,
    que conta processos distintos (não agendamentos) e não filtra por status.
    """
    contagem: defaultdict[str, int] = defaultdict(int)
    for row in agendamentos:
        status = _get_ag_status(row) or ""
        if status in _STATUS_INATIVO_EXEC:
            continue
        criacao = _get_ag_data_criacao(row)
        if not _ag_data_no_periodo(criacao, from_date, to_date):
            continue
        contagem[_get_ag_atividade_nome(row)] += 1

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


def group_atividades_criadas_por_atividade_LA(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Quantidade de agendamentos criados no período, agrupados por atividade —
    mesmo critério de contagem de ``total_atividades_criadas_execucao_LA``
    (:func:`get_kpis_atividades_execucao_LA`): conta tudo que chegou no
    período, mesmo já concluído, só excluindo Cancelado.

    Cada item também traz ``concluidos``: quantos desses agendamentos, da mesma
    atividade, foram encerrados (Cumprido ou Não Cumprido) com conclusão dentro do
    período — mesmo critério de ``atividades_execucao_concluidas_LA`` — para
    destacar no mesmo gráfico "Por Atividade" quantos do total já foram concluídos.

    Também traz ``abertas``: quantos agendamentos dessa atividade estão atualmente
    em aberto (não encerrados/cancelados), independente de quando foram criados —
    mesmo critério (e mesma população agregada) de ``atividades_execucao_abertas_LA``
    (:func:`get_kpis_atividades_execucao_LA`), só que quebrado por atividade. Não
    confundir com "value - concluidos": são populações diferentes, já que um
    agendamento aberto pode ter sido criado fora do período selecionado.
    """
    contagem: defaultdict[str, int] = defaultdict(int)
    concluidos: defaultdict[str, int] = defaultdict(int)
    abertas: defaultdict[str, int] = defaultdict(int)
    for row in agendamentos:
        status = _get_ag_status(row) or ""
        nome = _get_ag_atividade_nome(row)
        criacao = _get_ag_data_criacao(row)
        if status != "Cancelado" and _ag_data_no_periodo(criacao, from_date, to_date):
            contagem[nome] += 1
        if status in _STATUS_ENCERRADO_EXEC:
            conclusao = _get_ag_data_conclusao(row)
            if _ag_data_no_periodo(conclusao, from_date, to_date):
                concluidos[nome] += 1
        if status not in _STATUS_INATIVO_EXEC:
            abertas[nome] += 1

    total = float(sum(contagem.values()))
    nomes = set(contagem) | set(abertas)
    itens = [
        {
            "name": nome,
            "value": float(contagem.get(nome, 0)),
            "percent": round(100.0 * float(contagem.get(nome, 0)) / total, 1) if total > 0 else 0.0,
            "concluidos": float(concluidos.get(nome, 0)),
            "abertas": float(abertas.get(nome, 0)),
        }
        for nome in nomes
    ]
    return sorted(itens, key=lambda x: float(x["value"]), reverse=True)


def group_atividades_ativas_por_prazo_por_atividade_LA(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Quantidade de agendamentos ATIVOS com PRAZO no período, agrupados por
    atividade.

    Mesmo critério de contagem do "Total" na visão "Por prazo"
    (:func:`get_kpis_execucao_por_prazo_LA`), porém quebrado por nome da
    atividade.
    """
    contagem: defaultdict[str, int] = defaultdict(int)
    for row in agendamentos:
        status = _get_ag_status(row) or ""
        if status in _STATUS_INATIVO_EXEC:
            continue
        prazo = _get_ag_prazo(row)
        if not _ag_data_no_periodo(prazo, from_date, to_date):
            continue
        contagem[_get_ag_atividade_nome(row)] += 1

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


def group_execucao_demandas_por_funcionario_LA(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Demandas encerradas por funcionário (Cumprido / Não Cumprido) no período."""
    base = _filtrar_ag_encerrados_no_periodo(
        agendamentos, from_date, to_date, exigir_encerrador=True
    )
    grouped: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in base:
        funcionario = _get_ag_funcionario_encerramento(row)
        if not funcionario:
            continue
        status = _get_ag_status(row) or ""
        slug = _SLUG_POR_STATUS_EXEC.get(status)
        if slug is None:
            continue
        grouped[funcionario][slug] += 1

    itens: list[dict[str, Any]] = []
    for nome, contagens in grouped.items():
        item: dict[str, Any] = {"name": nome}
        total = 0
        for slug, _ in _STATUS_DEMANDAS_FUNCIONARIO_EXEC:
            valor = int(contagens.get(slug, 0))
            item[slug] = valor
            total += valor
        item["total"] = total
        if total > 0:
            itens.append(item)
    return sorted(itens, key=lambda x: int(x["total"]), reverse=True)


_SEM_FUNCIONARIO_ENCERRAMENTO_EXEC = "Sem funcionário identificado"


def group_execucao_demandas_por_funcionario_completo_LA(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Demandas encerradas por funcionário (Cumprido / Não Cumprido) no período,
    incluindo uma linha "Sem funcionário identificado" para agendamentos
    encerrados sem usuário de encerramento registrado.

    Ao contrário de :func:`group_execucao_demandas_por_funcionario_LA` (que
    descarta esses agendamentos), a soma deste resultado sempre bate com
    ``atividades_execucao_concluidas_LA`` (:func:`get_kpis_atividades_execucao_LA`).
    """
    base = _filtrar_ag_encerrados_no_periodo(agendamentos, from_date, to_date)
    grouped: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in base:
        funcionario = _get_ag_funcionario_encerramento(row) or _SEM_FUNCIONARIO_ENCERRAMENTO_EXEC
        status = _get_ag_status(row) or ""
        slug = _SLUG_POR_STATUS_EXEC.get(status)
        if slug is None:
            continue
        grouped[funcionario][slug] += 1

    itens: list[dict[str, Any]] = []
    for nome, contagens in grouped.items():
        item: dict[str, Any] = {"name": nome}
        total = 0
        for slug, _ in _STATUS_DEMANDAS_FUNCIONARIO_EXEC:
            valor = int(contagens.get(slug, 0))
            item[slug] = valor
            total += valor
        item["total"] = total
        if total > 0:
            itens.append(item)
    return sorted(itens, key=lambda x: int(x["total"]), reverse=True)


def group_taxa_conclusao_por_funcionario_LA(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Taxa de conclusão por colaborador — LA: agrupa por funcionário ATRIBUÍDO (não
    quem encerrou), diferente de :func:`group_execucao_demandas_por_funcionario_completo_LA`.
    Para cada colaborador, conta quantas atividades dele estão concluídas (encerrado
    Cumprido ou Não Cumprido, com conclusão no período selecionado — mesmo critério
    de ``atividades_execucao_concluidas_LA``) e quantas ainda estão em aberto com ele
    (status ativo, independente do período — mesmo critério de ``atividades_execucao_abertas_LA``).

    ``percent`` = concluídas ÷ (concluídas + abertas) dele — responde "que fração do
    que está com esse colaborador já foi resolvida", ao contrário da taxa geral da
    seção (que mistura todo mundo).
    """
    concluidas: dict[str, int] = defaultdict(int)
    abertas: dict[str, int] = defaultdict(int)
    for row in agendamentos:
        funcionario = _get_ag_funcionario_atribuido(row)
        status = _get_ag_status(row) or ""
        if status in _STATUS_ENCERRADO_EXEC:
            conclusao = _get_ag_data_conclusao(row)
            if _ag_data_no_periodo(conclusao, from_date, to_date):
                concluidas[funcionario] += 1
        elif status not in _STATUS_INATIVO_EXEC:
            abertas[funcionario] += 1

    nomes = set(concluidas) | set(abertas)
    itens: list[dict[str, Any]] = []
    for nome in nomes:
        c = concluidas.get(nome, 0)
        a = abertas.get(nome, 0)
        total = c + a
        if total == 0:
            continue
        itens.append({
            "name": nome,
            "encerrado_cumprido": c,
            "abertas": a,
            "total": total,
            "percent": round(100.0 * c / total, 1) if total > 0 else 0.0,
        })
    return sorted(itens, key=lambda x: int(x["total"]), reverse=True)


_ATIVIDADES_FLUXO_CS_1G_LA = frozenset(
    x.casefold() for x in ("Elaborar Cumprimento de Sentença (1G)", "Manifestação Cálculo 1")
)
_ATIVIDADES_FLUXO_CS_2G_LA = frozenset(
    x.casefold() for x in ("Elaborar Cumprimento de Sentença (2G)", "Manifestação Cálculo 2")
)
# Atividade antiga sem grau no nome: vai numa linha própria (decisão do negócio, out/2026 —
# inferir o grau pelo acórdão errava ~43% dos 1G no NG).
_ATIVIDADES_FLUXO_CS_SEM_GRAU_LA = frozenset({"Elaborar Cumprimento de Sentença".casefold()})
_FLUXO_CS_SEM_GRAU_LABEL_LA = "CS (sem grau)"
_JANELA_FLUXO_CS_DIAS_LA = 30


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

    grouped: dict[str, dict[str, Any]] = {}
    for p in _filtrar_entrada_execucao_no_periodo(execucao):
        data_exe = _get_data_execucao(p)
        pid = _to_int(p.get("id") or p.get("ID"))
        if data_exe is None:
            continue
        candidatos = [
            (abs((conclusao - data_exe).days), prioridade, grau)
            for conclusao, prioridade, grau in cs_por_processo.get(pid, ())
            if abs((conclusao - data_exe).days) <= _JANELA_FLUXO_CS_DIAS_LA
        ]
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
        grau = min(candidatos)[2] if candidatos else "Outros"
        grouped[month_key][grau] += 1

    return [grouped[k] for k in sorted(grouped)]


def group_execucao_resolvidos_por_dia_LA(
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
        if _get_ag_status(row) != _STATUS_CUMPRIDO_EXEC:
            continue
        conclusao = _get_ag_data_conclusao(row)
        if conclusao is None:
            continue
        grouped[conclusao.strftime("%Y-%m-%d")] += 1

    return [
        {"name": dia, "value": count}
        for dia, count in sorted(grouped.items(), key=lambda x: x[0])
    ]


def get_media_execucao_resolvidos_por_funcionario_LA(
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
        if _get_ag_status(row) != _STATUS_CUMPRIDO_EXEC:
            continue
        conclusao = _get_ag_data_conclusao(row)
        if conclusao is None or not _ag_data_no_periodo(conclusao, from_date, to_date):
            continue
        funcionario = _get_ag_funcionario_encerramento(row)
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


def group_valor_recuperado_por_funcionario_LA(
    agendamentos: list[dict[str, Any]],
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Valor recuperado (``VALOR_TED``) por funcionário responsável pelo encerramento
    das demandas de Execução no período.

    Atribui a cada funcionário o ``VALOR_TED`` dos processos que ele encerrou
    (agendamento com status Cumprido/Não Cumprido), deduplicando por par
    (funcionário, processo) para não contar o mesmo processo mais de uma vez
    quando há múltiplas atividades encerradas nele.
    """
    valor_ted_por_processo: dict[int, float] = {}
    for p in _filtrar_saida_no_periodo(execucao, from_date, to_date):
        processo_id = _to_int(p.get("id") or p.get("ID"))
        if processo_id is None:
            continue
        valor = _get_valor_ted(p)
        if valor is not None:
            valor_ted_por_processo[processo_id] = _converter_valor(valor)

    base = _filtrar_ag_encerrados_no_periodo(
        agendamentos, from_date, to_date, exigir_encerrador=True
    )
    vistos: set[tuple[str, int]] = set()
    totais: defaultdict[str, float] = defaultdict(float)

    for row in base:
        funcionario = _get_ag_funcionario_encerramento(row)
        if not funcionario:
            continue
        processo_id = _to_int(_get_ag_processo_id(row))
        if processo_id is None:
            continue
        valor_ted = valor_ted_por_processo.get(processo_id)
        if valor_ted is None:
            continue
        chave = (funcionario, processo_id)
        if chave in vistos:
            continue
        vistos.add(chave)
        totais[funcionario] += valor_ted

    total_geral = sum(totais.values())
    itens = [
        {
            "name": nome,
            "value": round(valor, 2),
            "percent": round(100.0 * valor / total_geral, 1) if total_geral > 0 else 0.0,
        }
        for nome, valor in totais.items()
        if valor > 0
    ]
    return sorted(itens, key=lambda x: float(x["value"]), reverse=True)


def list_execucao_atividades_periodo_LA(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Lista de agendamentos do setor Execução para a tabela de tarefas."""
    ref = ref_date or date.today()
    itens: list[dict[str, Any]] = []

    for row in agendamentos:
        if not _incluir_na_lista_exec(row, from_date, to_date, ref_date=ref):
            continue
        ag_id = _to_int(row.get("id") or row.get("ID"))
        if ag_id is None:
            continue
        status = _get_ag_status(row) or "—"
        prazo = _get_ag_prazo(row)
        criacao = _get_ag_data_criacao(row)
        situacao = _classificar_situacao_exec(row, from_date, to_date, ref_date=ref)
        funcionario_atrib = _get_ag_funcionario_atribuido(row)
        funcionario_enc = _get_ag_funcionario_encerramento(row)
        encerrado_pelo_responsavel: bool | None = None
        if status in _STATUS_ENCERRADO_EXEC and funcionario_enc is not None:
            encerrado_pelo_responsavel = (
                funcionario_enc.strip().lower() == funcionario_atrib.strip().lower()
            )
        setor = str(row.get("SETOR") or row.get("setor") or "EXECUÇÃO").strip().upper()
        atividade = _get_ag_atividade_nome(row)
        pessoa_setor = (
            f"{setor} - {atividade}"
            if atividade and atividade != _SEM_ATIVIDADE_EXEC
            else setor
        )
        descricao_raw = row.get("DESCRICAO") or row.get("descricao")
        descricao = str(descricao_raw).strip().upper() if descricao_raw else "—"
        operacao = str(row.get("OPERACAO") or row.get("operacao") or "").strip()

        conclusao = _get_ag_data_conclusao(row)

        itens.append({
            "id": ag_id,
            "status": status,
            "descricao": descricao,
            "pessoa_setor": pessoa_setor,
            "funcionario": _get_ag_funcionario_nome(row),
            "funcionario_atribuido": funcionario_atrib,
            "funcionario_encerramento": funcionario_enc,
            "atividade": atividade,
            "prazo": prazo.isoformat() if prazo else None,
            "criado_em": criacao.isoformat() if criacao else None,
            "concluido_em": conclusao.isoformat() if conclusao else None,
            "operacao": operacao,
            "encerrado_pelo_responsavel": encerrado_pelo_responsavel,
            "numero_processo": _get_ag_numero_processo(row),
            "valor_sentenca": _get_ag_valor_sentenca(row),
            "valor_acordao": _get_ag_valor_acordao(row),
            **situacao,
        })

    def _sort_key(item: dict[str, Any]) -> tuple[int, str, int]:
        prazo_raw = item.get("prazo")
        prazo_missing = 0 if prazo_raw else 1
        return (prazo_missing, str(prazo_raw or ""), int(item.get("id") or 0))

    return sorted(itens, key=_sort_key)


def list_execucao_atividades_abertas_LA(
    agendamentos: list[dict[str, Any]],
    *,
    ref_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Lista de agendamentos atualmente abertos (ainda não concluídos/cancelados) do
    setor Execução LA, independente de quando foram criados ou do período
    selecionado no calendário.

    Usada no modal do card unificado "Em andamento" da Confecção CS, que substitui
    os antigos cards separados "Em andamento" (restrito ao período) e "Represados"
    (o subconjunto vencido/vence hoje) — ver :func:`get_kpis_atividades_execucao_LA`.
    """
    ref = ref_date or date.today()
    itens: list[dict[str, Any]] = []

    for row in agendamentos:
        status = _get_ag_status(row) or ""
        if status in _STATUS_INATIVO_EXEC:
            continue
        ag_id = _to_int(row.get("id") or row.get("ID"))
        if ag_id is None:
            continue
        prazo = _get_ag_prazo(row)
        criacao = _get_ag_data_criacao(row)
        funcionario_atrib = _get_ag_funcionario_atribuido(row)
        setor = str(row.get("SETOR") or row.get("setor") or "EXECUÇÃO").strip().upper()
        atividade = _get_ag_atividade_nome(row)
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
            "funcionario": _get_ag_funcionario_nome(row),
            "funcionario_atribuido": funcionario_atrib,
            "funcionario_encerramento": None,
            "atividade": atividade,
            "prazo": prazo.isoformat() if prazo else None,
            "criado_em": criacao.isoformat() if criacao else None,
            "concluido_em": None,
            "operacao": operacao,
            "encerrado_pelo_responsavel": None,
            "numero_processo": _get_ag_numero_processo(row),
            "valor_sentenca": _get_ag_valor_sentenca(row),
            "valor_acordao": _get_ag_valor_acordao(row),
            "em_andamento": status in _STATUS_EM_ANDAMENTO_EXEC,
            "vencida": prazo is not None and prazo < ref,
            "vence_hoje": prazo is not None and prazo == ref,
            "concluida": False,
        })

    def _sort_key(item: dict[str, Any]) -> tuple[int, str, int]:
        prazo_raw = item.get("prazo")
        prazo_missing = 0 if prazo_raw else 1
        return (prazo_missing, str(prazo_raw or ""), int(item.get("id") or 0))

    return sorted(itens, key=_sort_key)


def get_opcoes_filtros_execucao_LA(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, Any]:
    """Opções de filtros da lista de tarefas (funcionários, atividades, status, situações)."""
    rows = list_execucao_atividades_periodo_LA(
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
            {"id": sid, "label": label} for sid, label in _SITUACOES_FILTRO_EXEC
        ],
    }


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

def _incluir_na_lista_por_prazo_exec(
    row: dict[str, Any],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> bool:
    prazo = _get_ag_prazo(row)
    return _ag_data_no_periodo(prazo, from_date, to_date)


def _classificar_situacao_por_prazo_exec(
    row: dict[str, Any],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, bool]:
    ref = ref_date or date.today()
    prazo = _get_ag_prazo(row)
    status = _get_ag_status(row) or ""
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


def group_execucao_processos_por_atividade_por_prazo_LA(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Processos distintos por atividade (agendamentos com prazo no período) — LA."""
    base = [
        row for row in agendamentos
        if _ag_data_no_periodo(_get_ag_prazo(row), from_date, to_date)
    ]
    grouped: dict[str, set[Any]] = defaultdict(set)
    for row in base:
        pid = _get_ag_processo_id(row)
        if pid is None:
            continue
        grouped[_get_ag_atividade_nome(row)].add(pid)

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


def group_execucao_demandas_por_funcionario_por_prazo_LA(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Demandas encerradas por funcionário (Cumprido / Não Cumprido), com PRAZO no período — LA."""
    base = [
        row for row in agendamentos
        if (_get_ag_status(row) or "") in _STATUS_ENCERRADO_EXEC
        and _ag_data_no_periodo(_get_ag_prazo(row), from_date, to_date)
        and _get_ag_funcionario_encerramento(row) is not None
    ]
    grouped: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in base:
        funcionario = _get_ag_funcionario_encerramento(row)
        if not funcionario:
            continue
        status = _get_ag_status(row) or ""
        slug = _SLUG_POR_STATUS_EXEC.get(status)
        if slug is None:
            continue
        grouped[funcionario][slug] += 1

    itens: list[dict[str, Any]] = []
    for nome, contagens in grouped.items():
        item: dict[str, Any] = {"name": nome}
        total = 0
        for slug, _ in _STATUS_DEMANDAS_FUNCIONARIO_EXEC:
            valor = int(contagens.get(slug, 0))
            item[slug] = valor
            total += valor
        item["total"] = total
        if total > 0:
            itens.append(item)
    return sorted(itens, key=lambda x: int(x["total"]), reverse=True)


def group_execucao_demandas_por_funcionario_por_prazo_completo_LA(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Demandas encerradas por funcionário (Cumprido / Não Cumprido), com PRAZO no
    período — LA, incluindo uma linha "Sem funcionário identificado" para
    agendamentos encerrados sem usuário de encerramento registrado.

    Ao contrário de :func:`group_execucao_demandas_por_funcionario_por_prazo_LA`
    (que descarta esses agendamentos), a soma deste resultado sempre bate com
    ``por_prazo_concluidas_execucao_LA`` (:func:`get_kpis_execucao_por_prazo_LA`).
    """
    base = [
        row for row in agendamentos
        if (_get_ag_status(row) or "") in _STATUS_ENCERRADO_EXEC
        and _ag_data_no_periodo(_get_ag_prazo(row), from_date, to_date)
    ]
    grouped: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in base:
        funcionario = _get_ag_funcionario_encerramento(row) or _SEM_FUNCIONARIO_ENCERRAMENTO_EXEC
        status = _get_ag_status(row) or ""
        slug = _SLUG_POR_STATUS_EXEC.get(status)
        if slug is None:
            continue
        grouped[funcionario][slug] += 1

    itens: list[dict[str, Any]] = []
    for nome, contagens in grouped.items():
        item: dict[str, Any] = {"name": nome}
        total = 0
        for slug, _ in _STATUS_DEMANDAS_FUNCIONARIO_EXEC:
            valor = int(contagens.get(slug, 0))
            item[slug] = valor
            total += valor
        item["total"] = total
        if total > 0:
            itens.append(item)
    return sorted(itens, key=lambda x: int(x["total"]), reverse=True)


def list_execucao_atividades_por_prazo_periodo_LA(
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
        if not _incluir_na_lista_por_prazo_exec(row, from_date, to_date, ref_date=ref):
            continue
        ag_id = _to_int(row.get("id") or row.get("ID"))
        if ag_id is None:
            continue
        status = _get_ag_status(row) or "—"
        prazo = _get_ag_prazo(row)
        criacao = _get_ag_data_criacao(row)
        situacao = _classificar_situacao_por_prazo_exec(row, from_date, to_date, ref_date=ref)
        funcionario_atrib = _get_ag_funcionario_atribuido(row)
        funcionario_enc = _get_ag_funcionario_encerramento(row)
        encerrado_pelo_responsavel: bool | None = None
        if status in _STATUS_ENCERRADO_EXEC and funcionario_enc is not None:
            encerrado_pelo_responsavel = (
                funcionario_enc.strip().lower() == funcionario_atrib.strip().lower()
            )
        setor = str(row.get("SETOR") or row.get("setor") or "EXECUÇÃO").strip().upper()
        atividade = _get_ag_atividade_nome(row)
        pessoa_setor = (
            f"{setor} - {atividade}"
            if atividade and atividade != _SEM_ATIVIDADE_EXEC
            else setor
        )
        descricao_raw = row.get("DESCRICAO") or row.get("descricao")
        descricao = str(descricao_raw).strip().upper() if descricao_raw else "—"
        operacao = str(row.get("OPERACAO") or row.get("operacao") or "").strip()

        conclusao = _get_ag_data_conclusao(row)

        itens.append({
            "id": ag_id,
            "status": status,
            "descricao": descricao,
            "pessoa_setor": pessoa_setor,
            "funcionario": _get_ag_funcionario_nome(row),
            "funcionario_atribuido": funcionario_atrib,
            "funcionario_encerramento": funcionario_enc,
            "atividade": atividade,
            "prazo": prazo.isoformat() if prazo else None,
            "criado_em": criacao.isoformat() if criacao else None,
            "concluido_em": conclusao.isoformat() if conclusao else None,
            "operacao": operacao,
            "encerrado_pelo_responsavel": encerrado_pelo_responsavel,
            "numero_processo": _get_ag_numero_processo(row),
            **situacao,
        })

    def _sort_key(item: dict[str, Any]) -> tuple[int, str, int]:
        prazo_raw = item.get("prazo")
        prazo_missing = 0 if prazo_raw else 1
        return (prazo_missing, str(prazo_raw or ""), int(item.get("id") or 0))

    return sorted(itens, key=_sort_key)


def get_opcoes_filtros_execucao_por_prazo_LA(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, Any]:
    """Opções de filtros da lista por prazo — LA."""
    rows = list_execucao_atividades_por_prazo_periodo_LA(
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
            {"id": sid, "label": label} for sid, label in _SITUACOES_FILTRO_EXEC
        ],
    }


def group_execucao_resolvidos_por_dia_por_prazo_LA(
    agendamentos: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Produção diária (por prazo): quantidade de atividades "Encerrado Cumprido"
    por dia de PRAZO, histórico completo — LA.
    """
    grouped: dict[str, int] = defaultdict(int)
    for row in agendamentos:
        if _get_ag_status(row) != _STATUS_CUMPRIDO_EXEC:
            continue
        prazo = _get_ag_prazo(row)
        if prazo is None:
            continue
        grouped[prazo.strftime("%Y-%m-%d")] += 1

    return [
        {"name": dia, "value": count}
        for dia, count in sorted(grouped.items(), key=lambda x: x[0])
    ]


def get_media_execucao_resolvidos_por_funcionario_por_prazo_LA(
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
        if _get_ag_status(row) != _STATUS_CUMPRIDO_EXEC:
            continue
        prazo = _get_ag_prazo(row)
        if prazo is None or not _ag_data_no_periodo(prazo, from_date, to_date):
            continue
        funcionario = _get_ag_funcionario_encerramento(row)
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

def _get_ag_motivo_encaminhamento_itens(item: dict[str, Any]) -> list[dict[str, Any]]:
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


def group_execucao_nao_cumprido_por_motivo_LA(
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
        if _get_ag_status(row) != "Encerrado Não Cumprido":
            continue
        for it in _get_ag_motivo_encaminhamento_itens(row):
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
# Detalhamento de atrasos (vencidas por dias de atraso)
# ---------------------------------------------------------------------------

_ATRASO_MAX_BUCKET = 6  # bucket 6 = "6 dias ou mais"

_BUCKET_META: dict[int, tuple[str, str]] = {
    1: ("1 dia",          "Venceu ontem"),
    2: ("2 dias",         "Há 2 dias de atraso"),
    3: ("3 dias",         "Há 3 dias de atraso"),
    4: ("4 dias",         "Há 4 dias de atraso"),
    5: ("5 dias",         "Há 5 dias de atraso"),
    6: ("6 dias ou mais", "Atraso prolongado"),
}


def get_atrasos_detalhamento_execucao_LA(
    agendamentos: list[dict[str, Any]],
    *,
    ref_date: Optional[date] = None,
) -> dict[str, Any]:
    """Detalhamento de agendamentos vencidos por dias de atraso (1–5 e 6+).

    Alinhado ao card «Vencidas»: qualquer agendamento ativo com prazo < hoje,
    independente do período de criação/conclusão.
    """
    ref = ref_date or date.today()
    counts: dict[int, int] = {d: 0 for d in range(1, _ATRASO_MAX_BUCKET + 1)}

    for row in agendamentos:
        status = _get_ag_status(row) or ""
        if status in _STATUS_INATIVO_EXEC:
            continue
        prazo = _get_ag_prazo(row)
        if prazo is None or prazo >= ref:
            continue
        dias = (ref - prazo).days
        bucket = min(dias, _ATRASO_MAX_BUCKET)
        counts[bucket] += 1

    total = sum(counts.values())

    buckets = []
    for dias in range(1, _ATRASO_MAX_BUCKET + 1):
        count = counts[dias]
        pct = round(100.0 * count / total, 1) if total > 0 else 0.0
        label, descricao = _BUCKET_META[dias]
        buckets.append({
            "dias": dias,
            "label": label,
            "descricao": descricao,
            "count": count,
            "pct": pct,
        })

    return {"total": total, "buckets": buckets}

def group_estoque_execucao_por_mes_LA(
    execucao: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Estoque em Execução ao fim de cada mês: (quantidade, valor em aberto) —
    base do "Ticket Médio Total" mês a mês.

    Reconstrução histórica: o processo conta do mês de ``DATA_EXECUCAO`` até o
    mês anterior ao de ``DATA_COMPENSACAO_ALVARA``; sem data de saída, só conta
    se ainda está em Execução hoje (mesmo critério do card "Total em Execução"),
    já que não dá pra saber quando um processo arquivado sem compensação saiu.
    O valor segue :func:`_get_valor_execucao_em_aberto` no tempo: VALOR_EXECUCAO
    até o mês da compensação do incontroverso, VALOR_REMANESCENTE a partir dele.
    """
    intervalos = []
    for p in _base_execucao_LA(execucao):
        entrada = _get_data_execucao(p)
        if entrada is None:
            continue
        saida = _get_data_compensacao_alvara(p)
        if saida is None and not _processo_em_execucao(p):
            continue
        ini = indice_mes(entrada)
        fim = indice_mes(saida) if saida is not None else None
        valor_cheio = _converter_valor(_get_valor_execucao(p))
        incontroverso = _get_data_compensacao_alvara_incontroverso(p)
        if incontroverso is None:
            intervalos.append((ini, fim, True, valor_cheio))
            continue
        corte = indice_mes(incontroverso)
        fim_cheio = corte if fim is None else min(corte, fim)
        intervalos.append((ini, fim_cheio, True, valor_cheio))
        intervalos.append((max(ini, corte), fim, True, _converter_valor(_get_valor_remanescente(p))))
    return estoque_por_mes(intervalos, _MONTH_NAMES)


def filtrar_saida_execucao_export_LA(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Recorte "Saída" do relatório exportado: processos com compensação do alvará
    (:func:`_filtrar_saida_no_periodo`) OU com compensação do alvará do
    incontroverso (:func:`_filtrar_saida_incontroverso_no_periodo`) no período,
    sem repetir processo — os mesmos dois conjuntos que somam o card "Valor saída
    Execução" (:func:`get_valor_execucao_saida_periodo_LA`).
    """
    vistos: set[Any] = set()
    filtrados: list[dict[str, Any]] = []
    for item in (
        _filtrar_saida_no_periodo(execucao, from_date, to_date)
        + _filtrar_saida_incontroverso_no_periodo(execucao, from_date, to_date)
    ):
        chave = item.get("NUMERO_PROCESSO") or item.get("id") or item.get("ID")
        if chave is not None:
            if chave in vistos:
                continue
            vistos.add(chave)
        filtrados.append(item)
    return filtrados


def anotar_saida_execucao_export_LA(
    rows: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Devolve cópias das linhas com duas colunas calculadas para o relatório,
    seguindo a regra do incontroverso do card "Valor saída Execução":

    - ``TIPO_SAIDA_PERIODO``: "Total" (só o alvará compensado no período),
      "Parcial (incontroverso)" (só o incontroverso compensado no período — o
      processo segue em Execução aguardando o remanescente), "Incontroverso +
      remanescente" (as duas compensações no período) ou vazio (nenhuma).
    - ``VALOR_SAIDA_PERIODO``: o que de fato saiu no período — VALOR_INCONTROVERSO
      se o incontroverso foi compensado no período, mais o valor do alvará se ele
      foi compensado no período (VALOR_REMANESCENTE quando já houve incontroverso,
      senão VALOR_EXECUCAO cheio, via :func:`_get_valor_execucao_em_aberto`). A
      soma desta coluna no recorte "Saída" bate com o card.
    """
    anotadas: list[dict[str, Any]] = []
    for item in rows:
        saiu_alvara = _data_no_periodo(_get_data_compensacao_alvara(item), from_date, to_date)
        saiu_incontroverso = _data_no_periodo(
            _get_data_compensacao_alvara_incontroverso(item), from_date, to_date
        )

        valor_saida: Optional[float] = None
        if saiu_alvara or saiu_incontroverso:
            valor_saida = 0.0
            if saiu_alvara:
                valor = _get_valor_execucao_em_aberto(item)
                if valor is not None:
                    valor_saida += _converter_valor(valor)
            if saiu_incontroverso:
                valor = _get_valor_incontroverso(item)
                if valor is not None:
                    valor_saida += _converter_valor(valor)
            valor_saida = round(valor_saida, 2)

        if saiu_alvara and saiu_incontroverso:
            tipo = "Incontroverso + remanescente"
        elif saiu_alvara:
            tipo = "Total"
        elif saiu_incontroverso:
            tipo = "Parcial (incontroverso)"
        else:
            tipo = None

        nova = dict(item)
        nova["TIPO_SAIDA_PERIODO"] = tipo
        nova["VALOR_SAIDA_PERIODO"] = valor_saida
        anotadas.append(nova)
    return anotadas
