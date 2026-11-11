# Funções de análises do setor da Fase Recursal — Escritório Nicolas Gomes (NG)

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from app.utils import parse_date_from_db
from app.analyses.common import matriz_julgamento as mj

# =============================================================================
# Constantes
# =============================================================================

ID_ESCRITORIO = 20
ID_FASE_RECURSAL = 8
ID_SETOR_RECURSOS_NG = 149

_COL_ID_ESCRITORIO = "ID_ESCRITORIO"
_COL_ID_FASE = "ID_FASE"
COL_DT_ENTRADA_RECURSAL = "DT_ENTRADA_RECURSAL"
COL_VALOR_CAUSA_ACORDO = "VALOR_CAUSA_ACORDO"
COL_VALOR_CAUSA_SENTENCA = "VALOR_CAUSA_SENTENCA"
_COL_ID_1G = "ID_1G"
_COL_STATUS_1G = "STATUS_1G"
_COL_ID_2G = "ID_2G"
_COL_STATUS_2G = "STATUS_2G"
_COL_DATA_SENTENCA = "DATA_SENTENCA"
_COL_DATA_ACORDAO = "DATA_ACORDAO"
_COL_DATA_ACORDAO_EMBARGOS = "DATA_ACORDAO_EMBARGOS"
_COL_JUIZ_1G = "JUIZ_1G"
_COL_RELATOR_2G = "RELATOR_2G"
_COL_SUBFASE = "SUBFASE"
_COL_FASE = "FASE"
_COL_OPERACAO = "OPERACAO"
_COL_MATERIA = "MATERIA"
_COL_PARTE_ADVERSA = "PARTE_ADVERSA"
_COL_NUMERO_PROCESSO = "NUMERO_PROCESSO"
_COL_COMPETENCIA = "COMPETENCIA"
_COL_VARA = "VARA"
_COL_ID_ATIVIDADE_RECURSOS = "ID_ATIVIDADE_RECURSOS"
_COL_ATIVIDADE_RECURSOS = "ATIVIDADE_RECURSOS"
_COL_STATUS_AGENDAMENTO_RECURSOS = "STATUS_AGENDAMENTO_RECURSOS"
_COL_ID_SETOR_ATIVIDADE_RECURSOS = "ID_SETOR_ATIVIDADE_RECURSOS"
_COL_FUNCIONARIO_ATRIBUIDO = "FUNCIONARIO_ATRIBUIDO"
_COL_FUNCIONARIO_ENCERRAMENTO = "FUNCIONARIO_ENCERRAMENTO"
_COL_ID_USUARIO_ENCERRAMENTO = "ID_USUARIO_ENCERRAMENTO"
_SEM_SUBFASE = "SEM SUBFASE"
_SEM_MATERIA = "SEM MATERIA"
_SEM_COMPETENCIA = "SEM COMPETÊNCIA"
_SEM_VARA = "Sem vara"
_SEM_ATIVIDADE_RECURSOS = "Sem atividade aberta"
_SEM_FUNCIONARIO_RECURSOS = "Sem funcionário"

# Setor RECURSOS (LexFlow) — escritório NG (``id_escritorio_assinante`` = 20)
_STATUS_AGENDAMENTO_ABERTO_RECURSOS = frozenset({"Recebido", "Visualizado"})
_STATUS_AGENDAMENTO_ENCERRADO_RECURSOS = frozenset({
    "Encerrado Cumprido",
    "Encerrado Não Cumprido",
})

# Status exibidos nos filtros da lista de tarefas (ordem fixa + extras do dataset)
_STATUS_FILTRO_TAREFAS_RECURSOS_NG: tuple[str, ...] = (
    "Recebido",
    "Visualizado",
    "Encerrado Cumprido",
    "Encerrado Não Cumprido",
    "Cancelado",
)

_SITUACOES_FILTRO_TAREFAS_RECURSOS_NG: tuple[tuple[str, str], ...] = (
    ("em_andamento", "Em andamento"),
    ("vencidas", "Vencidas"),
    ("vencem_hoje", "Vencem hoje"),
    ("concluidas", "Concluídas"),
)

# Ordem e slugs para gráfico de demandas encerradas por funcionário
_STATUS_DEMANDAS_FUNCIONARIO_NG: tuple[tuple[str, str], ...] = (
    ("encerrado_nao_cumprido", "Encerrado Não Cumprido"),
    ("encerrado_cumprido", "Encerrado Cumprido"),
)
_SLUG_POR_STATUS_AGENDAMENTO_RECURSOS: dict[str, str] = {
    label: slug for slug, label in _STATUS_DEMANDAS_FUNCIONARIO_NG
}

# Catálogo de atividades do setor RECURSOS (NG) — dinâmico, lido do banco
# (``setor_atividade`` / ``atividade`` do LexFlow, ``id_setor`` = 149). O NG usa uma
# nomenclatura própria e bem mais granular (65+ atividades) que a LA (``id_setor`` = 16,
# ver ``set_atividades_recursos_LA_catalogo`` em ``recurso_LA.py``, mesmo padrão). O
# catálogo é atualizado via ``set_atividades_recursos_NG_catalogo`` a cada ciclo de
# fetch, para que novas atividades cadastradas no setor apareçam automaticamente, sem
# precisar alterar código.
_ATIVIDADES_RECURSOS_NG: tuple[tuple[int, str], ...] = ()
_IDS_ATIVIDADE_RECURSOS_NG: frozenset[int] = frozenset()
_NOMES_ATIVIDADE_RECURSOS_NG: frozenset[str] = frozenset()


def set_atividades_recursos_NG_catalogo(catalogo: list[dict[str, Any]]) -> None:
    """
    Atualiza o catálogo dinâmico de atividades ativas do setor RECURSOS (NG).

    ``catalogo`` vem da query ``atividades_setor_recursos_NG`` (cacheada), com linhas
    ``{"id_atividade": int, "ATIVIDADE": str}``. Deve ser chamada antes de qualquer
    análise que dependa do catálogo (ex.: ``_build_recursal_NG_stats``).
    """
    global _ATIVIDADES_RECURSOS_NG, _IDS_ATIVIDADE_RECURSOS_NG, _NOMES_ATIVIDADE_RECURSOS_NG
    pares = tuple(
        (int(row["id_atividade"]), str(row["ATIVIDADE"]).strip())
        for row in catalogo
        if row.get("id_atividade") is not None and str(row.get("ATIVIDADE") or "").strip()
    )
    _ATIVIDADES_RECURSOS_NG = pares
    _IDS_ATIVIDADE_RECURSOS_NG = frozenset(aid for aid, _ in pares)
    _NOMES_ATIVIDADE_RECURSOS_NG = frozenset(nome for _, nome in pares)

_RESULTADO_FAV = "fav"
_RESULTADO_DES = "des"
_RESULTADO_OUTROS = "outros"

# ``public.status_primeiro_grau`` (LexFlow) — IDs usados na fase Recursal (globais, válidos para NG e LA)
_ID_1G_ACORDO_HOMOLOGADO = 17              # ACORDO HOMOLOGADO
_ID_1G_EXTINTO_SEM_MERITO = 18             # EXTINTO SEM MÉRITO
_ID_1G_IMPROCEDENTE = 19                   # IMPROCEDENTE
_ID_1G_PROCEDENTE_COM_PE = 20              # PROCEDENTE COM PROVEITO ECONÔMICO
_ID_1G_PARC_PROCEDENTE_COM_PE = 21         # PARCIALMENTE PROCEDENTE COM PROVEITO ECONÔMICO
_ID_1G_PROCEDENTE_SEM_PE = 22              # PROCEDENTE SEM PROVEITO ECONÔMICO
_ID_1G_PARC_PROCEDENTE_SEM_PE = 23         # PARCIALMENTE PROCEDENTE SEM PROVEITO ECONÔMICO
# Aliases legados (compatibilidade interna)
_ID_1G_SENTENCA_FAVORAVEL = _ID_1G_PROCEDENTE_SEM_PE
_ID_1G_SENTENCA_DESFAVORAVEL = _ID_1G_IMPROCEDENTE
_ID_1G_PROCEDENTE = _ID_1G_PROCEDENTE_COM_PE
_ID_1G_PARCIALMENTE_PROCEDENTE = _ID_1G_PARC_PROCEDENTE_COM_PE
_ID_1G_SENTENCA_EXTINCAO = _ID_1G_EXTINTO_SEM_MERITO
_ID_1G_SENTENCA_PARCIALMENTE_FAVORAVEL = _ID_1G_PARC_PROCEDENTE_SEM_PE

# Ordem de exibição nos gráficos (somente status com volume na recursal)
_STATUS_1G_RECURSAL_NG: tuple[tuple[int, str], ...] = (
    (_ID_1G_IMPROCEDENTE, "IMPROCEDENTE"),
    (_ID_1G_PROCEDENTE_COM_PE, "PROCEDENTE COM PROVEITO ECONÔMICO"),
    (_ID_1G_EXTINTO_SEM_MERITO, "EXTINTO SEM MÉRITO"),
    (_ID_1G_PROCEDENTE_SEM_PE, "PROCEDENTE SEM PROVEITO ECONÔMICO"),
    (_ID_1G_PARC_PROCEDENTE_COM_PE, "PARCIALMENTE PROCEDENTE COM PROVEITO ECONÔMICO"),
    (_ID_1G_PARC_PROCEDENTE_SEM_PE, "PARCIALMENTE PROCEDENTE SEM PROVEITO ECONÔMICO"),
    (_ID_1G_ACORDO_HOMOLOGADO, "ACORDO HOMOLOGADO"),
)

# ``public.status_segundo_grau`` (LexFlow) — IDs usados na fase Recursal (globais, válidos para NG e LA)
_ID_2G_ACORDO_HOMOLOGADO = 17              # ACORDO HOMOLOGADO
_ID_2G_EXTINTO_SEM_MERITO = 18             # EXTINTO SEM MÉRITO
_ID_2G_IMPROCEDENTE = 19                   # IMPROCEDENTE
_ID_2G_PARC_PROCEDENTE_COM_PE = 20         # PARCIALMENTE PROCEDENTE (COM PROVEITO ECONÔMICO)
_ID_2G_PROCEDENTE_COM_PE = 21               # PROCEDENTE (COM PROVEITO ECONÔMICO)
_ID_2G_SENTENCA_ANULADA = 22               # SENTENÇA ANULADA
_ID_2G_ENCERRADO_1G = 23                   # ENCERRADO 1G
_ID_2G_PROCEDENTE_SEM_PE = 24              # PROCEDENTE SEM PROVEITO ECONÔMICO
_ID_2G_PARC_PROCEDENTE_SEM_PE = 25         # PARCIALMENTE PROCEDENTE SEM PROVEITO ECONÔMICO
# Aliases legados (compatibilidade interna)
_ID_2G_ACORDAO_DESFAVORAVEL = _ID_2G_IMPROCEDENTE
_ID_2G_ACORDAO_FAVORAVEL = _ID_2G_PROCEDENTE_SEM_PE
_ID_2G_ACORDAO_PARCIALMENTE_FAVORAVEL = _ID_2G_PARC_PROCEDENTE_SEM_PE
_ID_2G_ACORDAO_PARCIAL_RETOMADA_INSTRUCAO = _ID_2G_SENTENCA_ANULADA
_ID_2G_ACORDAO_EXTINCAO = _ID_2G_EXTINTO_SEM_MERITO
_ID_2G_SENTENCA_ANULADA_NOVA = _ID_2G_SENTENCA_ANULADA
_ID_2G_PROCEDENTE_COM_PE_NOVO = _ID_2G_PROCEDENTE_COM_PE
_ID_2G_PARC_PROCEDENTE_COM_PE_NOVO = _ID_2G_PARC_PROCEDENTE_COM_PE
_ID_2G_PROCEDENTE_SEM_PE_NOVO = _ID_2G_PROCEDENTE_SEM_PE
_ID_2G_PARC_PROCEDENTE_SEM_PE_NOVO = _ID_2G_PARC_PROCEDENTE_SEM_PE
_ID_2G_IMPROCEDENTE_NOVO = _ID_2G_IMPROCEDENTE

_STATUS_2G_RECURSAL_NG: tuple[tuple[int, str], ...] = (
    (_ID_2G_IMPROCEDENTE, "IMPROCEDENTE"),
    (_ID_2G_PROCEDENTE_SEM_PE, "PROCEDENTE SEM PROVEITO ECONÔMICO"),
    (_ID_2G_PARC_PROCEDENTE_SEM_PE, "PARCIALMENTE PROCEDENTE SEM PROVEITO ECONÔMICO"),
    (_ID_2G_SENTENCA_ANULADA, "SENTENÇA ANULADA"),
    (_ID_2G_EXTINTO_SEM_MERITO, "EXTINTO SEM MÉRITO"),
    (_ID_2G_PARC_PROCEDENTE_COM_PE, "PARCIALMENTE PROCEDENTE (COM PROVEITO ECONÔMICO)"),
    (_ID_2G_PROCEDENTE_COM_PE, "PROCEDENTE (COM PROVEITO ECONÔMICO)"),
    (_ID_2G_ENCERRADO_1G, "ENCERRADO 1G"),
    (_ID_2G_ACORDO_HOMOLOGADO, "ACORDO HOMOLOGADO"),
)

# =============================================================================
# Grupos semânticos 1G × 2G — Matriz de Classificação (Resultado 1G × 2G)
# =============================================================================

# Linha 1G → categoria
_IDS_1G_PROCEDENTE_COM_PE = frozenset({
    _ID_1G_PROCEDENTE_COM_PE,  # ID 20
})
_IDS_1G_PROCEDENTE_SEM_PE = frozenset({
    _ID_1G_PROCEDENTE_SEM_PE,  # ID 22
})
_IDS_1G_PARC_PROCEDENTE_COM_PE = frozenset({
    _ID_1G_PARC_PROCEDENTE_COM_PE,  # ID 21
})
_IDS_1G_PARC_PROCEDENTE_SEM_PE = frozenset({
    _ID_1G_PARC_PROCEDENTE_SEM_PE,  # ID 23
})
_IDS_1G_IMPROCEDENTE_DECISAO = frozenset({
    _ID_1G_IMPROCEDENTE,  # ID 19
})
_IDS_1G_EXTINTO_DECISAO = frozenset({
    _ID_1G_EXTINTO_SEM_MERITO,  # ID 18
})
_IDS_1G_ACORDO_DECISAO = frozenset({
    _ID_1G_ACORDO_HOMOLOGADO,  # ID 17
})

