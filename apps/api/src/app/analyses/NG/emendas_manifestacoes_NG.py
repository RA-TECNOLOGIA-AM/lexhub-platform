# Atividades no período — Setor Manifestação (Emendas e Manifestações) — Escritório NG

from __future__ import annotations

from collections import defaultdict
from contextvars import ContextVar  # V2: _dilacao_extra_ctx
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Callable, Optional

from app.utils import parse_date_from_db, resolver_periodo_comparativo

# =============================================================================
# Constantes
# =============================================================================

# Inativos: excluídos de Total, Vencidas e Vencem hoje (alinhado com dashboard analítico)
_STATUS_INATIVO = frozenset({
    "Encerrado Cumprido", "Encerrado Não Cumprido", "Cancelado", "Concluído",
})
# Em andamento: qualquer status ativo (ainda não encerrado/cancelado)
_STATUS_EM_ANDAMENTO = frozenset({"Recebido", "Visualizado", "Iniciado", "Reaberto", "Encaminhado"})
_STATUS_ENCERRADO = frozenset({"Encerrado Cumprido", "Encerrado Não Cumprido"})

_STATUS_FILTRO_TAREFAS: tuple[str, ...] = (
    "Recebido",
    "Visualizado",
    "Iniciado",
    "Reaberto",
    "Encaminhado",
    "Encerrado Cumprido",
    "Encerrado Não Cumprido",
    "Cancelado",
)

_SITUACOES_FILTRO_TAREFAS: tuple[tuple[str, str], ...] = (
    ("em_andamento", "Em andamento"),
    ("vencidas", "Vencidas"),
    ("vencem_hoje", "Vencem hoje"),
    ("concluidas", "Concluídas"),
)

SITUACOES_VALIDAS_EMENDAS_MANIFESTACOES_NG = frozenset(sid for sid, _ in _SITUACOES_FILTRO_TAREFAS)

_STATUS_DEMANDAS_FUNCIONARIO: tuple[tuple[str, str], ...] = (
    ("encerrado_nao_cumprido", "Encerrado Não Cumprido"),
    ("encerrado_cumprido", "Encerrado Cumprido"),
)

_SLUG_POR_STATUS: dict[str, str] = {
    label: slug for slug, label in _STATUS_DEMANDAS_FUNCIONARIO
}

_SEM_ATIVIDADE = "Sem atividade"
_SEM_FUNCIONARIO = "Sem funcionário"

# Classificação do comissionamento (definida pelo usuário em 2026-10-02): a ÚNICA
# atividade do setor MANIFESTAÇÃO que NÃO comissiona é "ANÁLISE DE MANIFESTAÇÃO" — todas
# as outras comissionam. Por isso a regra é por exclusão (não lista fechada): o catálogo do
# setor cresce com frequência (Manifestação Simples/Específica/Provas, Conexão/Aditamento,
# Alegações Finais, Pedido de Providências...) e atividade nova já entra na comissão.
# "ELABORAR MANIFESTAÇÃO" é o nome antigo de "ANÁLISE DE MANIFESTAÇÃO" (renomeada no
# catálogo em 2026-07), mantido na exclusão por segurança. Não confundir com
# "ELABORAR MANIFESTAÇÃO - PEDIDO DE PROVIDÊNCIAS", que é outra atividade e comissiona.
_ATIVIDADES_NAO_COMISSIONAVEIS: frozenset[str] = frozenset({
    "ANÁLISE DE MANIFESTAÇÃO",
    "ELABORAR MANIFESTAÇÃO",
})

# Atividade que conta como "Dilação" para o comissionamento (R$ 0,50)
_ATIVIDADES_DILACAO: frozenset[str] = frozenset({
    "ELABORAR DILAÇÃO",
})


# V2 (19/11/2026): atividades que contam como Dilação além de _ATIVIDADES_DILACAO, ligadas pela casca só no RJ
# (app/dashboards/emendas_manifestacoes.py), que usa este cálculo do NG e também pede dilação como
# "MANIFESTAR DILAÇÃO DE PRAZO". Vazio (o padrão) = o cálculo da v1, sem mudança.
_dilacao_extra_ctx: ContextVar[frozenset[str]] = ContextVar("dilacao_extra_emendas_ng", default=frozenset())


def _is_atividade_dilacao(atividade: str) -> bool:
    return atividade in _ATIVIDADES_DILACAO or atividade in _dilacao_extra_ctx.get()  # V2: + extra (RJ)


def _is_atividade_manifestacao(atividade: str) -> bool:
    """Toda atividade comissionável que não é Dilação conta como Manifestação (R$ 1,00)."""
    return (
        atividade != _SEM_ATIVIDADE
        and atividade not in _ATIVIDADES_NAO_COMISSIONAVEIS
        and not _is_atividade_dilacao(atividade)  # V2: era "not in _ATIVIDADES_DILACAO" (mesmo efeito sem extra)
    )


_COL_FUNCIONARIO_ATRIBUIDO = "FUNCIONARIO_ATRIBUIDO"
_COL_FUNCIONARIO_ENCERRAMENTO = "FUNCIONARIO_ENCERRAMENTO"
_COL_ID_USUARIO_ENCERRAMENTO = "ID_USUARIO_ENCERRAMENTO"


# =============================================================================
# Utilitários
# =============================================================================

def _to_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_date(value: Any) -> Optional[date]:
    if not value:
        return None
    parsed = parse_date_from_db(value)
    if isinstance(parsed, datetime):
        return parsed.date()
    if isinstance(parsed, date):
        return parsed
    return None


def _data_no_periodo(
    d: Optional[date],
    from_date: Optional[date],
    to_date: Optional[date],
) -> bool:
    if d is None:
        return False
    if from_date and to_date:
        return from_date <= d <= to_date
    if from_date:
        return d >= from_date
    if to_date:
        return d <= to_date
    return True


def _nome_em_conjunto_filtro(nome: str, conjunto: frozenset[str] | None) -> bool:
    if not conjunto:
        return True
    chave = nome.casefold()
    return any(chave == x.casefold() for x in conjunto)


# =============================================================================
# Getters de campos dos agendamentos
# =============================================================================

