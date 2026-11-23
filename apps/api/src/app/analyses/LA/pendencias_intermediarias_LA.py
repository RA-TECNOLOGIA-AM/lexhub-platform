# Atividades no período — Setor Pendências Intermediárias — Escritório Luis Albert AM

from __future__ import annotations

from app.analyses.familias import pendencias_intermediarias as _familia  # V2: código único da família (familias/pendencias_intermediarias.py)
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
# Em andamento: subset ativo com fluxo explícito de progresso
_STATUS_EM_ANDAMENTO = _familia._STATUS_EM_ANDAMENTO

_STATUS_ENCERRADO = _familia._STATUS_ENCERRADO

_STATUS_FILTRO_TAREFAS = _familia._STATUS_FILTRO_TAREFAS

_SITUACOES_FILTRO_TAREFAS = _familia._SITUACOES_FILTRO_TAREFAS

SITUACOES_VALIDAS_INTERMEDIARIAS = _familia.SITUACOES_VALIDAS_INTERMEDIARIAS

_STATUS_DEMANDAS_FUNCIONARIO = _familia._STATUS_DEMANDAS_FUNCIONARIO

_SLUG_POR_STATUS = _familia._SLUG_POR_STATUS

_SEM_ATIVIDADE = _familia._SEM_ATIVIDADE

_SEM_FUNCIONARIO = _familia._SEM_FUNCIONARIO

# Atividades que configuram dilação (pedido de documentos → atraso no processo)
_ATIVIDADES_DILACAO: frozenset[str] = frozenset({
    "SOLICITAR DOCS DO CLIENTE",
    "SOLICITAR DOCS DE HIPOSSUFICIÊNCIA DO CLIENTE PARA RECURSO",
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

_MONTH_NAMES = _familia._MONTH_NAMES


group_intermediarias_concluidas_por_mes_LA = _familia.group_intermediarias_concluidas_por_mes


group_intermediarias_concluidas_por_dia_LA = _familia.group_intermediarias_concluidas_por_dia


get_intermediarias_concluidas_por_dia_por_funcionario_LA = _familia.get_intermediarias_concluidas_por_dia_por_funcionario


_media_concluidas_por_funcionario = _familia._media_concluidas_por_funcionario


get_media_intermediarias_concluidas_por_funcionario_LA = _familia.get_media_intermediarias_concluidas_por_funcionario


# =============================================================================
# Gráfico: processos distintos por atividade
# =============================================================================

group_intermediarias_processos_por_atividade_LA = _familia.group_intermediarias_processos_por_atividade


# =============================================================================
# Gráfico: demandas encerradas por funcionário
# =============================================================================

group_intermediarias_demandas_por_funcionario_LA = _familia.group_intermediarias_demandas_por_funcionario


# =============================================================================
# Gráfico (por prazo): processos distintos por atividade
# =============================================================================

group_intermediarias_processos_por_atividade_por_prazo_LA = _familia.group_intermediarias_processos_por_atividade_por_prazo


# =============================================================================
# Gráfico (por prazo): demandas encerradas por funcionário
# =============================================================================

group_intermediarias_demandas_por_funcionario_por_prazo_LA = _familia.group_intermediarias_demandas_por_funcionario_por_prazo


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

IntermediariasAtividadesFiltros = _familia.IntermediariasAtividadesFiltros


_agendamento_match_filtros = _familia._agendamento_match_filtros


filtrar_agendamentos_intermediarias_LA = _familia.filtrar_agendamentos_intermediarias


# =============================================================================
# Análise por Prazo — helpers internos
# =============================================================================

_incluir_na_lista_por_prazo = _familia._incluir_na_lista_por_prazo


_classificar_situacao_por_prazo = _familia._classificar_situacao_por_prazo


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

_filtrar_encerrados_com_prazo_no_periodo = _familia._filtrar_encerrados_com_prazo_no_periodo


group_intermediarias_concluidas_por_prazo_por_mes_LA = _familia.group_intermediarias_concluidas_por_prazo_por_mes


group_intermediarias_concluidas_por_prazo_por_dia_LA = _familia.group_intermediarias_concluidas_por_prazo_por_dia


get_intermediarias_concluidas_por_prazo_por_dia_por_funcionario_LA = _familia.get_intermediarias_concluidas_por_prazo_por_dia_por_funcionario


get_media_intermediarias_concluidas_por_prazo_por_funcionario_LA = _familia.get_media_intermediarias_concluidas_por_prazo_por_funcionario


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

_agendamento_match_filtros_por_prazo = _familia._agendamento_match_filtros_por_prazo


filtrar_agendamentos_intermediarias_por_prazo_LA = _familia.filtrar_agendamentos_intermediarias_por_prazo
