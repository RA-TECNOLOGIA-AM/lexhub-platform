"""Datas e períodos: as regras comuns das análises (V2).

As cópias da v1 tinham, cada uma, o próprio "a data está no período?" (`_data_no_periodo`, 21 cópias
iguais) e o próprio "variação vs período anterior" (dezenas de cópias da mesma conta). Aqui fica uma só.
"""

from collections.abc import Callable
from datetime import date
from typing import Any


def no_periodo(d: date | None, de: date | None, ate: date | None) -> bool:
    """`d` dentro de [de, ate] (inclusive); só um dos limites também vale; sem limites, qualquer data. Sem
    data: fora."""
    if d is None:
        return False
    return (not de or d >= de) and (not ate or d <= ate)


def variacao_percentual(
    atual: float, anterior: float, *, casas: int = 2, sem_base: float = 0.0
) -> float:
    """Variação (%) do atual sobre o anterior. Anterior 0: `sem_base` se o atual tem valor (crescimento a partir
    do zero; o LexPre e o Financeiro mostram +100%), senão 0.0."""
    if not anterior:
        return sem_base if atual and atual > 0 else 0.0
    return round(((atual - anterior) / anterior) * 100, casas)


def resolver_intervalo(de: date | None, ate: date | None) -> tuple[date | None, date | None]:
    """Normaliza o intervalo: com início e sem fim, o fim é hoje."""
    if de and not ate:
        return de, date.today()
    return de, ate


def filtrar_por_colunas(
    linhas: list[dict[str, Any]],
    colunas: list[str],
    de: date | None,
    ate: date | None,
    *,
    para_data: Callable[[Any], date | None],
) -> list[dict[str, Any]]:
    """As linhas em que QUALQUER uma das colunas (em maiúsculas ou minúsculas) tem data no período; sem
    período, todas (a mesma lista)."""
    if not de and not ate:
        return linhas
    resultado = []
    for linha in linhas:
        for coluna in colunas:
            bruto = linha.get(coluna) or linha.get(coluna.lower())
            if bruto is None:
                continue
            d = para_data(bruto)
            if d is not None and no_periodo(d, de, ate):
                resultado.append(linha)
                break
    return resultado
