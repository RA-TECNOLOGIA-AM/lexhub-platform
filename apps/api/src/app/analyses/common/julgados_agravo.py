"""Agravos fora das análises de Julgados.

No número CNJ (NNNNNNN-DD.AAAA.J.TR.OOOO), os 4 últimos dígitos são a origem; ``0000`` e ``9000``–``9002``
identificam recursos de agravo, que não são sentenças/acórdãos de mérito do processo e não entram nas
contagens. Só vale para números com os 20 dígitos do padrão (números malformados nunca são excluídos).
"""

from __future__ import annotations

import re
from typing import Any

ORIGENS_AGRAVO: frozenset[str] = frozenset({"0000", "9000", "9001", "9002"})


def eh_processo_agravo(numero: Any) -> bool:
    digitos = re.sub(r"\D", "", str(numero or ""))
    return len(digitos) == 20 and digitos[-4:] in ORIGENS_AGRAVO


def numero_processo(item: dict[str, Any]) -> Any:
    return item.get("NUMERO_PROCESSO") or item.get("numero_processo")
