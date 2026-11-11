"""
Reconstrução do estoque de Execução ao fim de cada mês (quantidade e valor em
aberto), compartilhada pelos módulos de Execução Condenação/Acordos NG e LA.

Cada processo vira um ou dois intervalos de meses ``[início, fim)`` com um valor
constante; o estoque do mês ``m`` é a soma dos intervalos que cobrem ``m``.
Usa arrays de diferença, então o custo é O(processos + meses).
"""

from __future__ import annotations

from datetime import date
from typing import Iterable, Optional, Sequence

# (mês de início, mês de fim exclusivo ou None = até o mês atual, conta no total?, valor)
Intervalo = tuple[int, Optional[int], bool, float]


def indice_mes(d: date) -> int:
    return d.year * 12 + (d.month - 1)


def estoque_por_mes(
    intervalos: Iterable[Intervalo],
    month_names: Sequence[str],
    hoje: Optional[date] = None,
) -> tuple[list[dict], list[dict]]:
    """Retorna (quantidade_por_mes, valor_por_mes), um item por mês desde o primeiro início até o mês atual."""
    atual = indice_mes(hoje or date.today())
    itens = [i for i in intervalos if i[0] <= atual]
    if not itens:
        return [], []

    inicio = min(i[0] for i in itens)
    tamanho = atual - inicio + 2
    diff_qtd = [0] * tamanho
    diff_valor = [0.0] * tamanho

    for ini, fim, conta, valor in itens:
        fim_efetivo = atual + 1 if fim is None else min(fim, atual + 1)
        if fim_efetivo <= ini:
            continue
        a, b = ini - inicio, fim_efetivo - inicio
        if conta:
            diff_qtd[a] += 1
            diff_qtd[b] -= 1
        diff_valor[a] += valor
        diff_valor[b] -= valor

    quantidade: list[dict] = []
    valores: list[dict] = []
    qtd_acum = 0
    valor_acum = 0.0
    for offset in range(atual - inicio + 1):
        qtd_acum += diff_qtd[offset]
        valor_acum += diff_valor[offset]
        mes = inicio + offset
        nome = f"{month_names[mes % 12]} {mes // 12}"
        quantidade.append({"name": nome, "value": qtd_acum})
        valores.append({"name": nome, "value": round(valor_acum, 2)})
    return quantidade, valores
