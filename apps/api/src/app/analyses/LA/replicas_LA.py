# Atividades no período — Setor Réplicas — Escritório Luis Albert AM

from __future__ import annotations

from app.analyses.familias import replicas as _familia  # V2: código único da família (familias/replicas.py)
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
_STATUS_INATIVO = _familia._STATUS_INATIVO
# Em andamento: qualquer status ativo (ainda não encerrado/cancelado)
_STATUS_EM_ANDAMENTO = _familia._STATUS_EM_ANDAMENTO

_STATUS_ENCERRADO = _familia._STATUS_ENCERRADO

_STATUS_FILTRO_TAREFAS = _familia._STATUS_FILTRO_TAREFAS

_SITUACOES_FILTRO_TAREFAS = _familia._SITUACOES_FILTRO_TAREFAS

SITUACOES_VALIDAS_REPLICAS = _familia.SITUACOES_VALIDAS_REPLICAS

_STATUS_DEMANDAS_FUNCIONARIO = _familia._STATUS_DEMANDAS_FUNCIONARIO

_SLUG_POR_STATUS = _familia._SLUG_POR_STATUS

_SEM_ATIVIDADE = _familia._SEM_ATIVIDADE

_SEM_FUNCIONARIO = _familia._SEM_FUNCIONARIO

_COL_FUNCIONARIO_ATRIBUIDO = _familia._COL_FUNCIONARIO_ATRIBUIDO

_COL_FUNCIONARIO_ENCERRAMENTO = _familia._COL_FUNCIONARIO_ENCERRAMENTO

_COL_ID_USUARIO_ENCERRAMENTO = _familia._COL_ID_USUARIO_ENCERRAMENTO


# =============================================================================
# Utilitários
# =============================================================================

_to_int = _familia._to_int


_to_date = _familia._to_date


_data_no_periodo = _familia._data_no_periodo


_nome_em_conjunto_filtro = _familia._nome_em_conjunto_filtro


# =============================================================================
# Getters de campos dos agendamentos
# =============================================================================

_get_status = _familia._get_status


_get_data_criacao = _familia._get_data_criacao


_get_data_conclusao = _familia._get_data_conclusao


_get_prazo = _familia._get_prazo


_get_processo_id = _familia._get_processo_id


_get_atividade_nome = _familia._get_atividade_nome


_get_funcionario_atribuido = _familia._get_funcionario_atribuido


_get_funcionario_encerramento = _familia._get_funcionario_encerramento


# V2: como estas atividades são lidas e quais status contam (app/analyses/common/atividades.py).
_ATIVIDADES = _familia._ATIVIDADES

_STATUS_ATIVIDADES = _familia._STATUS_ATIVIDADES


_get_funcionario_nome = _familia._get_funcionario_nome


# =============================================================================
# Filtros de período
# =============================================================================

_filtrar_criados_no_periodo = _familia._filtrar_criados_no_periodo


_filtrar_encerrados_no_periodo = _familia._filtrar_encerrados_no_periodo


_incluir_na_lista_tarefas = _familia._incluir_na_lista_tarefas


_classificar_situacao_tarefa = _familia._classificar_situacao_tarefa


# =============================================================================
# KPIs
# =============================================================================

def get_kpis_atividades_replicas_LA(
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
        "total_atividades_replicas_LA": total,
        "atividades_replicas_em_andamento_LA": em_andamento,
        "atividades_replicas_vencidas_LA": vencidas,
        "atividades_replicas_vencem_hoje_LA": vencem_hoje,
        "atividades_replicas_concluidas_LA": concluidas,
    }


# =============================================================================
# Histórico de concluídas (mensal e diário)
# =============================================================================

_MONTH_NAMES = _familia._MONTH_NAMES


group_replicas_concluidas_por_mes_LA = _familia.group_replicas_concluidas_por_mes


group_replicas_concluidas_por_dia_LA = _familia.group_replicas_concluidas_por_dia


get_replicas_concluidas_por_dia_por_funcionario_LA = _familia.get_replicas_concluidas_por_dia_por_funcionario


_media_concluidas_por_funcionario = _familia._media_concluidas_por_funcionario


get_media_replicas_concluidas_por_funcionario_LA = _familia.get_media_replicas_concluidas_por_funcionario


# =============================================================================
# Gráfico: processos distintos por atividade
# =============================================================================

group_replicas_processos_por_atividade_LA = _familia.group_replicas_processos_por_atividade


# =============================================================================
# Gráfico: demandas encerradas por funcionário
# =============================================================================

group_replicas_demandas_por_funcionario_LA = _familia.group_replicas_demandas_por_funcionario


