"""Agravos fora de todas as queries do LexFlow (regra da v1 de 06/11/2026, api_dashboards/src/app/queries.py).

Processos de agravo são cadastrados no LexFlow como processos próprios e NÃO entram em nenhuma análise.
Agravo = número CNJ com 20 dígitos cuja origem (4 últimos dígitos) é 0000 / 9000 / 9001 / 9002 — a mesma
regra do helper Python :func:`app.analyses.common.julgados_agravo.eh_processo_agravo`.

Na v1 o filtro era injetado no fim de ``queries.py``, num ponto só; as queries foram copiadas para
``source_queries.py`` "sem mudar o texto", então esse passo ficou para trás e os dashboards da V2 passaram a
contar agravos (2 a 4% das linhas, conferido em 23/11/2026). ``aplicar_em`` refaz o passo, em toda query do
banco ``lexflow`` que lê ``public.processo``:

- FROM/JOIN (inner) em ``public.processo X``: a tabela vira um subselect já sem agravos (o planner achata o
  subselect, sem custo extra relevante);
- LEFT JOIN em ``public.processo X`` (publicações, cuja linha base não é o processo): o predicado entra no
  WHERE principal, mantendo as linhas sem processo vinculado (número nulo => não é agravo).

Fora: as queries ``agendamentos_*`` — a atividade feita num agravo conta normalmente para o setor/funcionário.
"""

from __future__ import annotations

import re

from app.analyses.common.julgados_agravo import ORIGENS_AGRAVO

PREFIXOS_SEM_FILTRO_AGRAVO = ("agendamentos_",)

# Coluna de número usada no LEFT JOIN quando a linha base tem número próprio.
_NUMERO_LEFT_JOIN_OVERRIDE = {
    "publicacoes_NG": "COALESCE(pro.numero_processo, p.numero_processo)",
    "publicacoes_LA": "COALESCE(pro.numero_processo, p.numero_processo)",
    "publicacoes_LA_RJ": "COALESCE(pro.numero_processo, p.numero_processo)",
}

_RE_LEFT_JOIN_PROCESSO = re.compile(
    r"\bleft\s+(?:outer\s+)?join\s+public\.processo\s+(?:as\s+)?(\w+)", re.IGNORECASE
)
_RE_INNER_PROCESSO = re.compile(
    r"(?<![\w.])(from|join)(\s+)(?:public\.)?processo(?![\w])(\s+)(?:as\s+)?(\w+)", re.IGNORECASE
)
_RE_LE_PROCESSO = re.compile(r"(?<![\w.])(?:public\.)?processo(?![\w])", re.IGNORECASE)


def sql_nao_agravo(coluna_numero: str) -> str:
    """Predicado SQL verdadeiro quando o número NÃO é de agravo (nulo conta como não-agravo)."""
    digitos = f"regexp_replace(COALESCE({coluna_numero}, ''), '[^0-9]', '', 'g')"
    origens = ", ".join(f"'{o}'" for o in sorted(ORIGENS_AGRAVO))
    return f"NOT (length({digitos}) = 20 AND right({digitos}, 4) IN ({origens}))"


def precisa_filtro(nome: str, cfg: dict) -> bool:
    """Query do LexFlow que lê ``processo`` e não é de agendamentos."""
    return (
        cfg.get("database") == "lexflow"
        and not nome.startswith(PREFIXOS_SEM_FILTRO_AGRAVO)
        and bool(_RE_LE_PROCESSO.search(cfg["query"]))
    )


def _tem_or_topo(trecho: str) -> bool:
    """OR fora de parênteses (mudaria a precedência ao prefixar ``pred AND``)."""
    profundidade = 0
    for m in re.finditer(r"\(|\)|\bor\b", trecho, re.IGNORECASE):
        tok = m.group(0)
        if tok == "(":
            profundidade += 1
        elif tok == ")":
            profundidade -= 1
        elif profundidade == 0:
            return True
    return False


def excluir_agravos(nome: str, sql: str) -> str:
    """O SQL da query ``nome`` sem os processos de agravo. Para com erro se não souber onde injetar."""
    left = _RE_LEFT_JOIN_PROCESSO.findall(sql)
    if left:
        aliases = set(left)
        assert len(aliases) == 1, f"{nome}: mais de um LEFT JOIN em processo"
        alias = aliases.pop()
        coluna = _NUMERO_LEFT_JOIN_OVERRIDE.get(nome, f"{alias}.numero_processo")
        wheres = list(re.finditer(r"\bwhere\b", sql, re.IGNORECASE))
        assert len(wheres) == 1, f"{nome}: esperado 1 WHERE para injetar o filtro de agravo"
        resto = sql[wheres[0].end() :]
        assert not _tem_or_topo(resto) and not re.search(
            r"\bgroup\s+by\b|\border\s+by\b|\blimit\b|\bunion\b", resto, re.IGNORECASE
        ), f"{nome}: WHERE com OR de topo/GROUP/ORDER — injetar o filtro de agravo à mão"
        w = wheres[0]
        return f"{sql[: w.start()]}WHERE {sql_nao_agravo(coluna)}\n          AND{sql[w.end() :]}"

    def _sub(m: re.Match[str]) -> str:
        kw, sp1, sp2, alias = m.groups()
        if alias.lower() in {"on", "where", "left", "join", "inner", "group", "order"}:
            raise AssertionError(f"{nome}: public.processo sem alias")
        return f"{kw}{sp1}(SELECT * FROM public.processo WHERE {sql_nao_agravo('numero_processo')}){sp2}{alias}"

    # Sem LEFT JOIN: todo FROM/JOIN em public.processo é inner — filtra na fonte.
    return _RE_INNER_PROCESSO.sub(_sub, sql)


def aplicar_em(queries: dict[str, dict]) -> None:
    """Injeta o filtro de agravo, no lugar, em toda query que ``precisa_filtro``."""
    for nome, cfg in queries.items():
        if precisa_filtro(nome, cfg):
            cfg["query"] = excluir_agravos(nome, cfg["query"])