def _get_status(item: dict[str, Any]) -> str | None:
    raw = item.get("STATUS") or item.get("status")
    if raw is None or not str(raw).strip():
        return None
    return str(raw).strip()


def _get_data_criacao(item: dict[str, Any]) -> Optional[date]:
    raw = item.get("DATA_HORA_CRIACAO") or item.get("data_hora_criacao")
    return _to_date(raw)


def _get_data_conclusao(item: dict[str, Any]) -> Optional[date]:
    raw = item.get("DATA_HORA_CONCLUSAO") or item.get("data_hora_conclusao")
    return _to_date(raw)


def _get_prazo(item: dict[str, Any]) -> Optional[date]:
    raw = item.get("PRAZO") or item.get("prazo")
    return _to_date(raw)


def _get_processo_id(item: dict[str, Any]) -> Any | None:
    return item.get("processo_id") or item.get("PROCESSO_ID")


def _get_numero_processo(item: dict[str, Any]) -> str | None:
    raw = item.get("NUMERO_PROCESSO") or item.get("numero_processo")
    if raw is None or not str(raw).strip():
        return None
    return str(raw).strip()


def _get_uf(item: dict[str, Any]) -> str | None:
    raw = item.get("UF") or item.get("uf")
    if raw is None or not str(raw).strip():
        return None
    return str(raw).strip().upper()


def _get_atividade_nome(item: dict[str, Any]) -> str:
    raw = item.get("ATIVIDADE") or item.get("atividade")
    if raw is None or not str(raw).strip():
        return _SEM_ATIVIDADE
    return str(raw).strip()


def _get_funcionario_atribuido(item: dict[str, Any]) -> str:
    raw = (
        item.get(_COL_FUNCIONARIO_ATRIBUIDO)
        or item.get("FUNCIONARIO")
        or item.get("funcionario")
    )
    if raw is None or not str(raw).strip():
        return _SEM_FUNCIONARIO
    return str(raw).strip()


def _get_funcionario_encerramento(item: dict[str, Any]) -> str | None:
    uid = item.get(_COL_ID_USUARIO_ENCERRAMENTO) or item.get("id_usuario_encerramento")
    if uid is None or (isinstance(uid, str) and not str(uid).strip()):
        return None
    raw = item.get(_COL_FUNCIONARIO_ENCERRAMENTO) or item.get("funcionario_encerramento")
    if raw is not None and str(raw).strip():
        return str(raw).strip()
    return None


def _get_funcionario_nome(item: dict[str, Any]) -> str:
    status = _get_status(item) or ""
    if status in _STATUS_ENCERRADO:
        encerrador = _get_funcionario_encerramento(item)
        if encerrador:
            return encerrador
    return _get_funcionario_atribuido(item)


# =============================================================================
# Filtros de período
# =============================================================================