# Coluna 2G → categoria
_IDS_2G_PROCEDENTE_COM_PE = frozenset({
    _ID_2G_PROCEDENTE_COM_PE,  # ID 21
})
_IDS_2G_PROCEDENTE_SEM_PE = frozenset({
    _ID_2G_PROCEDENTE_SEM_PE,  # ID 24
})
_IDS_2G_PARC_PROCEDENTE_COM_PE = frozenset({
    _ID_2G_PARC_PROCEDENTE_COM_PE,  # ID 20
})
_IDS_2G_PARC_PROCEDENTE_SEM_PE = frozenset({
    _ID_2G_PARC_PROCEDENTE_SEM_PE,  # ID 25
})
_IDS_2G_IMPROCEDENTE_DECISAO = frozenset({
    _ID_2G_IMPROCEDENTE,  # ID 19
})
_IDS_2G_EXTINCAO_SEM_MERITO = frozenset({
    _ID_2G_EXTINTO_SEM_MERITO,  # ID 18
})
_IDS_2G_SENTENCA_ANULADA = frozenset({
    _ID_2G_SENTENCA_ANULADA,  # ID 22
})

# Cruzamento 1G × 2G — "Resultado Mapeado" (Matriz de Julgamento, ver
# ``app.analyses.common.matriz_julgamento``). Os 10 tipos antigos (com a
# distinção COM/SEM PE embutida no nome do bucket, "Acordo Homologado" e
# "Extinção Mantida (Reajuizar)") foram substituídos pelos 8 buckets da nova
# matriz de mérito — a distinção de PE agora é um atributo à parte
# (``efeito_pe`` na planilha, não modelado aqui) e Acordo virou um eixo
# próprio, fora de escopo desta migração (ver plano de 2026-09-15).
DECISAO_MANTIDO_GANHO = mj.BUCKET_MANTIDO_GANHO
DECISAO_GANHO_AMPLIADO = mj.BUCKET_GANHO_AMPLIADO
DECISAO_REVERTIDO_GANHO = mj.BUCKET_REVERTIDO_GANHO
DECISAO_GANHO_REDUZIDO = mj.BUCKET_GANHO_REDUZIDO
DECISAO_EXTINCAO_REAJUIZAR = mj.BUCKET_EXTINCAO_PERMITE_REAJUIZAR
DECISAO_INSTRUCAO_RETOMADA = mj.BUCKET_INSTRUCAO_RETOMADA
DECISAO_MANTIDO_PERDA = mj.BUCKET_MANTIDO_PERDA
DECISAO_REVERTIDO_PERDA = mj.BUCKET_REVERTIDO_PERDA

_LABEL_DECISAO_RECURSAL: dict[str, str] = {
    DECISAO_MANTIDO_GANHO: "Mantido Ganho",
    DECISAO_GANHO_AMPLIADO: "Ganho Ampliado",
    DECISAO_REVERTIDO_GANHO: "Revertido Ganho",
    DECISAO_GANHO_REDUZIDO: "Ganho Reduzido",
    DECISAO_EXTINCAO_REAJUIZAR: "Extinção (Permite Reajuizar)",
    DECISAO_INSTRUCAO_RETOMADA: "Instrução Retomada",
    DECISAO_MANTIDO_PERDA: "Mantido Perda",
    DECISAO_REVERTIDO_PERDA: "Revertido Perda",
}

_EXTINTOS_2G_FILTRO_VALIDOS = frozenset({"com_merito", "sem_merito"})
_LABEL_EXTINTO_2G: dict[str, str] = {
    "com_merito": "Extintos com mérito (2º grau)",
    "sem_merito": "Extintos sem mérito (2º grau)",
}

_DECISOES_RECURSAL_ORDEM: tuple[str, ...] = (
    DECISAO_MANTIDO_GANHO,
    DECISAO_GANHO_AMPLIADO,
    DECISAO_REVERTIDO_GANHO,
    DECISAO_GANHO_REDUZIDO,
    DECISAO_MANTIDO_PERDA,
    DECISAO_REVERTIDO_PERDA,
    DECISAO_EXTINCAO_REAJUIZAR,
    DECISAO_INSTRUCAO_RETOMADA,
)

# Grupos legados (mantidos para compatibilidade com funções de ranking/resultado)
_IDS_1G_FAVORAVEL = _IDS_1G_PROCEDENTE_COM_PE | _IDS_1G_PROCEDENTE_SEM_PE | _IDS_1G_PARC_PROCEDENTE_COM_PE | _IDS_1G_PARC_PROCEDENTE_SEM_PE
_IDS_1G_DESFAVORAVEL = _IDS_1G_IMPROCEDENTE_DECISAO
_IDS_1G_OUTROS = _IDS_1G_EXTINTO_DECISAO
_IDS_2G_FAVORAVEL = _IDS_2G_PROCEDENTE_COM_PE | _IDS_2G_PROCEDENTE_SEM_PE | _IDS_2G_PARC_PROCEDENTE_COM_PE | _IDS_2G_PARC_PROCEDENTE_SEM_PE
_IDS_2G_DESFAVORAVEL = _IDS_2G_IMPROCEDENTE_DECISAO
_IDS_2G_OUTROS = _IDS_2G_EXTINCAO_SEM_MERITO


# =============================================================================
# Helpers internos
# =============================================================================

def _converter_valor(valor: Any) -> float:
    if valor is None:
        return 0.0
    try:
        if isinstance(valor, Decimal):
            return float(valor)
        if isinstance(valor, (int, float)):
            return float(valor)
        if isinstance(valor, str):
            limpo = valor.strip().replace(",", ".")
            limpo = "".join(c for c in limpo if c.isdigit() or c == ".")
            return float(limpo) if limpo else 0.0
        return float(str(valor).replace(",", "."))
    except (ValueError, TypeError, AttributeError):
        return 0.0


def _get_valor_causa_acordo(item: dict[str, Any]) -> float:
    raw = item.get(COL_VALOR_CAUSA_ACORDO) or item.get(COL_VALOR_CAUSA_ACORDO.lower())
    return _converter_valor(raw)


def _get_valor_causa_sentenca(item: dict[str, Any]) -> float:
    raw = item.get(COL_VALOR_CAUSA_SENTENCA) or item.get(COL_VALOR_CAUSA_SENTENCA.lower())
    return _converter_valor(raw)


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


