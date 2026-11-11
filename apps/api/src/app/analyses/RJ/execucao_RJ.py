# Funções de análises do setor de Execução (Condenação) — RJ
#
# Mirror de app/analyses/NG/execucao.py para o escritório Luis Albert RJ (LARJ,
# ID_ESCRITORIO=27). Mesma lógica de negócio; só muda o escritório-alvo e os
# nomes das funções (sufixo _RJ), seguindo o padrão já usado em
# app/analyses/RJ/execucao_acordos_RJ.py.

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

ID_FASE_EXECUCAO = 12
ID_FASE_FINANCEIRO = 26
ID_ESCRITORIO = 27
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


def _get_data_execucao_RJ(item: dict[str, Any]) -> Optional[date]:
    return _to_date(item.get("DATA_EXECUCAO") or item.get("data_execucao"))


def _get_data_compensacao_alvara_RJ(item: dict[str, Any]) -> Optional[date]:
    return _to_date(item.get("DATA_COMPENSACAO_ALVARA") or item.get("data_compensacao_alvara"))


def _get_data_compensacao_alvara_incontroverso_RJ(item: dict[str, Any]) -> Optional[date]:
    return _to_date(
        item.get("DATA_COMPENSACAO_ALVARA_INCONTROVERSO")
        or item.get("data_compensacao_alvara_incontroverso")
    )


def _get_data_encerramento_RJ(item: dict[str, Any]) -> Optional[date]:
    return _to_date(item.get("DATA_ENCERRAMENTO") or item.get("data_encerramento"))


def _get_ultima_movimentacao_RJ(item: dict[str, Any]) -> Optional[date]:
    return _to_date(
        item.get("ULTIMA_MOVIMENTACAO")
        or item.get("ultima_movimentacao")
        or item.get("DATA_ULTIMA_MOVIMENTACAO")
    )


def _get_data_distribuicao_rj(item: dict[str, Any]) -> Optional[date]:
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


