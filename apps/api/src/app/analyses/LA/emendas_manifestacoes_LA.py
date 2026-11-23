# Atividades no período — Setor Intermediárias (Emendas e Manifestações) — Escritório Luis Albert AM

from __future__ import annotations

from app.analyses.common import unidade as _unidade  # V2: valores da unidade (common/unidade.py)
from app.analyses.familias import emendas_manifestacoes as _familia  # V2: código único da família (familias/emendas_manifestacoes.py)
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Callable, Optional

from app.analyses.common import periodo  # V2: período e variação vs período anterior num módulo só
from app.analyses.common import conversao  # V2: conversões dos valores do banco num módulo só
from app.analyses.common import atividades  # V2: regras das atividades num módulo só
from app.utils import parse_date_from_db

# V2: os valores desta unidade para a família, lidos ao vivo deste módulo (common/unidade.py).
_VALORES_UNIDADE = _unidade.ValoresDoModulo(globals(), {"_ATIVIDADES_DILACAO": "_ATIVIDADES_DILACAO"})

# =============================================================================
# Constantes
# =============================================================================

# Inativos: excluídos de Total, Vencidas e Vencem hoje (alinhado com dashboard analítico)
_STATUS_INATIVO = _familia._STATUS_INATIVO
# Em andamento: qualquer status ativo (ainda não encerrado/cancelado)
_STATUS_EM_ANDAMENTO = _familia._STATUS_EM_ANDAMENTO

_STATUS_ENCERRADO = _familia._STATUS_ENCERRADO

_STATUS_FILTRO_TAREFAS = _familia._STATUS_FILTRO_TAREFAS

_SITUACOES_FILTRO_TAREFAS = _familia._SITUACOES_FILTRO_TAREFAS

SITUACOES_VALIDAS_EMENDAS_MANIFESTACOES = _familia.SITUACOES_VALIDAS_EMENDAS_MANIFESTACOES

_STATUS_DEMANDAS_FUNCIONARIO = _familia._STATUS_DEMANDAS_FUNCIONARIO

_SLUG_POR_STATUS = _familia._SLUG_POR_STATUS

_SEM_ATIVIDADE = _familia._SEM_ATIVIDADE

_SEM_FUNCIONARIO = _familia._SEM_FUNCIONARIO

# Atividades que contam como "Manifestação" para o comissionamento (inclui Emenda à Inicial)
_ATIVIDADES_MANIFESTACAO: frozenset[str] = frozenset({
    "EMENDA À INICIAL",
    "MANIFESTAÇÃO (5D)",
    "MANIFESTAÇÃO (10D)",
    "MANIFESTAÇÃO (15D)",
    "MANIFESTAÇÃO CUSTAS DE CITAÇÃO",
    "MANIFESTAÇÃO REMESSA 2 GRAU",
    "MAN HIPO RECURSO",
    "MAN HIPOSSUFICIÊNCIA",
    "MAN DESNECESSIDADE DE AUDIÊNCIA",
    "MAN INTERPOSIÇÃO AGRAVO",
    "PEDIDO DE CELERIDADE",
    "PEDIDO SUSTENTAÇÃO ORAL",
})

# Atividade que conta como "Dilação" para o comissionamento
_ATIVIDADES_DILACAO: frozenset[str] = frozenset({
    "DILAÇÃO DE PRAZO",
})

_COL_FUNCIONARIO_ATRIBUIDO = _familia._COL_FUNCIONARIO_ATRIBUIDO

_COL_FUNCIONARIO_ENCERRAMENTO = _familia._COL_FUNCIONARIO_ENCERRAMENTO

_COL_ID_USUARIO_ENCERRAMENTO = _familia._COL_ID_USUARIO_ENCERRAMENTO


# =============================================================================
# Utilitários
# =============================================================================

_to_int = _familia._to_int


_to_date = _familia._to_date


_data_no_periodo = _familia._data_no_periodo


_nome_em_conjunto_filtro = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._nome_em_conjunto_filtro)


