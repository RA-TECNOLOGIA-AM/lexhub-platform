"""Tempo médio e mediana entre duas datas de uma linha: o cálculo comum das análises (V2).

As análises copiadas da v1 tinham, cada uma, a própria cópia de "extrair as durações", da média, da mediana e
da variação "vs período anterior". O que muda de uma análise para outra é só a configuração:

    entrada / saida   como ler as datas: `coluna("X")` ou a função de leitura da própria análise
    de / ate          o período, recortado pela data de SAÍDA (sem período: o histórico todo);
                      `data_periodo` quando o recorte lê a data de outro jeito que a duração
    unidade           "dias" (de calendário, `.days`), "dias_fracao" (com as horas) ou "horas"
    aceita_zero       se a duração 0 entra (Protocolo/Execução/LexPre da v1 só contam > 0)
    casas / vazio     arredondamento e o valor sem dados (2 casas e 0.0; Julgados: 1 casa e None)
    divisor           divide o resultado (LexPre: média e mediana em horas, divididas por 24 no fim)
    sem_base          a variação quando o anterior é 0 e o atual não (0.0; LexPre e Financeiro: 100.0)

O pré-filtro de cada análise (ex.: só os protocolos resolvidos) e o jeito de achar a entrada (ex.: no LexPre,
a última entrada no setor antes da saída) continuam nela: aqui entram as linhas e as funções de leitura.
Linha com data ausente, inválida ou com duração negativa fica fora.
"""

from collections import defaultdict
from collections.abc import Callable, Hashable, Iterable
from datetime import date, datetime
from typing import Any, Literal

from app.utils import parse_date_from_db, parse_datetime_from_db

LerData = Callable[[dict[str, Any]], Any]  # devolve date ou datetime (ou None)
Unidade = Literal["dias", "dias_fracao", "horas"]
FORA = (
    object()
)  # devolvido por `grupo` em duracoes_por_grupo: a linha fica fora (None é um grupo válido)


def para_data(valor: Any) -> date | None:
    """Valor bruto do banco -> `date` (datetime vira a data dele); ausente ou inválido -> None."""
    if not valor:
        return None
    convertido = parse_date_from_db(valor)
    if isinstance(convertido, datetime):
        return convertido.date()
    if isinstance(convertido, date):
        return convertido
    return None


def coluna(nome: str, *, com_hora: bool = False) -> LerData:
    """Lê a data de uma coluna, em maiúsculas ou minúsculas (como as cópias da v1: `p.get("X") or p.get("x")`).
    `com_hora`: data e hora (`parse_datetime_from_db`), para durações em horas ou com fração de dia."""
    minusculo = nome.lower()

    def ler(linha: dict[str, Any]) -> Any:
        valor = linha.get(nome) or linha.get(minusculo)
        if com_hora:
            return parse_datetime_from_db(valor) if valor else None
        return para_data(valor)

    return ler


def no_periodo(d: date | None, de: date | None, ate: date | None) -> bool:
    """`d` dentro de [de, ate] (inclusive); só um dos limites também vale. Sem data: fora."""
    if d is None:
        return False
    return (not de or d >= de) and (not ate or d <= ate)


def _medir(inicio: Any, fim: Any, unidade: Unidade) -> float:
    if unidade == "dias":
        return float((fim - inicio).days)
    segundos = (fim - inicio).total_seconds()
    return float(segundos / 86400.0) if unidade == "dias_fracao" else float(segundos / 3600)


def _pares(
    linhas: Iterable[dict[str, Any]],
    entrada: LerData,
    saida: LerData,
    de: date | None,
    ate: date | None,
    data_periodo: LerData | None,
    unidade: Unidade,
    aceita_zero: bool,
) -> Iterable[tuple[dict[str, Any], Any, float]]:
    """(linha, saída, duração) de cada linha que entra no cálculo, na ordem das linhas."""
    filtra = de is not None or ate is not None
    for linha in linhas:
        try:
            fim = saida(linha)
            if filtra and not no_periodo(data_periodo(linha) if data_periodo else fim, de, ate):
                continue
            inicio = entrada(linha)
            if not inicio or not fim:
                continue
            valor = _medir(inicio, fim, unidade)
        except (ValueError, AttributeError, TypeError):
            continue
        if valor > 0 or (aceita_zero and valor == 0):
            yield linha, fim, valor


def duracoes(
    linhas: Iterable[dict[str, Any]],
    entrada: LerData,
    saida: LerData,
    *,
    de: date | None = None,
    ate: date | None = None,
    data_periodo: LerData | None = None,
    unidade: Unidade = "dias",
    aceita_zero: bool = False,
) -> list[float]:
    """A duração (entrada -> saída) de cada linha, na ordem das linhas.

    Com `de`/`ate`, só as linhas cuja SAÍDA (ou `data_periodo`) caiu no período. Fica fora a linha sem uma das
    datas, com data inválida ou com duração negativa; a duração 0 só entra com `aceita_zero`."""
    return [
        valor
        for _, _, valor in _pares(
            linhas, entrada, saida, de, ate, data_periodo, unidade, aceita_zero
        )
    ]


def duracoes_por_grupo(
    linhas: Iterable[dict[str, Any]],
    entrada: LerData,
    saida: LerData,
    grupo: Callable[[dict[str, Any], Any], Hashable | None],
    *,
    de: date | None = None,
    ate: date | None = None,
    data_periodo: LerData | None = None,
    unidade: Unidade = "dias",
    aceita_zero: bool = False,
) -> dict[Hashable, list[float]]:
    """As durações separadas por grupo (`grupo(linha, saída)`, ex.: o mês da saída ou a comarca), na ordem em
    que cada grupo aparece. `grupo` devolve FORA para deixar a linha de fora."""
    por_grupo: dict[Hashable, list[float]] = defaultdict(list)
    for linha, fim, valor in _pares(
        linhas, entrada, saida, de, ate, data_periodo, unidade, aceita_zero
    ):
        chave = grupo(linha, fim)
        if chave is not FORA:
            por_grupo[chave].append(valor)
    return dict(por_grupo)


def media(
    valores: list[float], *, casas: int | None = 2, vazio: Any = 0.0, divisor: float = 1
) -> Any:
    """Média simples (÷ `divisor`), em `casas` (None: sem arredondar); sem valores, `vazio`."""
    if not valores:
        return vazio
    resultado = (sum(valores) / len(valores)) / divisor
    return resultado if casas is None else round(resultado, casas)


def mediana(
    valores: list[float], *, casas: int | None = 2, vazio: Any = 0.0, divisor: float = 1
) -> Any:
    """Mediana (número par de valores: a média dos dois do meio), ÷ `divisor`, em `casas`; sem valores,
    `vazio`."""
    if not valores:
        return vazio
    ordenados = sorted(valores)
    n = len(ordenados)
    meio = ordenados[n // 2] if n % 2 == 1 else (ordenados[n // 2 - 1] + ordenados[n // 2]) / 2.0
    resultado = meio / divisor
    return resultado if casas is None else round(resultado, casas)


def variacao_percentual(
    atual: float, anterior: float, *, casas: int = 2, sem_base: float = 0.0
) -> float:
    """Variação (%) do atual sobre o anterior. Anterior 0: `sem_base` se o atual tem valor (crescimento a partir
    do zero; o LexPre e o Financeiro mostram +100%), senão 0.0."""
    if not anterior:
        return sem_base if atual and atual > 0 else 0.0
    return round(((atual - anterior) / anterior) * 100, casas)
