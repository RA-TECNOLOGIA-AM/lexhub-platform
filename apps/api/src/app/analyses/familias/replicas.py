"""V2: código único da família replicas (era copiado em cada unidade: replicas_NG.py, replicas_LA.py).

Os arquivos de cada unidade
dão os nomes de hoje a estas funções, chamadas na unidade deles; o que for diferente fica no arquivo dela."""


from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Callable, Optional

from app.analyses.common import periodo  # V2: período e variação vs período anterior num módulo só
from app.analyses.common import conversao  # V2: conversões dos valores do banco num módulo só
from app.analyses.common import atividades  # V2: regras das atividades num módulo só
from app.utils import parse_date_from_db

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

SITUACOES_VALIDAS_REPLICAS = frozenset(sid for sid, _ in _SITUACOES_FILTRO_TAREFAS)

_STATUS_DEMANDAS_FUNCIONARIO: tuple[tuple[str, str], ...] = (
    ("encerrado_nao_cumprido", "Encerrado Não Cumprido"),
    ("encerrado_cumprido", "Encerrado Cumprido"),
)

_SLUG_POR_STATUS: dict[str, str] = {
    label: slug for slug, label in _STATUS_DEMANDAS_FUNCIONARIO
}

_SEM_ATIVIDADE = "Sem atividade"
_SEM_FUNCIONARIO = "Sem funcionário"

_COL_FUNCIONARIO_ATRIBUIDO = "FUNCIONARIO_ATRIBUIDO"
_COL_FUNCIONARIO_ENCERRAMENTO = "FUNCIONARIO_ENCERRAMENTO"
_COL_ID_USUARIO_ENCERRAMENTO = "ID_USUARIO_ENCERRAMENTO"


# =============================================================================
# Utilitários
# =============================================================================

_to_int = conversao.para_inteiro  # V2: era uma cópia local (app/analyses/common/conversao.py)


_to_date = conversao.para_data  # V2: era uma cópia local (app/analyses/common/conversao.py)


_data_no_periodo = periodo.no_periodo  # V2: era uma cópia local (app/analyses/common/periodo.py)


def _nome_em_conjunto_filtro(nome: str, conjunto: frozenset[str] | None) -> bool:
    return atividades.nome_em_conjunto(nome, conjunto)


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


# V2: como estas atividades são lidas e quais status contam (app/analyses/common/atividades.py).
_ATIVIDADES = atividades.Leitor(
    criacao=_get_data_criacao,
    conclusao=_get_data_conclusao,
    prazo=_get_prazo,
    status=_get_status,
    funcionario_encerramento=_get_funcionario_encerramento,
)
_STATUS_ATIVIDADES = atividades.Status(
    inativo=_STATUS_INATIVO, em_andamento=_STATUS_EM_ANDAMENTO, encerrado=_STATUS_ENCERRADO
)



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
    return atividades.encerrados_no_periodo(
        agendamentos, _ATIVIDADES, _STATUS_ATIVIDADES, from_date, to_date, exigir_encerrador=exigir_encerrador
    )


