# Atividades no período — Setor Pendências Intermediárias — Escritório Luis Albert AM

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
# Em andamento: subset ativo com fluxo explícito de progresso
_STATUS_EM_ANDAMENTO = frozenset({"Iniciado", "Reaberto", "Encaminhado"})
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

SITUACOES_VALIDAS_INTERMEDIARIAS = frozenset(sid for sid, _ in _SITUACOES_FILTRO_TAREFAS)

_STATUS_DEMANDAS_FUNCIONARIO: tuple[tuple[str, str], ...] = (
    ("encerrado_nao_cumprido", "Encerrado Não Cumprido"),
    ("encerrado_cumprido", "Encerrado Cumprido"),
)

_SLUG_POR_STATUS: dict[str, str] = {
    label: slug for slug, label in _STATUS_DEMANDAS_FUNCIONARIO
}

_SEM_ATIVIDADE = "Sem atividade"
_SEM_FUNCIONARIO = "Sem funcionário"

# Atividades que configuram dilação (pedido de documentos → atraso no processo)
_ATIVIDADES_DILACAO: frozenset[str] = frozenset({
    "SOLICITAR DOCS DO CLIENTE",
    "SOLICITAR DOCS DE HIPOSSUFICIÊNCIA DO CLIENTE PARA RECURSO",
})

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

def get_kpis_atividades_intermediarias_LA(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, int]:
    """
    KPIs de agendamentos do setor Pendências Intermediárias no período.

    - **Total**: ativas criadas no período (exclui Cancelado, Concluído, Encerrado*)
    - **Em andamento**: status Iniciado, Reaberto ou Encaminhado criadas no período
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
        "total_atividades_intermediarias_LA": total,
        "atividades_intermediarias_em_andamento_LA": em_andamento,
        "atividades_intermediarias_vencidas_LA": vencidas,
        "atividades_intermediarias_vencem_hoje_LA": vencem_hoje,
        "atividades_intermediarias_concluidas_LA": concluidas,
    }


# =============================================================================
# Histórico de concluídas (mensal e diário)
# =============================================================================

_MONTH_NAMES = (
    "jan", "fev", "mar", "abr", "mai", "jun",
    "jul", "ago", "set", "out", "nov", "dez",
)


def group_intermediarias_concluidas_por_mes_LA(
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


def group_intermediarias_concluidas_por_dia_LA(
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


def get_intermediarias_concluidas_por_dia_por_funcionario_LA(
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


def get_media_intermediarias_concluidas_por_funcionario_LA(
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

def group_intermediarias_processos_por_atividade_LA(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Processos distintos por atividade (agendamentos criados no período)."""
    base = _filtrar_criados_no_periodo(agendamentos, from_date, to_date)

    grouped: dict[str, set[Any]] = defaultdict(set)
    for row in base:
        pid = _get_processo_id(row)
        if pid is None:
            continue
        nome = _get_atividade_nome(row)
        grouped[nome].add(pid)

    total = float(sum(len(v) for v in grouped.values()))
    itens: list[dict[str, Any]] = []
    for nome, processos in grouped.items():
        qtd = len(processos)
        itens.append({
            "name": nome,
            "value": float(qtd),
            "percent": round(100.0 * float(qtd) / total, 1) if total > 0 else 0.0,
        })
    return sorted(itens, key=lambda x: float(x["value"]), reverse=True)


# =============================================================================
# Gráfico: demandas encerradas por funcionário
# =============================================================================

