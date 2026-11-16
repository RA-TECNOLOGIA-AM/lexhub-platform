"""Novo na V2 (veio da v1): "Rubricas dentro de RUBRICAS_REUNIDAS".

Na v1, clicar numa matéria de rubrica reunida (pacote) abria uma janela com as demandas desse pacote
no setor e as rubricas que compõem cada uma. Aqui sai pronto na resposta do dashboard, já com o
período e os filtros da página:

- resolvido  = a demanda saiu do setor no período (peticionada);
- represado  = está no setor agora (independe do período);
- protocolado = foi protocolada no período (pode ser também resolvida).

Os componentes de cada demanda vêm de `demanda_rubrica_reunida_lexpre_NG` (só os que o time
configurou para aquele caso, não o mapa genérico do pacote).
"""

from collections.abc import Callable, Iterable
from typing import Any

Row = dict[str, Any]


def componentes_por_demanda(componentes: Iterable[Row]) -> dict[Any, list[str]]:
    """demanda -> nomes das rubricas associadas (sem repetir, na ordem em que vieram)."""
    out: dict[Any, list[str]] = {}
    for c in componentes:
        demanda = c.get("DEMANDA_ID")
        nome = str(c.get("RUBRICA_ASSOCIADA_NOME") or "").strip()
        if demanda is None or not nome:
            continue
        nomes = out.setdefault(demanda, [])
        if nome not in nomes:
            nomes.append(nome)
    return out


def rubricas_reunidas(
    rows: Iterable[Row],
    *,
    resolvidos: set,
    protocolados: set,
    em_fila: Callable[[Row], bool],
    componentes: dict[Any, list[str]],
    normalizar: Callable[[Any], str],
) -> list[dict[str, Any]]:
    """Por matéria reunida: as demandas (resolvidas ou represadas) com cliente e rubricas.

    `rows` já vem com o escritório e os filtros da página aplicados. `em_fila` diz se a demanda está
    no setor agora (e não cancelada). Demanda que não foi resolvida no período nem está na fila não entra.
    Matérias e demandas em ordem: matéria pelo nome; demanda da mais nova (maior id) para a mais antiga.
    """
    por_materia: dict[str, dict[Any, dict[str, Any]]] = {}
    for row in rows:
        if not row.get("RUBRICA_REUNIDA"):
            continue
        demanda = row.get("ID_DEMANDA")
        if demanda is None:
            continue
        materia = normalizar(row.get("MATERIA"))
        demandas = por_materia.setdefault(materia, {})
        atual = demandas.get(demanda)
        represado = em_fila(row) or (atual is not None and atual["situacao"] == "represado")
        if not represado and demanda not in resolvidos:
            continue
        demandas[demanda] = {
            "id_demanda": demanda,
            "cliente": str(row.get("CLIENTE_NOME") or "").strip() or None,
            "situacao": "represado" if represado else "resolvido",
            "protocolado": demanda in protocolados,
            "rubricas": componentes.get(demanda, []),
        }
    return [
        {
            "materia": materia,
            "demandas": sorted(demandas.values(), key=lambda d: _ordem(d["id_demanda"])),
        }
        for materia, demandas in sorted(por_materia.items())
        if demandas
    ]


def _ordem(demanda: Any) -> tuple:
    """Mais nova primeiro (id numérico maior); id não numérico vai para o fim."""
    try:
        return (0, -int(demanda))
    except (TypeError, ValueError):
        return (1, str(demanda))