# =============================================================================
# Getters de campos dos agendamentos
# =============================================================================

_get_status = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_status)


_get_data_criacao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_data_criacao)


_get_data_conclusao = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_data_conclusao)


_get_prazo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_prazo)


_get_processo_id = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_processo_id)


_get_numero_processo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_numero_processo)


_get_atividade_nome = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_atividade_nome)


_get_funcionario_atribuido = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_funcionario_atribuido)


_get_funcionario_encerramento = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_funcionario_encerramento)


# V2: como estas atividades são lidas e quais status contam (app/analyses/common/atividades.py).
_ATIVIDADES = _familia._ATIVIDADES

_STATUS_ATIVIDADES = _familia._STATUS_ATIVIDADES


_get_funcionario_nome = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._get_funcionario_nome)


# =============================================================================
# Filtros de período
# =============================================================================

_filtrar_criados_no_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_criados_no_periodo)


_filtrar_encerrados_no_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_encerrados_no_periodo)


_incluir_na_lista_tarefas = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._incluir_na_lista_tarefas)


_classificar_situacao_tarefa = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._classificar_situacao_tarefa)


# =============================================================================
# KPIs
# =============================================================================

def get_kpis_atividades_emendas_manifestacoes_LA(
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
        "total_atividades_emendas_manifestacoes_LA": total,
        "atividades_emendas_manifestacoes_em_andamento_LA": em_andamento,
        "atividades_emendas_manifestacoes_vencidas_LA": vencidas,
        "atividades_emendas_manifestacoes_vencem_hoje_LA": vencem_hoje,
        "atividades_emendas_manifestacoes_concluidas_LA": concluidas,
    }


# =============================================================================
# Histórico de concluídas (mensal e diário)
# =============================================================================

_MONTH_NAMES = _familia._MONTH_NAMES


group_emendas_manifestacoes_concluidas_por_mes_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_emendas_manifestacoes_concluidas_por_mes)


group_emendas_manifestacoes_concluidas_por_dia_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_emendas_manifestacoes_concluidas_por_dia)


get_emendas_manifestacoes_concluidas_por_dia_por_funcionario_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_emendas_manifestacoes_concluidas_por_dia_por_funcionario)


_media_concluidas_por_funcionario = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._media_concluidas_por_funcionario)


get_media_emendas_manifestacoes_concluidas_por_funcionario_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_media_emendas_manifestacoes_concluidas_por_funcionario)


# =============================================================================
# Gráfico: processos distintos por atividade
# =============================================================================

group_emendas_manifestacoes_processos_por_atividade_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_emendas_manifestacoes_processos_por_atividade)


# =============================================================================
# Gráfico: demandas encerradas por funcionário
# =============================================================================

group_emendas_manifestacoes_demandas_por_funcionario_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_emendas_manifestacoes_demandas_por_funcionario)


# =============================================================================
# Gráfico (por prazo): processos distintos por atividade
# =============================================================================

group_emendas_manifestacoes_processos_por_atividade_por_prazo_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_emendas_manifestacoes_processos_por_atividade_por_prazo)


# =============================================================================
# Gráfico (por prazo): demandas encerradas por funcionário
# =============================================================================

group_emendas_manifestacoes_demandas_por_funcionario_por_prazo_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_emendas_manifestacoes_demandas_por_funcionario_por_prazo)


# =============================================================================
# Lista de tarefas
# =============================================================================

