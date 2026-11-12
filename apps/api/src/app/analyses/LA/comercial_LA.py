# Análises e processamento de dados de COMERCIAL LA

from typing import List, Dict, Any, Optional
from datetime import datetime, date
from collections import defaultdict
import statistics
from decimal import Decimal
from app.utils import parse_date_from_db, resolver_periodo_comparativo


# -----------------------------------------------------------------------------
# 1 - Funções auxiliares
# -----------------------------------------------------------------------------

def _formatar_nome_atendente(nome_completo: str) -> str:
    """Extrai apenas o primeiro e segundo nome da atendente e devolve em caixa alta."""
    if not nome_completo or nome_completo == "Sem atendente":
        return nome_completo

    partes = nome_completo.strip().split()

    if len(partes) == 1:
        return partes[0].upper()
    return " ".join(partes[:1]).upper()

def _filter_by_date_range(comercial_geral: List[Dict[str, Any]], from_date: date, to_date: date) -> List[Dict[str, Any]]:
    """Filtra dados comerciais por intervalo de datas usando a coluna ASSINATURA."""
    filtered = []
    for item in comercial_geral:
        try:
            assinatura_str = item.get("ASSINADO_EM") or item.get("assinado_em")
            if not assinatura_str:
                continue

            assinatura_date = parse_date_from_db(assinatura_str)
            if not assinatura_date:
                continue

            if isinstance(assinatura_date, datetime):
                assinatura_date = assinatura_date.date()
            elif not isinstance(assinatura_date, date):
                continue

            if from_date <= assinatura_date <= to_date:
                filtered.append(item)
        except (ValueError, AttributeError, TypeError):
            continue

    return filtered


_MONTH_NAMES = [
    "jan", "fev", "mar", "abr", "mai", "jun",
    "jul", "ago", "set", "out", "nov", "dez"
]


def _get_data_assinatura_LA(row: Dict[str, Any]) -> Optional[date]:
    assinatura_str = row.get("ASSINADO_EM") or row.get("assinado_em")
    if not assinatura_str:
        return None

    assinatura_date = parse_date_from_db(assinatura_str)
    if not assinatura_date:
        return None

    if isinstance(assinatura_date, datetime):
        return assinatura_date.date()
    if isinstance(assinatura_date, date):
        return assinatura_date
    return None


# Verifica qual atendente esta ativo ou inativo
def _is_atendente_ativo(row: Dict[str, Any]) -> bool:
    """
    Indica se o funcionário comercial está ativo (`ATIVO` na query, join com funcionarios).

    Se a coluna não existir (dados antigos em cache), assume ativo para não zerar o painel.
    """
    v = row.get("ATIVO")
    if v is None:
        return True
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    if s in ("false", "f", "0", "no", "n"):
        return False
    if s in ("true", "t", "1", "yes", "y"):
        return True
    return bool(v)

# Lista única de atendentes comerciais
def list_atendentes_comerciais(comercial_geral: List[Dict[str, Any]]) -> List[str]:
    vistos: set[str] = set()
    saida: List[str] = []
    for row in comercial_geral or []:
        if not _is_atendente_ativo(row):
            continue
        nome = row.get("ATENDENTE")
        if nome is None or str(nome).strip() == "":
            continue
        fmt = _formatar_nome_atendente(str(nome).strip())
        if not fmt or fmt == "Sem atendente" or fmt in vistos:
            continue
        vistos.add(fmt)
        saida.append(fmt)
    return sorted(saida, key=lambda x: x.lower())


def _rotulo_atendente(row: Dict[str, Any]) -> str:
    """Mesmo rótulo usado nos agrupamentos por atendente (coluna ``ATENDENTE``)."""
    raw = row.get("ATENDENTE")
    if raw is None or not str(raw).strip():
        return _formatar_nome_atendente("Sem atendente")
    return _formatar_nome_atendente(str(raw).strip())