def group_intermediarias_demandas_por_funcionario_LA(
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

def group_intermediarias_processos_por_atividade_por_prazo_LA(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Processos distintos por atividade (agendamentos com prazo no período)."""
    base = [
        row for row in agendamentos
        if _data_no_periodo(_get_prazo(row), from_date, to_date)
    ]

    grouped: dict[str, set[Any]] = defaultdict(set)
    for row in base:
        pid = _get_processo_id(row)
        if pid is None:
            continue
        nome = _get_atividade_nome(row)
        grouped[nome].add(pid)

    total = float(sum(len(v) for v in grouped.values()))
    itens: list[dict[str, Any]] = []
    for nome, processos in grouped.items():
        qtd = len(processos)
        itens.append({
            "name": nome,
            "value": float(qtd),
            "percent": round(100.0 * float(qtd) / total, 1) if total > 0 else 0.0,
        })
    return sorted(itens, key=lambda x: float(x["value"]), reverse=True)


# =============================================================================
# Gráfico (por prazo): demandas encerradas por funcionário
# =============================================================================

def group_intermediarias_demandas_por_funcionario_por_prazo_LA(
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

def list_intermediarias_atividades_periodo_LA(
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
        setor = str(row.get("SETOR") or row.get("setor") or "PENDÊNCIAS").strip().upper()
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

def get_opcoes_filtros_intermediarias_LA(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, Any]:
    """Opções de filtros da lista de tarefas (funcionários, atividades, status, situações)."""
    rows = list_intermediarias_atividades_periodo_LA(
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
class IntermediariasAtividadesFiltros:
    """Filtros cumulativos (AND) sobre agendamentos do setor Pendências Intermediárias."""

    funcionarios: frozenset[str] | None = None
    atividades: frozenset[str] | None = None
    status: frozenset[str] | None = None
    situacoes: frozenset[str] | None = None

    def ativo(self) -> bool:
        return bool(self.funcionarios or self.atividades or self.status or self.situacoes)


def _agendamento_match_filtros(
    row: dict[str, Any],
    filtros: IntermediariasAtividadesFiltros,
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


def filtrar_agendamentos_intermediarias_LA(
    agendamentos: list[dict[str, Any]],
    filtros: IntermediariasAtividadesFiltros | None,
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
# Dilações
# =============================================================================

def _solicitar_docs_nao_cumprido_por_processo(
    ag_pendencias: list[dict[str, Any]],
) -> dict[Any, list[tuple[Optional[date], str]]]:
    """
    SOLICITAR DOCS DO CLIENTE / DE HIPOSSUFICIÊNCIA do setor, agrupados por
    processo_id, restritos a quem foi **encerrado como "Encerrado Não
    Cumprido"** — só esses dois motivos (dentro do fluxo de Não Cumprido)
    podem encaminhar para "INTERMEDIÁRIAS - DILAÇÃO DE PRAZO"; o outro motivo
    de Não Cumprido encaminha para "Verificar Não Cumprimento" e não conta.
    """
    por_processo: dict[Any, list[tuple[Optional[date], str]]] = defaultdict(list)
    for row in ag_pendencias:
        if _get_atividade_nome(row) not in _ATIVIDADES_DILACAO:
            continue
        if (_get_status(row) or "") != "Encerrado Não Cumprido":
            continue
        pid = _get_processo_id(row)
        if pid is not None:
            por_processo[pid].append((_get_data_conclusao(row), _get_funcionario_nome(row)))
    return por_processo


def get_dilacoes_intermediarias_LA(
    ag_pendencias: list[dict[str, Any]],
    ag_dilacao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    filtros: Optional[IntermediariasAtividadesFiltros] = None,
    ag_pendencias_todos: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
    """
    Taxa de dilação do período.

    - Numerador:   agendamentos "INTERMEDIÁRIAS - DILAÇÃO DE PRAZO" (`ag_dilacao`,
                   query do escritório inteiro, sem filtro de setor de origem) com
                   DATA_HORA_CRIACAO no período E rastreáveis a um SOLICITAR DOCS
                   do setor **encerrado como "Encerrado Não Cumprido"** no mesmo
                   processo_id — só esse motivo de Não Cumprido encaminha para
                   Dilação de Prazo (o outro motivo de Não Cumprido encaminha para
                   "Verificar Não Cumprimento" e não gera esse agendamento).
                   Dilações órfãs (sem SOLICITAR DOCS Não Cumprido correspondente)
                   são descartadas — vieram de outro fluxo/setor do escritório.
                   Usa `ag_pendencias_todos` (não filtrado) para casar o dono, para
                   não perder referências de outros funcionários quando houver
                   filtro de funcionário ativo em `ag_pendencias`.
    - Se `filtros.funcionarios` estiver ativo (dropdown/gráfico de funcionário no
      dashboard), o numerador é restrito às dilações cujo dono seja um dos
      funcionários selecionados — o card passa a refletir só a pessoa filtrada.
    - Denominador: todos os encerrados do setor (todas as atividades) com
                   DATA_HORA_CONCLUSAO no período — mesmo valor do KPI "Concluídas".

    Faixas de comissão:
      Ouro   → taxa ≤  5 %
      Prata  →  6 % ≤ taxa ≤ 10 %
      Bronze → 11 % ≤ taxa ≤ 15 %
      None   → acima de 15 % (fora das faixas)
    """
    ag_ref = ag_pendencias_todos if ag_pendencias_todos is not None else ag_pendencias
    solicitar_por_processo = _solicitar_docs_nao_cumprido_por_processo(ag_ref)

    def _owner(dilacao_row: dict[str, Any]) -> str | None:
        pid = _get_processo_id(dilacao_row)
        candidates = solicitar_por_processo.get(pid)
        if not candidates:
            return None
        criacao = _get_data_criacao(dilacao_row)
        # Prefere o SOLICITAR DOCS (Não Cumprido) encerrado mais próximo (e
        # anterior) à criação da dilação
        valid = [
            (c, f) for c, f in candidates
            if c is not None and (criacao is None or c <= criacao)
        ] or candidates
        valid.sort(key=lambda x: x[0] or date.min)
        return valid[-1][1]  # mais recente

    if filtros and filtros.funcionarios:
        ag_dilacao = [
            row for row in ag_dilacao
            if _nome_em_conjunto_filtro(_owner(row) or "", filtros.funcionarios)
        ]
    else:
        ag_dilacao = [row for row in ag_dilacao if _owner(row) is not None]

    total_dilacoes = sum(
        1 for row in ag_dilacao
        if _data_no_periodo(_get_data_criacao(row), from_date, to_date)
    )

    # Denominador: todos os encerrados do setor no período (= valor "Concluídas" do KPI)
    total_base = sum(
        1 for row in ag_pendencias
        if (_get_status(row) or "") in _STATUS_ENCERRADO
        and _data_no_periodo(_get_data_conclusao(row), from_date, to_date)
    )

    taxa = round(100.0 * total_dilacoes / total_base, 1) if total_base > 0 else 0.0

    if total_base == 0 or taxa > 15:
        faixa: str | None = None
    elif taxa <= 5:
        faixa = "ouro"
    elif taxa <= 10:
        faixa = "prata"
    else:
        faixa = "bronze"

    return {
        "dilacoes_intermediarias_total_encerrados_LA": total_base,
        "dilacoes_intermediarias_count_LA": total_dilacoes,
        "dilacoes_intermediarias_taxa_LA": taxa,
        "dilacoes_intermediarias_faixa_LA": faixa,
    }


def get_dilacoes_intermediarias_por_funcionario_LA(
    ag_pendencias: list[dict[str, Any]],
    ag_dilacao: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    ag_pendencias_todos: Optional[list[dict[str, Any]]] = None,
) -> list[dict[str, Any]]:
    """
    Quebra por funcionário da taxa de dilação do período (mesma base de
    `get_dilacoes_intermediarias_LA`).

    - Dono da dilação: quem encerrou o SOLICITAR DOCS "Encerrado Não Cumprido"
      mais próximo (e anterior) à criação da dilação, no mesmo processo_id —
      mesmo critério de `get_dilacoes_intermediarias_LA`. Usa
      `ag_pendencias_todos` (não filtrado) para essa correspondência.
    - Denominador por funcionário (`total_encerrados`): encerrados do setor no
      período (DATA_HORA_CONCLUSAO), atribuídos a esse funcionário.
    - `qtd_resolvidos`: subconjunto de `total_encerrados` com status
      "Encerrado Cumprido".
    - Só aparecem no resultado funcionários que encerraram pelo menos um
      SOLICITAR DOCS (`_ATIVIDADES_DILACAO`) no período — o setor "PENDÊNCIAS"
      tem outras atividades (ex.: "VERIFICAR NÃO CUMPRIMENTO") trabalhadas por
      outra pessoa, que não faz parte do fluxo de pedido de documento/dilação
      e não deve entrar no relatório de comissão desta faixa.
    """
    ag_ref = ag_pendencias_todos if ag_pendencias_todos is not None else ag_pendencias
    solicitar_por_processo = _solicitar_docs_nao_cumprido_por_processo(ag_ref)

    def _owner(dilacao_row: dict[str, Any]) -> str | None:
        pid = _get_processo_id(dilacao_row)
        candidates = solicitar_por_processo.get(pid)
        if not candidates:
            return None
        criacao = _get_data_criacao(dilacao_row)
        valid = [
            (c, f) for c, f in candidates
            if c is not None and (criacao is None or c <= criacao)
        ] or candidates
        valid.sort(key=lambda x: x[0] or date.min)
        return valid[-1][1]

    dilacoes_por_funcionario: dict[str, int] = defaultdict(int)
    for row in ag_dilacao:
        if not _data_no_periodo(_get_data_criacao(row), from_date, to_date):
            continue
        owner = _owner(row)
        if owner and owner != _SEM_FUNCIONARIO:
            dilacoes_por_funcionario[owner] += 1

    encerrados_por_funcionario: dict[str, int] = defaultdict(int)
    resolvidos_por_funcionario: dict[str, int] = defaultdict(int)
    solicitantes_docs_no_periodo: set[str] = set()
    for row in ag_pendencias:
        status = _get_status(row) or ""
        if status not in _STATUS_ENCERRADO:
            continue
        if not _data_no_periodo(_get_data_conclusao(row), from_date, to_date):
            continue
        nome = _get_funcionario_nome(row)
        if not nome or nome == _SEM_FUNCIONARIO:
            continue
        encerrados_por_funcionario[nome] += 1
        if status == "Encerrado Cumprido":
            resolvidos_por_funcionario[nome] += 1
        if _get_atividade_nome(row) in _ATIVIDADES_DILACAO:
            solicitantes_docs_no_periodo.add(nome)

    nomes = (set(dilacoes_por_funcionario) | set(encerrados_por_funcionario)) & solicitantes_docs_no_periodo

    resultado = []
    for nome in sorted(nomes):
        qtd_dilacoes = dilacoes_por_funcionario.get(nome, 0)
        total_encerrados = encerrados_por_funcionario.get(nome, 0)
        qtd_resolvidos = resolvidos_por_funcionario.get(nome, 0)
        taxa_dilacao = (
            round(100.0 * qtd_dilacoes / total_encerrados, 1) if total_encerrados > 0 else 0.0
        )
        resultado.append({
            "funcionario": nome,
            "qtd_dilacoes": qtd_dilacoes,
            "total_encerrados": total_encerrados,
            "qtd_resolvidos": qtd_resolvidos,
            "taxa_dilacao": taxa_dilacao,
        })
    return resultado


# =============================================================================
# KPIs por Prazo
# =============================================================================

def get_kpis_intermediarias_por_prazo_LA(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, int]:
    """
    KPIs do setor Pendências Intermediárias usando PRAZO como eixo temporal.

    - **Total**: ativas com prazo no período (exclui Cancelado, Concluído, Encerrado*)
    - **Em andamento**: status Iniciado, Reaberto ou Encaminhado com prazo no período
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
        "total_por_prazo_intermediarias_LA": total,
        "por_prazo_em_andamento_intermediarias_LA": em_andamento,
        "por_prazo_vencidas_intermediarias_LA": vencidas,
        "por_prazo_vencem_hoje_intermediarias_LA": vencem_hoje,
        "por_prazo_concluidas_intermediarias_LA": concluidas,
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


def group_intermediarias_concluidas_por_prazo_por_mes_LA(
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


def group_intermediarias_concluidas_por_prazo_por_dia_LA(
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


def get_intermediarias_concluidas_por_prazo_por_dia_por_funcionario_LA(
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


def get_media_intermediarias_concluidas_por_prazo_por_funcionario_LA(
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

def list_intermediarias_por_prazo_LA(
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
        setor = str(row.get("SETOR") or row.get("setor") or "PENDÊNCIAS").strip().upper()
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

def get_opcoes_filtros_intermediarias_por_prazo_LA(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, Any]:
    """Opções de filtros da lista por prazo (funcionários, atividades, status, situações)."""
    rows = list_intermediarias_por_prazo_LA(
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
    filtros: IntermediariasAtividadesFiltros,
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


def filtrar_agendamentos_intermediarias_por_prazo_LA(
    agendamentos: list[dict[str, Any]],
    filtros: IntermediariasAtividadesFiltros | None,
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