def list_emendas_manifestacoes_atividades_periodo_LA(
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
        setor = str(row.get("SETOR") or row.get("setor") or "INTERMEDIÁRIAS").strip().upper()
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

def get_opcoes_filtros_emendas_manifestacoes_LA(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, Any]:
    """Opções de filtros da lista de tarefas (funcionários, atividades, status, situações)."""
    rows = list_emendas_manifestacoes_atividades_periodo_LA(
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
class EmendasManifestacoesAtividadesFiltros:
    """Filtros cumulativos (AND) sobre agendamentos do setor Emendas e Manifestações."""

    funcionarios: frozenset[str] | None = None
    atividades: frozenset[str] | None = None
    status: frozenset[str] | None = None
    situacoes: frozenset[str] | None = None

    def ativo(self) -> bool:
        return bool(self.funcionarios or self.atividades or self.status or self.situacoes)


def _agendamento_match_filtros(
    row: dict[str, Any],
    filtros: EmendasManifestacoesAtividadesFiltros,
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


def filtrar_agendamentos_emendas_manifestacoes_LA(
    agendamentos: list[dict[str, Any]],
    filtros: EmendasManifestacoesAtividadesFiltros | None,
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

_incluir_na_lista_por_prazo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._incluir_na_lista_por_prazo)


_classificar_situacao_por_prazo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._classificar_situacao_por_prazo)


# =============================================================================
# KPIs por Prazo
# =============================================================================

def get_kpis_emendas_manifestacoes_por_prazo_LA(
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
        "total_por_prazo_emendas_manifestacoes_LA": total,
        "por_prazo_em_andamento_emendas_manifestacoes_LA": em_andamento,
        "por_prazo_vencidas_emendas_manifestacoes_LA": vencidas,
        "por_prazo_vencem_hoje_emendas_manifestacoes_LA": vencem_hoje,
        "por_prazo_concluidas_emendas_manifestacoes_LA": concluidas,
    }


# =============================================================================
# Histórico de concluídas por Prazo (mensal e diário)
# =============================================================================

_filtrar_encerrados_com_prazo_no_periodo = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._filtrar_encerrados_com_prazo_no_periodo)


group_emendas_manifestacoes_concluidas_por_prazo_por_mes_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_emendas_manifestacoes_concluidas_por_prazo_por_mes)


group_emendas_manifestacoes_concluidas_por_prazo_por_dia_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.group_emendas_manifestacoes_concluidas_por_prazo_por_dia)


get_emendas_manifestacoes_concluidas_por_prazo_por_dia_por_funcionario_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_emendas_manifestacoes_concluidas_por_prazo_por_dia_por_funcionario)


get_media_emendas_manifestacoes_concluidas_por_prazo_por_funcionario_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia.get_media_emendas_manifestacoes_concluidas_por_prazo_por_funcionario)


# =============================================================================
# Lista de tarefas por Prazo
# =============================================================================