def _filtrar_criados_no_periodo(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    return [
        row for row in agendamentos
        if _data_no_periodo(_get_data_criacao(row), from_date, to_date)
    ]


def _filtrar_encerrados_no_periodo(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    exigir_encerrador: bool = False,
) -> list[dict[str, Any]]:
    resultado = []
    for row in agendamentos:
        status = _get_status(row) or ""
        if status not in _STATUS_ENCERRADO:
            continue
        if exigir_encerrador and _get_funcionario_encerramento(row) is None:
            continue
        conclusao = _get_data_conclusao(row)
        if _data_no_periodo(conclusao, from_date, to_date):
            resultado.append(row)
    return resultado


def _incluir_na_lista_tarefas(
    row: dict[str, Any],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> bool:
    criacao = _get_data_criacao(row)
    conclusao = _get_data_conclusao(row)
    status = _get_status(row) or ""
    prazo = _get_prazo(row)
    ref = ref_date or date.today()
    # Criada no período
    if _data_no_periodo(criacao, from_date, to_date):
        return True
    # Encerrada no período
    if status in _STATUS_ENCERRADO:
        return _data_no_periodo(conclusao, from_date, to_date)
    # Ativa com prazo vencido ou vencendo hoje — aparece independente de quando foi criada
    if status not in _STATUS_INATIVO and prazo is not None and prazo <= ref:
        return True
    return False


def _classificar_situacao_tarefa(
    row: dict[str, Any],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, bool]:
    ref = ref_date or date.today()
    criacao = _get_data_criacao(row)
    conclusao = _get_data_conclusao(row)
    status = _get_status(row) or ""
    prazo = _get_prazo(row)
    criada_periodo = _data_no_periodo(criacao, from_date, to_date)
    ativo = status not in _STATUS_INATIVO
    # "em andamento" = status de progresso E criada no período selecionado
    em_andamento = status in _STATUS_EM_ANDAMENTO and criada_periodo
    # "vencida" e "vence hoje" = ativa com prazo correspondente, independente de quando foi criada
    vencida = ativo and prazo is not None and prazo < ref
    vence_hoje = ativo and prazo is not None and prazo == ref
    concluida = (
        status in _STATUS_ENCERRADO
        and _data_no_periodo(conclusao, from_date, to_date)
    )
    return {
        "em_andamento": em_andamento,
        "vencida": vencida,
        "vence_hoje": vence_hoje,
        "concluida": concluida,
    }


# =============================================================================
# KPIs
# =============================================================================

def get_kpis_atividades_emendas_manifestacoes_NG(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, int]:
    """
    KPIs de agendamentos do setor Emendas e Manifestações no período.

    - **Total**: ativas criadas no período (exclui Cancelado, Concluído, Encerrado*)
    - **Em andamento**: qualquer status ativo (Recebido, Visualizado, Iniciado, Reaberto ou
      Encaminhado) criadas no período — coincide com Total, pois Total já exclui as encerradas/
      canceladas
    - **Vencidas**: ativas com prazo anterior a hoje (independente de quando foram criadas)
    - **Vencem hoje**: ativas com prazo = hoje (independente de quando foram criadas)
    - **Concluídas**: encerradas no período (contagem separada do Total)
    """
    ref = ref_date or date.today()
    total = em_andamento = vencidas = vencem_hoje = concluidas = 0

    for row in agendamentos:
        criacao = _get_data_criacao(row)
        conclusao = _get_data_conclusao(row)
        status = _get_status(row) or ""
        prazo = _get_prazo(row)
        ativo = status not in _STATUS_INATIVO

        if _data_no_periodo(criacao, from_date, to_date) and ativo:
            total += 1
            if status in _STATUS_EM_ANDAMENTO:
                em_andamento += 1

        # Vencidas e vencem hoje: consideram TODAS as ativas, não só as criadas no período
        if ativo and prazo is not None:
            if prazo < ref:
                vencidas += 1
            elif prazo == ref:
                vencem_hoje += 1

        if status in _STATUS_ENCERRADO:
            if _data_no_periodo(conclusao, from_date, to_date):
                concluidas += 1

    return {
        "total_atividades_emendas_manifestacoes_NG": total,
        "atividades_emendas_manifestacoes_em_andamento_NG": em_andamento,
        "atividades_emendas_manifestacoes_vencidas_NG": vencidas,
        "atividades_emendas_manifestacoes_vencem_hoje_NG": vencem_hoje,
        "atividades_emendas_manifestacoes_concluidas_NG": concluidas,
    }


# =============================================================================
# Histórico de concluídas (mensal e diário)
# =============================================================================

_MONTH_NAMES = (
    "jan", "fev", "mar", "abr", "mai", "jun",
    "jul", "ago", "set", "out", "nov", "dez",
)


def group_emendas_manifestacoes_concluidas_por_mes_NG(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Agrupa atividades encerradas por mês de DATA_HORA_CONCLUSAO."""
    encerrados = _filtrar_encerrados_no_periodo(agendamentos, from_date, to_date)
    grouped: dict[str, dict[str, Any]] = {}

    for row in encerrados:
        conclusao = _get_data_conclusao(row)
        if not conclusao:
            continue

        month_key = f"{conclusao.year}-{conclusao.month:02d}"
        if month_key not in grouped:
            month_name = f"{_MONTH_NAMES[conclusao.month - 1]} {conclusao.year}"
            grouped[month_key] = {"name": month_name, "value": 0, "sort_key": month_key}
        grouped[month_key]["value"] += 1

    return [
        {"name": item["name"], "value": item["value"]}
        for item in sorted(grouped.values(), key=lambda x: x["sort_key"])
    ]


def group_emendas_manifestacoes_concluidas_por_dia_NG(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Agrupa atividades encerradas por dia de DATA_HORA_CONCLUSAO."""
    encerrados = _filtrar_encerrados_no_periodo(agendamentos, from_date, to_date)
    grouped: dict[str, int] = defaultdict(int)

    for row in encerrados:
        conclusao = _get_data_conclusao(row)
        if not conclusao:
            continue
        grouped[conclusao.strftime("%Y-%m-%d")] += 1

    return [
        {"name": dia, "value": count}
        for dia, count in sorted(grouped.items(), key=lambda x: x[0])
    ]


def get_emendas_manifestacoes_concluidas_por_dia_por_funcionario_NG(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> dict[str, Any]:
    """Concluídas por dia e por funcionário (encerrador ou atribuído)."""
    encerrados = _filtrar_encerrados_no_periodo(agendamentos, from_date, to_date)
    grouped: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for row in encerrados:
        conclusao = _get_data_conclusao(row)
        if not conclusao:
            continue
        dia_key = conclusao.strftime("%Y-%m-%d")
        grouped[dia_key][_get_funcionario_nome(row)] += 1

    dias_ordenados = sorted(grouped.keys())
    funcionarios = sorted({f for dia_data in grouped.values() for f in dia_data.keys()})
    por_funcionario = {
        func: [
            {"name": dia, "value": grouped[dia].get(func, 0)}
            for dia in dias_ordenados
        ]
        for func in funcionarios
    }
    return {"funcionarios": funcionarios, "por_funcionario": por_funcionario}


def _media_concluidas_por_funcionario(
    encerrados: list[dict[str, Any]],
    get_data_ref: Callable[[dict[str, Any]], Optional[date]],
) -> list[dict[str, Any]]:
    """Média diária de concluídas por funcionário (total / dias distintos)."""
    grouped: dict[str, dict[str, Any]] = defaultdict(lambda: {"total": 0, "dias": set()})

    for row in encerrados:
        data_ref = get_data_ref(row)
        if not data_ref:
            continue
        funcionario = _get_funcionario_nome(row)
        grouped[funcionario]["total"] += 1
        grouped[funcionario]["dias"].add(data_ref)

    result: list[dict[str, Any]] = []
    for funcionario, stats in grouped.items():
        dias = len(stats["dias"])
        if dias > 0:
            result.append({
                "name": funcionario,
                "value": round(stats["total"] / dias, 2),
            })
    return sorted(result, key=lambda x: x["value"], reverse=True)


def get_media_emendas_manifestacoes_concluidas_por_funcionario_NG(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Média diária de atividades encerradas por funcionário (DATA_HORA_CONCLUSAO)."""
    encerrados = _filtrar_encerrados_no_periodo(agendamentos, from_date, to_date)
    return _media_concluidas_por_funcionario(encerrados, _get_data_conclusao)


# =============================================================================
# Gráfico: processos distintos por atividade
# =============================================================================

def group_emendas_manifestacoes_processos_por_atividade_NG(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Agendamentos encerrados (Cumprido ou Não Cumprido) por atividade, com
    DATA_HORA_CONCLUSAO no período — mesma base (e mesma contagem por linha de
    agendamento, sem dedupe por processo) do KPI "Concluídas" e do gráfico
    "Demandas por Funcionário" desta visão, para os três baterem entre si. Demais
    status (Recebido, Visualizado, Iniciado, Reaberto, Encaminhado, Cancelado)
    ficam de fora deste resumo; aparecem no detalhamento da lista de tarefas abaixo.
    """
    base = _filtrar_encerrados_no_periodo(agendamentos, from_date, to_date)

    grouped: dict[str, int] = defaultdict(int)
    for row in base:
        nome = _get_atividade_nome(row)
        grouped[nome] += 1

    total = float(sum(grouped.values()))
    itens: list[dict[str, Any]] = []
    for nome, qtd in grouped.items():
        itens.append({
            "name": nome,
            "value": float(qtd),
            "percent": round(100.0 * float(qtd) / total, 1) if total > 0 else 0.0,
        })
    return sorted(itens, key=lambda x: float(x["value"]), reverse=True)


# =============================================================================
# Gráfico: demandas encerradas por funcionário
# =============================================================================

def group_emendas_manifestacoes_demandas_por_funcionario_NG(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Demandas encerradas por funcionário (Cumprido / Não Cumprido),
    com DATA_HORA_CONCLUSAO no período.
    """
    base = _filtrar_encerrados_no_periodo(
        agendamentos, from_date, to_date, exigir_encerrador=True
    )

    grouped: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in base:
        funcionario = _get_funcionario_encerramento(row)
        if not funcionario:
            continue
        status = _get_status(row) or ""
        slug = _SLUG_POR_STATUS.get(status)
        if slug is None:
            continue
        grouped[funcionario][slug] += 1

    itens: list[dict[str, Any]] = []
    for nome, contagens in grouped.items():
        item: dict[str, Any] = {"name": nome}
        total = 0
        for slug, _ in _STATUS_DEMANDAS_FUNCIONARIO:
            valor = int(contagens.get(slug, 0))
            item[slug] = valor
            total += valor
        item["total"] = total
        if total > 0:
            itens.append(item)

    return sorted(itens, key=lambda x: int(x["total"]), reverse=True)


# =============================================================================
# Gráfico (por prazo): processos distintos por atividade
# =============================================================================

def group_emendas_manifestacoes_processos_por_atividade_por_prazo_NG(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Agendamentos encerrados (Cumprido ou Não Cumprido) por atividade, com PRAZO
    no período — mesma base (linha de agendamento, sem dedupe por processo) do
    KPI "Concluídas" e do gráfico "Demandas por Funcionário" desta visão, para os
    três baterem entre si. Demais status (Recebido, Visualizado, Iniciado,
    Reaberto, Encaminhado, Cancelado) ficam de fora deste resumo; aparecem no
    detalhamento da lista de tarefas abaixo.
    """
    base = [
        row for row in agendamentos
        if _data_no_periodo(_get_prazo(row), from_date, to_date)
        and (_get_status(row) or "") in _STATUS_ENCERRADO
    ]

    grouped: dict[str, int] = defaultdict(int)
    for row in base:
        nome = _get_atividade_nome(row)
        grouped[nome] += 1

    total = float(sum(grouped.values()))
    itens: list[dict[str, Any]] = []
    for nome, qtd in grouped.items():
        itens.append({
            "name": nome,
            "value": float(qtd),
            "percent": round(100.0 * float(qtd) / total, 1) if total > 0 else 0.0,
        })
    return sorted(itens, key=lambda x: float(x["value"]), reverse=True)


# =============================================================================
# Gráfico (por prazo): demandas encerradas por funcionário
# =============================================================================

def group_emendas_manifestacoes_demandas_por_funcionario_por_prazo_NG(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Demandas encerradas por funcionário (Cumprido / Não Cumprido),
    com PRAZO no período.
    """
    base = [
        row for row in agendamentos
        if (_get_status(row) or "") in _STATUS_ENCERRADO
        and _data_no_periodo(_get_prazo(row), from_date, to_date)
        and _get_funcionario_encerramento(row) is not None
    ]

    grouped: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in base:
        funcionario = _get_funcionario_encerramento(row)
        if not funcionario:
            continue
        status = _get_status(row) or ""
        slug = _SLUG_POR_STATUS.get(status)
        if slug is None:
            continue
        grouped[funcionario][slug] += 1

    itens: list[dict[str, Any]] = []
    for nome, contagens in grouped.items():
        item: dict[str, Any] = {"name": nome}
        total = 0
        for slug, _ in _STATUS_DEMANDAS_FUNCIONARIO:
            valor = int(contagens.get(slug, 0))
            item[slug] = valor
            total += valor
        item["total"] = total
        if total > 0:
            itens.append(item)

    return sorted(itens, key=lambda x: int(x["total"]), reverse=True)


# =============================================================================
# Lista de tarefas
# =============================================================================

def list_emendas_manifestacoes_atividades_periodo_NG(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Lista de agendamentos do setor para a tabela de tarefas."""
    ref = ref_date or date.today()
    itens: list[dict[str, Any]] = []

    for row in agendamentos:
        if not _incluir_na_lista_tarefas(row, from_date, to_date, ref_date=ref):
            continue
        ag_id = _to_int(row.get("id") or row.get("ID"))
        if ag_id is None:
            continue
        status = _get_status(row) or "—"
        prazo = _get_prazo(row)
        criacao = _get_data_criacao(row)
        situacao = _classificar_situacao_tarefa(row, from_date, to_date, ref_date=ref)
        funcionario_atrib = _get_funcionario_atribuido(row)
        funcionario_enc = _get_funcionario_encerramento(row)
        encerrado_pelo_responsavel: bool | None = None
        if status in _STATUS_ENCERRADO and funcionario_enc is not None:
            encerrado_pelo_responsavel = (
                funcionario_enc.strip().lower() == funcionario_atrib.strip().lower()
            )
        setor = str(row.get("SETOR") or row.get("setor") or "MANIFESTAÇÃO").strip().upper()
        atividade = _get_atividade_nome(row)
        pessoa_setor = f"{setor} - {atividade}" if atividade and atividade != _SEM_ATIVIDADE else setor
        descricao_raw = row.get("DESCRICAO") or row.get("descricao")
        descricao = str(descricao_raw).strip().upper() if descricao_raw else "—"
        operacao = str(row.get("OPERACAO") or row.get("operacao") or "").strip()

        itens.append({
            "id": ag_id,
            "status": status,
            "descricao": descricao,
            "pessoa_setor": pessoa_setor,
            "funcionario": _get_funcionario_nome(row),
            "funcionario_atribuido": funcionario_atrib,
            "funcionario_encerramento": funcionario_enc,
            "atividade": atividade,
            "prazo": prazo.isoformat() if prazo else None,
            "criado_em": criacao.isoformat() if criacao else None,
            "operacao": operacao,
            "encerrado_pelo_responsavel": encerrado_pelo_responsavel,
            "numero_processo": _get_numero_processo(row),
            **situacao,
        })

    def _sort_key(item: dict[str, Any]) -> tuple[int, str, int]:
        prazo_raw = item.get("prazo")
        prazo_missing = 0 if prazo_raw else 1
        return (prazo_missing, str(prazo_raw or ""), int(item.get("id") or 0))

    return sorted(itens, key=_sort_key)


# =============================================================================
# Opções de filtros
# =============================================================================

def get_opcoes_filtros_emendas_manifestacoes_NG(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, Any]:
    """Opções de filtros da lista de tarefas (funcionários, atividades, status, situações)."""
    rows = list_emendas_manifestacoes_atividades_periodo_NG(
        agendamentos, from_date=from_date, to_date=to_date, ref_date=ref_date
    )
    funcionarios: set[str] = set()
    atividades: set[str] = set()
    status_vistos: set[str] = set()

    for row in rows:
        funcionarios.add(str(row.get("funcionario") or _SEM_FUNCIONARIO))
        atividade = str(row.get("atividade") or "").strip()
        if atividade and atividade != _SEM_ATIVIDADE:
            atividades.add(atividade)
        status = str(row.get("status") or "").strip()
        if status and status != "—":
            status_vistos.add(status)

    status_ordenados: list[str] = []
    for label in _STATUS_FILTRO_TAREFAS:
        if label in status_vistos:
            status_ordenados.append(label)
    for label in sorted(status_vistos - set(status_ordenados), key=lambda x: x.casefold()):
        status_ordenados.append(label)

    return {
        "funcionarios": sorted(funcionarios, key=lambda x: x.casefold()),
        "atividades": sorted(atividades, key=lambda x: x.casefold()),
        "status": status_ordenados,
        "situacoes": [
            {"id": sid, "label": label} for sid, label in _SITUACOES_FILTRO_TAREFAS
        ],
    }


# =============================================================================
# Filtros cumulativos
# =============================================================================

@dataclass(frozen=True)
class EmendasManifestacoesAtividadesFiltrosNG:
    """Filtros cumulativos (AND) sobre agendamentos do setor Emendas e Manifestações."""

    funcionarios: frozenset[str] | None = None
    atividades: frozenset[str] | None = None
    status: frozenset[str] | None = None
    situacoes: frozenset[str] | None = None
    ufs: frozenset[str] | None = None

    def ativo(self) -> bool:
        return bool(
            self.funcionarios or self.atividades or self.status or self.situacoes or self.ufs
        )


def _agendamento_match_filtros(
    row: dict[str, Any],
    filtros: EmendasManifestacoesAtividadesFiltrosNG,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> bool:
    if filtros.funcionarios is not None:
        funcionario = _get_funcionario_nome(row)
        if not _nome_em_conjunto_filtro(funcionario, filtros.funcionarios):
            return False
    if filtros.atividades is not None:
        atividade = _get_atividade_nome(row)
        if not _nome_em_conjunto_filtro(atividade, filtros.atividades):
            return False
    if filtros.status is not None:
        status = (_get_status(row) or "—").strip()
        if not _nome_em_conjunto_filtro(status, filtros.status):
            return False
    if filtros.situacoes is not None:
        flags = _classificar_situacao_tarefa(row, from_date, to_date, ref_date=ref_date)
        if not any(flags.get(sid) for sid in filtros.situacoes):
            return False
    if filtros.ufs is not None:
        uf = _get_uf(row)
        if uf is None or not _nome_em_conjunto_filtro(uf, filtros.ufs):
            return False
    return True


def filtrar_agendamentos_emendas_manifestacoes_NG(
    agendamentos: list[dict[str, Any]],
    filtros: EmendasManifestacoesAtividadesFiltrosNG | None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Restringe agendamentos aos filtros cumulativos."""
    if filtros is None or not filtros.ativo():
        return agendamentos
    return [
        row for row in agendamentos
        if _agendamento_match_filtros(row, filtros, from_date, to_date, ref_date=ref_date)
    ]


# =============================================================================
# Análise por Prazo — helpers internos
# =============================================================================

def _incluir_na_lista_por_prazo(
    row: dict[str, Any],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> bool:
    prazo = _get_prazo(row)
    return _data_no_periodo(prazo, from_date, to_date)


def _classificar_situacao_por_prazo(
    row: dict[str, Any],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, bool]:
    ref = ref_date or date.today()
    prazo = _get_prazo(row)
    status = _get_status(row) or ""
    ativo = status not in _STATUS_INATIVO
    prazo_no_periodo = _data_no_periodo(prazo, from_date, to_date)
    em_andamento = status in _STATUS_EM_ANDAMENTO and prazo_no_periodo
    # Vencida e vence_hoje: filtradas pelo período (consistente com os KPIs)
    vencida = ativo and prazo_no_periodo and prazo is not None and prazo < ref
    vence_hoje = ativo and prazo_no_periodo and prazo is not None and prazo == ref
    concluida = status in _STATUS_ENCERRADO and prazo_no_periodo
    return {
        "em_andamento": em_andamento,
        "vencida": vencida,
        "vence_hoje": vence_hoje,
        "concluida": concluida,
    }


# =============================================================================
# KPIs por Prazo
# =============================================================================

def get_kpis_emendas_manifestacoes_por_prazo_NG(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, int]:
    """
    KPIs do setor Emendas e Manifestações usando PRAZO como eixo temporal.

    - **Total**: ativas com prazo no período (exclui Cancelado, Concluído, Encerrado*)
    - **Em andamento**: qualquer status ativo (Recebido, Visualizado, Iniciado, Reaberto ou
      Encaminhado) com prazo no período — coincide com Total, pois Total já exclui as
      encerradas/canceladas
    - **Vencidas**: ativas com prazo no período anterior a hoje
    - **Vencem hoje**: ativas com prazo = hoje no período
    - **Concluídas**: encerradas com prazo no período (contagem separada do Total)
    """
    ref = ref_date or date.today()
    total = em_andamento = vencidas = vencem_hoje = concluidas = 0

    for row in agendamentos:
        prazo = _get_prazo(row)
        status = _get_status(row) or ""
        ativo = status not in _STATUS_INATIVO
        prazo_no_periodo = _data_no_periodo(prazo, from_date, to_date)

        if not prazo_no_periodo:
            continue

        if ativo:
            total += 1
            if status in _STATUS_EM_ANDAMENTO:
                em_andamento += 1
            if prazo is not None and prazo < ref:
                vencidas += 1
            if prazo is not None and prazo == ref:
                vencem_hoje += 1
        elif status in _STATUS_ENCERRADO:
            concluidas += 1

    return {
        "total_por_prazo_emendas_manifestacoes_NG": total,
        "por_prazo_em_andamento_emendas_manifestacoes_NG": em_andamento,
        "por_prazo_vencidas_emendas_manifestacoes_NG": vencidas,
        "por_prazo_vencem_hoje_emendas_manifestacoes_NG": vencem_hoje,
        "por_prazo_concluidas_emendas_manifestacoes_NG": concluidas,
    }


# =============================================================================
# Histórico de concluídas por Prazo (mensal e diário)
# =============================================================================

def _filtrar_encerrados_com_prazo_no_periodo(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Encerradas com PRAZO dentro do intervalo informado."""
    resultado: list[dict[str, Any]] = []
    for row in agendamentos:
        status = _get_status(row) or ""
        if status not in _STATUS_ENCERRADO:
            continue
        prazo = _get_prazo(row)
        if prazo is None or not _data_no_periodo(prazo, from_date, to_date):
            continue
        resultado.append(row)
    return resultado


def group_emendas_manifestacoes_concluidas_por_prazo_por_mes_NG(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Agrupa atividades encerradas por mês do PRAZO."""
    encerrados = _filtrar_encerrados_com_prazo_no_periodo(agendamentos, from_date, to_date)
    grouped: dict[str, dict[str, Any]] = {}

    for row in encerrados:
        prazo = _get_prazo(row)
        if not prazo:
            continue

        month_key = f"{prazo.year}-{prazo.month:02d}"
        if month_key not in grouped:
            month_name = f"{_MONTH_NAMES[prazo.month - 1]} {prazo.year}"
            grouped[month_key] = {"name": month_name, "value": 0, "sort_key": month_key}
        grouped[month_key]["value"] += 1

    return [
        {"name": item["name"], "value": item["value"]}
        for item in sorted(grouped.values(), key=lambda x: x["sort_key"])
    ]


def group_emendas_manifestacoes_concluidas_por_prazo_por_dia_NG(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Agrupa atividades encerradas por dia do PRAZO."""
    encerrados = _filtrar_encerrados_com_prazo_no_periodo(agendamentos, from_date, to_date)
    grouped: dict[str, int] = defaultdict(int)

    for row in encerrados:
        prazo = _get_prazo(row)
        if not prazo:
            continue
        grouped[prazo.strftime("%Y-%m-%d")] += 1

    return [
        {"name": dia, "value": count}
        for dia, count in sorted(grouped.items(), key=lambda x: x[0])
    ]


def get_emendas_manifestacoes_concluidas_por_prazo_por_dia_por_funcionario_NG(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> dict[str, Any]:
    """Concluídas (por prazo) por dia do PRAZO e por funcionário."""
    encerrados = _filtrar_encerrados_com_prazo_no_periodo(agendamentos, from_date, to_date)
    grouped: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for row in encerrados:
        prazo = _get_prazo(row)
        if not prazo:
            continue
        dia_key = prazo.strftime("%Y-%m-%d")
        grouped[dia_key][_get_funcionario_nome(row)] += 1

    dias_ordenados = sorted(grouped.keys())
    funcionarios = sorted({f for dia_data in grouped.values() for f in dia_data.keys()})
    por_funcionario = {
        func: [
            {"name": dia, "value": grouped[dia].get(func, 0)}
            for dia in dias_ordenados
        ]
        for func in funcionarios
    }
    return {"funcionarios": funcionarios, "por_funcionario": por_funcionario}


def get_media_emendas_manifestacoes_concluidas_por_prazo_por_funcionario_NG(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Média diária de atividades encerradas por funcionário (PRAZO)."""
    encerrados = _filtrar_encerrados_com_prazo_no_periodo(agendamentos, from_date, to_date)
    return _media_concluidas_por_funcionario(encerrados, _get_prazo)


# =============================================================================
# Lista de tarefas por Prazo
# =============================================================================

def list_emendas_manifestacoes_por_prazo_NG(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Lista de agendamentos do setor filtrados pelo PRAZO para a tabela de tarefas."""
    ref = ref_date or date.today()
    itens: list[dict[str, Any]] = []

    for row in agendamentos:
        if not _incluir_na_lista_por_prazo(row, from_date, to_date, ref_date=ref):
            continue
        ag_id = _to_int(row.get("id") or row.get("ID"))
        if ag_id is None:
            continue
        status = _get_status(row) or "—"
        prazo = _get_prazo(row)
        criacao = _get_data_criacao(row)
        situacao = _classificar_situacao_por_prazo(row, from_date, to_date, ref_date=ref)
        funcionario_atrib = _get_funcionario_atribuido(row)
        funcionario_enc = _get_funcionario_encerramento(row)
        encerrado_pelo_responsavel: bool | None = None
        if status in _STATUS_ENCERRADO and funcionario_enc is not None:
            encerrado_pelo_responsavel = (
                funcionario_enc.strip().lower() == funcionario_atrib.strip().lower()
            )
        setor = str(row.get("SETOR") or row.get("setor") or "MANIFESTAÇÃO").strip().upper()
        atividade = _get_atividade_nome(row)
        pessoa_setor = f"{setor} - {atividade}" if atividade and atividade != _SEM_ATIVIDADE else setor
        descricao_raw = row.get("DESCRICAO") or row.get("descricao")
        descricao = str(descricao_raw).strip().upper() if descricao_raw else "—"
        operacao = str(row.get("OPERACAO") or row.get("operacao") or "").strip()

        itens.append({
            "id": ag_id,
            "status": status,
            "descricao": descricao,
            "pessoa_setor": pessoa_setor,
            "funcionario": _get_funcionario_nome(row),
            "funcionario_atribuido": funcionario_atrib,
            "funcionario_encerramento": funcionario_enc,
            "atividade": atividade,
            "prazo": prazo.isoformat() if prazo else None,
            "criado_em": criacao.isoformat() if criacao else None,
            "operacao": operacao,
            "encerrado_pelo_responsavel": encerrado_pelo_responsavel,
            "numero_processo": _get_numero_processo(row),
            **situacao,
        })

    def _sort_key(item: dict[str, Any]) -> tuple[int, str, int]:
        prazo_raw = item.get("prazo")
        prazo_missing = 0 if prazo_raw else 1
        return (prazo_missing, str(prazo_raw or ""), int(item.get("id") or 0))

    return sorted(itens, key=_sort_key)


# =============================================================================
# Opções de filtros por Prazo
# =============================================================================

def get_opcoes_filtros_emendas_manifestacoes_por_prazo_NG(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, Any]:
    """Opções de filtros da lista por prazo (funcionários, atividades, status, situações)."""
    rows = list_emendas_manifestacoes_por_prazo_NG(
        agendamentos, from_date=from_date, to_date=to_date, ref_date=ref_date
    )
    funcionarios: set[str] = set()
    atividades: set[str] = set()
    status_vistos: set[str] = set()

    for row in rows:
        funcionarios.add(str(row.get("funcionario") or _SEM_FUNCIONARIO))
        atividade = str(row.get("atividade") or "").strip()
        if atividade and atividade != _SEM_ATIVIDADE:
            atividades.add(atividade)
        status = str(row.get("status") or "").strip()
        if status and status != "—":
            status_vistos.add(status)

    status_ordenados: list[str] = []
    for label in _STATUS_FILTRO_TAREFAS:
        if label in status_vistos:
            status_ordenados.append(label)
    for label in sorted(status_vistos - set(status_ordenados), key=lambda x: x.casefold()):
        status_ordenados.append(label)

    return {
        "funcionarios": sorted(funcionarios, key=lambda x: x.casefold()),
        "atividades": sorted(atividades, key=lambda x: x.casefold()),
        "status": status_ordenados,
        "situacoes": [
            {"id": sid, "label": label} for sid, label in _SITUACOES_FILTRO_TAREFAS
        ],
    }


# =============================================================================
# Filtros cumulativos por Prazo
# =============================================================================

def _agendamento_match_filtros_por_prazo(
    row: dict[str, Any],
    filtros: EmendasManifestacoesAtividadesFiltrosNG,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> bool:
    if filtros.funcionarios is not None:
        funcionario = _get_funcionario_nome(row)
        if not _nome_em_conjunto_filtro(funcionario, filtros.funcionarios):
            return False
    if filtros.atividades is not None:
        atividade = _get_atividade_nome(row)
        if not _nome_em_conjunto_filtro(atividade, filtros.atividades):
            return False
    if filtros.status is not None:
        status = (_get_status(row) or "—").strip()
        if not _nome_em_conjunto_filtro(status, filtros.status):
            return False
    if filtros.situacoes is not None:
        flags = _classificar_situacao_por_prazo(row, from_date, to_date, ref_date=ref_date)
        if not any(flags.get(sid) for sid in filtros.situacoes):
            return False
    if filtros.ufs is not None:
        uf = _get_uf(row)
        if uf is None or not _nome_em_conjunto_filtro(uf, filtros.ufs):
            return False
    return True


def filtrar_agendamentos_emendas_manifestacoes_por_prazo_NG(
    agendamentos: list[dict[str, Any]],
    filtros: EmendasManifestacoesAtividadesFiltrosNG | None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Restringe agendamentos por prazo aos filtros cumulativos."""
    if filtros is None or not filtros.ativo():
        return agendamentos
    return [
        row for row in agendamentos
        if _agendamento_match_filtros_por_prazo(row, filtros, from_date, to_date, ref_date=ref_date)
    ]


# =============================================================================
# Comissionamento
# =============================================================================
#
# Regras (definidas pelo usuário em 2026-07 para o escritório NG — diferente da
# LA, que usa faixas 85%/97%): NG não tem faixa de comissionamento. Toda
# Manifestação produzida vale R$ 1,00 e toda Dilação vale R$ 0,50, sem gatilho
# mínimo de agenda cumprida — o valor é fixo e sempre aplicado.
#
# "Agenda do mês" (agenda_percentual) continua calculada e exposta como métrica
# informativa de aderência ao prazo (PRAZO no período; Cancelado/Concluído não
# entram), mas não influencia mais o valor da comissão.
#
# As peças (Manifestação/Dilação) só contam quando o resultado foi "Encerrado
# Cumprido" (Não Cumprido conta para a agenda, mas não é peça remunerada),
# usando o PRAZO no período como eixo temporal (mesma base da agenda) — não a
# DATA_HORA_CONCLUSAO (mesma lógica validada para a LA, ver
# analyses/LA/emendas_manifestacoes_LA.py).

_VALOR_MANIFESTACAO_NG = Decimal("1.00")
_VALOR_DILACAO_NG = Decimal("0.50")


def _agenda_cumprida_funcionario_NG(
    agendamentos_funcionario: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> tuple[int, int, float]:
    """Retorna (finalizados, total_agenda, percentual) com base no PRAZO no período."""
    finalizados = 0
    pendentes = 0
    for row in agendamentos_funcionario:
        prazo = _get_prazo(row)
        if not _data_no_periodo(prazo, from_date, to_date):
            continue
        status = _get_status(row) or ""
        if status in _STATUS_ENCERRADO:
            finalizados += 1
        elif status not in _STATUS_INATIVO:
            pendentes += 1
        # Cancelado/Concluído: não fazem parte da agenda de comissionamento

    total = finalizados + pendentes
    percentual = round(100.0 * finalizados / total, 1) if total > 0 else 0.0
    return finalizados, total, percentual


def get_emendas_manifestacoes_comissionamento_por_funcionario_NG(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Comissionamento por funcionário do setor Emendas e Manifestações (NG).

    Sem faixas: toda peça Encerrado Cumprido com PRAZO no período vale
    R$ 1,00 (Manifestação) ou R$ 0,50 (Dilação), independente da % de agenda
    cumprida. `agenda_percentual` fica só como métrica informativa.
    """
    por_funcionario: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in agendamentos:
        nome = _get_funcionario_nome(row)
        if nome == _SEM_FUNCIONARIO:
            continue
        por_funcionario[nome].append(row)

    linhas: list[dict[str, Any]] = []
    for nome in sorted(por_funcionario.keys()):
        rows = por_funcionario[nome]

        finalizados, total_agenda, percentual = _agenda_cumprida_funcionario_NG(
            rows, from_date, to_date
        )

        produzidas = [
            row for row in rows
            if (_get_status(row) or "") == "Encerrado Cumprido"
            and _data_no_periodo(_get_prazo(row), from_date, to_date)
        ]
        qtd_manifestacao = sum(
            1 for row in produzidas
            if _is_atividade_manifestacao(_get_atividade_nome(row))
        )
        qtd_dilacao = sum(
            1 for row in produzidas
            if _is_atividade_dilacao(_get_atividade_nome(row))
        )

        if qtd_manifestacao == 0 and qtd_dilacao == 0 and total_agenda == 0:
            continue

        sub_manifestacao = (Decimal(qtd_manifestacao) * _VALOR_MANIFESTACAO_NG).quantize(Decimal("0.01"))
        sub_dilacao = (Decimal(qtd_dilacao) * _VALOR_DILACAO_NG).quantize(Decimal("0.01"))
        total_comissao = (sub_manifestacao + sub_dilacao).quantize(Decimal("0.01"))

        por_uf: dict[str, dict[str, int]] = defaultdict(lambda: {"manifestacao": 0, "dilacao": 0})
        for row in produzidas:
            uf = _get_uf(row) or "Sem UF"
            atividade = _get_atividade_nome(row)
            if _is_atividade_manifestacao(atividade):
                por_uf[uf]["manifestacao"] += 1
            elif _is_atividade_dilacao(atividade):
                por_uf[uf]["dilacao"] += 1
        resolvidos_por_uf = [
            {
                "uf": uf,
                "qtd_manifestacao": contagens["manifestacao"],
                "qtd_dilacao": contagens["dilacao"],
                "qtd_total": contagens["manifestacao"] + contagens["dilacao"],
            }
            for uf, contagens in sorted(por_uf.items())
        ]

        linhas.append({
            "funcionario": nome,
            "agenda_finalizada": finalizados,
            "agenda_total": total_agenda,
            "agenda_percentual": percentual,
            "elegivel": True,
            "faixa": None,
            "qtd_manifestacao": qtd_manifestacao,
            "valor_manifestacao": float(_VALOR_MANIFESTACAO_NG),
            "qtd_x_valor_manifestacao": float(sub_manifestacao),
            "qtd_dilacao": qtd_dilacao,
            "valor_dilacao": float(_VALOR_DILACAO_NG),
            "qtd_x_valor_dilacao": float(sub_dilacao),
            "valor_comissao": float(total_comissao),
            "resolvidos_por_uf": resolvidos_por_uf,
        })

    linhas.sort(key=lambda x: (-x["valor_comissao"], x["funcionario"]))
    return linhas


# =============================================================================
# Comparativos (mesmo padrão de analyses/NG/comercial_geral.py)
# =============================================================================

def _resolver_periodos_comparativo_emendas_manifestacoes_NG(
    from_date: Optional[date],
    to_date: Optional[date],
) -> tuple[date, date, date, date]:
    """Retorna (início_atual, fim_atual, início_anterior, fim_anterior).

    O período anterior é o mesmo período um mês civil antes (ex.: 01/08-20/08 ->
    01/07-20/07).
    """
    return resolver_periodo_comparativo(from_date, to_date)


def _qtd_pecas_produzidas_emendas_manifestacoes_NG(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
    is_atividade: Callable[[str], bool],
) -> int:
    """Peças (Encerrado Cumprido, PRAZO no período) de um conjunto de atividades — mesma base do comissionamento."""
    return sum(
        1 for row in agendamentos
        if (_get_status(row) or "") == "Encerrado Cumprido"
        and _data_no_periodo(_get_prazo(row), from_date, to_date)
        and is_atividade(_get_atividade_nome(row))
    )


def _comparativo_variacao_percentual_emendas_manifestacoes_NG(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
    is_atividade: Callable[[str], bool],
) -> float:
    inicio_atual, fim_atual, inicio_anterior, fim_anterior = (
        _resolver_periodos_comparativo_emendas_manifestacoes_NG(from_date, to_date)
    )
    valor_atual = _qtd_pecas_produzidas_emendas_manifestacoes_NG(agendamentos, inicio_atual, fim_atual, is_atividade)
    valor_anterior = _qtd_pecas_produzidas_emendas_manifestacoes_NG(
        agendamentos, inicio_anterior, fim_anterior, is_atividade
    )

    if valor_anterior == 0:
        return 0.0

    variacao = ((valor_atual - valor_anterior) / valor_anterior) * 100
    return round(variacao, 2)


def get_comparativo_qtd_manifestacoes_emendas_manifestacoes_NG(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """Variação % de Manifestações produzidas vs período anterior de mesma duração."""
    return _comparativo_variacao_percentual_emendas_manifestacoes_NG(
        agendamentos, from_date, to_date, _is_atividade_manifestacao
    )


def get_comparativo_qtd_dilacoes_emendas_manifestacoes_NG(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """Variação % de Dilações produzidas vs período anterior de mesma duração."""
    return _comparativo_variacao_percentual_emendas_manifestacoes_NG(
        agendamentos, from_date, to_date, _is_atividade_dilacao
    )


# =============================================================================
# UF — opções de filtro
# =============================================================================

def get_opcoes_uf_emendas_manifestacoes_NG(
    agendamentos: list[dict[str, Any]],
) -> list[str]:
    """UFs distintas (não vazias) presentes na base — sempre a partir dos dados
    completos (não filtrados), para a lista de opções não encolher conforme o
    filtro de UF é aplicado."""
    ufs = {uf for row in agendamentos if (uf := _get_uf(row)) is not None}
    return sorted(ufs)