def _incluir_na_lista_tarefas(
    row: dict[str, Any],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> bool:
    return atividades.incluir_na_lista(row, _ATIVIDADES, _STATUS_ATIVIDADES, from_date, to_date, ref=ref_date)


def _classificar_situacao_tarefa(
    row: dict[str, Any],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, bool]:
    return atividades.situacao(row, _ATIVIDADES, _STATUS_ATIVIDADES, from_date, to_date, ref=ref_date)


# =============================================================================
# KPIs
# =============================================================================

def get_kpis_atividades_replicas(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, int]:
    """
    KPIs de agendamentos do setor Réplicas no período.

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
        "total_atividades_replicas_NG": total,
        "atividades_replicas_em_andamento_NG": em_andamento,
        "atividades_replicas_vencidas_NG": vencidas,
        "atividades_replicas_vencem_hoje_NG": vencem_hoje,
        "atividades_replicas_concluidas_NG": concluidas,
    }


# =============================================================================
# Histórico de concluídas (mensal e diário)
# =============================================================================

_MONTH_NAMES = (
    "jan", "fev", "mar", "abr", "mai", "jun",
    "jul", "ago", "set", "out", "nov", "dez",
)


def group_replicas_concluidas_por_mes(
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


def group_replicas_concluidas_por_dia(
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


def get_replicas_concluidas_por_dia_por_funcionario(
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
    return atividades.media_concluidas_por_funcionario(encerrados, get_data_ref, _get_funcionario_nome)


def get_media_replicas_concluidas_por_funcionario(
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

def group_replicas_processos_por_atividade(
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

def group_replicas_demandas_por_funcionario(
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

def group_replicas_processos_por_atividade_por_prazo(
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

def group_replicas_demandas_por_funcionario_por_prazo(
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

def list_replicas_atividades_periodo(
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
        setor = str(row.get("SETOR") or row.get("setor") or "RÉPLICA").strip().upper()
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

def get_opcoes_filtros_replicas(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, Any]:
    """Opções de filtros da lista de tarefas (funcionários, atividades, status, situações)."""
    rows = list_replicas_atividades_periodo(
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
class ReplicasAtividadesFiltros:
    """Filtros cumulativos (AND) sobre agendamentos do setor Réplicas."""

    funcionarios: frozenset[str] | None = None
    atividades: frozenset[str] | None = None
    status: frozenset[str] | None = None
    situacoes: frozenset[str] | None = None

    def ativo(self) -> bool:
        return bool(self.funcionarios or self.atividades or self.status or self.situacoes)


def _agendamento_match_filtros(
    row: dict[str, Any],
    filtros: ReplicasAtividadesFiltros,
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
    return True


def filtrar_agendamentos_replicas(
    agendamentos: list[dict[str, Any]],
    filtros: ReplicasAtividadesFiltros | None,
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
    return atividades.incluir_na_lista_por_prazo(row, _ATIVIDADES, from_date, to_date)


def _classificar_situacao_por_prazo(
    row: dict[str, Any],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, bool]:
    return atividades.situacao_por_prazo(row, _ATIVIDADES, _STATUS_ATIVIDADES, from_date, to_date, ref=ref_date)


# =============================================================================
# KPIs por Prazo
# =============================================================================

def get_kpis_replicas_por_prazo(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, int]:
    """
    KPIs do setor Réplicas usando PRAZO como eixo temporal.

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
        "total_por_prazo_replicas_NG": total,
        "por_prazo_em_andamento_replicas_NG": em_andamento,
        "por_prazo_vencidas_replicas_NG": vencidas,
        "por_prazo_vencem_hoje_replicas_NG": vencem_hoje,
        "por_prazo_concluidas_replicas_NG": concluidas,
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
    return atividades.encerrados_com_prazo_no_periodo(agendamentos, _ATIVIDADES, _STATUS_ATIVIDADES, from_date, to_date)


def group_replicas_concluidas_por_prazo_por_mes(
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


def group_replicas_concluidas_por_prazo_por_dia(
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


def get_replicas_concluidas_por_prazo_por_dia_por_funcionario(
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


def get_media_replicas_concluidas_por_prazo_por_funcionario(
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

def list_replicas_por_prazo(
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
        setor = str(row.get("SETOR") or row.get("setor") or "RÉPLICA").strip().upper()
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

def get_opcoes_filtros_replicas_por_prazo(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, Any]:
    """Opções de filtros da lista por prazo (funcionários, atividades, status, situações)."""
    rows = list_replicas_por_prazo(
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
    filtros: ReplicasAtividadesFiltros,
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
    return True


def filtrar_agendamentos_replicas_por_prazo(
    agendamentos: list[dict[str, Any]],
    filtros: ReplicasAtividadesFiltros | None,
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
# Taxa de procedência (1G) dos processos com Réplica apresentada
# =============================================================================
#
# Considerados "procedentes" os status de 1G (tabela public.status_primeiro_grau)
# que representam ganho de causa, com ou sem proveito econômico, total ou parcial:
#   20 PROCEDENTE COM PROVEITO ECONÔMICO
#   21 PARCIALMENTE PROCEDENTE COM PROVEITO ECONÔMICO
#   22 PROCEDENTE SEM PROVEITO ECONÔMICO
#   23 PARCIALMENTE PROCEDENTE SEM PROVEITO ECONÔMICO

_IDS_1G_PROCEDENTE_REPLICAS: frozenset[int] = frozenset({20, 21, 22, 23})

# Só esta atividade representa réplica apresentada; RÉPLICA CANCELADA e
# VERIFICAR CONTESTAÇÃO ficam fora do universo da taxa.
_ATIVIDADE_REPLICA_APRESENTADA = "ELABORAR RÉPLICA"
# V2 (decisão de 19/11/2026): no NG a atividade foi dividida em ELABORAR RÉPLICA SIMPLES e ELABORAR RÉPLICA
# ESPECÍFICA, e o nome exato acima não casava com nenhuma (a taxa ficava sempre zerada, também na v1). As três
# contam como réplica apresentada; ANÁLISE DE VIABILIDADE e RÉPLICA CANCELADA continuam fora. O RJ (que usa este
# cálculo) só tem ELABORAR RÉPLICA.
_ATIVIDADES_REPLICA_APRESENTADA: frozenset[str] = frozenset({
    _ATIVIDADE_REPLICA_APRESENTADA,
    "ELABORAR RÉPLICA SIMPLES",
    "ELABORAR RÉPLICA ESPECÍFICA",
})


def get_replicas_taxa_procedencia(
    agendamentos: list[dict[str, Any]],
    status_1g_por_processo: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> dict[str, Any]:
    """
    Taxa de procedência (1G) dos processos com Réplica apresentada no período.

    - Universo: processos distintos com réplica apresentada (DATA_HORA_CRIACAO)
      no período — mesmo eixo temporal de "apresentada". No NG, as atividades
      ELABORAR RÉPLICA (SIMPLES / ESPECÍFICA) contam como réplica apresentada (V2).
    - Denominador: desses processos, os que já possuem decisão de 1G (ID_1G
      não nulo em `status_1g_por_processo`, um dataset não filtrado por data,
      pois reflete o status atual/corrente do processo).
    - Numerador: subconjunto com 1G em `_IDS_1G_PROCEDENTE_REPLICAS`.
    """
    apresentadas_no_periodo = [
        row for row in _filtrar_criados_no_periodo(agendamentos, from_date, to_date)
        if _get_atividade_nome(row).upper() in _ATIVIDADES_REPLICA_APRESENTADA  # V2: era == (só ELABORAR RÉPLICA)
    ]
    processos_periodo = {
        pid for row in apresentadas_no_periodo
        if (pid := _get_processo_id(row)) is not None
    }

    status_por_processo: dict[Any, int | None] = {}
    for row in status_1g_por_processo:
        pid = row.get("processo_id") or row.get("PROCESSO_ID")
        if pid is None:
            continue
        id_1g_raw = row.get("ID_1G")
        status_por_processo[pid] = int(id_1g_raw) if id_1g_raw is not None else None

    total_processos = len(processos_periodo)
    total_decididos = 0
    total_procedentes = 0
    for pid in processos_periodo:
        id_1g = status_por_processo.get(pid)
        if id_1g is None:
            continue
        total_decididos += 1
        if id_1g in _IDS_1G_PROCEDENTE_REPLICAS:
            total_procedentes += 1

    taxa = round(100.0 * total_procedentes / total_decididos, 1) if total_decididos > 0 else 0.0

    return {
        "replicas_procedencia_total_processos_NG": total_processos,
        "replicas_procedencia_total_decididos_NG": total_decididos,
        "replicas_procedencia_procedentes_NG": total_procedentes,
        "replicas_procedencia_pendentes_NG": total_processos - total_decididos,
        "replicas_taxa_procedencia_NG": taxa,
    }