def _base_execucao_RJ(execucao: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Base padrão das análises de Execução RJ: ID_ESCRITORIO == 27, deduplicado por
    NUMERO_PROCESSO — o identificador único do processo (a mesma NUMERO_PROCESSO pode
    aparecer em mais de uma linha ``processo``, ex.: joins 1:N com tabelas auxiliares
    ou múltiplos registros por processo na origem).

    Exclui processos com a etiqueta Acordo (``TEM_ETIQUETA_ACORDO``) — para RJ,
    essa coluna é computada na query ``execucao_RJ`` a partir dos IDs de etiqueta
    73/74/75/76 (RJ não tem uma etiqueta base "Acordo" isolada por nome, diferente
    de NG/LA — ver comentário na query em ``queries.py``).
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


def _get_valor_execucao_RJ(item: dict[str, Any]) -> Optional[Any]:
    """Retorna o valor bruto de VALOR_EXECUCAO, ou ``None`` se ausente/vazio."""
    raw = item.get("VALOR_EXECUCAO")
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None
    return raw


def _get_valor_ted_RJ(item: dict[str, Any]) -> Optional[Any]:
    """Retorna o valor bruto de VALOR_TED, ou ``None`` se ausente/vazio."""
    raw = item.get("VALOR_TED")
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None
    return raw


def _get_valor_incontroverso_RJ(item: dict[str, Any]) -> Optional[Any]:
    """Retorna o valor bruto de VALOR_INCONTROVERSO, ou ``None`` se ausente/vazio."""
    raw = item.get("VALOR_INCONTROVERSO")
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None
    return raw


def _get_valor_remanescente_RJ(item: dict[str, Any]) -> Optional[Any]:
    """Retorna o valor bruto de VALOR_REMANESCENTE, ou ``None`` se ausente/vazio."""
    raw = item.get("VALOR_REMANESCENTE")
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None
    return raw


def _get_valor_execucao_em_aberto_RJ(item: dict[str, Any]) -> Optional[Any]:
    """
    Retorna o valor ainda em aberto do processo: VALOR_REMANESCENTE quando já
    houve compensação do alvará do incontroverso (DATA_COMPENSACAO_ALVARA_INCONTROVERSO
    preenchida — a parte incontroversa já caiu e não representa mais valor "em
    execução"), ou VALOR_EXECUCAO cheio caso contrário (processo sem pagamento
    parcial ainda).
    """
    if _get_data_compensacao_alvara_incontroverso_RJ(item) is not None:
        return _get_valor_remanescente_RJ(item)
    return _get_valor_execucao_RJ(item)


def _get_valor_honorarios_RJ(item: dict[str, Any]) -> Optional[Any]:
    """
    Retorna o valor bruto de VALOR_HONORARIOS somente para processos na fase
    Financeiro (ID_FASE == 26), ou ``None`` se ausente/vazio.
    """
    if not _processo_fase_financeiro_RJ(item):
        return None
    raw = item.get("VALOR_HONORARIOS")
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None
    return raw


def _processo_em_execucao_RJ(item: dict[str, Any]) -> bool:
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


def _processo_fase_financeiro_RJ(item: dict[str, Any]) -> bool:
    """Retorna True se o processo está na fase Financeiro."""
    id_fase = item.get("ID_FASE")
    return id_fase is not None and int(id_fase) == ID_FASE_FINANCEIRO


# =============================================================================
# 2 - Queries de filtragem
# =============================================================================

def _filtrar_em_execucao_RJ(execucao: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Retorna somente os processos na fase de Execução (ID_FASE == 12)."""
    return [e for e in _base_execucao_RJ(execucao) if _processo_em_execucao_RJ(e)]


def _filtrar_entrada_execucao_RJ_no_periodo(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Processos com ``DATA_EXECUCAO`` preenchida cuja data está no período informado,
    garantindo unicidade por NUMERO_PROCESSO, o identificador único do processo (mesmo critério de
    :func:`_filtrar_saida_no_periodo_RJ`).
    """
    vistos: set[Any] = set()
    filtrados: list[dict[str, Any]] = []

    for item in _base_execucao_RJ(execucao):
        data_exe = _get_data_execucao_RJ(item)
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


def _filtrar_saida_no_periodo_RJ(
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

    for item in _base_execucao_RJ(execucao):
        data_compensacao = _get_data_compensacao_alvara_RJ(item)
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


def _filtrar_saida_incontroverso_no_periodo_RJ(
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

    for item in _base_execucao_RJ(execucao):
        data_incontroverso = _get_data_compensacao_alvara_incontroverso_RJ(item)
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



def _primeiro_valor_preenchido_rj(p: dict[str, Any], *campos: str) -> float:
    """Primeiro campo com valor diferente de zero, ou ``0.0``."""
    for campo in campos:
        raw = p.get(campo)
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            continue
        valor = _converter_valor(raw)
        if valor:
            return valor
    return 0.0


def group_alvaras_expedidos_por_dia_RJ(execucao: list[dict[str, Any]]) -> list[dict[str, Any]]:
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

    for p in _base_execucao_RJ(execucao):
        exp_incontroverso = _to_date(p.get("DATA_EXPEDICAO_ALVARA_INCONTROVERSO"))
        exp_total = _to_date(p.get("DATA_EXPEDICAO_ALVARA"))
        if exp_incontroverso is not None:
            _somar(
                exp_incontroverso,
                _primeiro_valor_preenchido_rj(p, "VALOR_ALVARA_INCONTROVERSO", "VALOR_INCONTROVERSO"),
            )
        if exp_total is not None:
            teve_incontroverso = (
                exp_incontroverso is not None or _get_data_compensacao_alvara_incontroverso_RJ(p) is not None
            )
            campos = ("VALOR_ALVARA", "VALOR_REMANESCENTE") if teve_incontroverso else ("VALOR_ALVARA",)
            _somar(exp_total, _primeiro_valor_preenchido_rj(p, *campos))

    return [
        {**por_dia[k], "valor": round(por_dia[k]["valor"], 2)}
        for k in sorted(por_dia)
    ]


_SUBFASE_ALVARA_EXPEDIDO = "ALVARÁ EXPEDIDO"


def list_processos_alvara_expedido_RJ(execucao: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
    for p in _filtrar_em_execucao_RJ(execucao):
        if _normalizar_subfase(p.get("SUBFASE")).casefold() != _SUBFASE_ALVARA_EXPEDIDO.casefold():
            continue
        exp_total = _to_date(p.get("DATA_EXPEDICAO_ALVARA"))
        exp_incontroverso = _to_date(p.get("DATA_EXPEDICAO_ALVARA_INCONTROVERSO"))
        teve_incontroverso = (
            exp_incontroverso is not None
            or _get_data_compensacao_alvara_incontroverso_RJ(p) is not None
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


def filter_execucao_RJ_por_materia(
    execucao: list[dict[str, Any]],
    materia: Optional[Any] = None,
) -> list[dict[str, Any]]:
    # Aceita um valor único ou uma lista (seleção múltipla no filtro da página).
    valores = materia if isinstance(materia, (list, tuple, set)) else [materia]
    alvos = {_normalizar_materia(v) for v in valores if v is not None and str(v).strip()}
    if not alvos:
        return _base_execucao_RJ(execucao)
    return [
        p for p in _base_execucao_RJ(execucao)
        if _normalizar_materia(p.get("MATERIA")) in alvos
    ]


def filter_execucao_RJ_por_subfase(
    execucao: list[dict[str, Any]],
    subfase: Optional[Any] = None,
) -> list[dict[str, Any]]:
    # Aceita um valor único ou uma lista (seleção múltipla no filtro da página).
    valores = subfase if isinstance(subfase, (list, tuple, set)) else [subfase]
    alvos = {_normalizar_subfase(v) for v in valores if v is not None and str(v).strip()}
    if not alvos:
        return _base_execucao_RJ(execucao)
    return [
        p for p in _base_execucao_RJ(execucao)
        if _normalizar_subfase(p.get("SUBFASE")) in alvos
    ]


_SEM_ANO_AJUIZAMENTO_EXEC_RJ = "Sem data de ajuizamento"


def filter_execucao_RJ_por_ano_ajuizamento(
    execucao: list[dict[str, Any]],
    ano_ajuizamento: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Filtra pelo ano de ajuizamento (DATA_DISTRIBUICAO), ou por `_SEM_ANO_AJUIZAMENTO_EXEC_RJ`."""
    alvo = str(ano_ajuizamento).strip() if ano_ajuizamento else ""
    if not alvo:
        return _base_execucao_RJ(execucao)
    return [
        p for p in _base_execucao_RJ(execucao)
        if (
            str(d.year) if (d := _get_data_distribuicao_rj(p)) else _SEM_ANO_AJUIZAMENTO_EXEC_RJ
        )
        == alvo
    ]


def filter_execucao_RJ_por_uf(
    execucao: list[dict[str, Any]],
    ufs: Optional[list[str]] = None,
) -> list[dict[str, Any]]:
    """Sem UFs informadas, não filtra. Caso contrário, mantém só as UFs selecionadas."""
    base = _base_execucao_RJ(execucao)
    alvo = {str(u).strip().upper() for u in ufs if str(u).strip()} if ufs else set()
    if not alvo:
        return base
    return [p for p in base if str(p.get("UF") or "").strip().upper() in alvo]


def get_opcoes_uf_execucao_RJ(execucao: list[dict[str, Any]]) -> list[str]:
    """UFs distintas (não vazias) presentes na base de Execução RJ, em ordem alfabética."""
    ufs = {
        str(p.get("UF") or "").strip().upper()
        for p in _base_execucao_RJ(execucao)
    }
    ufs.discard("")
    return sorted(ufs)


def filter_execucao_RJ_por_comarca(
    execucao: list[dict[str, Any]],
    comarcas: Optional[list[str]] = None,
) -> list[dict[str, Any]]:
    """Sem comarcas informadas, não filtra. Caso contrário, mantém só as comarcas selecionadas."""
    base = _base_execucao_RJ(execucao)
    alvo = {_normalizar_comarca(c) for c in comarcas if str(c).strip()} if comarcas else set()
    if not alvo:
        return base
    return [p for p in base if _normalizar_comarca(p.get("COMARCA")) in alvo]


def get_opcoes_comarca_execucao_RJ(execucao: list[dict[str, Any]]) -> list[str]:
    """Comarcas distintas (não vazias) presentes na base de Execução RJ, em ordem alfabética."""
    comarcas = {
        _normalizar_comarca(p.get("COMARCA"))
        for p in _base_execucao_RJ(execucao)
    }
    comarcas.discard("Sem comarca")
    return sorted(comarcas)


def get_opcoes_materia_execucao_RJ(execucao: list[dict[str, Any]]) -> list[str]:
    """Matérias distintas (não vazias) presentes na base de Execução RJ, em ordem alfabética."""
    materias = {
        _normalizar_materia(p.get("MATERIA"))
        for p in _base_execucao_RJ(execucao)
    }
    materias.discard("Sem materia")
    return sorted(materias)


def get_opcoes_subfase_execucao_RJ(execucao: list[dict[str, Any]]) -> list[str]:
    """Subfases distintas (não vazias) presentes na base de Execução RJ, em ordem alfabética."""
    subfases = {
        _normalizar_subfase(p.get("SUBFASE"))
        for p in _base_execucao_RJ(execucao)
    }
    subfases.discard("Sem subfase")
    return sorted(subfases)


# =============================================================================
# 3 - Totais
# =============================================================================

def get_total_execucao_RJ(execucao: list[dict[str, Any]]) -> int:
    """Retorna o total de processos atualmente em Execução."""
    return len(_filtrar_em_execucao_RJ(execucao))


def get_total_entrada_execucao_RJ_periodo(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """Quantidade de processos que entraram na Execução no período (``DATA_EXECUCAO``)."""
    return len(_filtrar_entrada_execucao_RJ_no_periodo(execucao, from_date, to_date))


def get_total_saida_execucao_RJ_periodo(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """Quantidade de processos com ``DATA_COMPENSACAO_ALVARA`` no período (ver :func:`_filtrar_saida_no_periodo_RJ`)."""
    return len(_filtrar_saida_no_periodo_RJ(execucao, from_date, to_date))


def get_estoque_final_RJ(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    execucao_fluxos_periodo: Optional[list[dict[str, Any]]] = None,
) -> int:
    """
    Estoque final **calculado**: ``(total em Execução − entradas no período) + saídas no período``.
    """
    fluxos = execucao_fluxos_periodo if execucao_fluxos_periodo is not None else execucao
    resultado_subtracao = (
        get_total_execucao_RJ(execucao)
        - get_total_entrada_execucao_RJ_periodo(fluxos, from_date, to_date)
    )
    return resultado_subtracao + get_total_saida_execucao_RJ_periodo(
        fluxos, from_date, to_date
    )


def get_tre(estoque_inicial: int, estoque_final: int) -> float:
    """
    TRE segundo o modelo DAX:
    ``DIVIDE((Estoque_Inicial − Estoque_Final) × 100, Estoque_Final, 0)``
    """
    if estoque_final == 0:
        return 0.0
    diferenca = float(estoque_inicial) - float(estoque_final)
    diferenca_2 = diferenca * 100.0
    taxa = diferenca_2 / float(estoque_final)
    return taxa


def get_tre_execucao_RJ_dax(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    execucao_fluxos_periodo: Optional[list[dict[str, Any]]] = None,
) -> float:
    inicial = get_total_execucao_RJ(execucao)
    final = get_estoque_final_RJ(
        execucao,
        from_date,
        to_date,
        execucao_fluxos_periodo=execucao_fluxos_periodo,
    )
    return get_tre(inicial, final)


# =============================================================================
# 4 - Valores monetários
# =============================================================================

def get_valor_causa_total_execucao_RJ(execucao: list[dict[str, Any]]) -> float:
    """
    Soma do valor ainda em aberto de todos os processos em Execução —
    card "Valor Total em execução".
    """
    total = 0.0
    for p in _filtrar_em_execucao_RJ(execucao):
        valor = _get_valor_execucao_em_aberto_RJ(p)
        if valor is not None:
            total += _converter_valor(valor)
    return total


def get_detalhe_valor_execucao_vazio_RJ(execucao: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Processos em Execução com VALOR_EXECUCAO ausente/vazio — número do processo +
    campo faltando (alimenta o alerta clicável do dashboard)."""
    return [
        {
            "numero_processo": str(p.get("NUMERO_PROCESSO") or p.get("id") or p.get("ID") or ""),
            "campo": "Valor da Execução",
        }
        for p in _filtrar_em_execucao_RJ(execucao)
        if _get_valor_execucao_RJ(p) is None
    ]


def get_total_valor_execucao_vazio_RJ(execucao: list[dict[str, Any]]) -> int:
    """Quantidade de processos em Execução com VALOR_EXECUCAO ausente ou vazio."""
    return len(get_detalhe_valor_execucao_vazio_RJ(execucao))


def get_valor_honorarios_total_execucao_RJ(execucao: list[dict[str, Any]]) -> float:
    """Soma de VALOR_HONORARIOS dos processos na fase Financeiro (ID_FASE == 26)."""
    total = 0.0
    for p in _base_execucao_RJ(execucao):
        valor = _get_valor_honorarios_RJ(p)
        if valor is not None:
            total += _converter_valor(valor)
    return total


def get_valor_em_execucao_RJ(execucao: list[dict[str, Any]]) -> float:
    """
    Soma de VALOR_EXECUCAO dos processos que entraram na Execução.

    Valor cheio, mesmo quando já houve compensação parcial do alvará do
    incontroverso — ver :func:`get_valor_remanescente_em_execucao_RJ` para o valor
    ainda em aberto.
    """
    total = 0.0
    for p in _filtrar_entrada_execucao_RJ_no_periodo(execucao):
        valor = _get_valor_execucao_RJ(p)
        if valor is not None:
            total += _converter_valor(valor)
    return total


def get_valor_remanescente_em_execucao_RJ(execucao: list[dict[str, Any]]) -> float:
    """
    Soma de ``VALOR_REMANESCENTE`` de todos os processos atualmente em
    Execução — card "Valor Remanescente".
    """
    total = 0.0
    for p in _filtrar_em_execucao_RJ(execucao):
        valor = _get_valor_remanescente_RJ(p)
        if valor is not None:
            total += _converter_valor(valor)
    return total


def get_valor_execucao_saida_periodo_RJ(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """
    Soma do valor que efetivamente saiu da Execução no período — valor em
    destaque no card "Valor saída Execução".
    """
    total = 0.0
    for p in _filtrar_saida_no_periodo_RJ(execucao, from_date, to_date):
        valor = _get_valor_execucao_em_aberto_RJ(p)
        if valor is not None:
            total += _converter_valor(valor)
    total += get_valor_incontroverso_saida_periodo_RJ(execucao, from_date, to_date)
    return total


def get_valor_incontroverso_saida_periodo_RJ(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """
    Soma de ``VALOR_INCONTROVERSO`` dos processos com
    ``DATA_COMPENSACAO_ALVARA_INCONTROVERSO`` preenchida no período.
    """
    total = 0.0
    for p in _filtrar_saida_incontroverso_no_periodo_RJ(execucao, from_date, to_date):
        valor = _get_valor_incontroverso_RJ(p)
        if valor is not None:
            total += _converter_valor(valor)
    return total


def get_total_incontroverso_saida_periodo_RJ(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """
    Quantidade de processos com ``DATA_COMPENSACAO_ALVARA_INCONTROVERSO``
    preenchida no período, excluindo os que já têm ``DATA_COMPENSACAO_ALVARA``
    preenchida (já contam como saída normal).
    """
    return len([
        p for p in _filtrar_saida_incontroverso_no_periodo_RJ(execucao, from_date, to_date)
        if _get_data_compensacao_alvara_RJ(p) is None
    ])



def _somar_campos_ted_rj(item: dict[str, Any], campos: tuple[str, ...]) -> float:
    total = 0.0
    for campo in campos:
        raw = item.get(campo)
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            continue
        total += _converter_valor(raw)
    return total


def get_valor_ted_saida_execucao_RJ_periodo(
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
    for p in _filtrar_saida_no_periodo_RJ(execucao, from_date, to_date):
        if _get_data_compensacao_alvara_incontroverso_RJ(p) is not None:
            total += _somar_campos_ted_rj(p, ("VALOR_TED_2", "VALOR_TED_3"))
        else:
            total += _somar_campos_ted_rj(p, ("VALOR_TED", "VALOR_TED_2", "VALOR_TED_3"))
    for p in _filtrar_saida_incontroverso_no_periodo_RJ(execucao, from_date, to_date):
        total += _somar_campos_ted_rj(p, ("VALOR_TED",))
    return total


def get_taxa_recuperacao_execucao_RJ(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """
    Taxa de recuperação (%) do que saiu da Execução no período:
    ``Valor TED da saída ÷ Valor de saída × 100``.

    Numerador :func:`get_valor_ted_saida_execucao_RJ_periodo` e denominador
    :func:`get_valor_execucao_saida_periodo_RJ` — os dois com a mesma lógica de
    incontroverso. Razão agregada, não média por processo; ``0.0`` se o valor
    de saída for zero.
    """
    total_saida = get_valor_execucao_saida_periodo_RJ(execucao, from_date, to_date)
    if total_saida == 0:
        return 0.0
    total_ted = get_valor_ted_saida_execucao_RJ_periodo(execucao, from_date, to_date)
    return round((total_ted / total_saida) * 100.0, 2)


# =============================================================================
# 5 - Agrupamentos
# =============================================================================

def group_valor_saida_execucao_RJ_por_mes(
    execucao: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Agrupa a soma de ``VALOR_TED`` dos processos que saíram da Execução por mês."""
    saidas = _filtrar_saida_no_periodo_RJ(execucao)
    grouped: dict[str, dict[str, Any]] = {}

    for p in saidas:
        try:
            data_compensacao = _get_data_compensacao_alvara_RJ(p)
            if not data_compensacao:
                continue

            month_key = f"{data_compensacao.year}-{data_compensacao.month:02d}"

            if month_key not in grouped:
                month_name = f"{_MONTH_NAMES[data_compensacao.month - 1]} {data_compensacao.year}"
                grouped[month_key] = {"name": month_name, "value": 0.0}

            valor = _get_valor_ted_RJ(p)
            if valor is not None:
                grouped[month_key]["value"] += _converter_valor(valor)

        except (ValueError, AttributeError, TypeError):
            continue

    return [
        {**item, "value": round(item["value"], 2)}
        for item in sorted(grouped.values(), key=lambda x: x["name"])
    ]


def group_valor_execucao_saida_periodo_RJ_por_mes(
    execucao: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Agrupa por mês o valor total que saiu da Execução (saída + incontroverso).
    """
    grouped: dict[str, dict[str, Any]] = {}

    for p in _filtrar_saida_no_periodo_RJ(execucao):
        try:
            data_compensacao = _get_data_compensacao_alvara_RJ(p)
            if not data_compensacao:
                continue

            valor = _get_valor_execucao_em_aberto_RJ(p)
            if valor is None:
                continue

            month_key = f"{data_compensacao.year}-{data_compensacao.month:02d}"
            if month_key not in grouped:
                month_name = f"{_MONTH_NAMES[data_compensacao.month - 1]} {data_compensacao.year}"
                grouped[month_key] = {"name": month_name, "value": 0.0}
            grouped[month_key]["value"] += _converter_valor(valor)

        except (ValueError, AttributeError, TypeError):
            continue

    for p in _filtrar_saida_incontroverso_no_periodo_RJ(execucao):
        try:
            data_incontroverso = _get_data_compensacao_alvara_incontroverso_RJ(p)
            if not data_incontroverso:
                continue

            valor = _get_valor_incontroverso_RJ(p)
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


def group_valor_remanescente_por_mes_RJ(
    execucao: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Agrupa a soma de ``VALOR_REMANESCENTE`` por mês de entrada na Execução
    (``DATA_EXECUCAO``).
    """
    grouped: dict[str, dict[str, Any]] = {}

    for p in _filtrar_em_execucao_RJ(execucao):
        try:
            data_exe = _get_data_execucao_RJ(p)
            if not data_exe:
                continue

            valor = _get_valor_remanescente_RJ(p)
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


def group_quantidade_saida_execucao_RJ_por_mes(
    execucao: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Agrupa a quantidade de processos que saíram da Execução por mês."""
    saidas = _filtrar_saida_no_periodo_RJ(execucao)
    grouped: dict[str, dict[str, Any]] = {}

    for p in saidas:
        try:
            data_compensacao = _get_data_compensacao_alvara_RJ(p)
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


def group_quantidade_entrada_execucao_RJ_por_mes(
    execucao: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Agrupa a quantidade de processos que entraram na Execução por mês."""
    entradas = _filtrar_entrada_execucao_RJ_no_periodo(execucao)
    grouped: dict[str, dict[str, Any]] = {}

    for p in entradas:
        try:
            data_exe = _get_data_execucao_RJ(p)
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


def group_valor_entrada_execucao_RJ_por_mes(
    execucao: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Agrupa a soma de ``VALOR_EXECUCAO`` dos processos que entraram na Execução por mês."""
    entradas = _filtrar_entrada_execucao_RJ_no_periodo(execucao)
    grouped: dict[str, dict[str, Any]] = {}

    for p in entradas:
        try:
            data_exe = _get_data_execucao_RJ(p)
            if not data_exe:
                continue

            month_key = f"{data_exe.year}-{data_exe.month:02d}"

            if month_key not in grouped:
                month_name = f"{_MONTH_NAMES[data_exe.month - 1]} {data_exe.year}"
                grouped[month_key] = {"name": month_name, "value": 0.0}

            valor = _get_valor_execucao_RJ(p)
            if valor is not None:
                grouped[month_key]["value"] += _converter_valor(valor)

        except (ValueError, AttributeError, TypeError):
            continue

    return [
        {**item, "value": round(item["value"], 2)}
        for item in sorted(grouped.values(), key=lambda x: x["name"])
    ]


def group_execucao_RJ_por_subfase(execucao: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Agrupa os processos em Execução por SUBFASE."""
    contagem: defaultdict[str, int] = defaultdict(int)

    for p in _filtrar_em_execucao_RJ(execucao):
        contagem[_normalizar_subfase(p.get("SUBFASE"))] += 1

    return sorted(
        [{"name": name, "value": int(value)} for name, value in contagem.items()],
        key=lambda x: x["value"],
        reverse=True,
    )


def _uf_por_comarca_rj(execucao: list[dict[str, Any]]) -> dict[str, str]:
    """
    UF mais frequente associada a cada COMARCA (histórico completo,
    :func:`_base_execucao_RJ`) — usada para casar cada comarca com o estado certo
    no mapa coroplético.
    """
    contagem: defaultdict[str, defaultdict[str, int]] = defaultdict(lambda: defaultdict(int))
    for p in _base_execucao_RJ(execucao):
        uf = str(p.get("UF") or "").strip().upper()
        if not uf:
            continue
        contagem[_normalizar_comarca(p.get("COMARCA"))][uf] += 1
    return {
        name: max(por_uf.items(), key=lambda kv: kv[1])[0]
        for name, por_uf in contagem.items()
    }


def group_execucao_RJ_por_comarca(
    execucao: list[dict[str, Any]],
    *,
    criterio: str = "total",
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Agrupa processos em Execução por COMARCA, conforme ``criterio``:

    - "total": estoque atual em Execução — :func:`_filtrar_em_execucao_RJ`.
    - "entrada": processos com DATA_EXECUCAO no período — :func:`_filtrar_entrada_execucao_RJ_no_periodo`.
    - "saida": processos com DATA_COMPENSACAO_ALVARA no período — :func:`_filtrar_saida_no_periodo_RJ`.

    Cada item traz, além da quantidade (``value``): a soma do VALOR_EXECUCAO
    (``valor_execucao``), o tempo médio em dias (``tempo_medio_dias``, fixo por
    comarca, independente do ``criterio``) e a UF da comarca (``uf``), para o
    mapa coroplético.

    Retorna lista ordenada de forma decrescente por quantidade.
    """
    if criterio == "entrada":
        base = _filtrar_entrada_execucao_RJ_no_periodo(execucao, from_date, to_date)
    elif criterio == "saida":
        base = _filtrar_saida_no_periodo_RJ(execucao, from_date, to_date)
    else:
        base = _filtrar_em_execucao_RJ(execucao)

    duracoes_por_comarca: defaultdict[str, list[float]] = defaultdict(list)
    for p in _base_execucao_RJ(execucao):
        entrada = _get_data_execucao_RJ(p)
        saida = _get_data_compensacao_alvara_RJ(p)
        if entrada and saida:
            dias = (saida - entrada).days
            if dias > 0:
                duracoes_por_comarca[_normalizar_comarca(p.get("COMARCA"))].append(float(dias))
    tempo_medio_por_comarca = {
        name: round(sum(duracoes) / len(duracoes), 2)
        for name, duracoes in duracoes_por_comarca.items()
    }
    uf_por_comarca = _uf_por_comarca_rj(execucao)

    grupos: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for p in base:
        grupos[_normalizar_comarca(p.get("COMARCA"))].append(p)

    itens: list[dict[str, Any]] = []
    for name, rows in grupos.items():
        valor_total = 0.0
        for p in rows:
            valor = _get_valor_execucao_RJ(p)
            if valor is not None:
                valor_total += _converter_valor(valor)
        itens.append({
            "name": name,
            "value": len(rows),
            "valor_execucao": round(valor_total, 2),
            "tempo_medio_dias": tempo_medio_por_comarca.get(name),
            "uf": uf_por_comarca.get(name),
        })

    return sorted(itens, key=lambda x: x["value"], reverse=True)


def group_valor_execucao_RJ_por_comarca(
    execucao: list[dict[str, Any]],
    *,
    criterio: str = "total",
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Agrupa o valor dos processos em Execução por COMARCA, conforme ``criterio``
    (mesmo recorte de :func:`group_execucao_RJ_por_comarca`, mas somando valor em
    vez de contar).

    Cada item também traz ``uf`` (:func:`_uf_por_comarca_rj`), para casar a
    comarca com o estado certo no mapa coroplético.
    """
    if criterio == "entrada":
        base = _filtrar_entrada_execucao_RJ_no_periodo(execucao, from_date, to_date)
        get_valor = _get_valor_execucao_RJ
    elif criterio == "saida":
        base = _filtrar_saida_no_periodo_RJ(execucao, from_date, to_date)
        get_valor = _get_valor_execucao_em_aberto_RJ
    else:
        base = _filtrar_em_execucao_RJ(execucao)
        get_valor = _get_valor_execucao_em_aberto_RJ

    uf_por_comarca = _uf_por_comarca_rj(execucao)
    totais: defaultdict[str, float] = defaultdict(float)
    for p in base:
        valor = get_valor(p)
        if valor is not None:
            totais[_normalizar_comarca(p.get("COMARCA"))] += _converter_valor(valor)

    return sorted(
        [
            {"name": name, "value": float(value), "uf": uf_por_comarca.get(name)}
            for name, value in totais.items()
        ],
        key=lambda x: x["value"],
        reverse=True,
    )


def group_valor_execucao_RJ_por_subfase(execucao: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Agrupa o valor ainda em aberto dos processos em Execução por SUBFASE —
    sempre modo "Total" (estoque atual).
    """
    totais: defaultdict[str, float] = defaultdict(float)

    for p in _filtrar_em_execucao_RJ(execucao):
        valor = _get_valor_execucao_em_aberto_RJ(p)
        if valor is not None:
            totais[_normalizar_subfase(p.get("SUBFASE"))] += _converter_valor(valor)

    return sorted(
        [{"name": name, "value": float(value)} for name, value in totais.items()],
        key=lambda x: x["value"],
        reverse=True,
    )


def group_execucao_RJ_por_materia(
    execucao: list[dict[str, Any]],
    *,
    restringir_fase_atual: bool = False,
) -> list[dict[str, Any]]:
    """Agrupa os processos em Execução por matéria."""
    base = _filtrar_em_execucao_RJ(execucao) if restringir_fase_atual else _base_execucao_RJ(execucao)
    contagem: defaultdict[str, int] = defaultdict(int)

    for p in base:
        contagem[_normalizar_materia(p.get("MATERIA"))] += 1

    return sorted(
        [{"name": name, "value": int(qtd)} for name, qtd in contagem.items()],
        key=lambda x: x["value"],
        reverse=True,
    )


def group_valor_execucao_RJ_por_materia(
    execucao: list[dict[str, Any]],
    *,
    restringir_fase_atual: bool = False,
) -> list[dict[str, Any]]:
    """Agrupa o VALOR_EXECUCAO dos processos em Execução por matéria."""
    base = _filtrar_em_execucao_RJ(execucao) if restringir_fase_atual else _base_execucao_RJ(execucao)
    valor_getter = _get_valor_execucao_em_aberto_RJ if restringir_fase_atual else _get_valor_execucao_RJ
    totais: defaultdict[str, float] = defaultdict(float)

    for p in base:
        valor = valor_getter(p)
        if valor is not None:
            totais[_normalizar_materia(p.get("MATERIA"))] += _converter_valor(valor)

    return sorted(
        [{"name": name, "value": float(value)} for name, value in totais.items()],
        key=lambda x: x["value"],
        reverse=True,
    )


def group_execucao_RJ_por_ano_ajuizamento(
    execucao: list[dict[str, Any]],
    *,
    restringir_fase_atual: bool = False,
) -> list[dict[str, Any]]:
    """Agrupa os processos em Execução pelo ano de ajuizamento (DATA_DISTRIBUICAO)."""
    contagem: defaultdict[str, int] = defaultdict(int)
    valores: defaultdict[str, float] = defaultdict(float)

    base = _filtrar_em_execucao_RJ(execucao) if restringir_fase_atual else _base_execucao_RJ(execucao)
    valor_getter = _get_valor_execucao_em_aberto_RJ if restringir_fase_atual else _get_valor_execucao_RJ
    for p in base:
        data_distribuicao = _get_data_distribuicao_rj(p)
        ano = str(data_distribuicao.year) if data_distribuicao else _SEM_ANO_AJUIZAMENTO_EXEC_RJ
        contagem[ano] += 1
        valor = valor_getter(p)
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

def _extrair_duracoes_dias_rj(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[float]:
    """
    Calcula a duração em dias (DATA_COMPENSACAO_ALVARA - DATA_EXECUCAO) por
    processo. Amostra pela saída (DATA_COMPENSACAO_ALVARA) dentro do período,
    quando informado.
    """
    duracoes: list[float] = []

    for p in _base_execucao_RJ(execucao):
        try:
            saida = _get_data_compensacao_alvara_RJ(p)
            if from_date is not None or to_date is not None:
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


def get_media_tempo_execucao_RJ(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """Tempo médio (em dias) entre DATA_EXECUCAO e DATA_COMPENSACAO_ALVARA, amostrado pela saída no período."""
    duracoes = _extrair_duracoes_dias_rj(execucao, from_date, to_date)
    if not duracoes:
        return 0.0
    return round(sum(duracoes) / len(duracoes), 2)


def get_mediana_tempo_execucao_RJ(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """Mediana do tempo (em dias) entre DATA_EXECUCAO e DATA_COMPENSACAO_ALVARA, amostrada pela saída no período."""
    duracoes = sorted(_extrair_duracoes_dias_rj(execucao, from_date, to_date))
    n = len(duracoes)

    if not n:
        return 0.0

    meio = n // 2
    if n % 2 == 1:
        return round(duracoes[meio], 2)
    return round((duracoes[meio - 1] + duracoes[meio]) / 2.0, 2)


def get_media_tempo_execucao_RJ_por_mes(execucao: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Série mensal (todo o histórico) da média de dias entre DATA_EXECUCAO e
    DATA_COMPENSACAO_ALVARA, agrupada pelo mês/ano da saída.
    """
    grouped: dict[str, dict[str, Any]] = {}

    for p in _base_execucao_RJ(execucao):
        try:
            entrada = _get_data_execucao_RJ(p)
            saida = _get_data_compensacao_alvara_RJ(p)
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


def _classificar_faixa_ultima_movimentacao_rj(dias_desde: int) -> Optional[str]:
    """
    Faixas exclusivas de dias desde a última movimentação.
    """
    if dias_desde <= 30:
        return "Menos de 30 dias"
    if dias_desde <= 90:
        return "60+ dias"
    if dias_desde <= 180:
        return "90+ dias"
    return "180+ dias"


def group_execucao_RJ_por_faixa_ultima_movimentacao(
    execucao: list[dict[str, Any]],
    reference_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Conta processos em Execução por faixa exclusiva de dias desde a
    ``ULTIMA_MOVIMENTACAO``, no formato de gráfico (``name`` / ``value``).
    """
    ref = reference_date or date.today()
    contadores = {nome: 0 for nome in _FAIXAS_ULTIMA_MOVIMENTACAO_ORDEM}

    for p in _filtrar_em_execucao_RJ(execucao):
        ultima = _get_ultima_movimentacao_RJ(p)
        if ultima is None:
            contadores[SEM_DATA_ULTIMA_MOVIMENTACAO] += 1
            continue

        dias_desde = (ref - ultima).days
        if dias_desde < 0:
            continue

        faixa = _classificar_faixa_ultima_movimentacao_rj(dias_desde)
        if faixa is not None:
            contadores[faixa] += 1

    return [
        {"name": nome, "value": int(contadores[nome])}
        for nome in _FAIXAS_ULTIMA_MOVIMENTACAO_ORDEM
    ]


# =============================================================================
# 7 - Atividades no período (agendamentos do setor Execução RJ)
# =============================================================================

_STATUS_INATIVO_EXEC_RJ = frozenset({
    "Encerrado Cumprido", "Encerrado Não Cumprido", "Cancelado", "Concluído",
})
_STATUS_EM_ANDAMENTO_EXEC_RJ = frozenset({"Iniciado", "Reaberto"})
_STATUS_ENCERRADO_EXEC_RJ = frozenset({"Encerrado Cumprido", "Encerrado Não Cumprido"})

_STATUS_FILTRO_EXEC_RJ: tuple[str, ...] = (
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

_STATUS_DEMANDAS_FUNCIONARIO_EXEC_RJ: tuple[tuple[str, str], ...] = (
    ("encerrado_nao_cumprido", "Encerrado Não Cumprido"),
    ("encerrado_cumprido", "Encerrado Cumprido"),
)
_SLUG_POR_STATUS_EXEC_RJ: dict[str, str] = {
    label: slug for slug, label in _STATUS_DEMANDAS_FUNCIONARIO_EXEC_RJ
}

_SEM_ATIVIDADE_EXEC_RJ = "Sem atividade"
_SEM_FUNCIONARIO_EXEC_RJ = "Sem funcionário"
_STATUS_CUMPRIDO_EXEC_RJ = "Encerrado Cumprido"

_COL_FUNCIONARIO_ATRIBUIDO_EXEC_RJ = "FUNCIONARIO_ATRIBUIDO"
_COL_FUNCIONARIO_ENCERRAMENTO_EXEC_RJ = "FUNCIONARIO_ENCERRAMENTO"
_COL_ID_USUARIO_ENCERRAMENTO_EXEC_RJ = "ID_USUARIO_ENCERRAMENTO"

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


def _get_ag_numero_processo_rj(item: dict[str, Any]) -> Optional[str]:
    raw = item.get("NUMERO_PROCESSO") or item.get("numero_processo")
    if raw is None or not str(raw).strip():
        return None
    return str(raw).strip()


def _get_ag_valor_sentenca_rj(item: dict[str, Any]) -> Optional[float]:
    """Valor da sentença (``processo.valor_causa_vs``), ou ``None`` se ausente/zerado."""
    raw = item.get("VALOR_CAUSA_SENTENCA")
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None
    valor = _converter_valor(raw)
    return valor if valor else None


def _get_ag_valor_acordao_rj(item: dict[str, Any]) -> Optional[float]:
    """Valor do acórdão (``processo.valor_causa_va``), ou ``None`` se ausente/zerado."""
    raw = item.get("VALOR_CAUSA_ACORDO")
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None
    valor = _converter_valor(raw)
    return valor if valor else None


def _get_ag_atividade_nome_rj(item: dict[str, Any]) -> str:
    raw = item.get("ATIVIDADE") or item.get("atividade")
    if raw is None or not str(raw).strip():
        return _SEM_ATIVIDADE_EXEC_RJ
    return str(raw).strip()


def _get_ag_funcionario_atribuido_rj(item: dict[str, Any]) -> str:
    raw = (
        item.get(_COL_FUNCIONARIO_ATRIBUIDO_EXEC_RJ)
        or item.get("FUNCIONARIO")
        or item.get("funcionario")
    )
    if raw is None or not str(raw).strip():
        return _SEM_FUNCIONARIO_EXEC_RJ
    return str(raw).strip()


def _get_ag_funcionario_encerramento_rj(item: dict[str, Any]) -> str | None:
    uid = item.get(_COL_ID_USUARIO_ENCERRAMENTO_EXEC_RJ) or item.get("id_usuario_encerramento")
    if uid is None or (isinstance(uid, str) and not str(uid).strip()):
        return None
    raw = item.get(_COL_FUNCIONARIO_ENCERRAMENTO_EXEC_RJ) or item.get("funcionario_encerramento")
    if raw is not None and str(raw).strip():
        return str(raw).strip()
    return None


def _get_ag_funcionario_nome_rj(item: dict[str, Any]) -> str:
    status = _get_ag_status_rj(item) or ""
    if status in _STATUS_ENCERRADO_EXEC_RJ:
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
    if status in _STATUS_ENCERRADO_EXEC_RJ:
        return _ag_data_no_periodo(conclusao, from_date, to_date)
    if status not in _STATUS_INATIVO_EXEC_RJ and prazo is not None and prazo <= ref:
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
    ativo = status not in _STATUS_INATIVO_EXEC_RJ
    em_andamento = status in _STATUS_EM_ANDAMENTO_EXEC_RJ and criada_periodo
    vencida = ativo and prazo is not None and prazo < ref
    vence_hoje = ativo and prazo is not None and prazo == ref
    concluida = (
        status in _STATUS_ENCERRADO_EXEC_RJ
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
        if status not in _STATUS_ENCERRADO_EXEC_RJ:
            continue
        if exigir_encerrador and _get_ag_funcionario_encerramento_rj(row) is None:
            continue
        conclusao = _get_ag_data_conclusao_rj(row)
        if _ag_data_no_periodo(conclusao, from_date, to_date):
            resultado.append(row)
    return resultado


def get_kpis_atividades_execucao_RJ(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, int]:
    """KPIs de agendamentos do setor Execução RJ no período."""
    ref = ref_date or date.today()
    total = em_andamento = vencidas = vencem_hoje = concluidas = 0
    total_criadas = criadas_em_andamento = 0
    abertas = 0

    for row in agendamentos:
        criacao = _get_ag_data_criacao_rj(row)
        conclusao = _get_ag_data_conclusao_rj(row)
        status = _get_ag_status_rj(row) or ""
        prazo = _get_ag_prazo_rj(row)
        ativo = status not in _STATUS_INATIVO_EXEC_RJ
        criada_periodo = _ag_data_no_periodo(criacao, from_date, to_date)

        # "Abertas": tudo atualmente em aberto, independente do período (card
        # unificado "Em andamento" da Confecção CS) — mesmo critério do NG.
        if ativo:
            abertas += 1

        # "Criadas": tudo que chegou no período, mesmo já concluído; só exclui Cancelado.
        if criada_periodo and status != "Cancelado":
            total_criadas += 1
            if status not in _STATUS_ENCERRADO_EXEC_RJ:
                criadas_em_andamento += 1

        if criada_periodo and ativo:
            total += 1
            if status in _STATUS_EM_ANDAMENTO_EXEC_RJ:
                em_andamento += 1

        if ativo and prazo is not None:
            if prazo < ref:
                vencidas += 1
            elif prazo == ref:
                vencem_hoje += 1

        if status in _STATUS_ENCERRADO_EXEC_RJ:
            if _ag_data_no_periodo(conclusao, from_date, to_date):
                concluidas += 1

    return {
        "total_atividades_execucao_RJ": total,
        "atividades_execucao_em_andamento_RJ": em_andamento,
        "atividades_execucao_vencidas_RJ": vencidas,
        "atividades_execucao_vencem_hoje_RJ": vencem_hoje,
        "atividades_execucao_concluidas_RJ": concluidas,
        "total_atividades_criadas_execucao_RJ": total_criadas,
        "atividades_criadas_em_andamento_execucao_RJ": criadas_em_andamento,
        "atividades_execucao_abertas_RJ": abertas,
    }


def get_media_mensal_atividades_execucao_RJ(agendamentos: list[dict[str, Any]]) -> float:
    """Média mensal de agendamentos criados (DATA_HORA_CRIACAO), histórico completo."""
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


def group_execucao_processos_por_atividade_RJ(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Processos distintos por atividade (agendamentos criados no período) — RJ."""
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


def group_atividades_ativas_criadas_por_atividade_RJ(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Quantidade de agendamentos ATIVOS criados no período, agrupados por atividade — RJ."""
    contagem: defaultdict[str, int] = defaultdict(int)
    for row in agendamentos:
        status = _get_ag_status_rj(row) or ""
        if status in _STATUS_INATIVO_EXEC_RJ:
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


def group_atividades_criadas_por_atividade_RJ(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Agendamentos criados no período por atividade (só exclui Cancelado) — RJ, espelho de
    :func:`group_atividades_criadas_por_atividade_NG`. ``concluidos`` = encerrados com
    conclusão no período; ``abertas`` = atualmente em aberto, independente da criação.
    """
    contagem: defaultdict[str, int] = defaultdict(int)
    concluidos: defaultdict[str, int] = defaultdict(int)
    abertas: defaultdict[str, int] = defaultdict(int)
    for row in agendamentos:
        status = _get_ag_status_rj(row) or ""
        nome = _get_ag_atividade_nome_rj(row)
        criacao = _get_ag_data_criacao_rj(row)
        if status != "Cancelado" and _ag_data_no_periodo(criacao, from_date, to_date):
            contagem[nome] += 1
        if status in _STATUS_ENCERRADO_EXEC_RJ:
            conclusao = _get_ag_data_conclusao_rj(row)
            if _ag_data_no_periodo(conclusao, from_date, to_date):
                concluidos[nome] += 1
        if status not in _STATUS_INATIVO_EXEC_RJ:
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


def group_atividades_ativas_por_prazo_por_atividade_RJ(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Quantidade de agendamentos ATIVOS com PRAZO no período, agrupados por atividade — RJ."""
    contagem: defaultdict[str, int] = defaultdict(int)
    for row in agendamentos:
        status = _get_ag_status_rj(row) or ""
        if status in _STATUS_INATIVO_EXEC_RJ:
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


def group_execucao_demandas_por_funcionario_RJ(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Demandas encerradas por funcionário (Cumprido / Não Cumprido) no período — RJ."""
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


def group_execucao_demandas_por_funcionario_completo_RJ(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Demandas encerradas por funcionário (Cumprido / Não Cumprido) no período —
    RJ, incluindo uma linha "Sem funcionário identificado".
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


def group_taxa_conclusao_por_funcionario_RJ(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Taxa de conclusão por colaborador ATRIBUÍDO — RJ, espelho de
    :func:`group_taxa_conclusao_por_funcionario_NG`: ``percent`` = concluídas no
    período ÷ (concluídas + abertas atualmente) do próprio colaborador.
    """
    concluidas: dict[str, int] = defaultdict(int)
    abertas: dict[str, int] = defaultdict(int)
    for row in agendamentos:
        funcionario = _get_ag_funcionario_atribuido_rj(row)
        status = _get_ag_status_rj(row) or ""
        if status in _STATUS_ENCERRADO_EXEC_RJ:
            conclusao = _get_ag_data_conclusao_rj(row)
            if _ag_data_no_periodo(conclusao, from_date, to_date):
                concluidas[funcionario] += 1
        elif status not in _STATUS_INATIVO_EXEC_RJ:
            abertas[funcionario] += 1

    itens: list[dict[str, Any]] = []
    for nome in set(concluidas) | set(abertas):
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
            "percent": round(100.0 * c / total, 1),
        })
    return sorted(itens, key=lambda x: int(x["total"]), reverse=True)


_ATIVIDADES_FLUXO_CS_1G_RJ = frozenset(
    x.casefold() for x in ("Elaborar Cumprimento de Sentença (1G)", "Manifestação Cálculo 1")
)
_ATIVIDADES_FLUXO_CS_2G_RJ = frozenset(
    x.casefold() for x in ("Elaborar Cumprimento de Sentença (2G)", "Manifestação Cálculo 2")
)
# Atividade antiga sem grau no nome: vai numa linha própria (decisão do negócio, out/2026 —
# inferir o grau pelo acórdão errava ~43% dos 1G no NG).
_ATIVIDADES_FLUXO_CS_SEM_GRAU_RJ = frozenset({"Elaborar Cumprimento de Sentença".casefold()})
_FLUXO_CS_SEM_GRAU_LABEL_RJ = "CS (sem grau)"
_JANELA_FLUXO_CS_DIAS_RJ = 30


def group_entrada_execucao_por_fluxo_cs_por_mes_RJ(
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
        status = _get_ag_status_rj(row)
        if status == _STATUS_CUMPRIDO_EXEC_RJ:
            prioridade = 0
        elif status == "Cancelado":
            prioridade = 1
        else:
            continue
        nome = _get_ag_atividade_nome_rj(row).casefold()
        if nome in _ATIVIDADES_FLUXO_CS_1G_RJ:
            grau = "1G"
        elif nome in _ATIVIDADES_FLUXO_CS_2G_RJ:
            grau = "2G"
        elif nome in _ATIVIDADES_FLUXO_CS_SEM_GRAU_RJ:
            grau = _FLUXO_CS_SEM_GRAU_LABEL_RJ
        else:
            continue
        pid = _to_int(_get_ag_processo_id_rj(row))
        conclusao = _get_ag_data_conclusao_rj(row)
        if pid is None or conclusao is None:
            continue
        cs_por_processo[pid].append((conclusao, prioridade, grau))

    grouped: dict[str, dict[str, Any]] = {}
    for p in _filtrar_entrada_execucao_RJ_no_periodo(execucao):
        data_exe = _get_data_execucao_RJ(p)
        pid = _to_int(p.get("id") or p.get("ID"))
        if data_exe is None:
            continue
        candidatos = [
            (abs((conclusao - data_exe).days), prioridade, grau)
            for conclusao, prioridade, grau in cs_por_processo.get(pid, ())
            if abs((conclusao - data_exe).days) <= _JANELA_FLUXO_CS_DIAS_RJ
        ]
        month_key = f"{data_exe.year}-{data_exe.month:02d}"
        if month_key not in grouped:
            grouped[month_key] = {
                "name": f"{_MONTH_NAMES[data_exe.month - 1]} {data_exe.year}",
                "1G": 0,
                "2G": 0,
                _FLUXO_CS_SEM_GRAU_LABEL_RJ: 0,
                "Outros": 0,
            }
        # Sem CS por perto: a entrada veio por outro caminho — "Outros" faz a soma das
        # linhas bater com o total de entradas da Condenação (card "Quantidade de entrada").
        grau = min(candidatos)[2] if candidatos else "Outros"
        grouped[month_key][grau] += 1

    return [grouped[k] for k in sorted(grouped)]


def group_execucao_resolvidos_por_dia_RJ(
    agendamentos: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Produção diária: quantidade de atividades "Encerrado Cumprido" por dia de
    conclusão (DATA_HORA_CONCLUSAO), histórico completo — RJ.
    """
    grouped: dict[str, int] = defaultdict(int)
    for row in agendamentos:
        if _get_ag_status_rj(row) != _STATUS_CUMPRIDO_EXEC_RJ:
            continue
        conclusao = _get_ag_data_conclusao_rj(row)
        if conclusao is None:
            continue
        grouped[conclusao.strftime("%Y-%m-%d")] += 1

    return [
        {"name": dia, "value": count}
        for dia, count in sorted(grouped.items(), key=lambda x: x[0])
    ]


def get_media_execucao_resolvidos_por_funcionario_RJ(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Média de atividades "Encerrado Cumprido" por funcionário no período — RJ."""
    grouped: dict[str, dict[str, Any]] = defaultdict(lambda: {"total": 0, "dias": set()})
    for row in agendamentos:
        if _get_ag_status_rj(row) != _STATUS_CUMPRIDO_EXEC_RJ:
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


def group_valor_recuperado_por_funcionario_RJ(
    agendamentos: list[dict[str, Any]],
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Valor recuperado (``VALOR_TED``) por funcionário responsável pelo
    encerramento das demandas de Execução RJ no período.
    """
    valor_ted_por_processo: dict[int, float] = {}
    for p in _filtrar_saida_no_periodo_RJ(execucao, from_date, to_date):
        processo_id = _to_int(p.get("id") or p.get("ID"))
        if processo_id is None:
            continue
        valor = _get_valor_ted_RJ(p)
        if valor is not None:
            valor_ted_por_processo[processo_id] = _converter_valor(valor)

    base = _filtrar_ag_encerrados_no_periodo_rj(
        agendamentos, from_date, to_date, exigir_encerrador=True
    )
    vistos: set[tuple[str, int]] = set()
    totais: defaultdict[str, float] = defaultdict(float)

    for row in base:
        funcionario = _get_ag_funcionario_encerramento_rj(row)
        if not funcionario:
            continue
        processo_id = _to_int(_get_ag_processo_id_rj(row))
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


def list_execucao_atividades_periodo_RJ(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Lista de agendamentos do setor Execução RJ para a tabela de tarefas."""
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
        if status in _STATUS_ENCERRADO_EXEC_RJ and funcionario_enc is not None:
            encerrado_pelo_responsavel = (
                funcionario_enc.strip().lower() == funcionario_atrib.strip().lower()
            )
        setor = str(row.get("SETOR") or row.get("setor") or "EXECUÇÃO").strip().upper()
        atividade = _get_ag_atividade_nome_rj(row)
        pessoa_setor = (
            f"{setor} - {atividade}"
            if atividade and atividade != _SEM_ATIVIDADE_EXEC_RJ
            else setor
        )
        descricao_raw = row.get("DESCRICAO") or row.get("descricao")
        descricao = str(descricao_raw).strip().upper() if descricao_raw else "—"
        operacao = str(row.get("OPERACAO") or row.get("operacao") or "").strip()

        conclusao = _get_ag_data_conclusao_rj(row)

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
            "concluido_em": conclusao.isoformat() if conclusao else None,
            "operacao": operacao,
            "encerrado_pelo_responsavel": encerrado_pelo_responsavel,
            "numero_processo": _get_ag_numero_processo_rj(row),
            "valor_sentenca": _get_ag_valor_sentenca_rj(row),
            "valor_acordao": _get_ag_valor_acordao_rj(row),
            **situacao,
        })

    def _sort_key(item: dict[str, Any]) -> tuple[int, str, int]:
        prazo_raw = item.get("prazo")
        prazo_missing = 0 if prazo_raw else 1
        return (prazo_missing, str(prazo_raw or ""), int(item.get("id") or 0))

    return sorted(itens, key=_sort_key)


def get_opcoes_filtros_execucao_RJ(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, Any]:
    """Opções de filtros da lista de tarefas — RJ."""
    rows = list_execucao_atividades_periodo_RJ(
        agendamentos, from_date=from_date, to_date=to_date, ref_date=ref_date
    )
    funcionarios: set[str] = set()
    atividades: set[str] = set()
    status_vistos: set[str] = set()

    for row in rows:
        funcionarios.add(str(row.get("funcionario") or _SEM_FUNCIONARIO_EXEC_RJ))
        atividade = str(row.get("atividade") or "").strip()
        if atividade and atividade != _SEM_ATIVIDADE_EXEC_RJ:
            atividades.add(atividade)
        status = str(row.get("status") or "").strip()
        if status and status != "—":
            status_vistos.add(status)

    status_ordenados: list[str] = []
    for label in _STATUS_FILTRO_EXEC_RJ:
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
        if not any(flags.get(sid) for sid in filtros.situacoes):
            return False
    return True


def filtrar_agendamentos_execucao_RJ(
    agendamentos: list[dict[str, Any]],
    filtros: Any,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Restringe agendamentos RJ aos filtros cumulativos."""
    if filtros is None or not filtros.ativo():
        return agendamentos
    return [
        row for row in agendamentos
        if _agendamento_match_filtros_exec_rj(row, filtros, from_date, to_date, ref_date=ref_date)
    ]


# ---------------------------------------------------------------------------
# Análise por Prazo — RJ (mesmas 5 métricas, mas usando PRAZO como eixo
# temporal em vez de DATA_HORA_CRIACAO/DATA_HORA_CONCLUSAO).
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
    ativo = status not in _STATUS_INATIVO_EXEC_RJ
    prazo_no_periodo = _ag_data_no_periodo(prazo, from_date, to_date)
    em_andamento = status in _STATUS_EM_ANDAMENTO_EXEC_RJ and prazo_no_periodo
    vencida = ativo and prazo_no_periodo and prazo is not None and prazo < ref
    vence_hoje = ativo and prazo_no_periodo and prazo is not None and prazo == ref
    concluida = status in _STATUS_ENCERRADO_EXEC_RJ and prazo_no_periodo
    return {
        "em_andamento": em_andamento,
        "vencida": vencida,
        "vence_hoje": vence_hoje,
        "concluida": concluida,
    }


def get_kpis_execucao_por_prazo_RJ(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, int]:
    """KPIs de agendamentos do setor Execução RJ usando PRAZO como eixo temporal."""
    ref = ref_date or date.today()
    total = em_andamento = vencidas = vencem_hoje = concluidas = 0

    for row in agendamentos:
        prazo = _get_ag_prazo_rj(row)
        status = _get_ag_status_rj(row) or ""
        ativo = status not in _STATUS_INATIVO_EXEC_RJ
        prazo_no_periodo = _ag_data_no_periodo(prazo, from_date, to_date)

        if not prazo_no_periodo:
            continue

        if ativo:
            total += 1
            if status in _STATUS_EM_ANDAMENTO_EXEC_RJ:
                em_andamento += 1
            if prazo is not None and prazo < ref:
                vencidas += 1
            if prazo is not None and prazo == ref:
                vencem_hoje += 1
        elif status in _STATUS_ENCERRADO_EXEC_RJ:
            concluidas += 1

    return {
        "total_por_prazo_execucao_RJ": total,
        "por_prazo_em_andamento_execucao_RJ": em_andamento,
        "por_prazo_vencidas_execucao_RJ": vencidas,
        "por_prazo_vencem_hoje_execucao_RJ": vencem_hoje,
        "por_prazo_concluidas_execucao_RJ": concluidas,
    }


def group_execucao_processos_por_atividade_por_prazo_RJ(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Processos distintos por atividade (agendamentos com prazo no período) — RJ."""
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


def group_execucao_demandas_por_funcionario_por_prazo_RJ(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Demandas encerradas por funcionário (Cumprido / Não Cumprido), com PRAZO no período — RJ."""
    base = [
        row for row in agendamentos
        if (_get_ag_status_rj(row) or "") in _STATUS_ENCERRADO_EXEC_RJ
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


def group_execucao_demandas_por_funcionario_por_prazo_completo_RJ(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Demandas encerradas por funcionário, com PRAZO no período — RJ, incluindo
    uma linha "Sem funcionário identificado".
    """
    base = [
        row for row in agendamentos
        if (_get_ag_status_rj(row) or "") in _STATUS_ENCERRADO_EXEC_RJ
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


def list_execucao_atividades_abertas_RJ(
    agendamentos: list[dict[str, Any]],
    *,
    ref_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Agendamentos atualmente abertos do setor Execução RJ, independente do período —
    modal do card "Em andamento" da Confecção CS (espelho de
    :func:`list_execucao_atividades_abertas_NG`).
    """
    ref = ref_date or date.today()
    itens: list[dict[str, Any]] = []

    for row in agendamentos:
        status = _get_ag_status_rj(row) or ""
        if status in _STATUS_INATIVO_EXEC_RJ:
            continue
        ag_id = _to_int(row.get("id") or row.get("ID"))
        if ag_id is None:
            continue
        prazo = _get_ag_prazo_rj(row)
        criacao = _get_ag_data_criacao_rj(row)
        setor = str(row.get("SETOR") or row.get("setor") or "EXECUÇÃO").strip().upper()
        atividade = _get_ag_atividade_nome_rj(row)
        pessoa_setor = (
            f"{setor} - {atividade}"
            if atividade and atividade != _SEM_ATIVIDADE_EXEC_RJ
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
            "funcionario_atribuido": _get_ag_funcionario_atribuido_rj(row),
            "funcionario_encerramento": None,
            "atividade": atividade,
            "prazo": prazo.isoformat() if prazo else None,
            "criado_em": criacao.isoformat() if criacao else None,
            "concluido_em": None,
            "operacao": operacao,
            "encerrado_pelo_responsavel": None,
            "numero_processo": _get_ag_numero_processo_rj(row),
            "valor_sentenca": _get_ag_valor_sentenca_rj(row),
            "valor_acordao": _get_ag_valor_acordao_rj(row),
            "em_andamento": status in _STATUS_EM_ANDAMENTO_EXEC_RJ,
            "vencida": prazo is not None and prazo < ref,
            "vence_hoje": prazo is not None and prazo == ref,
            "concluida": False,
        })

    def _sort_key(item: dict[str, Any]) -> tuple[int, str, int]:
        prazo_raw = item.get("prazo")
        prazo_missing = 0 if prazo_raw else 1
        return (prazo_missing, str(prazo_raw or ""), int(item.get("id") or 0))

    return sorted(itens, key=_sort_key)


def list_execucao_atividades_por_prazo_periodo_RJ(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Lista de agendamentos do setor Execução RJ filtrados pelo PRAZO para a tabela de tarefas."""
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
        if status in _STATUS_ENCERRADO_EXEC_RJ and funcionario_enc is not None:
            encerrado_pelo_responsavel = (
                funcionario_enc.strip().lower() == funcionario_atrib.strip().lower()
            )
        setor = str(row.get("SETOR") or row.get("setor") or "EXECUÇÃO").strip().upper()
        atividade = _get_ag_atividade_nome_rj(row)
        pessoa_setor = (
            f"{setor} - {atividade}"
            if atividade and atividade != _SEM_ATIVIDADE_EXEC_RJ
            else setor
        )
        descricao_raw = row.get("DESCRICAO") or row.get("descricao")
        descricao = str(descricao_raw).strip().upper() if descricao_raw else "—"
        operacao = str(row.get("OPERACAO") or row.get("operacao") or "").strip()

        conclusao = _get_ag_data_conclusao_rj(row)

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
            "concluido_em": conclusao.isoformat() if conclusao else None,
            "operacao": operacao,
            "encerrado_pelo_responsavel": encerrado_pelo_responsavel,
            "numero_processo": _get_ag_numero_processo_rj(row),
            **situacao,
        })

    def _sort_key(item: dict[str, Any]) -> tuple[int, str, int]:
        prazo_raw = item.get("prazo")
        prazo_missing = 0 if prazo_raw else 1
        return (prazo_missing, str(prazo_raw or ""), int(item.get("id") or 0))

    return sorted(itens, key=_sort_key)


def get_opcoes_filtros_execucao_por_prazo_RJ(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, Any]:
    """Opções de filtros da lista por prazo — RJ."""
    rows = list_execucao_atividades_por_prazo_periodo_RJ(
        agendamentos, from_date=from_date, to_date=to_date, ref_date=ref_date
    )
    funcionarios: set[str] = set()
    atividades: set[str] = set()
    status_vistos: set[str] = set()

    for row in rows:
        funcionarios.add(str(row.get("funcionario") or _SEM_FUNCIONARIO_EXEC_RJ))
        atividade = str(row.get("atividade") or "").strip()
        if atividade and atividade != _SEM_ATIVIDADE_EXEC_RJ:
            atividades.add(atividade)
        status = str(row.get("status") or "").strip()
        if status and status != "—":
            status_vistos.add(status)

    status_ordenados: list[str] = []
    for label in _STATUS_FILTRO_EXEC_RJ:
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


def group_execucao_resolvidos_por_dia_por_prazo_RJ(
    agendamentos: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Produção diária (por prazo): quantidade de atividades "Encerrado Cumprido"
    por dia de PRAZO, histórico completo — RJ.
    """
    grouped: dict[str, int] = defaultdict(int)
    for row in agendamentos:
        if _get_ag_status_rj(row) != _STATUS_CUMPRIDO_EXEC_RJ:
            continue
        prazo = _get_ag_prazo_rj(row)
        if prazo is None:
            continue
        grouped[prazo.strftime("%Y-%m-%d")] += 1

    return [
        {"name": dia, "value": count}
        for dia, count in sorted(grouped.items(), key=lambda x: x[0])
    ]


def get_media_execucao_resolvidos_por_funcionario_por_prazo_RJ(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Média de atividades "Encerrado Cumprido" por funcionário no período,
    usando PRAZO como eixo temporal — RJ.
    """
    grouped: dict[str, dict[str, Any]] = defaultdict(lambda: {"total": 0, "dias": set()})
    for row in agendamentos:
        if _get_ag_status_rj(row) != _STATUS_CUMPRIDO_EXEC_RJ:
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
# Motivo de "Encerrado Não Cumprido" — RJ
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


def group_execucao_nao_cumprido_por_motivo_RJ(
    agendamentos: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Agrupa as atividades "Encerrado Não Cumprido" pelo motivo registrado no
    encaminhamento (MOTIVO_ENCAMINHAMENTO), histórico completo — RJ.

    Depende da coluna MOTIVO_ENCAMINHAMENTO estar disponível na query de
    agendamentos (``agendamentos_setor_execucao_LA_RJ``); sem ela, sempre
    retorna lista vazia.
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
# Detalhamento de atrasos (vencidas por dias de atraso) — RJ
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


def get_atrasos_detalhamento_execucao_RJ(
    agendamentos: list[dict[str, Any]],
    *,
    ref_date: Optional[date] = None,
) -> dict[str, Any]:
    """Detalhamento de agendamentos vencidos por dias de atraso (1–5 e 6+) — RJ."""
    ref = ref_date or date.today()
    counts: dict[int, int] = {d: 0 for d in range(1, _ATRASO_MAX_BUCKET_RJ + 1)}

    for row in agendamentos:
        status = _get_ag_status_rj(row) or ""
        if status in _STATUS_INATIVO_EXEC_RJ:
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
# X - Diligências (subconjunto de agendamentos do setor EXECUÇÃO)
# =============================================================================

def _eh_diligencia_rj(item: dict[str, Any]) -> bool:
    atividade = str(item.get("ATIVIDADE") or item.get("atividade") or "").upper()
    return "DILIG" in atividade


def filtrar_agendamentos_diligencia_RJ(
    agendamentos: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Restringe agendamentos do setor EXECUÇÃO aos que são diligência."""
    return [row for row in agendamentos if _eh_diligencia_rj(row)]


def get_total_diligencias_execucao_RJ(
    agendamentos_diligencia: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """Total de agendamentos de diligência criados no período."""
    return sum(
        1 for row in agendamentos_diligencia
        if _ag_data_no_periodo(_get_ag_data_criacao_rj(row), from_date, to_date)
    )


def group_execucao_diligencias_por_processo_RJ(
    agendamentos_diligencia: list[dict[str, Any]],
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Quantidade de agendamentos de diligência por processo, no período
    informado, com o valor de execução do processo (``valor_execucao``).
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
        valor = p.get("VALOR_EXECUCAO")
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


def _eh_diligencia_expedicao_alvara_rj(item: dict[str, Any]) -> bool:
    atividade = str(item.get("ATIVIDADE") or item.get("atividade") or "").upper()
    return "EXPEDIÇÃO DE ALVARÁ" in atividade


def filtrar_agendamentos_diligencia_expedicao_alvara_RJ(
    agendamentos_diligencia: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Restringe agendamentos de diligência aos de expedição de alvará."""
    return [
        row for row in agendamentos_diligencia
        if _eh_diligencia_expedicao_alvara_rj(row)
    ]


def get_kpis_diligencias_expedicao_alvara_execucao_RJ(
    agendamentos_expedicao_alvara: list[dict[str, Any]],
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    colaborador: Optional[str] = None,
) -> dict[str, Any]:
    """
    KPIs das diligências de expedição de alvará (subconjunto de diligências):
    total, cumpridas e valor (soma do VALOR_EXECUCAO dos processos com
    diligência cumprida no período, deduplicado por processo).
    """
    agendamentos_expedicao_alvara = filtrar_agendamentos_diligencia_por_colaborador_RJ(
        agendamentos_expedicao_alvara, colaborador
    )
    total = sum(
        1 for row in agendamentos_expedicao_alvara
        if _ag_data_no_periodo(_get_ag_data_criacao_rj(row), from_date, to_date)
    )

    cumpridas_rows, processos_cumpridos = _diligencias_expedicao_alvara_cumpridas_rj(
        agendamentos_expedicao_alvara, from_date, to_date
    )

    valor_por_id: dict[Any, float] = {}
    for p in processos:
        pid = p.get("id") or p.get("ID")
        valor = p.get("VALOR_EXECUCAO")
        if pid is not None and valor is not None:
            try:
                valor_por_id[pid] = float(valor)
            except (TypeError, ValueError):
                pass

    valor = sum(valor_por_id.get(pid, 0.0) for pid in processos_cumpridos)

    return {"total": total, "cumpridas": len(cumpridas_rows), "valor": valor}


def _diligencias_expedicao_alvara_cumpridas_rj(
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
        if _get_ag_status_rj(row) == _STATUS_CUMPRIDO_EXEC_RJ
    ]
    processos_cumpridos: set[Any] = {
        pid for row in cumpridas_rows
        if (pid := _get_ag_processo_id_rj(row)) is not None
    }
    return cumpridas_rows, processos_cumpridos


def list_processos_diligencia_expedicao_alvara_cumprida_execucao_RJ(
    agendamentos_expedicao_alvara: list[dict[str, Any]],
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    colaborador: Optional[str] = None,
) -> list[dict[str, Any]]:
    """
    Lista os processos que compõem o valor do card "Valor Realizado (Alvará)".
    """
    agendamentos_expedicao_alvara = filtrar_agendamentos_diligencia_por_colaborador_RJ(
        agendamentos_expedicao_alvara, colaborador
    )
    _, processos_cumpridos = _diligencias_expedicao_alvara_cumpridas_rj(
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
        valor = _get_valor_execucao_RJ(p)
        data_execucao = _get_data_execucao_RJ(p)
        itens.append({
            "numero_processo": str((p.get("NUMERO_PROCESSO") or p.get("numero_processo")) or "").strip() or "—",
            "uf": str(p.get("UF") or "").strip().upper() or "—",
            "data_execucao": data_execucao.isoformat() if data_execucao else None,
            "valor_execucao": _converter_valor(valor) if valor is not None else None,
            "subfase": _normalizar_subfase(p.get("SUBFASE")),
        })
    return sorted(itens, key=lambda x: (x["valor_execucao"] or 0), reverse=True)


_TIPOS_VALIDOS_DILIGENCIA_RJ = ("expedicao_alvara", "expedicao_alvara_cumprida")


def filtrar_agendamentos_diligencia_por_tipo_RJ(
    agendamentos_diligencia: list[dict[str, Any]],
    tipo: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Filtra diligências pelo card clicado na seção Diligências."""
    if tipo not in _TIPOS_VALIDOS_DILIGENCIA_RJ:
        return agendamentos_diligencia
    base = filtrar_agendamentos_diligencia_expedicao_alvara_RJ(agendamentos_diligencia)
    if tipo == "expedicao_alvara_cumprida":
        base = [row for row in base if _get_ag_status_rj(row) == _STATUS_CUMPRIDO_EXEC_RJ]
    return base


def filtrar_agendamentos_diligencia_por_colaborador_RJ(
    agendamentos_diligencia: list[dict[str, Any]],
    colaborador: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Filtra diligências pelo colaborador clicado no ranking."""
    if colaborador is None or not str(colaborador).strip():
        return agendamentos_diligencia
    alvo = str(colaborador).strip()
    return [
        row for row in agendamentos_diligencia
        if (_get_ag_funcionario_encerramento_rj(row) or "").strip() == alvo
    ]


def group_estoque_execucao_RJ_por_mes(
    execucao: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Estoque em Execução ao fim de cada mês: (quantidade, valor em aberto) —
    base do "Ticket Médio Total" mês a mês.
    """
    intervalos = []
    for p in _base_execucao_RJ(execucao):
        entrada = _get_data_execucao_RJ(p)
        if entrada is None:
            continue
        saida = _get_data_compensacao_alvara_RJ(p)
        if saida is None and not _processo_em_execucao_RJ(p):
            continue
        ini = indice_mes(entrada)
        fim = indice_mes(saida) if saida is not None else None
        valor_cheio = _converter_valor(_get_valor_execucao_RJ(p))
        incontroverso = _get_data_compensacao_alvara_incontroverso_RJ(p)
        if incontroverso is None:
            intervalos.append((ini, fim, True, valor_cheio))
            continue
        corte = indice_mes(incontroverso)
        fim_cheio = corte if fim is None else min(corte, fim)
        intervalos.append((ini, fim_cheio, True, valor_cheio))
        intervalos.append((max(ini, corte), fim, True, _converter_valor(_get_valor_remanescente_RJ(p))))
    return estoque_por_mes(intervalos, _MONTH_NAMES)


def filtrar_saida_execucao_export_RJ(
    execucao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Recorte "Saída" do relatório exportado: processos com compensação do alvará
    (:func:`_filtrar_saida_no_periodo_RJ`) OU com compensação do alvará do
    incontroverso (:func:`_filtrar_saida_incontroverso_no_periodo_RJ`) no período,
    sem repetir processo — os mesmos dois conjuntos que somam o card "Valor saída
    Execução" (:func:`get_valor_execucao_saida_periodo_RJ`).
    """
    vistos: set[Any] = set()
    filtrados: list[dict[str, Any]] = []
    for item in (
        _filtrar_saida_no_periodo_RJ(execucao, from_date, to_date)
        + _filtrar_saida_incontroverso_no_periodo_RJ(execucao, from_date, to_date)
    ):
        chave = item.get("NUMERO_PROCESSO") or item.get("id") or item.get("ID")
        if chave is not None:
            if chave in vistos:
                continue
            vistos.add(chave)
        filtrados.append(item)
    return filtrados


def anotar_saida_execucao_export_RJ(
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
      senão VALOR_EXECUCAO cheio, via :func:`_get_valor_execucao_em_aberto_RJ`). A
      soma desta coluna no recorte "Saída" bate com o card.
    """
    anotadas: list[dict[str, Any]] = []
    for item in rows:
        saiu_alvara = _data_no_periodo(_get_data_compensacao_alvara_RJ(item), from_date, to_date)
        saiu_incontroverso = _data_no_periodo(
            _get_data_compensacao_alvara_incontroverso_RJ(item), from_date, to_date
        )

        valor_saida: Optional[float] = None
        if saiu_alvara or saiu_incontroverso:
            valor_saida = 0.0
            if saiu_alvara:
                valor = _get_valor_execucao_em_aberto_RJ(item)
                if valor is not None:
                    valor_saida += _converter_valor(valor)
            if saiu_incontroverso:
                valor = _get_valor_incontroverso_RJ(item)
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