def _base_recurso_NG(recurso: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Base padrão das análises Recursal NG: ``ID_ESCRITORIO`` == 20."""
    return [
        item
        for item in recurso
        if _to_int(item.get(_COL_ID_ESCRITORIO) or item.get("id_escritorio"))
        == ID_ESCRITORIO
    ]


def _processo_fase_recursal(item: dict[str, Any]) -> bool:
    id_fase = item.get(_COL_ID_FASE) or item.get("id_fase")
    return _to_int(id_fase) == ID_FASE_RECURSAL


def _get_id_atividade_recursos(item: dict[str, Any]) -> int | None:
    return _to_int(
        item.get(_COL_ID_ATIVIDADE_RECURSOS) or item.get("id_atividade_recursos")
    )


def _get_nome_atividade_recursos(item: dict[str, Any]) -> str | None:
    raw = item.get(_COL_ATIVIDADE_RECURSOS) or item.get("atividade_recursos")
    if raw is None or not str(raw).strip():
        return None
    return str(raw).strip()


def _status_agendamento_recursos(item: dict[str, Any]) -> str | None:
    raw = item.get(_COL_STATUS_AGENDAMENTO_RECURSOS) or item.get(
        "status_agendamento_recursos"
    )
    if raw is None or not str(raw).strip():
        return None
    return str(raw).strip()


def _atividade_recursos_catalogo_valida(item: dict[str, Any]) -> bool:
    """
    Valida agendamento aberto do setor RECURSOS (quando presente na linha).

    Processos sem agendamento aberto no setor (colunas nulas) permanecem no estoque
    da fase Recursal; com agendamento, só entram atividades do catálogo
    ``_ATIVIDADES_RECURSOS_NG``.
    """
    id_ativ = _get_id_atividade_recursos(item)
    if id_ativ is None:
        return True
    status = _status_agendamento_recursos(item)
    if status is not None and status not in _STATUS_AGENDAMENTO_ABERTO_RECURSOS:
        return True
    return id_ativ in _IDS_ATIVIDADE_RECURSOS_NG


def _rotulo_atividade_recursos_NG(item: dict[str, Any]) -> str:
    nome = _get_nome_atividade_recursos(item)
    if nome and nome in _NOMES_ATIVIDADE_RECURSOS_NG:
        return nome
    return _SEM_ATIVIDADE_RECURSOS


def _filtrar_recursos_NG(recurso: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Base das análises Recursal NG: escritório 20, fase 8 e escopo do setor RECURSOS.

    O filtro de atividades do setor é aplicado aqui (não na query SQL).
    """
    return [
        item
        for item in _base_recurso_NG(recurso)
        if _processo_fase_recursal(item) and _atividade_recursos_catalogo_valida(item)
    ]


def _get_dt_entrada_recursal(item: dict[str, Any]) -> Optional[date]:
    raw = item.get(COL_DT_ENTRADA_RECURSAL) or item.get(COL_DT_ENTRADA_RECURSAL.lower())
    return _to_date(raw)


def _get_data_sentenca(item: dict[str, Any]) -> Optional[date]:
    raw = item.get(_COL_DATA_SENTENCA) or item.get(_COL_DATA_SENTENCA.lower())
    return _to_date(raw)


def _get_data_acordao(item: dict[str, Any]) -> Optional[date]:
    raw = item.get(_COL_DATA_ACORDAO) or item.get(_COL_DATA_ACORDAO.lower())
    return _to_date(raw)


def _get_data_acordao_embargos(item: dict[str, Any]) -> Optional[date]:
    raw = item.get(_COL_DATA_ACORDAO_EMBARGOS) or item.get(_COL_DATA_ACORDAO_EMBARGOS.lower())
    return _to_date(raw)


def _get_data_acordao_provimento_mensal(item: dict[str, Any]) -> Optional[date]:
    """
    Data de referência para a Meta de Provimento Mensal: prioriza o acórdão dos
    embargos de declaração (``acordao_embargos``) quando existir, já que é ele
    que define a procedência final — o acórdão original (``acordao_data``) só é
    usado quando não há embargos.
    """
    return _get_data_acordao_embargos(item) or _get_data_acordao(item)


def _valor_coluna_preenchido(val: Any) -> bool:
    if val is None:
        return False
    if isinstance(val, str):
        return bool(val.strip())
    return True


def _col_recursal_ng(row: dict[str, Any], *nomes: str) -> Any:
    """Lê coluna do dataset tentando variações de chave (maiúsc./minúsc.)."""
    for nome in nomes:
        if nome in row:
            val = row[nome]
            if _valor_coluna_preenchido(val):
                return val
        lower = nome.lower()
        if lower in row:
            val = row[lower]
            if _valor_coluna_preenchido(val):
                return val
        upper = nome.upper()
        if upper in row:
            val = row[upper]
            if _valor_coluna_preenchido(val):
                return val
    return None


def _get_numero_processo_recursal_ng(row: dict[str, Any]) -> str:
    raw = _col_recursal_ng(
        row,
        _COL_NUMERO_PROCESSO,
        "numero_processo",
        "Numero_Processo",
    )
    if raw is None:
        return ""
    return str(raw).strip()


def _mesclar_item_processo_recursal_ng(
    base: dict[str, Any],
    novo: dict[str, Any],
) -> dict[str, Any]:
    """Une linhas duplicadas do mesmo processo, preservando valores não vazios."""
    merged = dict(base)
    for chave, valor in novo.items():
        if not _valor_coluna_preenchido(valor):
            continue
        atual = merged.get(chave)
        if not _valor_coluna_preenchido(atual):
            merged[chave] = valor
    return merged


def _chave_processo_recursal_ng(item: dict[str, Any]) -> Any | None:
    pid = _get_recurso_processo_id(item)
    if pid is not None:
        return pid
    numero = _get_numero_processo_recursal_ng(item)
    return numero or None


def _deduplicar_por_processo(itens: list[dict[str, Any]]) -> list[dict[str, Any]]:
    por_chave: dict[Any, dict[str, Any]] = {}
    ordem: list[Any] = []
    sem_chave: list[dict[str, Any]] = []

    for item in itens:
        chave = _chave_processo_recursal_ng(item)
        if chave is None:
            sem_chave.append(item)
            continue
        if chave in por_chave:
            por_chave[chave] = _mesclar_item_processo_recursal_ng(por_chave[chave], item)
        else:
            por_chave[chave] = dict(item)
            ordem.append(chave)

    return [por_chave[chave] for chave in ordem] + sem_chave


def _enriquecer_numero_processo_export_ng(
    itens: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Garante NUMERO_PROCESSO preenchido quando alguma linha duplicada do mesmo
    processo trouxe o valor em chave alternativa.
    """
    numero_por_id: dict[int, str] = {}
    for item in itens:
        pid = _get_recurso_processo_id(item)
        numero = _get_numero_processo_recursal_ng(item)
        if pid is not None and numero:
            numero_por_id[pid] = numero

    enriquecidos: list[dict[str, Any]] = []
    for item in itens:
        row = dict(item)
        numero = _get_numero_processo_recursal_ng(row)
        if not numero:
            pid = _get_recurso_processo_id(row)
            if pid is not None and pid in numero_por_id:
                row[_COL_NUMERO_PROCESSO] = numero_por_id[pid]
        elif _COL_NUMERO_PROCESSO not in row or not _valor_coluna_preenchido(
            row.get(_COL_NUMERO_PROCESSO)
        ):
            row[_COL_NUMERO_PROCESSO] = numero
        enriquecidos.append(row)
    return enriquecidos


def _filtrar_fase_recursal(recurso: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Escritório NG, fase Recursal (``ID_FASE`` = 8) e filtro de atividades do setor RECURSOS."""
    return _filtrar_recursos_NG(recurso)


def _filtrar_entrada_recursal_no_periodo(
    recurso: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """``ID_FASE`` = 8, atividades do setor RECURSOS e ``DT_ENTRADA_RECURSAL`` no período."""
    filtrados: list[dict[str, Any]] = []
    for item in _filtrar_recursos_NG(recurso):
        dt_entrada = _get_dt_entrada_recursal(item)
        if not _data_no_periodo(dt_entrada, from_date, to_date):
            continue
        filtrados.append(item)
    return _deduplicar_por_processo(filtrados)


# =============================================================================
# Totais
# =============================================================================

def get_total_recurso_NG(recurso: list[dict[str, Any]]) -> int:
    """Total na fase Recursal (``ID_FASE`` = 8), independente de data."""
    return len(_deduplicar_por_processo(_filtrar_fase_recursal(recurso)))


def _rotulo_subfase_recursal_NG(item: dict[str, Any]) -> str:
    raw = item.get(_COL_SUBFASE) or item.get("subfase")
    if raw is None or not str(raw).strip():
        return _SEM_SUBFASE
    return str(raw).strip().upper()


def _rotulo_fase_recursal_NG(item: dict[str, Any]) -> str:
    raw = item.get(_COL_FASE) or item.get("fase")
    if raw is None or not str(raw).strip():
        return "Sem fase"
    return str(raw).strip()


def _rotulo_operacao_recursal_NG(item: dict[str, Any]) -> str:
    raw = item.get(_COL_OPERACAO) or item.get("operacao")
    if raw is None or not str(raw).strip():
        return "Sem operação"
    return str(raw).strip()


def _rotulo_parte_adversa_recursal_NG(item: dict[str, Any]) -> str:
    raw = item.get(_COL_PARTE_ADVERSA) or item.get("parte_adversa")
    if raw is None or not str(raw).strip():
        return "Sem parte adversa"
    return str(raw).strip()


def _normalizar_materia_recursal_NG(raw: Any) -> str:
    """Extrai matéria: parte antes de `` - `` (alinhado a protocolo/execução LA)."""
    if raw is None or not str(raw).strip():
        return _SEM_MATERIA
    s = str(raw).strip()
    if " - " in s:
        s = s.split(" - ", 1)[0].strip()
    return s if s else _SEM_MATERIA


def _rotulo_competencia_recursal_NG(item: dict[str, Any]) -> str:
    raw = item.get(_COL_COMPETENCIA) or item.get("competencia")
    if raw is None or not str(raw).strip():
        return _SEM_COMPETENCIA
    return str(raw).strip()


def _rotulo_vara_recursal_NG(item: dict[str, Any]) -> str:
    """Rótulo para gráficos: ``1º vara``, ``2º vara``, … ou ``Sem vara``."""
    raw = item.get(_COL_VARA) or item.get("vara")
    if raw is None or str(raw).strip() == "":
        return _SEM_VARA
    try:
        numero = int(raw)
        return f"{numero}º vara"
    except (TypeError, ValueError):
        texto = str(raw).strip()
        if texto.lower().startswith("vara "):
            sufixo = texto[5:].strip()
            try:
                return f"{int(sufixo)}º vara"
            except ValueError:
                pass
        return texto


def _processos_recursal_por_base(
    recurso: list[dict[str, Any]],
    *,
    base: str = "estoque",
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Estoque (fase 8) ou entrada no período (`DT_ENTRADA_RECURSAL`)."""
    base_norm = (base or "estoque").strip().lower()
    if base_norm == "entrada":
        return _filtrar_entrada_recursal_no_periodo(
            recurso, from_date=from_date, to_date=to_date
        )
    return _deduplicar_por_processo(_filtrar_fase_recursal(recurso))


def _agrupar_recursal_por_chave(
    processos: list[dict[str, Any]],
    obter_chave: Any,
) -> list[dict[str, Any]]:
    """Agrupa processos por chave; ``percent`` soma 100% sobre ``len(processos)``."""
    grouped: dict[str, dict[str, float]] = defaultdict(
        lambda: {"count": 0.0, "valor_causa": 0.0}
    )
    for item in processos:
        chave = obter_chave(item)
        grouped[chave]["count"] += 1.0
        grouped[chave]["valor_causa"] += _get_valor_causa_acordo(item)

    total = float(len(processos))
    itens: list[dict[str, Any]] = []
    for nome, dados in grouped.items():
        qtd = int(dados["count"])
        itens.append(
            {
                "name": nome,
                "value": float(qtd),
                "valor_causa": round(float(dados["valor_causa"]), 2),
                "percent": round(100.0 * float(qtd) / total, 1) if total > 0 else 0.0,
            }
        )
    return sorted(itens, key=lambda x: float(x["value"]), reverse=True)


def group_recursal_por_subfase_NG(
    recurso: list[dict[str, Any]],
    *,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    base: str = "estoque",
) -> list[dict[str, Any]]:
    """
    Agrupa processos na fase Recursal (``ID_FASE`` = 8) por ``SUBFASE``.

    ``base="estoque"`` (padrão): todo o estoque atual, sem filtro de data.
    ``base="entrada"``: processos cuja ``DT_ENTRADA_RECURSAL`` está no período.

    A soma dos ``value`` coincide com o total da base escolhida; ``percent`` usa
    esse total como denominador (soma = 100%).
    """
    processos = _processos_recursal_por_base(
        recurso, base=base, from_date=from_date, to_date=to_date
    )
    return _agrupar_recursal_por_chave(processos, _rotulo_subfase_recursal_NG)


def group_recursal_por_atividade_NG(
    recurso: list[dict[str, Any]],
    *,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    base: str = "estoque",
) -> list[dict[str, Any]]:
    """
    Agrupa por atividade aberta do setor RECURSOS (``ATIVIDADE_RECURSOS``).

    Processos sem agendamento aberto no setor entram em ``Sem atividade aberta``.
    """
    processos = _processos_recursal_por_base(
        recurso, base=base, from_date=from_date, to_date=to_date
    )
    return _agrupar_recursal_por_chave(processos, _rotulo_atividade_recursos_NG)


def group_recursal_por_materia_NG(
    recurso: list[dict[str, Any]],
    *,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    base: str = "estoque",
) -> list[dict[str, Any]]:
    """Distribuição por matéria na fase Recursal (estoque ou entrada no período)."""
    processos = _processos_recursal_por_base(
        recurso, base=base, from_date=from_date, to_date=to_date
    )
    return _agrupar_recursal_por_chave(
        processos,
        lambda item: _normalizar_materia_recursal_NG(
            item.get(_COL_MATERIA) or item.get("materia")
        ),
    )


def group_recursal_por_competencia_NG(
    recurso: list[dict[str, Any]],
    *,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    base: str = "estoque",
) -> list[dict[str, Any]]:
    """Distribuição por competência na fase Recursal (estoque ou entrada no período)."""
    processos = _processos_recursal_por_base(
        recurso, base=base, from_date=from_date, to_date=to_date
    )
    return _agrupar_recursal_por_chave(processos, _rotulo_competencia_recursal_NG)


def group_recursal_por_vara_NG(
    recurso: list[dict[str, Any]],
    *,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    base: str = "estoque",
) -> list[dict[str, Any]]:
    """Distribuição por vara na fase Recursal (estoque ou entrada no período)."""
    processos = _processos_recursal_por_base(
        recurso, base=base, from_date=from_date, to_date=to_date
    )
    return _agrupar_recursal_por_chave(processos, _rotulo_vara_recursal_NG)


def get_entrada_recurso_NG(
    recurso: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """Processos na fase 8 cuja entrada na recursal (`DT_ENTRADA_RECURSAL`) está no período."""
    return len(_filtrar_entrada_recursal_no_periodo(recurso, from_date, to_date))

# =============================================================================
# Valores monetários
# =============================================================================

def get_valor_causa_acordo_recurso_NG(recurso: list[dict[str, Any]]) -> float:
    """
    Soma de ``VALOR_CAUSA_ACORDO`` dos processos na fase Recursal (``ID_FASE`` = 8).

    Usa a mesma base de ``get_total_recurso_NG`` (escritório NG, sem filtro de data).
    """
    processos = _deduplicar_por_processo(_filtrar_fase_recursal(recurso))
    return round(sum(_get_valor_causa_acordo(p) for p in processos), 2)


# =============================================================================
# Totais por status 1º grau (``ID_1G`` / ``STATUS_1G``)
# =============================================================================

def _filtrar_por_id_status_1g(
    recurso: list[dict[str, Any]],
    id_1g: int,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Fase Recursal (8) + escritório NG + ``ID_1G`` e ``DATA_SENTENCA`` no período."""
    filtrados: list[dict[str, Any]] = []
    for item in _filtrar_fase_recursal(recurso):
        if _to_int(item.get(_COL_ID_1G) or item.get("id_status_grau1")) == id_1g:
            if not _data_no_periodo(_get_data_sentenca(item), from_date, to_date):
                continue
            filtrados.append(item)
    return _deduplicar_por_processo(filtrados)


def get_total_por_id_status_1g_recurso_NG(
    recurso: list[dict[str, Any]],
    id_1g: int,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """Total na fase Recursal com o ``ID_1G`` informado e ``DATA_SENTENCA`` no período."""
    return len(_filtrar_por_id_status_1g(recurso, id_1g, from_date=from_date, to_date=to_date))


def get_valor_causa_sentenca_por_id_status_1g_recurso_NG(
    recurso: list[dict[str, Any]],
    id_1g: int,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """Soma de ``VALOR_CAUSA_SENTENCA`` na fase Recursal por ``ID_1G`` e ``DATA_SENTENCA`` no período."""
    processos = _filtrar_por_id_status_1g(recurso, id_1g, from_date=from_date, to_date=to_date)
    return round(sum(_get_valor_causa_sentenca(p) for p in processos), 2)


def get_total_sentenca_favoravel_recurso_NG(
    recurso: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """``ID_1G`` = 4 — SENTENÇA FAVORÁVEL."""
    return get_total_por_id_status_1g_recurso_NG(
        recurso, _ID_1G_SENTENCA_FAVORAVEL, from_date=from_date, to_date=to_date
    )


def get_valor_causa_sentenca_sentenca_favoravel_recurso_NG(
    recurso: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """Soma ``VALOR_CAUSA_SENTENCA`` com ``ID_1G`` = 4 — SENTENÇA FAVORÁVEL."""
    return get_valor_causa_sentenca_por_id_status_1g_recurso_NG(
        recurso, _ID_1G_SENTENCA_FAVORAVEL, from_date=from_date, to_date=to_date
    )


def get_total_sentenca_desfavoravel_recurso_NG(
    recurso: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """``ID_1G`` = 5 — SENTENÇA DESFAVORÁVEL."""
    return get_total_por_id_status_1g_recurso_NG(
        recurso, _ID_1G_SENTENCA_DESFAVORAVEL, from_date=from_date, to_date=to_date
    )


def get_valor_causa_sentenca_sentenca_desfavoravel_recurso_NG(
    recurso: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    return get_valor_causa_sentenca_por_id_status_1g_recurso_NG(
        recurso, _ID_1G_SENTENCA_DESFAVORAVEL, from_date=from_date, to_date=to_date
    )


def get_total_procedente_1g_recurso_NG(
    recurso: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """``ID_1G`` = 6 — PROCEDENTE."""
    return get_total_por_id_status_1g_recurso_NG(
        recurso, _ID_1G_PROCEDENTE, from_date=from_date, to_date=to_date
    )


def get_valor_causa_sentenca_procedente_1g_recurso_NG(
    recurso: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    return get_valor_causa_sentenca_por_id_status_1g_recurso_NG(
        recurso, _ID_1G_PROCEDENTE, from_date=from_date, to_date=to_date
    )


def get_total_parcialmente_procedente_recurso_NG(
    recurso: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """``ID_1G`` = 7 — PARCIALMENTE PROCEDENTE."""
    return get_total_por_id_status_1g_recurso_NG(
        recurso, _ID_1G_PARCIALMENTE_PROCEDENTE, from_date=from_date, to_date=to_date
    )


def get_valor_causa_sentenca_parcialmente_procedente_recurso_NG(
    recurso: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    return get_valor_causa_sentenca_por_id_status_1g_recurso_NG(
        recurso, _ID_1G_PARCIALMENTE_PROCEDENTE, from_date=from_date, to_date=to_date
    )


def get_total_sentenca_extincao_recurso_NG(
    recurso: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """``ID_1G`` = 8 — SENTENÇA DE EXTINÇÃO."""
    return get_total_por_id_status_1g_recurso_NG(
        recurso, _ID_1G_SENTENCA_EXTINCAO, from_date=from_date, to_date=to_date
    )


def get_valor_causa_sentenca_sentenca_extincao_recurso_NG(
    recurso: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    return get_valor_causa_sentenca_por_id_status_1g_recurso_NG(
        recurso, _ID_1G_SENTENCA_EXTINCAO, from_date=from_date, to_date=to_date
    )


def get_total_sentenca_parcialmente_favoravel_recurso_NG(
    recurso: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """``ID_1G`` = 9 — SENTENÇA PARCIALMENTE FAVORÁVEL."""
    return get_total_por_id_status_1g_recurso_NG(
        recurso, _ID_1G_SENTENCA_PARCIALMENTE_FAVORAVEL, from_date=from_date, to_date=to_date
    )


def get_valor_causa_sentenca_parcialmente_favoravel_recurso_NG(
    recurso: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    return get_valor_causa_sentenca_por_id_status_1g_recurso_NG(
        recurso, _ID_1G_SENTENCA_PARCIALMENTE_FAVORAVEL, from_date=from_date, to_date=to_date
    )


def group_recursal_por_status_1g_NG(
    recurso: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Lista ``{name, value, valor_causa}`` por status 1G filtrando por ``DATA_SENTENCA``."""
    itens: list[dict[str, Any]] = []
    for id_1g, label in _STATUS_1G_RECURSAL_NG:
        total = get_total_por_id_status_1g_recurso_NG(
            recurso, id_1g, from_date=from_date, to_date=to_date
        )
        if total > 0:
            itens.append(
                {
                    "name": label,
                    "value": total,
                    "valor_causa": get_valor_causa_sentenca_por_id_status_1g_recurso_NG(
                        recurso, id_1g, from_date=from_date, to_date=to_date
                    ),
                    "id_1g": id_1g,
                }
            )
    return sorted(itens, key=lambda x: float(x["value"]), reverse=True)


# =============================================================================
# Totais por status 2º grau (``ID_2G`` / ``STATUS_2G``)
# =============================================================================

def _filtrar_por_id_status_2g(
    recurso: list[dict[str, Any]],
    id_2g: int,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Fase Recursal (8) + escritório NG + ``ID_2G`` e ``DATA_ACORDAO`` no período."""
    filtrados: list[dict[str, Any]] = []
    for item in _filtrar_fase_recursal(recurso):
        if _to_int(item.get(_COL_ID_2G) or item.get("id_status_grau2")) == id_2g:
            if not _data_no_periodo(_get_data_acordao(item), from_date, to_date):
                continue
            filtrados.append(item)
    return _deduplicar_por_processo(filtrados)


def get_total_por_id_status_2g_recurso_NG(
    recurso: list[dict[str, Any]],
    id_2g: int,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """Total na fase Recursal com o ``ID_2G`` informado e ``DATA_ACORDAO`` no período."""
    return len(_filtrar_por_id_status_2g(recurso, id_2g, from_date=from_date, to_date=to_date))


def get_valor_causa_por_id_status_2g_recurso_NG(
    recurso: list[dict[str, Any]],
    id_2g: int,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """Soma de ``VALOR_CAUSA_SENTENCA`` na fase Recursal por ``ID_2G`` e ``DATA_ACORDAO`` no período."""
    processos = _filtrar_por_id_status_2g(recurso, id_2g, from_date=from_date, to_date=to_date)
    return round(sum(_get_valor_causa_sentenca(p) for p in processos), 2)


def get_total_acordao_desfavoravel_recurso_NG(
    recurso: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """``ID_2G`` = 4 — ACÓRDÃO DESFAVORÁVEL."""
    return get_total_por_id_status_2g_recurso_NG(
        recurso, _ID_2G_ACORDAO_DESFAVORAVEL, from_date=from_date, to_date=to_date
    )


def get_valor_causa_acordao_desfavoravel_recurso_NG(
    recurso: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    return get_valor_causa_por_id_status_2g_recurso_NG(
        recurso, _ID_2G_ACORDAO_DESFAVORAVEL, from_date=from_date, to_date=to_date
    )


def get_total_acordao_favoravel_recurso_NG(
    recurso: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """``ID_2G`` = 5 — ACÓRDÃO FAVORÁVEL."""
    return get_total_por_id_status_2g_recurso_NG(
        recurso, _ID_2G_ACORDAO_FAVORAVEL, from_date=from_date, to_date=to_date
    )


def get_valor_causa_acordao_favoravel_recurso_NG(
    recurso: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    return get_valor_causa_por_id_status_2g_recurso_NG(
        recurso, _ID_2G_ACORDAO_FAVORAVEL, from_date=from_date, to_date=to_date
    )


def get_total_acordao_parcialmente_favoravel_recurso_NG(
    recurso: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """``ID_2G`` = 6 — ACÓRDÃO PARCIALMENTE FAVORÁVEL."""
    return get_total_por_id_status_2g_recurso_NG(
        recurso, _ID_2G_ACORDAO_PARCIALMENTE_FAVORAVEL, from_date=from_date, to_date=to_date
    )


def get_valor_causa_acordao_parcialmente_favoravel_recurso_NG(
    recurso: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    return get_valor_causa_por_id_status_2g_recurso_NG(
        recurso, _ID_2G_ACORDAO_PARCIALMENTE_FAVORAVEL, from_date=from_date, to_date=to_date
    )


def get_total_acordao_parcial_retomada_recurso_NG(
    recurso: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """``ID_2G`` = 7 — ACÓRDÃO PARCIAL (RETOMADA DA INSTRUÇÃO)."""
    return get_total_por_id_status_2g_recurso_NG(
        recurso, _ID_2G_ACORDAO_PARCIAL_RETOMADA_INSTRUCAO, from_date=from_date, to_date=to_date
    )


def get_valor_causa_acordao_parcial_retomada_recurso_NG(
    recurso: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    return get_valor_causa_por_id_status_2g_recurso_NG(
        recurso, _ID_2G_ACORDAO_PARCIAL_RETOMADA_INSTRUCAO, from_date=from_date, to_date=to_date
    )


def get_total_acordao_extincao_recurso_NG(
    recurso: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """``ID_2G`` = 8 — ACÓRDÃO DE EXTINÇÃO."""
    return get_total_por_id_status_2g_recurso_NG(
        recurso, _ID_2G_ACORDAO_EXTINCAO, from_date=from_date, to_date=to_date
    )


def get_valor_causa_acordao_extincao_recurso_NG(
    recurso: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    return get_valor_causa_por_id_status_2g_recurso_NG(
        recurso, _ID_2G_ACORDAO_EXTINCAO, from_date=from_date, to_date=to_date
    )



# =============================================================================
# Meta de Provimento Mensal (NG) — 80 processos providos/mês
# =============================================================================
#
# Conta processos com ``ID_2G`` em: Procedente (COM PE), Parc. Procedente (COM PE),
# Sentença Anulada (ambos os IDs legado/novo) e Procedente Sem Proveito Econômico —
# filtrado por ``DATA_ACORDAO`` no período, mesma base de ``group_recursal_por_status_2g_NG``.

META_PROVIMENTO_MENSAL_NG = 80

_IDS_2G_PROVIMENTO_MENSAL_NG = frozenset({
    _ID_2G_PROCEDENTE_COM_PE,       # ID 21 — Procedente (COM PE)
    _ID_2G_PARC_PROCEDENTE_COM_PE,  # ID 20 — Parc. Procedente (COM PE)
    _ID_2G_SENTENCA_ANULADA,       # ID 22 — Sentença Anulada
    _ID_2G_PROCEDENTE_SEM_PE,       # ID 24 — Procedente Sem Proveito Econômico
})


def get_total_provimento_mensal_NG(
    recurso: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """
    Total de processos providos (para a Meta de Provimento Mensal) no período.

    Data de referência: ``DATA_ACORDAO_EMBARGOS`` quando o processo teve embargos
    de declaração (é o acórdão dos embargos que define a procedência final),
    caindo para ``DATA_ACORDAO`` quando não houve embargos.
    """
    filtrados: list[dict[str, Any]] = []
    for item in _filtrar_fase_recursal(recurso):
        id_2g = _to_int(item.get(_COL_ID_2G) or item.get("id_status_grau2"))
        if id_2g not in _IDS_2G_PROVIMENTO_MENSAL_NG:
            continue
        if not _data_no_periodo(_get_data_acordao_provimento_mensal(item), from_date, to_date):
            continue
        filtrados.append(item)
    return len(_deduplicar_por_processo(filtrados))


def group_recursal_por_status_2g_NG(
    recurso: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Lista ``{name, value, valor_causa}`` por status 2G filtrando por ``DATA_ACORDAO``."""
    itens: list[dict[str, Any]] = []
    for id_2g, label in _STATUS_2G_RECURSAL_NG:
        total = get_total_por_id_status_2g_recurso_NG(
            recurso, id_2g, from_date=from_date, to_date=to_date
        )
        if total > 0:
            itens.append(
                {
                    "name": label,
                    "value": total,
                    "valor_causa": get_valor_causa_por_id_status_2g_recurso_NG(
                        recurso, id_2g, from_date=from_date, to_date=to_date
                    ),
                    "id_2g": id_2g,
                }
            )
    return sorted(itens, key=lambda x: float(x["value"]), reverse=True)


# =============================================================================
# Análise de decisões (cruzamento 1G × 2G)
# =============================================================================

def _classificar_decisao_recursal(
    id_merito_1g: Optional[int],
    id_merito_2g: Optional[int],
) -> str | None:
    """Classifica o resultado recursal via Matriz de Julgamento (mérito 1G × 2G)."""
    resultado = mj.classificar_resultado_merito(id_merito_1g, id_merito_2g)
    return resultado.bucket if resultado else None


def _get_id_1g(item: dict[str, Any]) -> int | None:
    return _to_int(item.get(_COL_ID_1G) or item.get("id_status_grau1"))


def _get_id_2g(item: dict[str, Any]) -> int | None:
    return _to_int(item.get(_COL_ID_2G) or item.get("id_status_grau2"))


def _get_id_merito_1g(item: dict[str, Any]) -> Optional[int]:
    """ID de mérito 1G: usa a coluna nova quando presente, senão traduz o status antigo."""
    novo = _to_int(item.get("ID_SENTENCA_MERITO_1G") or item.get("id_sentenca_merito_grau1"))
    status_antigo = item.get(_COL_STATUS_1G) or item.get("status_1g")
    return mj.resolver_id_merito_1g(novo, status_antigo)


def _get_id_merito_2g(item: dict[str, Any]) -> Optional[int]:
    """ID de mérito 2G: usa a coluna nova quando presente, senão traduz o status antigo."""
    novo = _to_int(item.get("ID_ACORDAO_MERITO_2G") or item.get("id_acordao_merito_grau2"))
    status_antigo = item.get(_COL_STATUS_2G) or item.get("status_2g")
    return mj.resolver_id_merito_2g(novo, status_antigo)


def rotulo_decisao_recursal_export_NG(item: dict[str, Any]) -> str:
    """Rótulo legível da decisão recursal (Matriz de Julgamento, mérito 1G × 2G) para exportação."""
    id_1g = _get_id_merito_1g(item)
    id_2g = _get_id_merito_2g(item)
    if id_1g is None or id_2g is None:
        return ""
    tipo = _classificar_decisao_recursal(id_1g, id_2g)
    if tipo is None:
        return ""
    return _LABEL_DECISAO_RECURSAL.get(tipo, tipo)


def _filtrar_decisoes_recursal(
    recurso: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    tipo_decisao: str | None = None,
) -> list[dict[str, Any]]:
    """
    Processos na fase Recursal com mérito 1G e 2G classificáveis.

    O recorte de período usa ``DATA_ACORDAO`` (data do acórdão). Exige 2G
    presente (não classifica o caso "sem recurso" da Matriz de Julgamento) —
    mesmo comportamento de antes desta migração, para não inflar os cartões
    de Decisões com processos que nunca chegaram a ter acórdão.
    """
    filtrados: list[dict[str, Any]] = []
    for item in _filtrar_fase_recursal(recurso):
        id_1g = _get_id_merito_1g(item)
        id_2g = _get_id_merito_2g(item)
        if id_1g is None or id_2g is None:
            continue
        decisao = _classificar_decisao_recursal(id_1g, id_2g)
        if decisao is None:
            continue
        if tipo_decisao is not None and decisao != tipo_decisao:
            continue
        if not _data_no_periodo(_get_data_acordao(item), from_date, to_date):
            continue
        filtrados.append(item)
    return _deduplicar_por_processo(filtrados)


def get_total_decisoes_recursal_NG(
    recurso: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """Total de processos com decisão recursal classificável no período (``DATA_ACORDAO``)."""
    return len(_filtrar_decisoes_recursal(recurso, from_date=from_date, to_date=to_date))


def get_total_por_tipo_decisao_recursal_NG(
    recurso: list[dict[str, Any]],
    tipo_decisao: str,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    return len(
        _filtrar_decisoes_recursal(
            recurso, from_date=from_date, to_date=to_date, tipo_decisao=tipo_decisao
        )
    )


def get_valor_causa_por_tipo_decisao_recursal_NG(
    recurso: list[dict[str, Any]],
    tipo_decisao: str,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    processos = _filtrar_decisoes_recursal(
        recurso, from_date=from_date, to_date=to_date, tipo_decisao=tipo_decisao
    )
    return round(sum(_get_valor_causa_sentenca(p) for p in processos), 2)


def _percentual_decisao(total_tipo: int, total_decisoes: int) -> float:
    if total_decisoes <= 0:
        return 0.0
    return round((total_tipo / total_decisoes) * 100, 1)


def get_decisoes_recursal_resumo_NG(
    recurso: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> dict[str, Any]:
    """Resumo das decisões: totais, valores e percentuais sobre o total classificado."""
    total = get_total_decisoes_recursal_NG(recurso, from_date=from_date, to_date=to_date)
    itens: list[dict[str, Any]] = []
    for tipo in _DECISOES_RECURSAL_ORDEM:
        qtd = get_total_por_tipo_decisao_recursal_NG(
            recurso, tipo, from_date=from_date, to_date=to_date
        )
        itens.append(
            {
                "tipo": tipo,
                "name": _LABEL_DECISAO_RECURSAL[tipo],
                "value": qtd,
                "valor_causa": get_valor_causa_por_tipo_decisao_recursal_NG(
                    recurso, tipo, from_date=from_date, to_date=to_date
                ),
                "percent": _percentual_decisao(qtd, total),
            }
        )
    return {"total": total, "itens": itens}


def group_decisoes_recursal_NG(
    recurso: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Lista ``{name, value, valor_causa, percent}`` para gráfico de decisões."""
    resumo = get_decisoes_recursal_resumo_NG(recurso, from_date=from_date, to_date=to_date)
    return [x for x in resumo["itens"] if int(x.get("value") or 0) > 0]


# =============================================================================
# Rankings por juiz (1G / sentença) e relator (2G / acórdão)
# =============================================================================

def _normalizar_nome_magistrado(value: Any) -> str:
    nome = str(value or "").strip()
    if not nome or nome.lower() in {"none", "null", "-", "n/a"}:
        return ""
    return nome


def _iniciais_nome(nome: str) -> str:
    partes = [p for p in nome.split() if p]
    if not partes:
        return "—"
    if len(partes) == 1:
        return partes[0][:2].upper()
    return f"{partes[0][0]}{partes[1][0]}".upper()


def _nome_magistrado_coincide(nome: str, filtro: Optional[str]) -> bool:
    if filtro is None:
        return True
    filtro_norm = _normalizar_nome_magistrado(filtro).casefold()
    if not filtro_norm:
        return True
    return nome.casefold() == filtro_norm


def _classificar_resultado_1g(id_1g: int | None) -> str | None:
    if id_1g in _IDS_1G_FAVORAVEL:
        return _RESULTADO_FAV
    if id_1g in _IDS_1G_DESFAVORAVEL:
        return _RESULTADO_DES
    if id_1g in _IDS_1G_OUTROS:
        return _RESULTADO_OUTROS
    return None


def _classificar_resultado_2g(id_2g: int | None) -> str | None:
    if id_2g in _IDS_2G_FAVORAVEL:
        return _RESULTADO_FAV
    if id_2g in _IDS_2G_DESFAVORAVEL:
        return _RESULTADO_DES
    if id_2g in _IDS_2G_OUTROS:
        return _RESULTADO_OUTROS
    return None


def _get_juiz_1g(item: dict[str, Any]) -> str:
    return _normalizar_nome_magistrado(item.get(_COL_JUIZ_1G) or item.get("juiz_1g"))


def _get_relator_2g(item: dict[str, Any]) -> str:
    return _normalizar_nome_magistrado(item.get(_COL_RELATOR_2G) or item.get("relator_2g"))


def filtrar_por_juiz_1g_recurso_NG(
    recurso: list[dict[str, Any]],
    juiz: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Processos na fase Recursal com sentença (1G) classificável.

    Filtro opcional por nome do juiz (``JUIZ_1G``) e período em ``DATA_SENTENCA``.
    """
    filtrados: list[dict[str, Any]] = []
    for item in _filtrar_fase_recursal(recurso):
        nome_juiz = _get_juiz_1g(item)
        if not nome_juiz or not _nome_magistrado_coincide(nome_juiz, juiz):
            continue
        if _classificar_resultado_1g(_get_id_1g(item)) is None:
            continue
        if not _data_no_periodo(_get_data_sentenca(item), from_date, to_date):
            continue
        filtrados.append(item)
    return _deduplicar_por_processo(filtrados)


def filtrar_por_relator_2g_recurso_NG(
    recurso: list[dict[str, Any]],
    relator: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Processos na fase Recursal com acórdão (2G) classificável.

    Filtro opcional por nome do relator (``RELATOR_2G``) e período em ``DATA_ACORDAO``.
    """
    filtrados: list[dict[str, Any]] = []
    for item in _filtrar_fase_recursal(recurso):
        nome_relator = _get_relator_2g(item)
        if not nome_relator or not _nome_magistrado_coincide(nome_relator, relator):
            continue
        if _classificar_resultado_2g(_get_id_2g(item)) is None:
            continue
        if not _data_no_periodo(_get_data_acordao(item), from_date, to_date):
            continue
        filtrados.append(item)
    return _deduplicar_por_processo(filtrados)


def _montar_ranking_magistrado(
    processos: list[dict[str, Any]],
    obter_nome: Any,
    obter_id_status: Any,
    classificar: Any,
) -> list[dict[str, Any]]:
    acc: dict[str, dict[str, Any]] = {}
    for item in processos:
        nome = obter_nome(item)
        if not nome:
            continue
        resultado = classificar(obter_id_status(item))
        if resultado is None:
            continue
        chave = nome.casefold()
        if chave not in acc:
            acc[chave] = {
                "name": nome,
                "fav": 0,
                "des": 0,
                "outros": 0,
            }
        acc[chave][resultado] += 1

    linhas: list[dict[str, Any]] = []
    for row in acc.values():
        fav = int(row["fav"])
        des = int(row["des"])
        outros = int(row["outros"])
        total = fav + des + outros
        if total <= 0:
            continue
        linhas.append(
            {
                "name": row["name"],
                "initials": _iniciais_nome(str(row["name"])),
                "total_casos": total,
                "taxa_sucesso": round((fav / total) * 100, 1),
                "fav": fav,
                "des": des,
                "outros": outros,
                "percent_fav": round((fav / total) * 100, 1),
                "percent_des": round((des / total) * 100, 1),
                "percent_outros": round((outros / total) * 100, 1),
            }
        )

    linhas.sort(
        key=lambda x: (
            -float(x.get("taxa_sucesso") or 0),
            -int(x.get("total_casos") or 0),
            str(x.get("name") or ""),
        )
    )
    return linhas


def get_ranking_juizes_recursal_NG(
    recurso: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    juiz: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Ranking de juízes (1G): taxa de sucesso e distribuição Fav / Des / Outros."""
    processos = filtrar_por_juiz_1g_recurso_NG(
        recurso, juiz=juiz, from_date=from_date, to_date=to_date
    )
    return _montar_ranking_magistrado(
        processos,
        obter_nome=_get_juiz_1g,
        obter_id_status=_get_id_1g,
        classificar=_classificar_resultado_1g,
    )


def get_ranking_relatores_recursal_NG(
    recurso: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    relator: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Ranking de relatores (2G): taxa de sucesso e distribuição Fav / Des / Outros."""
    processos = filtrar_por_relator_2g_recurso_NG(
        recurso, relator=relator, from_date=from_date, to_date=to_date
    )
    return _montar_ranking_magistrado(
        processos,
        obter_nome=_get_relator_2g,
        obter_id_status=_get_id_2g,
        classificar=_classificar_resultado_2g,
    )


# =============================================================================
# Filtros combinados (status 1G/2G, juiz, relator, decisão)
# =============================================================================

@dataclass(frozen=True)
class RecursalLAFiltros:
    """Filtros cumulativos (AND) sobre processos na fase Recursal."""

    id_1g: frozenset[int] | None = None
    id_2g: frozenset[int] | None = None
    juizes: frozenset[str] | None = None
    relatores: frozenset[str] | None = None
    decisoes: frozenset[str] | None = None
    materias: frozenset[str] | None = None
    partes_adversas: frozenset[str] | None = None
    competencias: frozenset[str] | None = None
    varas: frozenset[str] | None = None
    subfases: frozenset[str] | None = None
    fases: frozenset[str] | None = None
    operacoes: frozenset[str] | None = None
    atividades: frozenset[str] | None = None
    extintos_2g: frozenset[str] | None = None

    def ativo(self) -> bool:
        return bool(
            self.id_1g
            or self.id_2g
            or self.juizes
            or self.relatores
            or self.decisoes
            or self.materias
            or self.partes_adversas
            or self.competencias
            or self.varas
            or self.subfases
            or self.fases
            or self.operacoes
            or self.atividades
            or self.extintos_2g
        )


def _classificar_extinto_2g_recursal_NG(item: dict[str, Any]) -> str | None:
    """``com_merito`` ou ``sem_merito`` (Extinto Sem Mérito), via mérito 2G (novo ou traduzido)."""
    id_2g = _get_id_merito_2g(item)
    if id_2g is None:
        return None
    if mj.eh_extinto_sem_merito_2g(id_2g):
        return "sem_merito"
    if mj.eh_extinto_com_merito_2g(id_2g):
        return "com_merito"
    return None


def _nome_em_conjunto_filtro(nome: str, conjunto: frozenset[str] | None) -> bool:
    if not conjunto:
        return True
    chave = nome.casefold()
    return any(chave == x.casefold() for x in conjunto)


def filtrar_recursal_NG(
    recurso: list[dict[str, Any]],
    filtros: RecursalLAFiltros | None,
) -> list[dict[str, Any]]:
    """
    Restringe à fase Recursal e aplica filtros cumulativos.

    - ``id_1g`` / ``id_2g``: conjuntos de IDs de status
    - ``juizes`` / ``relatores``: nomes exatos (case-insensitive)
    - ``decisoes``: chaves ``mantido_ganho``, ``revertido_ganho``, etc.
    - ``materias`` / ``competencias`` / ``varas`` / ``subfases``: rótulos exatos (case-insensitive)
    - ``atividades``: nomes do catálogo do setor RECURSOS (``ATIVIDADE_RECURSOS``)
    - ``extintos_2g``: ``com_merito`` ou ``sem_merito`` (classificação por ``ID_2G``)
    """
    base = _filtrar_fase_recursal(recurso)
    if filtros is None or not filtros.ativo():
        return _deduplicar_por_processo(base)

    filtrados: list[dict[str, Any]] = []
    for item in base:
        id_1g = _get_id_1g(item)
        id_2g = _get_id_2g(item)

        if filtros.id_1g is not None:
            if id_1g is None or id_1g not in filtros.id_1g:
                continue
        if filtros.id_2g is not None:
            if id_2g is None or id_2g not in filtros.id_2g:
                continue
        if filtros.juizes is not None:
            juiz = _get_juiz_1g(item)
            if not juiz or not _nome_em_conjunto_filtro(juiz, filtros.juizes):
                continue
        if filtros.relatores is not None:
            relator = _get_relator_2g(item)
            if not relator or not _nome_em_conjunto_filtro(relator, filtros.relatores):
                continue
        if filtros.decisoes is not None:
            if id_1g is None or id_2g is None:
                continue
            status_2g_text = str(item.get(_COL_STATUS_2G) or "").strip()
            decisao = _classificar_decisao_recursal(id_1g, id_2g, status_2g_text)
            if decisao is None or decisao not in filtros.decisoes:
                continue
        if filtros.materias is not None:
            materia = _normalizar_materia_recursal_NG(
                item.get(_COL_MATERIA) or item.get("materia")
            )
            if not _nome_em_conjunto_filtro(materia, filtros.materias):
                continue
        if filtros.partes_adversas is not None:
            parte = _rotulo_parte_adversa_recursal_NG(item)
            if not _nome_em_conjunto_filtro(parte, filtros.partes_adversas):
                continue
        if filtros.competencias is not None:
            competencia = _rotulo_competencia_recursal_NG(item)
            if not _nome_em_conjunto_filtro(competencia, filtros.competencias):
                continue
        if filtros.varas is not None:
            vara = _rotulo_vara_recursal_NG(item)
            if not _nome_em_conjunto_filtro(vara, filtros.varas):
                continue
        if filtros.subfases is not None:
            subfase = _rotulo_subfase_recursal_NG(item)
            if not _nome_em_conjunto_filtro(subfase, filtros.subfases):
                continue
        if filtros.fases is not None:
            fase = _rotulo_fase_recursal_NG(item)
            if not _nome_em_conjunto_filtro(fase, filtros.fases):
                continue
        if filtros.operacoes is not None:
            operacao = _rotulo_operacao_recursal_NG(item)
            if not _nome_em_conjunto_filtro(operacao, filtros.operacoes):
                continue
        if filtros.atividades is not None:
            atividade = _rotulo_atividade_recursos_NG(item)
            if not _nome_em_conjunto_filtro(atividade, filtros.atividades):
                continue
        if filtros.extintos_2g is not None:
            tipo_extinto = _classificar_extinto_2g_recursal_NG(item)
            if tipo_extinto is None or tipo_extinto not in filtros.extintos_2g:
                continue

        filtrados.append(item)

    return _deduplicar_por_processo(filtrados)


def get_opcoes_filtros_recursal_NG(recurso: list[dict[str, Any]]) -> dict[str, Any]:
    """Opções para o painel de filtros (status fixos + juízes/relatores do dataset)."""
    juizes: set[str] = set()
    relatores: set[str] = set()
    materias: set[str] = set()
    partes_adversas: set[str] = set()
    competencias: set[str] = set()
    varas: set[str] = set()
    subfases: set[str] = set()
    fases: set[str] = set()
    operacoes: set[str] = set()
    atividades: set[str] = set()
    for item in _filtrar_fase_recursal(recurso):
        nome_juiz = _get_juiz_1g(item)
        if nome_juiz:
            juizes.add(nome_juiz)
        nome_relator = _get_relator_2g(item)
        if nome_relator:
            relatores.add(nome_relator)
        materias.add(
            _normalizar_materia_recursal_NG(item.get(_COL_MATERIA) or item.get("materia"))
        )
        partes_adversas.add(_rotulo_parte_adversa_recursal_NG(item))
        competencias.add(_rotulo_competencia_recursal_NG(item))
        varas.add(_rotulo_vara_recursal_NG(item))
        subfases.add(_rotulo_subfase_recursal_NG(item))
        fases.add(_rotulo_fase_recursal_NG(item))
        operacoes.add(_rotulo_operacao_recursal_NG(item))
        rotulo_ativ = _rotulo_atividade_recursos_NG(item)
        if rotulo_ativ != _SEM_ATIVIDADE_RECURSOS:
            atividades.add(rotulo_ativ)

    return {
        "status_1g": [{"id": sid, "label": label} for sid, label in _STATUS_1G_RECURSAL_NG],
        "status_2g": [{"id": sid, "label": label} for sid, label in _STATUS_2G_RECURSAL_NG],
        "decisoes": [
            {"id": tipo, "label": _LABEL_DECISAO_RECURSAL[tipo]}
            for tipo in _DECISOES_RECURSAL_ORDEM
        ],
        "juizes": sorted(juizes, key=lambda x: x.casefold()),
        "relatores": sorted(relatores, key=lambda x: x.casefold()),
        "materias": sorted(materias, key=lambda x: x.casefold()),
        "partes_adversas": sorted(partes_adversas, key=lambda x: x.casefold()),
        "competencias": sorted(competencias, key=lambda x: x.casefold()),
        "varas": sorted(varas, key=lambda x: _ordem_rotulo_vara(x)),
        "subfases": sorted(subfases, key=lambda x: x.casefold()),
        "fases": sorted(fases, key=lambda x: x.casefold()),
        "operacoes": sorted(operacoes, key=lambda x: x.casefold()),
        "atividades": sorted(
            atividades or _NOMES_ATIVIDADE_RECURSOS_NG,
            key=lambda x: x.casefold(),
        ),
        "atividades_catalogo": [
            {"id": aid, "label": nome} for aid, nome in _ATIVIDADES_RECURSOS_NG
        ],
        "id_setor_recursos": ID_SETOR_RECURSOS_NG,
        "extintos_2g": [
            {"id": chave, "label": _LABEL_EXTINTO_2G[chave]}
            for chave in ("com_merito", "sem_merito")
        ],
    }


def _ordem_rotulo_vara(rotulo: str) -> tuple[int, str]:
    """Ordena ``1º vara``, ``2º vara``, … e deixa ``Sem vara`` por último."""
    chave = rotulo.casefold()
    if chave == _SEM_VARA.casefold():
        return (2, rotulo)
    if chave.endswith("º vara") and chave[:-6].strip().isdigit():
        return (0, f"{int(chave[:-6].strip()):08d}")
    return (1, rotulo.casefold())


# =============================================================================
# KPIs — agendamentos do setor RECURSOS (LexFlow)
# =============================================================================

def _get_agendamento_status(item: dict[str, Any]) -> str | None:
    raw = item.get("STATUS") or item.get("status")
    if raw is None or not str(raw).strip():
        return None
    return str(raw).strip()


def _get_agendamento_data_criacao(item: dict[str, Any]) -> Optional[date]:
    raw = item.get("DATA_HORA_CRIACAO") or item.get("data_hora_criacao")
    return _to_date(raw)


def _get_agendamento_data_conclusao(item: dict[str, Any]) -> Optional[date]:
    raw = item.get("DATA_HORA_CONCLUSAO") or item.get("data_hora_conclusao")
    return _to_date(raw)


def _get_agendamento_prazo(item: dict[str, Any]) -> Optional[date]:
    raw = item.get("PRAZO") or item.get("prazo")
    return _to_date(raw)


# =============================================================================
# Recurso Cancelado — AVR-RETORNO (análise equivocada) / RETORNO-CR (perda de prazo)
# =============================================================================
#
# O motivo "RECURSO CANCELADO OU ALTERADO" / "RECURSO ERRADO OU PERDIDO" NÃO
# fica registrado no encerramento das próprias "AVR - RETORNO"/"RETORNO - CR"
# — fica em ``agendamento.motivo_encaminhamento`` da atividade de ORIGEM (a
# que deu errado), quando ela é encerrada como "Cancelado" ou "Encerrado Não
# Cumprido". Esse jsonb também informa para qual ``id_setor_atividade`` de
# retorno o caso foi encaminhado (``itens[].id_setor_atividade``): validado
# contra os 4 casos reais em produção (2026-07). Aqui contamos pelo DESTINO
# (família AVR-RETORNO = análise de viabilidade equivocada; família
# RETORNO-CR = perda de prazo) — independente de quem cometeu o erro (isso é
# tratado separadamente no comissionamento, por subsetor de origem).

_STATUS_AGENDAMENTO_CUMPRIDO = "Encerrado Cumprido"
_STATUS_ORIGEM_ERRO_NG = frozenset({"Cancelado", "Encerrado Não Cumprido"})
_MOTIVOS_ERRO_RECURSO_NG = frozenset({"RECURSO CANCELADO OU ALTERADO", "RECURSO ERRADO OU PERDIDO"})

# Família "AVR - RETORNO": base (973, staffada pela Confecção) + variantes
# 2G/CTRR/DECISÃO (staffadas pela Análise) — staffing verificado em
# usuario_setor_atividade (a base 1G é sempre invertida em relação às
# variantes 2G/CTRR/DECISÃO da mesma família).
_IDS_FAMILIA_AVR_RETORNO_NG = frozenset({973, 990, 986, 1006, 1019, 1025, 1013, 1023})
# Família "RETORNO - CR": base (978, staffada pela Análise) + variantes
# (staffadas pela Confecção).
_IDS_FAMILIA_RETORNO_CR_NG = frozenset({978, 994, 988, 1007, 1020, 1026, 1014, 1024})


def _get_agendamento_motivo_encaminhamento_itens(item: dict[str, Any]) -> list[dict[str, Any]]:
    """Lê e faz parse de ``MOTIVO_ENCAMINHAMENTO`` (jsonb serializado como texto)."""
    raw = item.get("MOTIVO_ENCAMINHAMENTO") or item.get("motivo_encaminhamento")
    if not raw:
        return []
    try:
        parsed = json.loads(raw) if isinstance(raw, str) else raw
    except (TypeError, ValueError):
        return []
    if not isinstance(parsed, dict):
        return []
    itens = parsed.get("itens")
    return itens if isinstance(itens, list) else []


def _normalizar_motivo_encaminhamento(raw: Any) -> str:
    """Normaliza texto de motivo (alguns registros têm ``;`` sobrando no fim)."""
    return str(raw or "").strip().rstrip(";").strip().casefold()


def _itens_erro_recurso_NG(item: dict[str, Any]) -> list[dict[str, Any]]:
    """Itens de ``motivo_encaminhamento`` cujo motivo é um erro de recurso conhecido."""
    alvos = {_normalizar_motivo_encaminhamento(m): m for m in _MOTIVOS_ERRO_RECURSO_NG}
    encontrados = []
    for it in _get_agendamento_motivo_encaminhamento_itens(item):
        motivo_norm = _normalizar_motivo_encaminhamento(it.get("motivo"))
        if motivo_norm in alvos:
            encontrados.append(it)
    return encontrados


def _get_agendamento_data_cancelamento(item: dict[str, Any]) -> Optional[date]:
    raw = item.get("DATA_HORA_CANCELAMENTO") or item.get("data_hora_cancelamento")
    return _to_date(raw)


def _get_agendamento_data_referencia_erro_NG(item: dict[str, Any]) -> Optional[date]:
    """Data usada para posicionar o erro no período: conclusão, com fallback no cancelamento."""
    return _get_agendamento_data_conclusao(item) or _get_agendamento_data_cancelamento(item)


def _contar_recurso_cancelado_por_destino_NG(
    agendamentos: list[dict[str, Any]],
    familia_destino: frozenset[int],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """
    Conta processos cuja atividade de origem foi encerrada como erro
    (Cancelado / Encerrado Não Cumprido) com ``motivo_encaminhamento``
    apontando para uma atividade de retorno da família informada.
    """
    total = 0
    for row in agendamentos:
        if _get_agendamento_status(row) not in _STATUS_ORIGEM_ERRO_NG:
            continue
        itens = _itens_erro_recurso_NG(row)
        if not itens:
            continue
        data_ref = _get_agendamento_data_referencia_erro_NG(row)
        if not _data_no_periodo(data_ref, from_date, to_date):
            continue
        if any(_to_int(it.get("id_setor_atividade")) in familia_destino for it in itens):
            total += 1
    return total


def get_total_avr_retorno_recurso_cancelado_NG(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """Casos encaminhados para a família "AVR - RETORNO" (análise de viabilidade equivocada)."""
    return _contar_recurso_cancelado_por_destino_NG(
        agendamentos, _IDS_FAMILIA_AVR_RETORNO_NG, from_date, to_date
    )


def get_total_retorno_cr_recurso_cancelado_NG(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """Casos encaminhados para a família "RETORNO - CR" (perda de prazo)."""
    return _contar_recurso_cancelado_por_destino_NG(
        agendamentos, _IDS_FAMILIA_RETORNO_CR_NG, from_date, to_date
    )


# =============================================================================
# Comissão — setor RECURSOS (NG)
# =============================================================================
#
# Regras do escritório (documento de 2026-07):
#   - Quantidade: R$0,50 por atividade de Análise concluída (Encerrado
#     Cumprido, DATA_HORA_CONCLUSAO no período) e R$2,00 por atividade de
#     Confecção concluída. A família AVR-RETORNO/RETORNO-CR (retrabalho) não
#     conta para quantidade.
#   - Qualidade: bônus de R$200,00 a cada colaborador do setor se a meta de
#     80 processos providos/mês (``META_PROVIMENTO_MENSAL_NG``) for atingida;
#     bônus de R$100,00 individual se o colaborador não teve nenhum erro no
#     mês ("zero retrabalho").
#   - Erros: quando uma atividade é encerrada como "Cancelado" ou "Encerrado
#     Não Cumprido" com motivo "RECURSO CANCELADO OU ALTERADO" ou "RECURSO
#     ERRADO OU PERDIDO" (únicos motivos usados na prática — o sistema não
#     distingue "cancelado" de "alterado" nem "errado" de "perdido" como
#     textos separados), o desconto é atribuído a quem foi ATRIBUÍDO na
#     atividade de ORIGEM, e o valor (R$1,00 ou R$4,00) é definido pelo
#     SUBSETOR dessa atividade de origem — não pelo texto do motivo, já que a
#     mesma string aparece em origens de ambos os subsetores na prática.
#
# Roster e classificação de atividades por subsetor verificados diretamente
# contra ``usuario_setor_atividade`` (2026-07): não existe tabela dedicada de
# "subsetor", por isso o roster é fixo (Giovanna atua nos dois subsetores e
# comissiona pela atividade que efetivamente concluir). Vivian Alessandra Souza
# Fernandes é a líder do setor e fica fora do relatório de comissão (11/2026).

_ROSTER_ANALISE_RECURSOS_NG = frozenset({
    "Alessandra Souza de Aquino",  # entrou no setor em 14/10/2026
    "Anderton Matheus Aquino dos Santos",
    "Giovanna Santos Gualberto da Costa",
})
_ROSTER_CONFECCAO_RECURSOS_NG = frozenset({
    "Giovanna Santos Gualberto da Costa",  # passou a fazer Confecção também (11/2026)
    "Bárbara Vitória Arirama Bezerra",
    "Isa Fernanda Morais da Silva Sousa",
    "Náthaly Blanca Nunes de Sousa",
})
_ROSTER_COMISSAO_RECURSOS_NG = _ROSTER_ANALISE_RECURSOS_NG | _ROSTER_CONFECCAO_RECURSOS_NG

_IDS_ATIVIDADE_ANALISE_QTD_NG = frozenset({
    1079, 1081, 1084, 1091, 1078, 1083, 1087, 1077,
    2604,  # ANÁLISE SENTENÇA - EMBARGOS (incluída em 30/10/2026)
})
_IDS_ATIVIDADE_CONFECCAO_QTD_NG = frozenset({
    1012, 996, 998, 1089, 970, 984, 1018, 1002, 1082, 1092, 985, 1004, 1005,
    983, 982, 1001, 968, 992, 972, 1080, 971, 997, 999, 969,
})

_STATUS_QTD_ANALISE_NG = frozenset({_STATUS_AGENDAMENTO_CUMPRIDO, "Encerrado Não Cumprido"})

VALOR_UNITARIO_ANALISE_NG = Decimal("0.50")
VALOR_UNITARIO_CONFECCAO_NG = Decimal("2.00")
VALOR_DESCONTO_ERRO_ANALISE_NG = Decimal("1.00")
VALOR_DESCONTO_ERRO_ANALISE_ALTERADO_NG = Decimal("0.50")
VALOR_DESCONTO_ERRO_CONFECCAO_NG = Decimal("4.00")
VALOR_BONUS_META_QUALIDADE_NG = Decimal("200.00")
VALOR_BONUS_ZERO_RETRABALHO_NG = Decimal("100.00")

def _get_agendamento_id_setor_atividade_NG(item: dict[str, Any]) -> Optional[int]:
    raw = item.get("ID_SETOR_ATIVIDADE") or item.get("id_setor_atividade")
    return _to_int(raw)


def _get_agendamento_funcionario_atribuido_NG(item: dict[str, Any]) -> str:
    raw = item.get("FUNCIONARIO_ATRIBUIDO") or item.get("funcionario_atribuido")
    return str(raw or "").strip()


def _get_agendamento_motivo_texto_NG(item: dict[str, Any]) -> str:
    """Texto livre explicando o fechamento (``agendamento.motivo``, distinto do JSONB de roteamento)."""
    raw = item.get("MOTIVO") or item.get("motivo")
    return str(raw or "").strip()


def _get_agendamento_numero_processo_NG(item: dict[str, Any]) -> str:
    raw = item.get("NUMERO_PROCESSO") or item.get("numero_processo")
    return str(raw or "").strip()


def get_comissao_recursos_NG_por_funcionario(
    agendamentos: list[dict[str, Any]],
    meta_qualidade_atingida: bool,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    funcionarios: Optional[frozenset[str]] = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Comissão mensal do setor RECURSOS (NG): quantidade (Análise/Confecção) +
    bônus de qualidade - descontos por erro, por colaborador do roster fixo.
    Retorna ``(resumo_por_funcionario, detalhamento_dos_descontos)``.

    Quantidade de Análise conta ``Encerrado Cumprido`` e ``Encerrado Não
    Cumprido`` (a análise de viabilidade é remunerada independente do
    resultado); Confecção conta só ``Encerrado Cumprido`` (só remunera o
    recurso de fato interposto). Os dois cálculos (quantidade e erro) são
    independentes: uma análise "Não Cumprido" pode gerar quantidade e, se
    tiver motivo de erro, também gerar desconto.

    Erro de Análise: cada fechamento (Cumprido ou Não Cumprido) da própria
    atividade AVR-RETORNO (qualquer variante da família) conta 1 erro,
    atribuído a quem está atribuído àquela tarefa — não à tarefa de origem
    que a gerou. Desconto R$0,50 quando o texto do motivo do fechamento
    menciona "ALTERADO"; R$1,00 nos demais casos (inclusive sem esse texto).

    Erro de Confecção: mesma lógica, mas na atividade RETORNO - CR (qualquer
    variante da família); desconto fixo de R$4,00.

    O detalhamento retornado traz o texto do motivo de cada desconto (quando
    houver) para revisão manual antes de fechar a folha — muitos casos reais
    (renúncia do cliente, ausência em audiência sem justificativa, trânsito
    em julgado, etc.) não são erro do colaborador, e isso não é algo que o
    sistema consiga distinguir com segurança de forma automática.

    ``funcionarios``, se informado, restringe o relatório a esse subconjunto
    do roster (mesmo filtro de funcionário usado no dashboard).
    """
    roster = _ROSTER_COMISSAO_RECURSOS_NG
    if funcionarios is not None:
        roster = roster & funcionarios

    qtd_analise: dict[str, int] = defaultdict(int)
    qtd_confeccao: dict[str, int] = defaultdict(int)
    erros_analise: dict[str, int] = defaultdict(int)
    erros_confeccao: dict[str, int] = defaultdict(int)
    desconto_analise_acumulado: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    detalhes: list[dict[str, Any]] = []

    for row in agendamentos:
        nome = _get_agendamento_funcionario_atribuido_NG(row)
        if not nome or nome not in roster:
            continue

        id_setor_atividade = _get_agendamento_id_setor_atividade_NG(row)
        status = _get_agendamento_status(row)

        if id_setor_atividade in _IDS_ATIVIDADE_ANALISE_QTD_NG and status in _STATUS_QTD_ANALISE_NG:
            conclusao = _get_agendamento_data_conclusao(row)
            if _data_no_periodo(conclusao, from_date, to_date):
                qtd_analise[nome] += 1
        elif id_setor_atividade in _IDS_ATIVIDADE_CONFECCAO_QTD_NG and status == _STATUS_AGENDAMENTO_CUMPRIDO:
            conclusao = _get_agendamento_data_conclusao(row)
            if _data_no_periodo(conclusao, from_date, to_date):
                qtd_confeccao[nome] += 1

        eh_avr_retorno = id_setor_atividade in _IDS_FAMILIA_AVR_RETORNO_NG
        eh_retorno_cr = id_setor_atividade in _IDS_FAMILIA_RETORNO_CR_NG
        if (eh_avr_retorno or eh_retorno_cr) and status in _STATUS_AGENDAMENTO_ENCERRADO_RECURSOS:
            data_ref = _get_agendamento_data_referencia_erro_NG(row)
            if not _data_no_periodo(data_ref, from_date, to_date):
                continue

            motivo_texto = _get_agendamento_motivo_texto_NG(row)

            if eh_avr_retorno:
                erros_analise[nome] += 1
                eh_alterado = "ALTERADO" in motivo_texto.upper()
                valor_desconto = (
                    VALOR_DESCONTO_ERRO_ANALISE_ALTERADO_NG if eh_alterado else VALOR_DESCONTO_ERRO_ANALISE_NG
                )
                desconto_analise_acumulado[nome] += valor_desconto
                subsetor_label = "Análise"
                tipo_desconto = "Recurso Alterado" if eh_alterado else "Recurso Cancelado"
            else:
                erros_confeccao[nome] += 1
                valor_desconto = VALOR_DESCONTO_ERRO_CONFECCAO_NG
                subsetor_label = "Confecção"
                tipo_desconto = "Recurso Errado/Perdido"

            detalhes.append({
                "funcionario": nome,
                "subsetor": subsetor_label,
                "numero_processo": _get_agendamento_numero_processo_NG(row),
                "atividade_origem": row.get("ATIVIDADE") or row.get("atividade") or "",
                "data": data_ref.isoformat() if data_ref else "",
                "tipo_desconto": tipo_desconto,
                "valor_desconto": float(valor_desconto),
                "motivo_texto": motivo_texto or "(sem texto do fechamento do retorno)",
            })

    linhas: list[dict[str, Any]] = []
    for nome in sorted(roster):
        q_analise = qtd_analise.get(nome, 0)
        q_confeccao = qtd_confeccao.get(nome, 0)
        n_erros_analise = erros_analise.get(nome, 0)
        n_erros_confeccao = erros_confeccao.get(nome, 0)
        total_erros = n_erros_analise + n_erros_confeccao

        if q_analise == 0 and q_confeccao == 0 and total_erros == 0 and not meta_qualidade_atingida:
            continue

        valor_qtd_analise = (Decimal(q_analise) * VALOR_UNITARIO_ANALISE_NG).quantize(Decimal("0.01"))
        valor_qtd_confeccao = (Decimal(q_confeccao) * VALOR_UNITARIO_CONFECCAO_NG).quantize(Decimal("0.01"))
        valor_desconto_analise = desconto_analise_acumulado.get(nome, Decimal("0")).quantize(Decimal("0.01"))
        valor_desconto_confeccao = (Decimal(n_erros_confeccao) * VALOR_DESCONTO_ERRO_CONFECCAO_NG).quantize(Decimal("0.01"))
        bonus_meta = VALOR_BONUS_META_QUALIDADE_NG if meta_qualidade_atingida else Decimal("0")
        bonus_zero_retrabalho = VALOR_BONUS_ZERO_RETRABALHO_NG if total_erros == 0 else Decimal("0")

        total = (
            valor_qtd_analise + valor_qtd_confeccao
            - valor_desconto_analise - valor_desconto_confeccao
            + bonus_meta + bonus_zero_retrabalho
        ).quantize(Decimal("0.01"))

        subsetores = []
        if nome in _ROSTER_ANALISE_RECURSOS_NG:
            subsetores.append("Análise")
        if nome in _ROSTER_CONFECCAO_RECURSOS_NG:
            subsetores.append("Confecção")

        linhas.append({
            "funcionario": nome,
            "subsetores": subsetores,
            "qtd_analise": q_analise,
            "valor_unitario_analise": float(VALOR_UNITARIO_ANALISE_NG),
            "valor_qtd_analise": float(valor_qtd_analise),
            "qtd_confeccao": q_confeccao,
            "valor_unitario_confeccao": float(VALOR_UNITARIO_CONFECCAO_NG),
            "valor_qtd_confeccao": float(valor_qtd_confeccao),
            "erros_analise": n_erros_analise,
            "desconto_analise": float(valor_desconto_analise),
            "erros_confeccao": n_erros_confeccao,
            "desconto_confeccao": float(valor_desconto_confeccao),
            "total_erros": total_erros,
            "meta_qualidade_atingida": meta_qualidade_atingida,
            "bonus_meta_qualidade": float(bonus_meta),
            "zero_retrabalho": total_erros == 0,
            "bonus_zero_retrabalho": float(bonus_zero_retrabalho),
            "valor_total": float(total),
        })

    linhas.sort(key=lambda x: (-x["valor_total"], x["funcionario"]))
    detalhes.sort(key=lambda x: (x["funcionario"], x["data"]))
    return linhas, detalhes


def _agendamento_atividade_recursos_valida(item: dict[str, Any]) -> bool:
    nome = str(item.get("ATIVIDADE") or item.get("atividade") or "").strip()
    return bool(nome) and nome in _NOMES_ATIVIDADE_RECURSOS_NG


def get_kpis_atividades_recursos_NG(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, int]:
    """
    KPIs de agendamentos do setor RECURSOS no período selecionado.

    - **Total**: criadas no período (``DATA_HORA_CRIACAO``)
    - **Em andamento**: criadas no período e ainda abertas (Recebido / Visualizado)
    - **Vencidas**: abertas criadas no período com ``PRAZO`` anterior a ``ref_date``
    - **Vencem hoje**: abertas criadas no período com ``PRAZO`` = ``ref_date``
    - **Concluídas**: encerradas no período (``DATA_HORA_CONCLUSAO``)
    """
    ref = ref_date or date.today()
    rows = [row for row in agendamentos if _agendamento_atividade_recursos_valida(row)]

    total = 0
    em_andamento = 0
    vencidas = 0
    vencem_hoje = 0
    concluidas = 0

    for row in rows:
        criacao = _get_agendamento_data_criacao(row)
        conclusao = _get_agendamento_data_conclusao(row)
        status = _get_agendamento_status(row) or ""
        prazo = _get_agendamento_prazo(row)
        aberta = status in _STATUS_AGENDAMENTO_ABERTO_RECURSOS

        if _data_no_periodo(criacao, from_date, to_date):
            total += 1
            if aberta:
                em_andamento += 1
                if prazo is not None:
                    if prazo < ref:
                        vencidas += 1
                    elif prazo == ref:
                        vencem_hoje += 1

        if status in _STATUS_AGENDAMENTO_ENCERRADO_RECURSOS:
            if _data_no_periodo(conclusao, from_date, to_date):
                concluidas += 1

    return {
        "total_atividades_recursos_NG": total,
        "atividades_recursos_em_andamento_NG": em_andamento,
        "atividades_recursos_vencidas_NG": vencidas,
        "atividades_recursos_vencem_hoje_NG": vencem_hoje,
        "atividades_recursos_concluidas_NG": concluidas,
    }


def get_kpis_atividades_recursos_por_prazo_NG(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, int]:
    """
    KPIs de agendamentos do setor RECURSOS usando ``PRAZO`` como eixo temporal,
    em vez de criação/conclusão (mesma lógica de
    ``get_kpis_emendas_manifestacoes_por_prazo_NG``).

    - **Total**: abertas (Recebido/Visualizado) com ``PRAZO`` no período
    - **Em andamento**: coincide com Total (toda aberta já conta como "em andamento")
    - **Vencidas**: abertas com ``PRAZO`` no período anterior a ``ref_date``
    - **Vencem hoje**: abertas com ``PRAZO`` no período igual a ``ref_date``
    - **Concluídas**: encerradas com ``PRAZO`` no período (contagem separada do Total)
    """
    ref = ref_date or date.today()
    rows = [row for row in agendamentos if _agendamento_atividade_recursos_valida(row)]

    total = 0
    em_andamento = 0
    vencidas = 0
    vencem_hoje = 0
    concluidas = 0

    for row in rows:
        prazo = _get_agendamento_prazo(row)
        status = _get_agendamento_status(row) or ""
        if not _data_no_periodo(prazo, from_date, to_date):
            continue

        if status in _STATUS_AGENDAMENTO_ABERTO_RECURSOS:
            total += 1
            em_andamento += 1
            if prazo is not None and prazo < ref:
                vencidas += 1
            elif prazo is not None and prazo == ref:
                vencem_hoje += 1
        elif status in _STATUS_AGENDAMENTO_ENCERRADO_RECURSOS:
            concluidas += 1

    return {
        "total_por_prazo_atividades_recursos_NG": total,
        "por_prazo_em_andamento_atividades_recursos_NG": em_andamento,
        "por_prazo_vencidas_atividades_recursos_NG": vencidas,
        "por_prazo_vencem_hoje_atividades_recursos_NG": vencem_hoje,
        "por_prazo_concluidas_atividades_recursos_NG": concluidas,
    }


def _get_agendamento_processo_id(item: dict[str, Any]) -> Any | None:
    pid = item.get("processo_id") or item.get("PROCESSO_ID")
    return pid


def _get_agendamento_atividade_nome(item: dict[str, Any]) -> str:
    raw = item.get("ATIVIDADE") or item.get("atividade")
    if raw is None or not str(raw).strip():
        return _SEM_ATIVIDADE_RECURSOS
    nome = str(raw).strip()
    if nome in _NOMES_ATIVIDADE_RECURSOS_NG:
        return nome
    return _SEM_ATIVIDADE_RECURSOS


def _get_agendamento_funcionario_atribuido(item: dict[str, Any]) -> str:
    """Responsável atribuído (``agendamento.id_usuario_atribuido``)."""
    raw = (
        item.get(_COL_FUNCIONARIO_ATRIBUIDO)
        or item.get("FUNCIONARIO")
        or item.get("funcionario")
    )
    if raw is None or not str(raw).strip():
        return _SEM_FUNCIONARIO_RECURSOS
    return str(raw).strip()


def _get_agendamento_funcionario_encerramento(item: dict[str, Any]) -> str | None:
    """Quem encerrou de fato (``agendamento.id_usuario_encerramento``), quando informado."""
    uid = item.get(_COL_ID_USUARIO_ENCERRAMENTO) or item.get("id_usuario_encerramento")
    if uid is None or (isinstance(uid, str) and not str(uid).strip()):
        return None
    raw = item.get(_COL_FUNCIONARIO_ENCERRAMENTO) or item.get("funcionario_encerramento")
    if raw is not None and str(raw).strip():
        return str(raw).strip()
    return None


def _get_agendamento_funcionario_nome(item: dict[str, Any]) -> str:
    """
    Responsável exibido no contexto geral: atribuído em tarefas abertas;
    quem encerrou quando o status é encerrado e ``id_usuario_encerramento`` existe.
    """
    status = _get_agendamento_status(item) or ""
    if status in _STATUS_AGENDAMENTO_ENCERRADO_RECURSOS:
        encerrador = _get_agendamento_funcionario_encerramento(item)
        if encerrador:
            return encerrador
    return _get_agendamento_funcionario_atribuido(item)


def _agendamento_tem_encerrador_identificado(item: dict[str, Any]) -> bool:
    return _get_agendamento_funcionario_encerramento(item) is not None


def _filtrar_agendamentos_recursos_no_periodo(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Agendamentos válidos do setor RECURSOS com ``DATA_HORA_CRIACAO`` no período."""
    filtrados: list[dict[str, Any]] = []
    for row in agendamentos:
        if not _agendamento_atividade_recursos_valida(row):
            continue
        criacao = _get_agendamento_data_criacao(row)
        if not _data_no_periodo(criacao, from_date, to_date):
            continue
        if _get_agendamento_processo_id(row) is None:
            continue
        filtrados.append(row)
    return filtrados


def _filtrar_agendamentos_encerrados_recursos_no_periodo(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    exigir_encerrador: bool = False,
) -> list[dict[str, Any]]:
    """
    Agendamentos encerrados (Cumprido / Não Cumprido) com ``DATA_HORA_CONCLUSAO`` no período.

    Com ``exigir_encerrador=True``, mantém apenas linhas com ``id_usuario_encerramento``
    preenchido (encerramento atribuível a um funcionário).
    """
    filtrados: list[dict[str, Any]] = []
    for row in agendamentos:
        if not _agendamento_atividade_recursos_valida(row):
            continue
        status = _get_agendamento_status(row) or ""
        if status not in _STATUS_AGENDAMENTO_ENCERRADO_RECURSOS:
            continue
        if exigir_encerrador and not _agendamento_tem_encerrador_identificado(row):
            continue
        conclusao = _get_agendamento_data_conclusao(row)
        if not _data_no_periodo(conclusao, from_date, to_date):
            continue
        if _get_agendamento_processo_id(row) is None:
            continue
        filtrados.append(row)
    return filtrados


def _agrupar_processos_distintos_por_chave(
    agendamentos: list[dict[str, Any]],
    obter_chave: Any,
) -> list[dict[str, Any]]:
    """Conta processos distintos por chave; ``percent`` sobre a soma dos grupos."""
    grouped: dict[str, set[Any]] = defaultdict(set)
    for row in agendamentos:
        pid = _get_agendamento_processo_id(row)
        if pid is None:
            continue
        chave = obter_chave(row)
        grouped[chave].add(pid)

    total = float(sum(len(v) for v in grouped.values()))
    itens: list[dict[str, Any]] = []
    for nome, processos in grouped.items():
        qtd = len(processos)
        itens.append(
            {
                "name": nome,
                "value": float(qtd),
                "percent": round(100.0 * float(qtd) / total, 1) if total > 0 else 0.0,
            }
        )
    return sorted(itens, key=lambda x: float(x["value"]), reverse=True)


def group_recursal_processos_por_atividade_NG(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Processos distintos por atividade (agendamentos criados no período)."""
    base = _filtrar_agendamentos_recursos_no_periodo(
        agendamentos, from_date=from_date, to_date=to_date
    )
    return _agrupar_processos_distintos_por_chave(base, _get_agendamento_atividade_nome)


def _status_agendamento_para_slug_demandas(status: str | None) -> str:
    if status is None or not str(status).strip():
        return "sem_status"
    normalizado = str(status).strip()
    return _SLUG_POR_STATUS_AGENDAMENTO_RECURSOS.get(normalizado, "outros")


def group_recursal_demandas_por_funcionario_NG(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Demandas encerradas por funcionário (Cumprido / Não Cumprido),
    com ``DATA_HORA_CONCLUSAO`` no período.

    Contabiliza somente registros com ``id_usuario_encerramento`` preenchido;
    o nome exibido vem de ``nome_usuario_encerramento`` (quem de fato encerrou,
    que pode diferir do responsável atribuído).
    """
    base = _filtrar_agendamentos_encerrados_recursos_no_periodo(
        agendamentos,
        from_date=from_date,
        to_date=to_date,
        exigir_encerrador=True,
    )

    grouped: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in base:
        funcionario = _get_agendamento_funcionario_encerramento(row)
        if not funcionario:
            continue
        slug = _status_agendamento_para_slug_demandas(_get_agendamento_status(row))
        if slug not in {s for s, _ in _STATUS_DEMANDAS_FUNCIONARIO_NG}:
            continue
        grouped[funcionario][slug] += 1

    itens: list[dict[str, Any]] = []
    for nome, contagens in grouped.items():
        item: dict[str, Any] = {"name": nome}
        total = 0
        for slug, _ in _STATUS_DEMANDAS_FUNCIONARIO_NG:
            valor = int(contagens.get(slug, 0))
            item[slug] = valor
            total += valor
        item["total"] = total
        if total > 0:
            itens.append(item)

    return sorted(itens, key=lambda x: int(x["total"]), reverse=True)


def group_recursal_resolvidos_por_dia_NG(
    agendamentos: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Produção diária: quantidade de atividades do setor RECURSOS "Encerrado
    Cumprido" por dia de conclusão (``DATA_HORA_CONCLUSAO``), histórico
    completo — NG. O filtro por período (calendário do dashboard) é aplicado
    no frontend, como em :func:`group_execucao_resolvidos_por_dia_NG`.
    """
    grouped: dict[str, int] = defaultdict(int)
    for row in agendamentos:
        if not _agendamento_atividade_recursos_valida(row):
            continue
        if _get_agendamento_status(row) != _STATUS_AGENDAMENTO_CUMPRIDO:
            continue
        conclusao = _get_agendamento_data_conclusao(row)
        if conclusao is None:
            continue
        grouped[conclusao.strftime("%Y-%m-%d")] += 1

    return [
        {"name": dia, "value": count}
        for dia, count in sorted(grouped.items(), key=lambda x: x[0])
    ]


_MESES_ABREVIADOS_NG = (
    "jan", "fev", "mar", "abr", "mai", "jun",
    "jul", "ago", "set", "out", "nov", "dez",
)


def group_recursal_resolvidos_por_mes_NG(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Produção mensal: quantidade de atividades do setor RECURSOS "Encerrado
    Cumprido" por mês de conclusão (``DATA_HORA_CONCLUSAO``) — NG. Usado como
    visão inicial (drill-down) de :func:`group_recursal_resolvidos_por_dia_NG`.
    """
    grouped: dict[str, dict[str, Any]] = {}
    for row in agendamentos:
        if not _agendamento_atividade_recursos_valida(row):
            continue
        if _get_agendamento_status(row) != _STATUS_AGENDAMENTO_CUMPRIDO:
            continue
        conclusao = _get_agendamento_data_conclusao(row)
        if conclusao is None or not _data_no_periodo(conclusao, from_date, to_date):
            continue
        month_key = f"{conclusao.year}-{conclusao.month:02d}"
        if month_key not in grouped:
            month_name = f"{_MESES_ABREVIADOS_NG[conclusao.month - 1]} {conclusao.year}"
            grouped[month_key] = {"name": month_name, "value": 0, "sort_key": month_key}
        grouped[month_key]["value"] += 1

    return [
        {"name": item["name"], "value": item["value"]}
        for item in sorted(grouped.values(), key=lambda x: x["sort_key"])
    ]


def get_recursal_resolvidos_por_dia_por_funcionario_NG(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> dict[str, Any]:
    """
    Produção diária por funcionário (encerrador) — NG. Usado para recalcular a
    visão mensal/diária de produção quando o filtro de funcionário da seção
    Atividades está ativo (mesmo mecanismo de Réplicas).
    """
    grouped: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in agendamentos:
        if not _agendamento_atividade_recursos_valida(row):
            continue
        if _get_agendamento_status(row) != _STATUS_AGENDAMENTO_CUMPRIDO:
            continue
        conclusao = _get_agendamento_data_conclusao(row)
        if conclusao is None or not _data_no_periodo(conclusao, from_date, to_date):
            continue
        funcionario = _get_agendamento_funcionario_encerramento(row)
        if not funcionario:
            continue
        grouped[conclusao.strftime("%Y-%m-%d")][funcionario] += 1

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


def get_media_recursal_resolvidos_por_funcionario_NG(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Média de atividades do setor RECURSOS "Encerrado Cumprido" por
    funcionário no período (NG).

    Média = total de atividades cumpridas ÷ número de dias distintos com
    conclusão no período, mesmo critério de
    :func:`get_media_execucao_resolvidos_por_funcionario_NG`.
    """
    grouped: dict[str, dict[str, Any]] = defaultdict(lambda: {"total": 0, "dias": set()})
    for row in agendamentos:
        if not _agendamento_atividade_recursos_valida(row):
            continue
        if _get_agendamento_status(row) != _STATUS_AGENDAMENTO_CUMPRIDO:
            continue
        conclusao = _get_agendamento_data_conclusao(row)
        if conclusao is None or not _data_no_periodo(conclusao, from_date, to_date):
            continue
        funcionario = _get_agendamento_funcionario_encerramento(row)
        if not funcionario:
            continue
        grouped[funcionario]["total"] += 1
        grouped[funcionario]["dias"].add(conclusao)

    itens: list[dict[str, Any]] = []
    for nome, info in grouped.items():
        dias = len(info["dias"])
        if dias == 0:
            continue
        itens.append({"name": nome, "value": round(info["total"] / dias, 2)})
    return sorted(itens, key=lambda x: x["value"], reverse=True)


def _formatar_pessoa_setor_recursos(row: dict[str, Any]) -> str:
    setor = str(row.get("SETOR") or row.get("setor") or "RECURSOS").strip().upper()
    atividade = str(row.get("ATIVIDADE") or row.get("atividade") or "").strip().upper()
    if atividade:
        return f"{setor} - {atividade}"
    return setor


def _formatar_descricao_tarefa_recursos(row: dict[str, Any]) -> str:
    raw = row.get("DESCRICAO") or row.get("descricao") or row.get("STATUS_1G") or row.get("status_1g")
    if raw is None or not str(raw).strip():
        return "—"
    return str(raw).strip().upper()


def _get_agendamento_atividade_nome_lista(row: dict[str, Any]) -> str:
    raw = row.get("ATIVIDADE") or row.get("atividade")
    if raw is None or not str(raw).strip():
        return _SEM_ATIVIDADE_RECURSOS
    nome = str(raw).strip()
    if nome in _NOMES_ATIVIDADE_RECURSOS_NG:
        return nome
    return _SEM_ATIVIDADE_RECURSOS


def _agendamento_incluir_lista_tarefas_recursos(
    row: dict[str, Any],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> bool:
    """Inclui agendamentos criados no período ou encerrados no período."""
    criacao = _get_agendamento_data_criacao(row)
    conclusao = _get_agendamento_data_conclusao(row)
    status = _get_agendamento_status(row) or ""
    if _data_no_periodo(criacao, from_date, to_date):
        return True
    if status in _STATUS_AGENDAMENTO_ENCERRADO_RECURSOS:
        return _data_no_periodo(conclusao, from_date, to_date)
    return False


def _classificar_situacao_tarefa_recursos(
    row: dict[str, Any],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, bool]:
    ref = ref_date or date.today()
    criacao = _get_agendamento_data_criacao(row)
    conclusao = _get_agendamento_data_conclusao(row)
    status = _get_agendamento_status(row) or ""
    prazo = _get_agendamento_prazo(row)
    criada_periodo = _data_no_periodo(criacao, from_date, to_date)
    aberta = status in _STATUS_AGENDAMENTO_ABERTO_RECURSOS
    em_andamento = aberta and criada_periodo
    vencida = em_andamento and prazo is not None and prazo < ref
    vence_hoje = em_andamento and prazo is not None and prazo == ref
    concluida = (
        status in _STATUS_AGENDAMENTO_ENCERRADO_RECURSOS
        and _data_no_periodo(conclusao, from_date, to_date)
    )
    return {
        "em_andamento": em_andamento,
        "vencida": vencida,
        "vence_hoje": vence_hoje,
        "concluida": concluida,
    }


_SITUACOES_RECURSOS_VALIDAS = frozenset(
    sid for sid, _ in _SITUACOES_FILTRO_TAREFAS_RECURSOS_NG
)


@dataclass(frozen=True)
class RecursalAtividadesRecursosFiltros:
    """Filtros cumulativos (AND) sobre agendamentos do setor RECURSOS no período."""

    funcionarios: frozenset[str] | None = None
    atividades: frozenset[str] | None = None
    status: frozenset[str] | None = None
    situacoes: frozenset[str] | None = None

    def ativo(self) -> bool:
        return bool(
            self.funcionarios
            or self.atividades
            or self.status
            or self.situacoes
        )


def _agendamento_match_filtros_recursos(
    row: dict[str, Any],
    filtros: RecursalAtividadesRecursosFiltros,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> bool:
    """Aplica filtros de funcionário, atividade, status e situação (OR entre situações)."""
    if filtros.funcionarios is not None:
        # Filtra sempre pelo responsável atribuído, independente do status.
        # Isso inclui tarefas encerradas por outra pessoa (encerrado_pelo_responsavel=False)
        # e é o que permite contabilizar "Encerradas por outros" na seção Atribuição.
        funcionario = _get_agendamento_funcionario_atribuido(row)
        if not _nome_em_conjunto_filtro(funcionario, filtros.funcionarios):
            return False
    if filtros.atividades is not None:
        atividade = _get_agendamento_atividade_nome_lista(row)
        if not _nome_em_conjunto_filtro(atividade, filtros.atividades):
            return False
    if filtros.status is not None:
        status = (_get_agendamento_status(row) or "—").strip()
        if not _nome_em_conjunto_filtro(status, filtros.status):
            return False
    if filtros.situacoes is not None:
        flags = _classificar_situacao_tarefa_recursos(
            row, from_date, to_date, ref_date=ref_date
        )
        if not any(flags.get(sid) for sid in filtros.situacoes):
            return False
    return True


def filtrar_agendamentos_recursos_NG(
    agendamentos: list[dict[str, Any]],
    filtros: RecursalAtividadesRecursosFiltros | None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Restringe agendamentos válidos do setor RECURSOS aos filtros cumulativos."""
    if filtros is None or not filtros.ativo():
        return agendamentos
    return [
        row
        for row in agendamentos
        if _agendamento_atividade_recursos_valida(row)
        and _agendamento_match_filtros_recursos(
            row, filtros, from_date, to_date, ref_date=ref_date
        )
    ]


def _get_recurso_processo_id(item: dict[str, Any]) -> int | None:
    return _to_int(
        item.get("id")
        or item.get("ID")
        or item.get("processo_id")
        or item.get("PROCESSO_ID")
    )


def processo_ids_recursal_de_agendamentos_recursos_NG(
    agendamentos: list[dict[str, Any]],
    filtros: RecursalAtividadesRecursosFiltros,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> frozenset[int]:
    """
    Processos na fase Recursal relacionados a agendamentos RECURSOS que passam
    nos filtros e entram no escopo do período (criados ou encerrados no intervalo).
    """
    filtrados = filtrar_agendamentos_recursos_NG(
        agendamentos, filtros, from_date, to_date, ref_date=ref_date
    )
    ids: set[int] = set()
    for row in filtrados:
        if not _agendamento_incluir_lista_tarefas_recursos(row, from_date, to_date):
            continue
        pid = _to_int(_get_agendamento_processo_id(row))
        if pid is not None:
            ids.add(pid)
    return frozenset(ids)


def filtrar_recursal_NG_por_processo_ids(
    recurso: list[dict[str, Any]],
    processo_ids: frozenset[int],
) -> list[dict[str, Any]]:
    """Restringe linhas de processo aos IDs vindos de agendamentos filtrados."""
    if not processo_ids:
        return []
    return [
        item
        for item in recurso
        if (pid := _get_recurso_processo_id(item)) is not None and pid in processo_ids
    ]


def list_recursal_atividades_periodo_NG(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Lista de agendamentos do setor RECURSOS para a tabela de tarefas."""
    ref = ref_date or date.today()
    itens: list[dict[str, Any]] = []
    for row in agendamentos:
        if not _agendamento_atividade_recursos_valida(row):
            continue
        if not _agendamento_incluir_lista_tarefas_recursos(row, from_date, to_date):
            continue
        ag_id = _to_int(row.get("id") or row.get("ID"))
        if ag_id is None:
            continue
        status = _get_agendamento_status(row) or "—"
        prazo = _get_agendamento_prazo(row)
        criacao = _get_agendamento_data_criacao(row)
        situacao = _classificar_situacao_tarefa_recursos(
            row, from_date, to_date, ref_date=ref
        )
        funcionario_atrib = _get_agendamento_funcionario_atribuido(row)
        funcionario_enc = _get_agendamento_funcionario_encerramento(row)
        encerrado_pelo_responsavel: bool | None = None
        if status in _STATUS_AGENDAMENTO_ENCERRADO_RECURSOS and funcionario_enc is not None:
            encerrado_pelo_responsavel = (
                funcionario_enc.strip().lower() == funcionario_atrib.strip().lower()
            )
        operacao = str(row.get("OPERACAO") or row.get("operacao") or "").strip()
        itens.append(
            {
                "id": ag_id,
                "status": status,
                "descricao": _formatar_descricao_tarefa_recursos(row),
                "pessoa_setor": _formatar_pessoa_setor_recursos(row),
                "funcionario": _get_agendamento_funcionario_nome(row),
                "funcionario_atribuido": funcionario_atrib,
                "funcionario_encerramento": funcionario_enc,
                "atividade": _get_agendamento_atividade_nome_lista(row),
                "prazo": prazo.isoformat() if prazo else None,
                "criado_em": criacao.isoformat() if criacao else None,
                "operacao": operacao,
                "encerrado_pelo_responsavel": encerrado_pelo_responsavel,
                **situacao,
            }
        )

    def _sort_key(item: dict[str, Any]) -> tuple[int, str, int]:
        prazo_raw = item.get("prazo")
        prazo_missing = 0 if prazo_raw else 1
        return (prazo_missing, str(prazo_raw or ""), int(item.get("id") or 0))

    return sorted(itens, key=_sort_key)


def get_opcoes_filtros_atividades_lista_NG(
    agendamentos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    *,
    ref_date: Optional[date] = None,
) -> dict[str, Any]:
    """Opções de filtros da lista de tarefas (funcionários, atividades, status)."""
    rows = list_recursal_atividades_periodo_NG(
        agendamentos, from_date=from_date, to_date=to_date, ref_date=ref_date
    )
    funcionarios: set[str] = set()
    atividades: set[str] = set()
    status_vistos: set[str] = set()
    for row in rows:
        funcionarios.add(str(row.get("funcionario") or _SEM_FUNCIONARIO_RECURSOS))
        atividade = str(row.get("atividade") or "").strip()
        if atividade and atividade != _SEM_ATIVIDADE_RECURSOS:
            atividades.add(atividade)
        status = str(row.get("status") or "").strip()
        if status and status != "—":
            status_vistos.add(status)

    status_ordenados: list[str] = []
    for label in _STATUS_FILTRO_TAREFAS_RECURSOS_NG:
        if label in status_vistos:
            status_ordenados.append(label)
    for label in sorted(status_vistos - set(status_ordenados), key=lambda x: x.casefold()):
        status_ordenados.append(label)

    return {
        "funcionarios": sorted(funcionarios, key=lambda x: x.casefold()),
        "atividades": sorted(
            atividades or _NOMES_ATIVIDADE_RECURSOS_NG,
            key=lambda x: x.casefold(),
        ),
        "status": status_ordenados,
        "situacoes": [
            {"id": sid, "label": label} for sid, label in _SITUACOES_FILTRO_TAREFAS_RECURSOS_NG
        ],
    }
