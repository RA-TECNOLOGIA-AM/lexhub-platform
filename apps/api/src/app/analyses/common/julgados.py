"""Julgados (Sentença e Acórdão): leitores e agrupamentos comuns (V2).

As cópias de Julgados Sentença e Julgados Acórdão (NG, LA e RJ) tinham, cada uma, os mesmos leitores de coluna
(matéria, comarca, competência, UF, fase, ano de ajuizamento...), o mesmo agrupamento e a mesma base. Aqui fica
uma só; a base recebe o escritório da unidade.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Any

from app.analyses.common import conversao, textos
from app.analyses.common import matriz_julgamento as mj
from app.analyses.common.julgados_agravo import eh_processo_agravo, numero_processo
from app.utils import resolver_periodo_comparativo

_COL_ID_ESCRITORIO = "ID_ESCRITORIO"
_COL_STATUS_2G = "STATUS_2G"
_COL_DATA_AJUIZAMENTO = "DATA_AJUIZAMENTO"
_COL_MATERIA = "MATERIA"
_COL_COMPETENCIA = "COMPETENCIA"
_COL_COMARCA = "COMARCA"
_COL_UF = "UF"
_SEM_MATERIA = "Sem matéria"
_SEM_COMPETENCIA = "Sem competência"
_SEM_COMARCA = "Sem comarca"
_SEM_ANO_AJUIZAMENTO = "Sem data de ajuizamento"


def base(processos: list[dict[str, Any]], escritorio: int) -> list[dict[str, Any]]:
    """Base padrão dos Julgados: só o escritório pedido (``ID_ESCRITORIO``), sem agravos
    (ver :func:`~app.analyses.common.julgados_agravo.eh_processo_agravo`)."""
    return [
        item
        for item in processos
        if conversao.para_inteiro(
            item.get(_COL_ID_ESCRITORIO) or item.get("id_escritorio_assinante")
        )
        == escritorio
        and not eh_processo_agravo(numero_processo(item))
    ]


def id_2g(item: dict[str, Any]) -> int | None:
    """ID de mérito 2G do MESMO processo (a query `julgados` traz 1G e 2G na mesma linha) —
    usa a coluna nova quando presente, senão traduz o status antigo por nome. Usado para achar
    sentenças extintas em 1G cujo acórdão em 2G foi "Sentença Anulada" (extinção revertida)."""
    novo = conversao.para_inteiro(
        item.get("ID_ACORDAO_MERITO_2G") or item.get("id_acordao_merito_grau2")
    )
    status_antigo = item.get(_COL_STATUS_2G) or item.get("status_2g")
    return mj.resolver_id_merito_2g(novo, status_antigo)


def data_ajuizamento(item: dict[str, Any]) -> date | None:
    return conversao.para_data(item.get(_COL_DATA_AJUIZAMENTO) or item.get("data_ajuizamento"))


def ano_ajuizamento(item: dict[str, Any]) -> str:
    ajuizamento = data_ajuizamento(item)
    return str(ajuizamento.year) if ajuizamento else _SEM_ANO_AJUIZAMENTO


def para_float(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def materia(item: dict[str, Any]) -> str:
    nome = str(item.get(_COL_MATERIA) or item.get("materia") or "").strip()
    return nome if nome else _SEM_MATERIA


def competencia(item: dict[str, Any]) -> str:
    nome = str(item.get(_COL_COMPETENCIA) or item.get("competencia") or "").strip()
    return nome if nome else _SEM_COMPETENCIA


def comarca(item: dict[str, Any]) -> str:
    nome = str(item.get(_COL_COMARCA) or item.get("comarca") or "").strip()
    return nome if nome else _SEM_COMARCA


def uf(item: dict[str, Any]) -> str:
    return str(item.get(_COL_UF) or item.get("uf") or "").strip().upper()


iniciais_nome = textos.iniciais_nome


def valor_em_conjunto(valor: str, conjunto: frozenset[str] | None) -> bool:
    if not conjunto:
        return True
    chave = valor.casefold()
    return any(chave == v.casefold() for v in conjunto)


def resolver_periodos_comparativo(
    from_date: date | None,
    to_date: date | None,
) -> tuple[date, date, date, date]:
    """Retorna (início_atual, fim_atual, início_anterior, fim_anterior).

    O período anterior é o mesmo período um mês civil antes (ex.: 01/08-20/08 ->
    01/07-20/07).
    """
    return resolver_periodo_comparativo(from_date, to_date)


def agrupar_por_campo(
    itens_base: list[dict[str, Any]],
    obter_campo: Any,
) -> list[dict[str, Any]]:
    grouped: dict[str, int] = defaultdict(int)
    for item in itens_base:
        grouped[obter_campo(item)] += 1
    total = float(sum(grouped.values()))
    itens: list[dict[str, Any]] = []
    for nome, qtd in grouped.items():
        itens.append(
            {
                "name": nome,
                "value": float(qtd),
                "percent": round(100.0 * float(qtd) / total, 1) if total > 0 else 0.0,
            }
        )
    return sorted(itens, key=lambda x: float(x["value"]), reverse=True)


def fase(item: dict[str, Any]) -> str:
    nome = str(item.get("FASE") or item.get("fase") or "").strip()
    return nome if nome else "—"


def subfase(item: dict[str, Any]) -> str:
    nome = str(item.get("SUBFASE") or item.get("subfase") or "").strip()
    return nome if nome else "—"


def numero_processo_linha(item: dict[str, Any]) -> str:
    numero = str(item.get("NUMERO_PROCESSO") or item.get("numero_processo") or "").strip()
    return numero if numero else "—"
