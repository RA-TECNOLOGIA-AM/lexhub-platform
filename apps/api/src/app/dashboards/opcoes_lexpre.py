"""Novo na V2: valores possíveis dos filtros de um dashboard por setor do LexPre (log_setor_demanda).

Calculados nas linhas da unidade ANTES de aplicar os filtros, com os mesmos campos que os filtros
da v1 comparam: MATERIA (normalizada pela função do módulo da v1), funcionários (a mesma lista de
GET /<dashboard>-lexpre/funcionarios da v1), UF do cliente e área de atuação (AREA_ATUACAO_ID/NOME).
"""

from collections.abc import Callable, Iterable
from typing import Any

Rows = list[dict[str, Any]]


def opcoes_filtro_setor(
    rows: Rows,
    normalizar_materia: Callable[[Any], str],
    list_funcionarios: Callable[[Rows], list[str]],
    campos: Iterable[str] = ("materias", "funcionarios", "ufs", "areas"),
) -> dict[str, Any]:
    """Só as listas dos filtros que o dashboard tem (`campos`)."""
    materias: dict[str, str] = {}
    ufs: set[str] = set()
    areas: dict[int, str] = {}
    for row in rows:
        materia = row.get("MATERIA")
        if materia is not None and str(materia).strip():
            materias.setdefault(normalizar_materia(materia), str(materia).strip())
        uf = str(row.get("UF") or "").strip().upper()
        if uf:
            ufs.add(uf)
        area_id = row.get("AREA_ATUACAO_ID")
        if area_id is not None:
            areas.setdefault(int(area_id), str(row.get("AREA_ATUACAO_NOME") or area_id).strip())
    todas = {
        "materias": lambda: sorted(materias.values(), key=str.lower),
        "funcionarios": lambda: list_funcionarios(rows),
        "ufs": lambda: sorted(ufs),
        "areas": lambda: [
            {"id": i, "nome": n} for i, n in sorted(areas.items(), key=lambda a: a[1].lower())
        ],
    }
    return {nome: todas[nome]() for nome in campos}
