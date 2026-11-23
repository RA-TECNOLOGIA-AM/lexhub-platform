"""Atividades (agendamentos do LexFlow): as regras comuns das análises (V2).

Pendências Intermediárias, Emendas e Manifestações, Réplicas, Execução e Acordos (NG, LA e RJ) tinham, cada
um, a própria cópia de "em que situação está a tarefa", "quem entra na lista", "encerradas no período" e
"média de concluídas por funcionário". A regra é a mesma; muda só a configuração:

    Leitor   como ler a linha: datas de criação, conclusão e prazo, status e quem encerrou
             (cada análise lê das próprias colunas, com as próprias funções)
    Status   quais status contam como inativo, em andamento e encerrado (ex.: "Encaminhado" é "em
             andamento" nas Pendências e não na Execução)

Duas visões, como na v1:
    por período   a tarefa criada no período (em andamento), a ativa vencida ou que vence hoje (qualquer
                  data de criação) e a encerrada no período (concluída)
    por prazo     tudo pelo PRAZO dentro do período (em andamento, vencida, vence hoje e concluída)

O Recursal usa outra regra (só conta vencida a tarefa aberta criada no período) e continua no módulo dele.
"""

from collections import defaultdict
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date
from typing import Any

from app.analyses.common.periodo import no_periodo

Linha = dict[str, Any]
LerData = Callable[[Linha], date | None]


@dataclass(frozen=True)
class Leitor:
    """Como uma análise lê a linha de um agendamento."""

    criacao: LerData
    conclusao: LerData
    prazo: LerData
    status: Callable[[Linha], str | None]
    funcionario_encerramento: Callable[[Linha], str | None]


@dataclass(frozen=True)
class Status:
    """Os status que contam como inativo (cancelada/encerrada), em andamento e encerrado (concluída)."""

    inativo: frozenset[str]
    em_andamento: frozenset[str]
    encerrado: frozenset[str]


def _situacao(
    em_andamento: bool, vencida: bool, vence_hoje: bool, concluida: bool
) -> dict[str, bool]:
    return {
        "em_andamento": em_andamento,
        "vencida": vencida,
        "vence_hoje": vence_hoje,
        "concluida": concluida,
    }


# --- por período -------------------------------------------------------------------------------------------


def incluir_na_lista(
    row: Linha,
    leitor: Leitor,
    status: Status,
    de: date | None,
    ate: date | None,
    *,
    ref: date | None = None,
) -> bool:
    """Entra na lista do período: criada no período, encerrada no período ou ativa com prazo até hoje
    (vencida ou vencendo hoje, independente de quando foi criada)."""
    ref = ref or date.today()
    if no_periodo(leitor.criacao(row), de, ate):
        return True
    atual = leitor.status(row) or ""
    if atual in status.encerrado:
        return no_periodo(leitor.conclusao(row), de, ate)
    prazo = leitor.prazo(row)
    return atual not in status.inativo and prazo is not None and prazo <= ref


def situacao(
    row: Linha,
    leitor: Leitor,
    status: Status,
    de: date | None,
    ate: date | None,
    *,
    ref: date | None = None,
) -> dict[str, bool]:
    """Situação no período: em andamento (status de progresso e criada no período), vencida e vence hoje
    (ativa, qualquer data de criação) e concluída (encerrada no período)."""
    ref = ref or date.today()
    atual = leitor.status(row) or ""
    prazo = leitor.prazo(row)
    ativo = atual not in status.inativo
    return _situacao(
        em_andamento=atual in status.em_andamento and no_periodo(leitor.criacao(row), de, ate),
        vencida=ativo and prazo is not None and prazo < ref,
        vence_hoje=ativo and prazo is not None and prazo == ref,
        concluida=atual in status.encerrado and no_periodo(leitor.conclusao(row), de, ate),
    )


# --- por prazo ---------------------------------------------------------------------------------------------


def incluir_na_lista_por_prazo(
    row: Linha, leitor: Leitor, de: date | None, ate: date | None
) -> bool:
    """Entra na lista por prazo: o PRAZO caiu no período."""
    return no_periodo(leitor.prazo(row), de, ate)


def situacao_por_prazo(
    row: Linha,
    leitor: Leitor,
    status: Status,
    de: date | None,
    ate: date | None,
    *,
    ref: date | None = None,
) -> dict[str, bool]:
    """Situação pelo PRAZO no período (as quatro só contam com o prazo dentro do período)."""
    ref = ref or date.today()
    atual = leitor.status(row) or ""
    prazo = leitor.prazo(row)
    ativo = atual not in status.inativo
    no_prazo = no_periodo(prazo, de, ate)
    return _situacao(
        em_andamento=atual in status.em_andamento and no_prazo,
        vencida=ativo and no_prazo and prazo is not None and prazo < ref,
        vence_hoje=ativo and no_prazo and prazo is not None and prazo == ref,
        concluida=atual in status.encerrado and no_prazo,
    )


# --- recortes ----------------------------------------------------------------------------------------------


def encerrados_no_periodo(
    linhas: Iterable[Linha],
    leitor: Leitor,
    status: Status,
    de: date | None,
    ate: date | None,
    *,
    exigir_encerrador: bool = False,
) -> list[Linha]:
    """Encerradas com a CONCLUSÃO no período (com `exigir_encerrador`, só as que têm quem encerrou)."""
    return [
        row
        for row in linhas
        if (leitor.status(row) or "") in status.encerrado
        and not (exigir_encerrador and leitor.funcionario_encerramento(row) is None)
        and no_periodo(leitor.conclusao(row), de, ate)
    ]


def encerrados_com_prazo_no_periodo(
    linhas: Iterable[Linha], leitor: Leitor, status: Status, de: date | None, ate: date | None
) -> list[Linha]:
    """Encerradas com o PRAZO no período."""
    return [
        row
        for row in linhas
        if (leitor.status(row) or "") in status.encerrado and no_periodo(leitor.prazo(row), de, ate)
    ]


def nome_em_conjunto(nome: str, conjunto: frozenset[str] | None) -> bool:
    """Filtro por nome (funcionário, atividade, status) sem diferenciar maiúsculas; sem filtro, tudo passa."""
    if not conjunto:
        return True
    chave = nome.casefold()
    return any(chave == x.casefold() for x in conjunto)


def media_concluidas_por_funcionario(
    encerrados: Iterable[Linha],
    data_ref: LerData,
    funcionario: Callable[[Linha], str],
) -> list[dict[str, Any]]:
    """Média diária de concluídas por funcionário (total ÷ dias distintos com conclusão), maior primeiro."""
    grupos: dict[str, dict[str, Any]] = defaultdict(lambda: {"total": 0, "dias": set()})
    for row in encerrados:
        dia = data_ref(row)
        if not dia:
            continue
        grupo = grupos[funcionario(row)]
        grupo["total"] += 1
        grupo["dias"].add(dia)
    resultado = [
        {"name": nome, "value": round(g["total"] / len(g["dias"]), 2)}
        for nome, g in grupos.items()
        if g["dias"]
    ]
    return sorted(resultado, key=lambda x: x["value"], reverse=True)