def list_emendas_manifestacoes_por_prazo_LA(
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
        setor = str(row.get("SETOR") or row.get("setor") or "INTERMEDIÁRIAS").strip().upper()
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

def get_opcoes_filtros_emendas_manifestacoes_por_prazo_LA(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, Any]:
    """Opções de filtros da lista por prazo (funcionários, atividades, status, situações)."""
    rows = list_emendas_manifestacoes_por_prazo_LA(
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
    filtros: EmendasManifestacoesAtividadesFiltros,
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


def filtrar_agendamentos_emendas_manifestacoes_por_prazo_LA(
    agendamentos: list[dict[str, Any]],
    filtros: EmendasManifestacoesAtividadesFiltros | None,
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
# Regras (definidas pelo escritório LA em 2026-07):
#   - Gatilho mínimo (Faixa 1): >= 85% da agenda do mês finalizada.
#   - Acelerador (Faixa 2): >= 97% da agenda do mês finalizada.
#   - Abaixo de 85%: não elegível para comissão.
#   - Faixa 1 (85% a 96,9%): R$ 1,00 por Manifestação e R$ 0,25 por Dilação.
#   - Faixa 2 (>= 97%): R$ 1,50 por Manifestação e R$ 0,50 por Dilação.
#
# "Agenda do mês" = agendamentos do funcionário com PRAZO no período selecionado
# (mesmo eixo temporal da visão "por prazo" acima). Cancelado e Concluído não
# entram na agenda (não são responsabilidade ativa nem entrega finalizada).
# "Finalizado" = Encerrado Cumprido ou Encerrado Não Cumprido (ambos contam
# para o cumprimento da agenda, independente do resultado do processo).
#
# As peças (Manifestação/Dilação) só contam quando o resultado foi "Encerrado
# Cumprido" (Não Cumprido conta para a agenda, mas não é peça remunerada),
# usando o PRAZO no período como eixo temporal (mesma base da agenda) — não a
# DATA_HORA_CONCLUSAO. Validado contra produção real de funcionário (Roberta
# Batista Fernandes, Jun/2026: 484 manifestações + 29 dilações = R$740,50).


_agenda_cumprida_funcionario_LA = _unidade.na_unidade(_familia._UNIDADE, _VALORES_UNIDADE, _familia._agenda_cumprida_funcionario)


def _preco_unitario_emendas_manifestacoes_LA(percentual_agenda: float) -> tuple[Decimal, Decimal]:
    """Valores unitários (manifestação, dilação) conforme faixa de agenda cumprida."""
    if percentual_agenda >= 97:
        return Decimal("1.50"), Decimal("0.50")
    if percentual_agenda >= 85:
        return Decimal("1.00"), Decimal("0.25")
    return Decimal("0"), Decimal("0")


def get_emendas_manifestacoes_comissionamento_por_funcionario_LA(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Comissionamento por funcionário do setor Emendas e Manifestações.

    Faixas aplicadas sobre o percentual de agenda cumprida (PRAZO no período):
    < 85% não elegível; 85%-96,9% Faixa 1; >= 97% Faixa 2. O valor unitário da
    faixa se aplica às peças (Manifestação/Dilação) com PRAZO no período e
    status "Encerrado Cumprido" — Encerrado Não Cumprido conta para a agenda,
    mas não gera peça remunerada.
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

        finalizados, total_agenda, percentual = _agenda_cumprida_funcionario_LA(
            rows, from_date, to_date
        )
        elegivel = total_agenda > 0 and percentual >= 85.0
        if percentual >= 97:
            faixa: str | None = "faixa_2"
        elif percentual >= 85:
            faixa = "faixa_1"
        else:
            faixa = None

        produzidas = [
            row for row in rows
            if (_get_status(row) or "") == "Encerrado Cumprido"
            and _data_no_periodo(_get_prazo(row), from_date, to_date)
        ]
        qtd_manifestacao = sum(
            1 for row in produzidas
            if _get_atividade_nome(row) in _ATIVIDADES_MANIFESTACAO
        )
        qtd_dilacao = sum(
            1 for row in produzidas
            if _get_atividade_nome(row) in _ATIVIDADES_DILACAO
        )

        if qtd_manifestacao == 0 and qtd_dilacao == 0 and total_agenda == 0:
            continue

        valor_manifestacao, valor_dilacao = (
            _preco_unitario_emendas_manifestacoes_LA(percentual)
            if elegivel else (Decimal("0"), Decimal("0"))
        )
        sub_manifestacao = (Decimal(qtd_manifestacao) * valor_manifestacao).quantize(Decimal("0.01"))
        sub_dilacao = (Decimal(qtd_dilacao) * valor_dilacao).quantize(Decimal("0.01"))
        total_comissao = (sub_manifestacao + sub_dilacao).quantize(Decimal("0.01"))

        linhas.append({
            "funcionario": nome,
            "agenda_finalizada": finalizados,
            "agenda_total": total_agenda,
            "agenda_percentual": percentual,
            "elegivel": elegivel,
            "faixa": faixa,
            "qtd_manifestacao": qtd_manifestacao,
            "valor_manifestacao": float(valor_manifestacao),
            "qtd_x_valor_manifestacao": float(sub_manifestacao),
            "qtd_dilacao": qtd_dilacao,
            "valor_dilacao": float(valor_dilacao),
            "qtd_x_valor_dilacao": float(sub_dilacao),
            "valor_comissao": float(total_comissao),
        })

    linhas.sort(key=lambda x: (-x["valor_comissao"], x["funcionario"]))
    return linhas