def filter_comercial_LA_por_atendente(
    comercial_geral: List[Dict[str, Any]],
    atendente: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Restringe a lista aos registros de um único atendente.

    O critério de identidade é o mesmo de :func:`list_atendentes_comerciais` e dos
    gráficos por atendente LA (``_formatar_nome_atendente`` em caixa alta). O parâmetro
    ``atendente`` pode ser o nome completo vindo do banco ou o valor do filtro.

    Exemplo::

        base = filter_comercial_LA_por_atendente(dados, "Maria Silva")
        get_clientes_campanha(base)

    Se ``atendente`` for ``None`` ou string vazia, devolve uma cópia da lista sem filtro.
    """
    if atendente is None or not str(atendente).strip():
        return list(comercial_geral)
    alvo = _formatar_nome_atendente(str(atendente).strip())
    return [row for row in comercial_geral if _rotulo_atendente(row) == alvo]


def filter_comercial_LA_por_atendentes(
    comercial_geral: List[Dict[str, Any]],
    atendentes: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Restringe aos registros de um ou mais atendentes LA (união — OR)."""
    if not atendentes:
        return list(comercial_geral)
    alvos = {
        _formatar_nome_atendente(str(a).strip())
        for a in atendentes
        if a is not None and str(a).strip()
    }
    if not alvos:
        return list(comercial_geral)
    return [row for row in comercial_geral if _rotulo_atendente(row) in alvos]


# --- Segmento comercial (canal) — alinhado a get_clientes_*_LA / CANAL_AQUISICAO, motivo_encerramento == 4 ---

_MOTIVO_ENC_COMERCIAL_LA = 4

_CANAIS_CONTRATO_FECHADO_LA = frozenset({
    "ANUNCIO",
    "INDICAÇÃO",
    "REDES SOCIAIS",
    "RETORNO",
    "PARCEIRO",
    "EXTERNO",
})

SEGMENTOS_COMERCIAL_LA_ORDENADOS: tuple[str, ...] = (
    "CAMPANHA",
    "REDES_SOCIAIS",
    "INDICACAO",
    "RETORNO",
    "PARCEIROS",
    "EXTERNOS",
    "CANCELADOS",
)

SEGMENTOS_COMERCIAL_LA = frozenset(SEGMENTOS_COMERCIAL_LA_ORDENADOS)


def list_segmentos_comercial_la() -> List[str]:
    """Slugs para :func:`filter_comercial_LA_por_segmento` e query ``segmento_comercial_la``."""
    return list(SEGMENTOS_COMERCIAL_LA_ORDENADOS)


def normalizar_segmento_comercial_la(raw: str) -> str:
    """Normaliza texto da UI (ex.: ``REDES SOCIAIS``, ``indicacao``) para slug LA."""
    s = str(raw).strip().upper().replace(" ", "_")
    if s in ("INDICAÇÃO", "INDICAÇAO"):
        s = "INDICACAO"
    if s in SEGMENTOS_COMERCIAL_LA:
        return s
    raise ValueError(
        "segmento_comercial_la inválido: {!r}. Valores: {}".format(
            raw, ", ".join(SEGMENTOS_COMERCIAL_LA_ORDENADOS)
        )
    )


def _canal_aquisicao_comercial_la(row: Dict[str, Any]) -> str:
    v = row.get("CANAL_AQUISICAO") or row.get("canal_aquisicao")
    return str(v or "").strip().upper()


def _is_contrato_fechado_LA(row: Dict[str, Any]) -> bool:
    return (
        row.get("motivo_encerramento") == _MOTIVO_ENC_COMERCIAL_LA
        and _canal_aquisicao_comercial_la(row) in _CANAIS_CONTRATO_FECHADO_LA
    )


def row_pertence_segmento_comercial_LA(row: Dict[str, Any], segmento_normalizado: str) -> bool:
    """Predicado alinhado a ``get_clientes_*_LA`` e ``get_clientes_cancelados_LA``."""
    seg = segmento_normalizado
    if seg == "CANCELADOS":
        return (
            row.get("motivo_encerramento") == _MOTIVO_ENC_COMERCIAL_LA
            and str(row.get("STATUS_PROCESSO") or "").strip().upper() == "CANCELADO"
        )
    if row.get("motivo_encerramento") != _MOTIVO_ENC_COMERCIAL_LA:
        return False
    canal = _canal_aquisicao_comercial_la(row)
    if seg == "CAMPANHA":
        return canal == "ANUNCIO"
    if seg == "REDES_SOCIAIS":
        return canal == "REDES SOCIAIS"
    if seg == "INDICACAO":
        return canal == "INDICAÇÃO"
    if seg == "RETORNO":
        return canal == "RETORNO"
    if seg == "PARCEIROS":
        return canal == "PARCEIRO"
    if seg == "EXTERNOS":
        return canal == "EXTERNO"
    return False


def filter_comercial_LA_por_segmento(
    comercial_geral: List[Dict[str, Any]],
    segmento: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Restringe linhas ao segmento de canal LA (ou cancelados).

    ``segmento`` deve ser slug normalizado ou ``None``; strings brutas são normalizadas se necessário.
    """
    if segmento is None or not str(segmento).strip():
        return list(comercial_geral)
    key = normalizar_segmento_comercial_la(str(segmento).strip())
    return [r for r in comercial_geral if row_pertence_segmento_comercial_LA(r, key)]

# -----------------------------------------------------------------------------
# 2 - Funções de clientes
# -----------------------------------------------------------------------------

# Retorna os contratos de clientes de campanha
def get_clientes_campanha(comercial_geral: List[Dict[str, Any]]) -> int:
    # Filtrar registros que atendem aos critérios
    filtered = [
        c for c in comercial_geral
        if c.get("motivo_encerramento") == 4
        and c.get("CANAL_AQUISICAO") and str(c.get("CANAL_AQUISICAO", "")).upper() == "ANUNCIO"
    ]
    
    # Extrair valores distintos de ID_ACTION
    distinct_ids = set()
    for item in filtered:
        id_action = item.get("ID_ACTION")
        if id_action is not None:
            distinct_ids.add(id_action)
    return len(distinct_ids) if distinct_ids else 0

# Retorna os contratos de clientes de indicação
def get_clientes_indicacao_LA(comercial_geral: List[Dict[str, Any]]) -> int:
    # Filtrar registros que atendem aos critérios
    filtered = [
        c for c in comercial_geral
        if c.get("motivo_encerramento") == 4
        and c.get("CANAL_AQUISICAO") and str(c.get("CANAL_AQUISICAO", "")).upper() == "INDICAÇÃO"
    ]
    
    # Extrair valores distintos de ID_ACTION
    distinct_ids = set()
    for item in filtered:
        id_action = item.get("ID_ACTION")
        if id_action is not None:
            distinct_ids.add(id_action)
    return len(distinct_ids) if distinct_ids else 0

# Retorna os contratos de clientes de Redes Sociais
def get_clientes_redes_sociais_LA(comercial_geral: List[Dict[str, Any]]) -> int:
    # Filtrar registros que atendem aos critérios
    filtered = [
        c for c in comercial_geral
        if c.get("motivo_encerramento") == 4
        and c.get("CANAL_AQUISICAO") and str(c.get("CANAL_AQUISICAO", "")).upper() == "REDES SOCIAIS"
    ]
    
    # Extrair valores distintos de ID_ACTION
    distinct_ids = set()
    for item in filtered:
        id_action = item.get("ID_ACTION")
        if id_action is not None:
            distinct_ids.add(id_action)
    return len(distinct_ids) if distinct_ids else 0

# Retorna os contratos de clientes de Retorno
def get_clientes_retorno_LA(comercial_geral: List[Dict[str, Any]]) -> int:
    # Filtrar registros que atendem aos critérios
    filtered = [
        c for c in comercial_geral
        if c.get("motivo_encerramento") == 4
        and c.get("CANAL_AQUISICAO") and str(c.get("CANAL_AQUISICAO", "")).upper() == "RETORNO"
    ]
    
    # Extrair valores distintos de ID_ACTION
    distinct_ids = set()
    for item in filtered:
        id_action = item.get("ID_ACTION")
        if id_action is not None:
            distinct_ids.add(id_action)
    return len(distinct_ids) if distinct_ids else 0
    
# Retorna os contratos de clientes de Parceiro
def get_clientes_parceiro_LA(comercial_geral: List[Dict[str, Any]]) -> int:
    # Filtrar registros que atendem aos critérios
    filtered = [
        c for c in comercial_geral
        if c.get("motivo_encerramento") == 4
        and c.get("CANAL_AQUISICAO") and str(c.get("CANAL_AQUISICAO", "")).upper() == "PARCEIRO"
    ]
    
    # Extrair valores distintos de ID_ACTION
    distinct_ids = set()
    for item in filtered:
        id_action = item.get("ID_ACTION")
        if id_action is not None:
            distinct_ids.add(id_action)
    return len(distinct_ids) if distinct_ids else 0

# Retorna os contratos de clientes de Externos
def get_clientes_externos_LA(comercial_geral: List[Dict[str, Any]]) -> int:
    # Filtrar registros que atendem aos critérios
    filtered = [
        c for c in comercial_geral
        if c.get("motivo_encerramento") == 4
        and c.get("CANAL_AQUISICAO") and str(c.get("CANAL_AQUISICAO", "")).upper() == "EXTERNO"
    ]
    
    # Extrair valores distintos de ID_ACTION
    distinct_ids = set()
    for item in filtered:
        id_action = item.get("ID_ACTION")
        if id_action is not None:
            distinct_ids.add(id_action)
    return len(distinct_ids) if distinct_ids else 0

# Retorna Todos os contratos de clientes
def get_clientes_todos_LA(comercial_geral: List[Dict[str, Any]]) -> int:
    # Soma todas as análises comerciais realizadas
    return (
        get_clientes_campanha(comercial_geral) +
        get_clientes_indicacao_LA(comercial_geral) +
        get_clientes_redes_sociais_LA(comercial_geral) +
        get_clientes_retorno_LA(comercial_geral) +
        get_clientes_parceiro_LA(comercial_geral) +
        get_clientes_externos_LA(comercial_geral)
    )

# Retorna o total de cancelados
def get_clientes_cancelados_LA(comercial_geral: List[Dict[str, Any]]) -> int:
    # Filtrar registros que atendem aos critérios
    filtered = [
        c for c in comercial_geral
        if c.get("motivo_encerramento") == 4
        and c.get("STATUS_PROCESSO") == "CANCELADO"
    ]
    return len(filtered) if filtered else 0

# -----------------------------------------------------------------------------
# 3 - Funções de ações
# -----------------------------------------------------------------------------

# Retorna o total de ações fechadas LA
def get_acoes_fechadas_LA(comercial_geral: List[Dict[str, Any]]) -> int:
    # Filtrar registros que atendem aos critérios
    filtered = [
        c for c in comercial_geral
        if c.get("motivo_encerramento") == 4
        and c.get("STATUS_PROCESSO") == "EM ANDAMENTO"
    ]
    return len(filtered) if filtered else 0


_RUBRICAS_REUNIDAS_IDS_LA = frozenset({184, 209})


def get_rubricas_reunidas_fechadas_LA(comercial_geral: List[Dict[str, Any]]) -> int:
    """Conta ações distintas do tipo rubrica reunida (IDs 184 e 209) fechadas no período."""
    seen: set = set()
    for c in comercial_geral:
        if (
            c.get("motivo_encerramento") == 4
            and c.get("STATUS_PROCESSO") == "EM ANDAMENTO"
            and c.get("ID_RUBRICA") in _RUBRICAS_REUNIDAS_IDS_LA
        ):
            id_action = c.get("ID_ACTION")
            if id_action is not None:
                seen.add(id_action)
    return len(seen)


def group_contratos_fechados_por_mes_LA(comercial_geral: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa a quantidade de contratos fechados por mês."""
    grouped: Dict[str, Dict[str, Any]] = {}
    ids_por_mes: Dict[str, set] = defaultdict(set)

    for c in comercial_geral:
        try:
            if not _is_contrato_fechado_LA(c):
                continue

            assinatura_date = _get_data_assinatura_LA(c)
            if not assinatura_date:
                continue

            id_action = c.get("ID_ACTION")
            if id_action is None:
                continue

            month_key = f"{assinatura_date.year}-{assinatura_date.month:02d}"

            if month_key not in grouped:
                month_name = f"{_MONTH_NAMES[assinatura_date.month - 1]} {assinatura_date.year}"
                grouped[month_key] = {"name": month_name, "value": 0}

            ids_por_mes[month_key].add(id_action)

        except (ValueError, AttributeError, TypeError):
            continue

    for month_key, ids in ids_por_mes.items():
        grouped[month_key]["value"] = len(ids)

    return [item for _, item in sorted(grouped.items(), key=lambda x: x[0])]


def group_processos_fechados_por_mes_LA(comercial_geral: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa a quantidade de processos fechados por mês."""
    grouped: Dict[str, Dict[str, Any]] = {}

    for c in comercial_geral:
        try:
            if not _is_acao_fechada_LA(c):
                continue

            assinatura_date = _get_data_assinatura_LA(c)
            if not assinatura_date:
                continue

            month_key = f"{assinatura_date.year}-{assinatura_date.month:02d}"

            if month_key not in grouped:
                month_name = f"{_MONTH_NAMES[assinatura_date.month - 1]} {assinatura_date.year}"
                grouped[month_key] = {"name": month_name, "value": 0}

            grouped[month_key]["value"] += 1

        except (ValueError, AttributeError, TypeError):
            continue

    return [item for _, item in sorted(grouped.items(), key=lambda x: x[0])]


def group_contratos_fechados_por_dia_LA(comercial_geral: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa a quantidade de contratos fechados por dia."""
    grouped: Dict[str, Dict[str, Any]] = {}
    ids_por_dia: Dict[str, set] = defaultdict(set)

    for c in comercial_geral:
        try:
            if not _is_contrato_fechado_LA(c):
                continue

            assinatura_date = _get_data_assinatura_LA(c)
            if not assinatura_date:
                continue

            id_action = c.get("ID_ACTION")
            if id_action is None:
                continue

            dia_key = assinatura_date.strftime("%Y-%m-%d")

            if dia_key not in grouped:
                grouped[dia_key] = {"name": dia_key, "value": 0}

            ids_por_dia[dia_key].add(id_action)

        except (ValueError, AttributeError, TypeError):
            continue

    for dia_key, ids in ids_por_dia.items():
        grouped[dia_key]["value"] = len(ids)

    return [item for _, item in sorted(grouped.items(), key=lambda x: x[0])]


def group_acoes_fechadas_por_dia_LA(comercial_geral: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa a quantidade de ações fechadas por dia."""
    grouped: Dict[str, Dict[str, Any]] = {}

    for c in comercial_geral:
        try:
            if not _is_acao_fechada_LA(c):
                continue

            assinatura_date = _get_data_assinatura_LA(c)
            if not assinatura_date:
                continue

            dia_key = assinatura_date.strftime("%Y-%m-%d")

            if dia_key not in grouped:
                grouped[dia_key] = {"name": dia_key, "value": 0}

            grouped[dia_key]["value"] += 1

        except (ValueError, AttributeError, TypeError):
            continue

    return [item for _, item in sorted(grouped.items(), key=lambda x: x[0])]

def _agrupar_acoes_fechadas_por_rubrica_canal_LA(
    comercial_geral: List[Dict[str, Any]],
    *,
    canal_aquisicao: str,
) -> List[Dict[str, Any]]:
    """
    Ações fechadas LA (`motivo_encerramento == 4`, `STATUS_PROCESSO == "EM ANDAMENTO"`),
    filtradas por `CANAL_AQUISICAO`, agrupadas por `RUBRICA`.

    Retorno: `[{"name": str, "value": int, "percent": float}, ...]` (percent 0–100, 1 casa).
    """
    canal_alvo = str(canal_aquisicao or "").strip().upper()
    grouped: Dict[str, int] = defaultdict(int)
    for item in get_acoes_fechadas_registros_LA(comercial_geral):
        canal = str(item.get("CANAL_AQUISICAO") or "").strip().upper()
        if not canal or canal != canal_alvo:
            continue
        rubrica = item.get("RUBRICA") or "Sem rubrica"
        grouped[str(rubrica)] += 1

    items: List[Dict[str, Any]] = [
        {"name": str(name), "value": int(value)}
        for name, value in grouped.items()
    ]
    items.sort(key=lambda x: x["value"], reverse=True)
    total = sum(int(x["value"]) for x in items)
    if total > 0:
        for x in items:
            x["percent"] = round(100.0 * float(x["value"]) / float(total), 1)
    else:
        for x in items:
            x["percent"] = 0.0
    return items


def get_acoes_fechadas_campanha_LA(comercial_geral: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ações fechadas LA de campanha: `CANAL_AQUISICAO == CAMPANHA`."""
    return _agrupar_acoes_fechadas_por_rubrica_canal_LA(
        comercial_geral, canal_aquisicao="ANUNCIO"
    )


def get_acoes_fechadas_indicacao_LA(comercial_geral: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ações fechadas LA de indicação: `CANAL_AQUISICAO == INDICAÇÃO`."""
    return _agrupar_acoes_fechadas_por_rubrica_canal_LA(
        comercial_geral, canal_aquisicao="INDICAÇÃO"
    )


def get_acoes_fechadas_retorno_LA(comercial_geral: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ações fechadas LA de retorno: `CANAL_AQUISICAO == RETORNO`."""
    return _agrupar_acoes_fechadas_por_rubrica_canal_LA(
        comercial_geral, canal_aquisicao="RETORNO"
    )


def get_acoes_fechadas_redes_sociais_LA(
    comercial_geral: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Ações fechadas LA de redes sociais: `CANAL_AQUISICAO == REDES SOCIAIS`."""
    return _agrupar_acoes_fechadas_por_rubrica_canal_LA(
        comercial_geral, canal_aquisicao="REDES SOCIAIS"
    )


def get_acoes_fechadas_parceiros_LA(comercial_geral: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ações fechadas LA de parceiros: `CANAL_AQUISICAO == PARCEIRO`."""
    return _agrupar_acoes_fechadas_por_rubrica_canal_LA(
        comercial_geral, canal_aquisicao="PARCEIRO"
    )


def get_acoes_fechadas_externos_LA(comercial_geral: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ações fechadas LA de clientes externos: `CANAL_AQUISICAO == EXTERNO`."""
    return _agrupar_acoes_fechadas_por_rubrica_canal_LA(
        comercial_geral, canal_aquisicao="EXTERNO"
    )

# Retorna o total de ações fechadas agrupadas por RUBRICA (LA)
def get_total_acoes_fechadas_por_rubrica_LA(
    comercial_geral: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    listas = [
        get_acoes_fechadas_campanha_LA(comercial_geral),
        get_acoes_fechadas_indicacao_LA(comercial_geral),
        get_acoes_fechadas_retorno_LA(comercial_geral),
        get_acoes_fechadas_redes_sociais_LA(comercial_geral),
        get_acoes_fechadas_parceiros_LA(comercial_geral),
        get_acoes_fechadas_externos_LA(comercial_geral),
    ]
    grouped: Dict[str, int] = defaultdict(int)
    for lista in listas:
        for item in lista:
            name = item.get("name") or "Sem rubrica"
            value = item.get("value") or 0
            grouped[str(name)] += int(value)
    items: List[Dict[str, Any]] = [
        {"name": str(name), "value": int(value)}
        for name, value in grouped.items()
    ]
    items.sort(key=lambda x: x["value"], reverse=True)
    total = sum(int(x["value"]) for x in items)
    if total > 0:
        for x in items:
            x["percent"] = round(100.0 * float(x["value"]) / float(total), 1)
    else:
        for x in items:
            x["percent"] = 0.0
    return items


# Retorna a taxa de aproveitamento
def get_taxa_aproveitamento_LA(comercial_geral: List[Dict[str, Any]]) -> float:
    acoes_fechadas = get_acoes_fechadas_LA(comercial_geral)
    clientes_todos = get_clientes_todos_LA(comercial_geral)
    
    # Evitar divisão por zero
    if clientes_todos == 0:
        return 0.0
    
    # Calcular taxa em porcentagem
    taxa = (acoes_fechadas / clientes_todos)
    return round(taxa, 2)


# -----------------------------------------------------------------------------
# 4 - Funções de comparativos
# -----------------------------------------------------------------------------

def _valor_periodo_anterior_LA(
    comercial_geral: List[Dict[str, Any]],
    all_comercial_geral: Optional[List[Dict[str, Any]]],
    from_date: Optional[date],
    to_date: Optional[date],
    metrica_fn,
) -> float:
    """
    Valor absoluto da métrica no período anterior (mesmo recorte de calendário
    usado pelas funções ``get_comparativo_*_LA``).

    Necessário porque o Estratégico Geral combina NG+LA+RJ somando os valores
    absolutos de cada escritório antes de calcular UM percentual combinado —
    nunca somando os percentuais de cada escritório entre si (matematicamente
    inválido: dois +30% de bases diferentes não fazem um +60% combinado).
    """
    dados_para_busca = all_comercial_geral if all_comercial_geral is not None else comercial_geral
    _, _, data_inicio_anterior, data_fim_anterior = resolver_periodo_comparativo(from_date, to_date)
    return metrica_fn(
        _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)
    )


def get_clientes_total_periodo_anterior_LA(
    comercial_geral: List[Dict[str, Any]],
    all_comercial_geral: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    return _valor_periodo_anterior_LA(
        comercial_geral, all_comercial_geral, from_date, to_date, get_clientes_todos_LA
    )


def get_acoes_fechadas_periodo_anterior_LA(
    comercial_geral: List[Dict[str, Any]],
    all_comercial_geral: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    return _valor_periodo_anterior_LA(
        comercial_geral, all_comercial_geral, from_date, to_date, get_acoes_fechadas_LA
    )


# Retorna a Variação percentual comparativa de clientes de campanha LA
def get_comparativo_clientes_campanha_LA(
    comercial_geral: List[Dict[str, Any]],
    all_comercial_geral: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    # Usar dados não filtrados para calcular período anterior (pode estar fora do filtro atual)
    dados_para_busca = all_comercial_geral if all_comercial_geral is not None else comercial_geral
    
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )
    
    # Filtrar dados dos períodos atual e anterior
    # Período atual: usar dados filtrados se disponível, senão filtrar dos dados completos
    dados_periodo_atual = _filter_by_date_range(comercial_geral, data_inicio_atual, data_fim_atual)
    # Período anterior: sempre usar dados completos (pode estar fora do filtro)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)
    
    # Calcular quantidade de clientes de campanha LA para cada período
    qtd_atual = get_clientes_campanha(dados_periodo_atual)
    qtd_anterior = get_clientes_campanha(dados_periodo_anterior)
    
    # Calcular variação percentual: (atual - anterior) / anterior * 100
    # Equivalente ao DIVIDE do DAX
    if qtd_anterior == 0:
        return 0.0
    
    variacao = ((qtd_atual - qtd_anterior) / qtd_anterior) * 100
    return round(variacao, 2)

# Retorna a Variação percentual comparativa de clientes de indicação LA
def get_comparativo_clientes_indicacao_LA(
    comercial_geral: List[Dict[str, Any]],
    all_comercial_geral: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    # Usar dados não filtrados para calcular período anterior (pode estar fora do filtro atual)
    dados_para_busca = all_comercial_geral if all_comercial_geral is not None else comercial_geral
    
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )
    
    # Filtrar dados dos períodos atual e anterior
    # Período atual: usar dados filtrados se disponível, senão filtrar dos dados completos
    dados_periodo_atual = _filter_by_date_range(comercial_geral, data_inicio_atual, data_fim_atual)
    # Período anterior: sempre usar dados completos (pode estar fora do filtro)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)
    
    # Calcular quantidade de clientes de indicação LA para cada período
    qtd_atual = get_clientes_indicacao_LA(dados_periodo_atual)
    qtd_anterior = get_clientes_indicacao_LA(dados_periodo_anterior)
    
    # Calcular variação percentual: (atual - anterior) / anterior * 100
    # Equivalente ao DIVIDE do DAX
    if qtd_anterior == 0:
        return 0.0
    
    variacao = ((qtd_atual - qtd_anterior) / qtd_anterior) * 100
    return round(variacao, 2)

# Retorna a Variação percentual comparativa de clientes de redes sociais LA
def get_comparativo_clientes_redes_sociais_LA(
    comercial_geral: List[Dict[str, Any]],
    all_comercial_geral: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    # Usar dados não filtrados para calcular período anterior (pode estar fora do filtro atual)
    dados_para_busca = all_comercial_geral if all_comercial_geral is not None else comercial_geral
    
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )
    
    # Filtrar dados dos períodos atual e anterior
    # Período atual: usar dados filtrados se disponível, senão filtrar dos dados completos
    dados_periodo_atual = _filter_by_date_range(comercial_geral, data_inicio_atual, data_fim_atual)
    # Período anterior: sempre usar dados completos (pode estar fora do filtro)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)
    
    # Calcular quantidade de clientes de redes sociais LA para cada período
    qtd_atual = get_clientes_redes_sociais_LA(dados_periodo_atual)
    qtd_anterior = get_clientes_redes_sociais_LA(dados_periodo_anterior)
    
    # Calcular variação percentual: (atual - anterior) / anterior * 100
    # Equivalente ao DIVIDE do DAX
    if qtd_anterior == 0:
        return 0.0
    
    variacao = ((qtd_atual - qtd_anterior) / qtd_anterior) * 100
    return round(variacao, 2)

# Retorna a Variação percentual comparativa de clientes de retorno LA
def get_comparativo_clientes_retorno_LA(
    comercial_geral: List[Dict[str, Any]],
    all_comercial_geral: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    # Usar dados não filtrados para calcular período anterior (pode estar fora do filtro atual)
    dados_para_busca = all_comercial_geral if all_comercial_geral is not None else comercial_geral
    
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )
    
    # Filtrar dados dos períodos atual e anterior
    # Período atual: usar dados filtrados se disponível, senão filtrar dos dados completos
    dados_periodo_atual = _filter_by_date_range(comercial_geral, data_inicio_atual, data_fim_atual)
    # Período anterior: sempre usar dados completos (pode estar fora do filtro)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)
    
    # Calcular quantidade de clientes de retorno LA para cada período
    qtd_atual = get_clientes_retorno_LA(dados_periodo_atual)
    qtd_anterior = get_clientes_retorno_LA(dados_periodo_anterior)
    
    # Calcular variação percentual: (atual - anterior) / anterior * 100
    # Equivalente ao DIVIDE do DAX
    if qtd_anterior == 0:
        return 0.0
    
    variacao = ((qtd_atual - qtd_anterior) / qtd_anterior) * 100
    return round(variacao, 2)

# Retorna a Variação percentual comparativa de clientes de parceiro LA
def get_comparativo_clientes_parceiro_LA(
    comercial_geral: List[Dict[str, Any]],
    all_comercial_geral: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    # Usar dados não filtrados para calcular período anterior (pode estar fora do filtro atual)
    dados_para_busca = all_comercial_geral if all_comercial_geral is not None else comercial_geral
    
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )
    
    # Filtrar dados dos períodos atual e anterior
    # Período atual: usar dados filtrados se disponível, senão filtrar dos dados completos
    dados_periodo_atual = _filter_by_date_range(comercial_geral, data_inicio_atual, data_fim_atual)
    # Período anterior: sempre usar dados completos (pode estar fora do filtro)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)
    
    # Calcular quantidade de clientes de parceiro LA para cada período
    qtd_atual = get_clientes_parceiro_LA(dados_periodo_atual)
    qtd_anterior = get_clientes_parceiro_LA(dados_periodo_anterior)
    
    # Calcular variação percentual: (atual - anterior) / anterior * 100
    # Equivalente ao DIVIDE do DAX
    if qtd_anterior == 0:
        return 0.0
    
    variacao = ((qtd_atual - qtd_anterior) / qtd_anterior) * 100
    return round(variacao, 2)

# Retorna a Variação percentual comparativa de clientes de externos LA
def get_comparativo_clientes_externos_LA(
    comercial_geral: List[Dict[str, Any]],
    all_comercial_geral: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    # Usar dados não filtrados para calcular período anterior (pode estar fora do filtro atual)
    dados_para_busca = all_comercial_geral if all_comercial_geral is not None else comercial_geral
    
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )
    
    # Filtrar dados dos períodos atual e anterior
    # Período atual: usar dados filtrados se disponível, senão filtrar dos dados completos
    dados_periodo_atual = _filter_by_date_range(comercial_geral, data_inicio_atual, data_fim_atual)
    # Período anterior: sempre usar dados completos (pode estar fora do filtro)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)
    
    # Calcular quantidade de clientes de externos LA para cada período
    qtd_atual = get_clientes_externos_LA(dados_periodo_atual)
    qtd_anterior = get_clientes_externos_LA(dados_periodo_anterior)
    
    # Calcular variação percentual: (atual - anterior) / anterior * 100
    # Equivalente ao DIVIDE do DAX
    if qtd_anterior == 0:
        return 0.0
    
    variacao = ((qtd_atual - qtd_anterior) / qtd_anterior) * 100
    return round(variacao, 2)

# Retorna a Variação percentual comparativa de total de clientes LA
def get_comparativo_clientes_total_LA(
    comercial_geral: List[Dict[str, Any]],
    all_comercial_geral: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    # Usar dados não filtrados para calcular período anterior (pode estar fora do filtro atual)
    dados_para_busca = all_comercial_geral if all_comercial_geral is not None else comercial_geral
    
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )
    
    # Filtrar dados dos períodos atual e anterior
    # Período atual: usar dados filtrados se disponível, senão filtrar dos dados completos
    dados_periodo_atual = _filter_by_date_range(comercial_geral, data_inicio_atual, data_fim_atual)
    # Período anterior: sempre usar dados completos (pode estar fora do filtro)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)
    
    # Calcular quantidade de clientes total LA para cada período
    qtd_atual = get_clientes_todos_LA(dados_periodo_atual)
    qtd_anterior = get_clientes_todos_LA(dados_periodo_anterior)
    
    # Calcular variação percentual: (atual - anterior) / anterior * 100
    # Equivalente ao DIVIDE do DAX
    if qtd_anterior == 0:
        return 0.0
    
    variacao = ((qtd_atual - qtd_anterior) / qtd_anterior) * 100
    return round(variacao, 2)

# Retorna a Variação percentual comparativa de clientes cancelados LA
def get_comparativo_clientes_cancelados_LA(
    comercial_geral: List[Dict[str, Any]],
    all_comercial_geral: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    # Usar dados não filtrados para calcular período anterior (pode estar fora do filtro atual)
    dados_para_busca = all_comercial_geral if all_comercial_geral is not None else comercial_geral
    
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )
    
    # Filtrar dados dos períodos atual e anterior
    # Período atual: usar dados filtrados se disponível, senão filtrar dos dados completos
    dados_periodo_atual = _filter_by_date_range(comercial_geral, data_inicio_atual, data_fim_atual)
    # Período anterior: sempre usar dados completos (pode estar fora do filtro)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)
    
    # Calcular quantidade de clientes cancelados LA para cada período
    qtd_atual = get_clientes_cancelados_LA(dados_periodo_atual)
    qtd_anterior = get_clientes_cancelados_LA(dados_periodo_anterior)
    
    # Calcular variação percentual: (atual - anterior) / anterior * 100
    # Equivalente ao DIVIDE do DAX
    if qtd_anterior == 0:
        return 0.0
    
    variacao = ((qtd_atual - qtd_anterior) / qtd_anterior) * 100
    return round(variacao, 2)

# Retorna o comparativo da taxa de aproveitamento LA
def get_comparativo_taxa_aproveitamento_LA(
    comercial_geral: List[Dict[str, Any]],
    all_comercial_geral: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    # Usar dados não filtrados para calcular período anterior (pode estar fora do filtro atual)
    dados_para_busca = all_comercial_geral if all_comercial_geral is not None else comercial_geral
    
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )
    
    # Filtrar dados dos períodos atual e anterior
    # Período atual: usar dados filtrados se disponível, senão filtrar dos dados completos
    dados_periodo_atual = _filter_by_date_range(comercial_geral, data_inicio_atual, data_fim_atual)
    # Período anterior: sempre usar dados completos (pode estar fora do filtro)

    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)
    
    # Calcular quantidade de clientes de parceiro LA para cada período
    qtd_atual = get_taxa_aproveitamento_LA(dados_periodo_atual) 
    qtd_anterior = get_taxa_aproveitamento_LA(dados_periodo_anterior)
    if qtd_anterior == 0:
        return 0.0
    
    variacao = ((qtd_atual - qtd_anterior) / qtd_anterior) * 100
    return round(variacao, 2)

# Retorna a variação comparativa de ações fechadas LA
def get_comparativo_acoes_fechadas_LA(
    comercial_geral: List[Dict[str, Any]],
    all_comercial_geral: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    # Usar dados não filtrados para calcular período anterior (pode estar fora do filtro atual)
    dados_para_busca = all_comercial_geral if all_comercial_geral is not None else comercial_geral
    
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )
    
    # Filtrar dados dos períodos atual e anterior
    # Período atual: usar dados filtrados se disponível, senão filtrar dos dados completos
    dados_periodo_atual = _filter_by_date_range(comercial_geral, data_inicio_atual, data_fim_atual)
    # Período anterior: sempre usar dados completos (pode estar fora do filtro)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)
    
    # Calcular quantidade de ações fechadas LA para cada período
    qtd_atual = get_acoes_fechadas_LA(dados_periodo_atual)
    qtd_anterior = get_acoes_fechadas_LA(dados_periodo_anterior)
    
    # Calcular variação percentual: (atual - anterior) / anterior * 100
    # Equivalente ao DIVIDE do DAX
    if qtd_anterior == 0:
        return 0.0
    
    variacao = ((qtd_atual - qtd_anterior) / qtd_anterior) * 100
    return round(variacao, 2)

# -----------------------------------------------------------------------------
# 5 - Funções por atendente
# -----------------------------------------------------------------------------

# Retorna ações fechadas por atendente
def get_total_acoes_fechadas_por_atendente_LA(comercial_geral: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Filtrar registros que atendem aos critérios
    filtered = [
        c for c in comercial_geral
        if c.get("motivo_encerramento") == 4
        and c.get("STATUS_PROCESSO") == "EM ANDAMENTO"
    ]
    grouped = defaultdict(int)
    for item in filtered:
        atendente = item.get("ATENDENTE") or "Sem atendente"
        atendente_formatado = _formatar_nome_atendente(atendente)
        grouped[atendente_formatado] += 1
    result = [
        {"name": name, "value": value}
        for name, value in grouped.items()
    ]
    return sorted(result, key=lambda x: x["value"], reverse=True) [:5]

# Agrupa ações fechadas diariamente (por atendente)
def group_acoes_fechadas_diariamente_por_atendente_LA(comercial_geral: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa ações fechadas do dia atual por atendente usando os mesmos critérios de get_total_acoes_fechadas_por_atendente_LA."""
    from datetime import date as date_type, datetime as datetime_type

    hoje = date.today()
    filtered = []
    for c in comercial_geral:
        if (c.get("motivo_encerramento") == 4
            and c.get("STATUS_PROCESSO") == "EM ANDAMENTO"):
            data = c.get("ASSINADO_EM") or c.get("assinado_em")
            if data:
                data_obj = parse_date_from_db(data)
                if data_obj:
                    if isinstance(data_obj, datetime_type):
                        data_key = data_obj.date()
                    elif isinstance(data_obj, date_type):
                        data_key = data_obj
                    else:
                        continue

                    if data_key == hoje:
                        filtered.append(c)

    grouped = defaultdict(int)
    for item in filtered:
        atendente = item.get("ATENDENTE") or "Sem atendente"
        atendente_formatado = _formatar_nome_atendente(atendente)
        grouped[atendente_formatado] += 1
    result = [
        {"name": name, "value": value}
        for name, value in grouped.items()
    ]
    return sorted(result, key=lambda x: x["value"], reverse=True)

# Agrupa contratos fechados diariamente por atendente
def group_contratos_fechados_diariamente_por_atendente_LA(comercial_geral: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa contratos fechados do dia atual por atendente usando os mesmos critérios de get_clientes_todos_LA."""
    from datetime import date as date_type, datetime as datetime_type

    hoje = date.today()
    filtered = []
    for c in comercial_geral:
        if (c.get("motivo_encerramento") == 4
            and c.get("STATUS_PROCESSO") == "EM ANDAMENTO"):
            data = c.get("ASSINADO_EM") or c.get("assinado_em")
            if data:
                data_obj = parse_date_from_db(data)
                if data_obj:
                    if isinstance(data_obj, datetime_type):
                        data_key = data_obj.date()
                    elif isinstance(data_obj, date_type):
                        data_key = data_obj
                    else:
                        continue

                    if data_key == hoje:
                        filtered.append(c)

    atendente_ids = defaultdict(set)
    for item in filtered:
        id_action = item.get("ID_ACTION")
        if id_action is not None:
            atendente = item.get("ATENDENTE") or "Sem atendente"
            atendente_formatado = _formatar_nome_atendente(atendente)
            atendente_ids[atendente_formatado].add(id_action)

    grouped = {atendente: len(ids) for atendente, ids in atendente_ids.items()}
    result = [
        {"name": name, "value": value}
        for name, value in grouped.items()
    ]
    return sorted(result, key=lambda x: x["value"], reverse=True)

# -----------------------------------------------------------------------------
# 6 - Analises de comissão
# -----------------------------------------------------------------------------

def _converter_valor_LA(valor_raw: any) -> float:
    """Converte um valor monetário (string ou numérico) para float."""
    if valor_raw is None:
        return 0.0

    # asyncpg pode retornar Decimal para campos NUMERIC
    if isinstance(valor_raw, (int, float, Decimal)):
        return float(valor_raw)

    valor_str = str(valor_raw).strip()
    if not valor_str:
        return 0.0

    # Normaliza prefixo/sufixo e espaços
    valor_str = (
        valor_str.replace("R$", "")
        .replace("\u00a0", "")  # NBSP
        .replace(" ", "")
        .strip()
    )

    # Heurística pt-BR vs en-US:
    # - Se tiver "." e "," assume "." milhar e "," decimal (ex.: 1.234,56)
    # - Se tiver só "," assume "," decimal (ex.: 470,00)
    # - Se tiver só "." assume "." decimal (ex.: 470.00) -> NÃO remover o ponto
    if "," in valor_str and "." in valor_str:
        valor_str = valor_str.replace(".", "").replace(",", ".")
    elif "," in valor_str and "." not in valor_str:
        valor_str = valor_str.replace(",", ".")
    else:
        # somente "." ou nenhum separador: mantém como está
        pass

    try:
        return float(valor_str)
    except (ValueError, TypeError):
        return 0.0


def _is_acao_fechada_LA(row: Dict[str, Any]) -> bool:
    """
    Critérios base de "ação fechada" usados no painel comercial.
    Mantém a mesma regra de `get_acoes_fechadas` para evitar divergência.
    """
    return (
        row.get("motivo_encerramento") == 4
        and row.get("STATUS_PROCESSO") == "EM ANDAMENTO"
    )


def get_acoes_fechadas_registros_LA(
    comercial_geral: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Retorna os registros (linhas) de ações fechadas.

    No LA, o recorte é apenas um estado (AM). O critério de "fechada" é `motivo_encerramento = 4`
    (com `STATUS_PROCESSO = "EM ANDAMENTO"`), e os valores monetários vêm do campo `VALOR`.
    """
    filtered = [c for c in comercial_geral if _is_acao_fechada_LA(c)]
    return filtered


def get_comissao_base_por_acao_LA(comercial_geral: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Lista a comissão base calculada por ação (LA/AM).

    O valor unitário vem da coluna `VALOR` (juridico.rubricas); o payload expõe `VALOR_AM`
    para o mesmo contrato do painel NG / tabela de rubricas.
    """
    acoes = get_acoes_fechadas_registros_LA(comercial_geral)
    itens: List[Dict[str, Any]] = []
    for item in acoes:
        valor_am = _converter_valor_LA(item.get("VALOR"))
        itens.append(
            {
                "ID_ACTION": item.get("ID_ACTION"),
                "RUBRICA": item.get("RUBRICA"),
                "VALOR_AM": valor_am,
                "COMISSAO_BASE": round(valor_am, 2),
            }
        )
    return itens


def get_comissao_base_por_rubrica_LA(comercial_geral: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Soma a comissão base agrupada por RUBRICA (LA/AM).
    Formato compatível com outros agrupamentos: [{"name": <rubrica>, "value": <total>}]
    """
    grouped: Dict[str, float] = defaultdict(float)
    for item in get_comissao_base_por_acao_LA(comercial_geral):
        rubrica = item.get("RUBRICA") or "Sem rubrica"
        grouped[str(rubrica)] += float(item.get("COMISSAO_BASE") or 0.0)

    result = [{"name": name, "value": round(value, 2)} for name, value in grouped.items()]
    return sorted(result, key=lambda x: x["value"], reverse=True)


def get_rubricas_total_tabela_LA(comercial_geral: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Tabela "RUBRICAS TOTAL" (LA): por rubrica, AÇÕES (ações fechadas),
    valor_am (unitário a partir da coluna `VALOR` no banco) e TOTAL (soma da comissão base),
    no mesmo formato JSON que `get_rubricas_total_tabela` (NG) — chave `valor_am`.

    Quando todas as linhas da rubrica têm o mesmo valor unitário, TOTAL = ACOES × valor_am.
    """
    por_acao = get_comissao_base_por_acao_LA(comercial_geral)
    grouped: Dict[str, Dict[str, Any]] = {}
    for item in por_acao:
        rub = str(item.get("RUBRICA") or "Sem rubrica")
        if rub not in grouped:
            grouped[rub] = {"acoes": 0, "linhas_cb": [], "valores_unit": []}
        grouped[rub]["acoes"] += 1
        grouped[rub]["linhas_cb"].append(float(item.get("COMISSAO_BASE") or 0.0))
        grouped[rub]["valores_unit"].append(float(item.get("VALOR_AM") or 0.0))

    rows: List[Dict[str, Any]] = []
    for rubrica, data in grouped.items():
        acoes = int(data["acoes"])
        linhas_cb = data["linhas_cb"]
        valores_unit = data["valores_unit"]
        total = round(sum(linhas_cb), 2)
        if acoes > 0 and valores_unit and all(
            abs(u - valores_unit[0]) < 1e-9 for u in valores_unit
        ):
            valor_am = round(valores_unit[0], 2)
        elif acoes > 0:
            valor_am = round(total / acoes, 2)
        else:
            valor_am = 0.0
        rows.append(
            {
                "rubrica": rubrica,
                "acoes": acoes,
                "valor_am": valor_am,
                "total": total,
            }
        )
    rows.sort(key=lambda x: (-x["acoes"], str(x["rubrica"])))
    return rows


def get_comissao_base_LA(comercial_geral: List[Dict[str, Any]]) -> float:
    """
    Calcula a comissão base (LA/AM): para cada ação fechada, soma o `VALOR`.

    Equivalente DAX:
    COMISSAO_BASE = SUMX(FILTER(comercial_geral_NG, UF <> "RJ"), [QTD_TOTAL_ACOES] * VALUE(SUBSTITUTE(VALOR_AM, "R$ ", "")))
    """
    total = 0.0
    for item in get_acoes_fechadas_registros_LA(comercial_geral):
        total += _converter_valor_LA(item.get("VALOR"))
    return round(total, 2)


def get_comercial_comissionamento_por_atendente_LA(
    comercial_geral: List[Dict[str, Any]],
    protocolos: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Relatório de comissão LA por atendente (sem proporcional AM/PA/PB).

    Campos: atendente, acoes, comissao_base, valor_fm (1–4 conforme valor de causa protocolado
    daquele atendente), comissao_com_fm = comissao_base × valor_fm.
    """
    from app.analyses.LA.protocolo_LA import (
        get_fator_multiplicador_para_atingido_LA,
        get_valor_causa_protocolado_por_atendente_LA,
    )

    acoes_regs = get_acoes_fechadas_registros_LA(comercial_geral)
    por_atendente: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"acoes": 0, "comissao_base": 0.0})
    for item in acoes_regs:
        nome = item.get("ATENDENTE") or "Sem atendente"
        chave = _formatar_nome_atendente(str(nome).strip())
        por_atendente[chave]["acoes"] += 1
        por_atendente[chave]["comissao_base"] += _converter_valor_LA(item.get("VALOR"))

    valor_causa_por_atendente = get_valor_causa_protocolado_por_atendente_LA(protocolos)

    linhas: List[Dict[str, Any]] = []
    for atendente, agg in por_atendente.items():
        cb = round(float(agg["comissao_base"]), 2)
        n_acoes = int(agg["acoes"])
        atingido_att = float(valor_causa_por_atendente.get(atendente, 0.0) or 0.0)
        fm_att = float(get_fator_multiplicador_para_atingido_LA(atingido_att))
        valor_fm = round(fm_att, 2)
        comissao_com_fm = round(cb * fm_att, 2)
        linhas.append({
            "atendente": atendente,
            "acoes": n_acoes,
            "comissao_base": cb,
            "valor_fm": valor_fm,
            "comissao_com_fm": comissao_com_fm,
        })

    linhas.sort(key=lambda x: (-x["comissao_com_fm"], str(x["atendente"])))
    return linhas