# =============================================================================
# Gráfico (por prazo): processos distintos por atividade
# =============================================================================

group_replicas_processos_por_atividade_por_prazo_LA = _familia.group_replicas_processos_por_atividade_por_prazo


# =============================================================================
# Gráfico (por prazo): demandas encerradas por funcionário
# =============================================================================

group_replicas_demandas_por_funcionario_por_prazo_LA = _familia.group_replicas_demandas_por_funcionario_por_prazo


# =============================================================================
# Lista de tarefas
# =============================================================================

def list_replicas_atividades_periodo_LA(
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
        setor = str(row.get("SETOR") or row.get("setor") or "RÉPLICAS").strip().upper()
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

def get_opcoes_filtros_replicas_LA(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, Any]:
    """Opções de filtros da lista de tarefas (funcionários, atividades, status, situações)."""
    rows = list_replicas_atividades_periodo_LA(
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

ReplicasAtividadesFiltros = _familia.ReplicasAtividadesFiltros


_agendamento_match_filtros = _familia._agendamento_match_filtros


filtrar_agendamentos_replicas_LA = _familia.filtrar_agendamentos_replicas


# =============================================================================
# Análise por Prazo — helpers internos
# =============================================================================

_incluir_na_lista_por_prazo = _familia._incluir_na_lista_por_prazo


_classificar_situacao_por_prazo = _familia._classificar_situacao_por_prazo


# =============================================================================
# KPIs por Prazo
# =============================================================================

def get_kpis_replicas_por_prazo_LA(
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
        "total_por_prazo_replicas_LA": total,
        "por_prazo_em_andamento_replicas_LA": em_andamento,
        "por_prazo_vencidas_replicas_LA": vencidas,
        "por_prazo_vencem_hoje_replicas_LA": vencem_hoje,
        "por_prazo_concluidas_replicas_LA": concluidas,
    }


# =============================================================================
# Histórico de concluídas por Prazo (mensal e diário)
# =============================================================================

_filtrar_encerrados_com_prazo_no_periodo = _familia._filtrar_encerrados_com_prazo_no_periodo


group_replicas_concluidas_por_prazo_por_mes_LA = _familia.group_replicas_concluidas_por_prazo_por_mes


group_replicas_concluidas_por_prazo_por_dia_LA = _familia.group_replicas_concluidas_por_prazo_por_dia


get_replicas_concluidas_por_prazo_por_dia_por_funcionario_LA = _familia.get_replicas_concluidas_por_prazo_por_dia_por_funcionario


get_media_replicas_concluidas_por_prazo_por_funcionario_LA = _familia.get_media_replicas_concluidas_por_prazo_por_funcionario


# =============================================================================
# Lista de tarefas por Prazo
# =============================================================================

def list_replicas_por_prazo_LA(
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
        setor = str(row.get("SETOR") or row.get("setor") or "RÉPLICAS").strip().upper()
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

def get_opcoes_filtros_replicas_por_prazo_LA(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, Any]:
    """Opções de filtros da lista por prazo (funcionários, atividades, status, situações)."""
    rows = list_replicas_por_prazo_LA(
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

_agendamento_match_filtros_por_prazo = _familia._agendamento_match_filtros_por_prazo


filtrar_agendamentos_replicas_por_prazo_LA = _familia.filtrar_agendamentos_replicas_por_prazo


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

_IDS_1G_PROCEDENTE_REPLICAS = _familia._IDS_1G_PROCEDENTE_REPLICAS


def get_replicas_taxa_procedencia_LA(
    agendamentos: list[dict[str, Any]],
    status_1g_por_processo: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> dict[str, Any]:
    """
    Taxa de procedência (1G) dos processos com Réplica apresentada no período.

    - Universo: processos distintos com réplica apresentada (DATA_HORA_CRIACAO)
      no período — mesmo eixo temporal de "apresentada".
    - Denominador: desses processos, os que já possuem decisão de 1G (ID_1G
      não nulo em `status_1g_por_processo`, um dataset não filtrado por data,
      pois reflete o status atual/corrente do processo).
    - Numerador: subconjunto com 1G em `_IDS_1G_PROCEDENTE_REPLICAS`.
    """
    apresentadas_no_periodo = _filtrar_criados_no_periodo(agendamentos, from_date, to_date)
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
        "replicas_procedencia_total_processos_LA": total_processos,
        "replicas_procedencia_total_decididos_LA": total_decididos,
        "replicas_procedencia_procedentes_LA": total_procedentes,
        "replicas_procedencia_pendentes_LA": total_processos - total_decididos,
        "replicas_taxa_procedencia_LA": taxa,
    }
