# Análises e processamento de dados de COMERCIAL GERAL

from typing import List, Dict, Any, Optional, Callable, Set, Union
from datetime import datetime, date
from collections import defaultdict
import logging
import statistics
from decimal import Decimal
from app.utils import parse_date_from_db, resolver_periodo_comparativo, normalizar_filtro_ids

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# 1 - Funções auxiliares
# -----------------------------------------------------------------------------

def _formatar_nome_atendente(nome_completo: str) -> str:
    """Extrai apenas o primeiro e segundo nome da atendente."""
    if not nome_completo or nome_completo == "Sem atendente":
        return nome_completo

    partes = nome_completo.strip().split()

    if len(partes) == 1:
        return partes[0]

    return " ".join(partes[:1])


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


def list_atendentes_comerciais(comercial_geral: List[Dict[str, Any]]) -> List[str]:
    """
    Lista única de atendentes comerciais (nome formatado como nos gráficos por atendente),
    ordenada alfabeticamente, para popular filtro no front.
    Apenas funcionários com `ATIVO` verdadeiro na origem dos dados.
    """
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


def filter_comercial_geral_por_atendente(
    comercial_geral: List[Dict[str, Any]],
    atendente: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Restringe a lista aos registros de um único atendente.

    O critério de identidade é o mesmo de :func:`list_atendentes_comerciais` e dos
    gráficos por atendente (``_formatar_nome_atendente``). O parâmetro ``atendente``
    pode ser o nome completo vindo do banco ou o valor já retornado pela lista do filtro.

    Exemplo::

        base = filter_comercial_geral_por_atendente(dados, "Maria Silva")
        get_clientes_campanha_NG(base)

    Se ``atendente`` for ``None`` ou string vazia, devolve uma cópia da lista sem filtro.
    """
    if atendente is None or not str(atendente).strip():
        return list(comercial_geral)
    alvo = _formatar_nome_atendente(str(atendente).strip())
    return [row for row in comercial_geral if _rotulo_atendente(row) == alvo]


def filter_comercial_geral_por_atendentes(
    comercial_geral: List[Dict[str, Any]],
    atendentes: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Restringe aos registros de um ou mais atendentes (união — OR)."""
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


def _normalizar_uf_comercial_ng(raw: Any) -> str:
    """Normaliza a UF vinda da query para comparação e retorno ao frontend."""
    return str(raw or "").strip().upper()


def list_ufs_comercial_ng(comercial_geral: List[Dict[str, Any]]) -> List[str]:
    """
    Lista única de UFs disponíveis no recorte atual de `comercial_geral`.

    A lista é usada para popular o filtro de UF no frontend.
    """
    vistos: set[str] = set()
    saida: List[str] = []
    for row in comercial_geral or []:
        uf = _normalizar_uf_comercial_ng(row.get("UF") or row.get("uf"))
        if not uf or uf in vistos:
            continue
        vistos.add(uf)
        saida.append(uf)
    return sorted(saida)


def filter_comercial_geral_por_uf(
    comercial_geral: List[Dict[str, Any]],
    uf: Optional[Union[str, List[str]]] = None,
) -> List[Dict[str, Any]]:
    """
    Restringe a lista aos registros de uma ou mais UFs.

    Se ``uf`` for ``None`` (ou lista vazia), devolve uma cópia da lista sem filtro.
    """
    if uf is None:
        return list(comercial_geral)
    ufs = [uf] if isinstance(uf, str) else list(uf)
    alvo = {_normalizar_uf_comercial_ng(u) for u in ufs if str(u).strip()}
    if not alvo:
        return list(comercial_geral)
    return [
        row for row in comercial_geral
        if _normalizar_uf_comercial_ng(row.get("UF") or row.get("uf")) in alvo
    ]


# --- Segmento comercial (canal) — alinhado a get_clientes_* / CANAL_ATUAL, motivo_encerramento == 11 ---

_MOTIVO_ENC_COMERCIAL_NG = 11

_REDES_CANAIS_COMERCIAL_NG = frozenset({
    "REDES SOCIAIS",
    "INSTAGRAM",
    "GOOGLE",
    "FACEBOOK",
    "YOUTUBE",
})

_CANAIS_CONTRATO_FECHADO_NG = frozenset({
    "ANUNCIO",
    "ANUNCIO_NG",
    "INDICAÇÃO",
    "RETORNO",
    "SITE",
    "RESGATE",
    "PARCEIRO",
    "EXTERNO",
    "REDES SOCIAIS",
    "INSTAGRAM",
    "GOOGLE",
    "FACEBOOK",
    "YOUTUBE",
})

SEGMENTOS_COMERCIAL_NG_ORDENADOS: tuple[str, ...] = (
    "CAMPANHA_RA",
    "CAMPANHA_NG",
    "REDES_SOCIAIS",
    "INDICACAO",
    "RETORNO",
    "SITE",
    "RESGATE",
    "CANCELADOS",
)

SEGMENTOS_COMERCIAL_NG = frozenset(SEGMENTOS_COMERCIAL_NG_ORDENADOS)


def list_segmentos_comercial_ng() -> List[str]:
    """Slugs aceitos em :func:`filter_comercial_geral_por_segmento` e na API (query ``segmento_comercial_ng``)."""
    return list(SEGMENTOS_COMERCIAL_NG_ORDENADOS)


def normalizar_segmento_comercial_ng(raw: str) -> str:
    """
    Normaliza texto da UI ou query string para um slug de :data:`SEGMENTOS_COMERCIAL_NG`.

    Aceita por exemplo ``CAMPANHA RA``, ``campanha_ra``, ``INDICAÇÃO``.
    """
    s = str(raw).strip().upper().replace(" ", "_")
    if s in ("INDICAÇÃO", "INDICAÇAO"):
        s = "INDICACAO"
    if s in SEGMENTOS_COMERCIAL_NG:
        return s
    raise ValueError(
        "segmento_comercial_ng inválido: {!r}. Valores: {}".format(
            raw, ", ".join(SEGMENTOS_COMERCIAL_NG_ORDENADOS)
        )
    )


def _canal_atual_comercial_ng(row: Dict[str, Any]) -> str:
    v = row.get("CANAL_ATUAL") or row.get("canal_atual")
    return str(v or "").strip().upper()


def row_pertence_segmento_comercial_NG(row: Dict[str, Any], segmento_normalizado: str) -> bool:
    """Predicado alinhado às regras de ``get_clientes_*`` / ``get_clientes_cancelados`` (NG)."""
    seg = segmento_normalizado
    if seg == "CANCELADOS":
        return (
            row.get("motivo_encerramento") == _MOTIVO_ENC_COMERCIAL_NG
            and row.get("STATUS") == 2
        )
    if row.get("motivo_encerramento") != _MOTIVO_ENC_COMERCIAL_NG:
        return False
    canal = _canal_atual_comercial_ng(row)
    if seg == "CAMPANHA_RA":
        return canal == "ANUNCIO"
    if seg == "CAMPANHA_NG":
        return canal == "ANUNCIO_NG"
    if seg == "REDES_SOCIAIS":
        return canal in _REDES_CANAIS_COMERCIAL_NG
    if seg == "INDICACAO":
        return canal == "INDICAÇÃO"
    if seg == "RETORNO":
        return canal == "RETORNO"
    if seg == "SITE":
        return canal == "SITE"
    if seg == "RESGATE":
        return canal == "RESGATE"
    return False


def filter_comercial_geral_por_segmento(
    comercial_geral: List[Dict[str, Any]],
    segmento: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Restringe linhas ao segmento de canal (ou cancelados), com as mesmas regras das métricas de clientes NG.

    ``segmento`` deve ser um slug já normalizado (use :func:`normalizar_segmento_comercial_ng`) ou ``None``.
    """
    if segmento is None or not str(segmento).strip():
        return list(comercial_geral)
    key = normalizar_segmento_comercial_ng(str(segmento).strip())
    return [r for r in comercial_geral if row_pertence_segmento_comercial_NG(r, key)]


def filter_comercial_geral_por_area_atuacao(
    comercial_geral: List[Dict[str, Any]],
    area_atuacao_id: Optional[Union[int, List[int]]] = None,
) -> List[Dict[str, Any]]:
    """Restringe linhas à área de atuação (AREA_ATUACAO_ID) informada. None = todas."""
    alvos = normalizar_filtro_ids(area_atuacao_id)
    if not alvos:
        return list(comercial_geral)
    return [r for r in comercial_geral if r.get("AREA_ATUACAO_ID") in alvos]


def _filter_by_date_range(comercial_geral: List[Dict[str, Any]], from_date: date, to_date: date) -> List[Dict[str, Any]]:
    """Filtra dados comerciais por intervalo de datas usando a coluna ASSINATURA."""
    filtered = []
    for item in comercial_geral:
        try:
            assinatura_str = item.get("ASSINATURA") or item.get("assinatura")
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


def _get_data_assinatura(row: Dict[str, Any]) -> Optional[date]:
    assinatura_str = row.get("ASSINATURA") or row.get("assinatura")
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


def _is_contrato_fechado(row: Dict[str, Any]) -> bool:
    return (
        row.get("motivo_encerramento") == _MOTIVO_ENC_COMERCIAL_NG
        and _canal_atual_comercial_ng(row) in _CANAIS_CONTRATO_FECHADO_NG
    )


def audit_comercial_geral_duplication(
    comercial_geral: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Mede inflação de linhas por ID_ACTION (processos × rubricas).
    Usado no aquecimento de cache para observabilidade em produção.
    """
    total_linhas = len(comercial_geral or [])
    ids: Set[Any] = set()
    linhas_por_id: Dict[Any, int] = defaultdict(int)
    com_rubrica = 0

    for row in comercial_geral or []:
        id_action = row.get("ID_ACTION")
        if id_action is not None:
            ids.add(id_action)
            linhas_por_id[id_action] += 1
        if row.get("RUBRICA") is not None:
            com_rubrica += 1

    distinct_actions = len(ids)
    max_linhas = max(linhas_por_id.values()) if linhas_por_id else 0
    media_linhas = (total_linhas / distinct_actions) if distinct_actions else 0.0
    infladas = sum(1 for n in linhas_por_id.values() if n > 1)

    return {
        "total_linhas": total_linhas,
        "distinct_id_action": distinct_actions,
        "linhas_com_rubrica": com_rubrica,
        "max_linhas_por_action": max_linhas,
        "media_linhas_por_action": round(media_linhas, 2),
        "actions_com_mais_de_uma_linha": infladas,
    }


def log_comercial_geral_audit(comercial_geral: List[Dict[str, Any]]) -> None:
    """Registra estatísticas de duplicação do dataset comercial NG."""
    stats = audit_comercial_geral_duplication(comercial_geral)
    logger.info(
        "comercial_geral audit: %d linhas, %d actions distintas, "
        "%d actions com >1 linha, média %.2f linhas/action, máx %d linhas/action",
        stats["total_linhas"],
        stats["distinct_id_action"],
        stats["actions_com_mais_de_uma_linha"],
        stats["media_linhas_por_action"],
        stats["max_linhas_por_action"],
    )


def _distinct_id_actions(
    comercial_geral: List[Dict[str, Any]],
    predicate: Callable[[Dict[str, Any]], bool],
) -> int:
    """Conta ID_ACTION distintos que satisfazem o predicado."""
    ids: Set[Any] = set()
    for row in comercial_geral:
        if not predicate(row):
            continue
        id_action = row.get("ID_ACTION")
        if id_action is not None:
            ids.add(id_action)
    return len(ids)


def _coletar_ids_clientes_por_canal(
    comercial_geral: List[Dict[str, Any]],
) -> Dict[str, Set[Any]]:
    """Uma passagem: classifica ID_ACTION por canal (métricas de clientes fechados)."""
    buckets: Dict[str, Set[Any]] = {
        "campanha_ra": set(),
        "campanha_ng": set(),
        "indicacao": set(),
        "redes_sociais": set(),
        "retorno": set(),
        "site": set(),
        "resgate": set(),
        "parceiros_externos": set(),
    }

    for row in comercial_geral:
        if row.get("motivo_encerramento") != _MOTIVO_ENC_COMERCIAL_NG:
            continue
        id_action = row.get("ID_ACTION")
        if id_action is None:
            continue

        canal = _canal_atual_comercial_ng(row)
        if canal == "ANUNCIO":
            buckets["campanha_ra"].add(id_action)
        elif canal == "ANUNCIO_NG":
            buckets["campanha_ng"].add(id_action)
        elif canal == "INDICAÇÃO":
            buckets["indicacao"].add(id_action)
        elif canal in _REDES_CANAIS_COMERCIAL_NG:
            buckets["redes_sociais"].add(id_action)
        elif canal == "RETORNO":
            buckets["retorno"].add(id_action)
        elif canal == "SITE":
            buckets["site"].add(id_action)
        elif canal == "RESGATE":
            buckets["resgate"].add(id_action)
        elif canal in ("PARCEIRO", "EXTERNO"):
            buckets["parceiros_externos"].add(id_action)

    return buckets


# -----------------------------------------------------------------------------
# 2 - Funções de clientes
# -----------------------------------------------------------------------------

def get_clientes_campanha_RA(comercial_geral: List[Dict[str, Any]]) -> int:
    return _distinct_id_actions(
        comercial_geral,
        lambda c: (
            c.get("motivo_encerramento") == _MOTIVO_ENC_COMERCIAL_NG
            and _canal_atual_comercial_ng(c) == "ANUNCIO"
        ),
    )


_CANAIS_CAMPANHA_NG = frozenset({"ANUNCIO_NG", "ANUNCIO_LA_RJ"})

def get_clientes_campanha_NG(comercial_geral: List[Dict[str, Any]]) -> int:
    return _distinct_id_actions(
        comercial_geral,
        lambda c: (
            c.get("motivo_encerramento") == _MOTIVO_ENC_COMERCIAL_NG
            and _canal_atual_comercial_ng(c) in _CANAIS_CAMPANHA_NG
        ),
    )


def get_clientes_indicacao(comercial_geral: List[Dict[str, Any]]) -> int:
    return _distinct_id_actions(
        comercial_geral,
        lambda c: (
            c.get("motivo_encerramento") == _MOTIVO_ENC_COMERCIAL_NG
            and _canal_atual_comercial_ng(c) == "INDICAÇÃO"
        ),
    )


def get_clientes_redes_sociais(comercial_geral: List[Dict[str, Any]]) -> int:
    return _distinct_id_actions(
        comercial_geral,
        lambda c: (
            c.get("motivo_encerramento") == _MOTIVO_ENC_COMERCIAL_NG
            and _canal_atual_comercial_ng(c) in _REDES_CANAIS_COMERCIAL_NG
        ),
    )


def get_clientes_retorno(comercial_geral: List[Dict[str, Any]]) -> int:
    return _distinct_id_actions(
        comercial_geral,
        lambda c: (
            c.get("motivo_encerramento") == _MOTIVO_ENC_COMERCIAL_NG
            and _canal_atual_comercial_ng(c) == "RETORNO"
        ),
    )


def get_clientes_site(comercial_geral: List[Dict[str, Any]]) -> int:
    return _distinct_id_actions(
        comercial_geral,
        lambda c: (
            c.get("motivo_encerramento") == _MOTIVO_ENC_COMERCIAL_NG
            and _canal_atual_comercial_ng(c) == "SITE"
        ),
    )


def get_clientes_resgate(comercial_geral: List[Dict[str, Any]]) -> int:
    return _distinct_id_actions(
        comercial_geral,
        lambda c: (
            c.get("motivo_encerramento") == _MOTIVO_ENC_COMERCIAL_NG
            and _canal_atual_comercial_ng(c) == "RESGATE"
        ),
    )


def get_clientes_parceiros_externos(comercial_geral: List[Dict[str, Any]]) -> int:
    return _distinct_id_actions(
        comercial_geral,
        lambda c: (
            c.get("motivo_encerramento") == _MOTIVO_ENC_COMERCIAL_NG
            and _canal_atual_comercial_ng(c) in ("PARCEIRO", "EXTERNO")
        ),
    )


def get_clientes_todos(comercial_geral: List[Dict[str, Any]]) -> int:
    buckets = _coletar_ids_clientes_por_canal(comercial_geral)
    return (
        len(buckets["campanha_ra"])
        + len(buckets["campanha_ng"])
        + len(buckets["indicacao"])
        + len(buckets["redes_sociais"])
        + len(buckets["retorno"])
        + len(buckets["site"])
        + len(buckets["resgate"])
        + len(buckets["parceiros_externos"])
    )


def get_clientes_cancelados(comercial_geral: List[Dict[str, Any]]) -> int:
    """
    Total de ações canceladas (contagem por linha/processos, não DISTINCT ID_ACTION).

    Alinhado a ``get_acoes_fechadas``: cada linha com ``STATUS == 2`` conta como uma ação.
    """
    return sum(
        1
        for c in comercial_geral
        if c.get("motivo_encerramento") == _MOTIVO_ENC_COMERCIAL_NG
        and c.get("STATUS") == 2
    )


# -----------------------------------------------------------------------------
# 3 - Funções de ações
# -----------------------------------------------------------------------------

# Retorna o total de ações fechadas
def get_acoes_fechadas(comercial_geral: List[Dict[str, Any]]) -> int:
    # Filtrar registros que atendem aos critérios
    filtered = [
        c for c in comercial_geral
        if c.get("motivo_encerramento") == 11
        and c.get("STATUS") != 2
        and c.get("REAJUIZAMENTO") is not None
        and str(c.get("REAJUIZAMENTO", "")).lower() == "false"
    ]
    
    # Retornar a contagem de linhas (COUNTROWS equivalente)
    return len(filtered) if filtered else 0


_RUBRICAS_REUNIDAS_IDS = frozenset({79, 85})

def get_rubricas_reunidas_fechadas(comercial_geral: List[Dict[str, Any]]) -> int:
    """Conta contratos distintos do tipo rubrica reunida fechados no período."""
    seen: set = set()
    for c in comercial_geral:
        if (
            c.get("motivo_encerramento") == 11
            and c.get("STATUS") != 2
            and c.get("REAJUIZAMENTO") is not None
            and str(c.get("REAJUIZAMENTO", "")).lower() == "false"
            and c.get("ID_RUBRICA") in _RUBRICAS_REUNIDAS_IDS
        ):
            id_action = c.get("ID_ACTION")
            if id_action is not None:
                seen.add(id_action)
    return len(seen)


def group_contratos_fechados_por_mes(comercial_geral: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa a quantidade de contratos fechados por mês."""
    grouped: Dict[str, Dict[str, Any]] = {}
    ids_por_mes: Dict[str, set] = defaultdict(set)

    for c in comercial_geral:
        try:
            if not _is_contrato_fechado(c):
                continue

            assinatura_date = _get_data_assinatura(c)
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


def group_processos_fechados_por_mes(comercial_geral: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa a quantidade de processos fechados por mês."""
    grouped: Dict[str, Dict[str, Any]] = {}

    for c in comercial_geral:
        try:
            if not _is_acao_fechada(c):
                continue

            assinatura_date = _get_data_assinatura(c)
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


def group_contratos_fechados_por_dia(comercial_geral: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa a quantidade de contratos fechados por dia."""
    grouped: Dict[str, Dict[str, Any]] = {}
    ids_por_dia: Dict[str, set] = defaultdict(set)

    for c in comercial_geral:
        try:
            if not _is_contrato_fechado(c):
                continue

            assinatura_date = _get_data_assinatura(c)
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


def group_acoes_fechadas_por_dia(comercial_geral: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa a quantidade de ações fechadas por dia."""
    grouped: Dict[str, Dict[str, Any]] = {}

    for c in comercial_geral:
        try:
            if not _is_acao_fechada(c):
                continue

            assinatura_date = _get_data_assinatura(c)
            if not assinatura_date:
                continue

            dia_key = assinatura_date.strftime("%Y-%m-%d")

            if dia_key not in grouped:
                grouped[dia_key] = {"name": dia_key, "value": 0}

            grouped[dia_key]["value"] += 1

        except (ValueError, AttributeError, TypeError):
            continue

    return [item for _, item in sorted(grouped.items(), key=lambda x: x[0])]

# Retorna ações fechadas de campanha NG agrupadas por RUBRICA
def get_acoes_fechadas_campanha_NG(comercial_geral: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ações de clientes ANUNCIO_NG (motivo_encerramento=11, etc.) agrupadas por RUBRICA."""
    filtered = [
        c for c in comercial_geral
        if c.get("motivo_encerramento") == 11
        and c.get("STATUS") == 1
        and c.get("REAJUIZAMENTO") is not None
        and str(c.get("REAJUIZAMENTO", "")).lower() == "false"
        and c.get("CANAL_ATUAL") and str(c.get("CANAL_ATUAL", "")).upper() == "ANUNCIO_NG"
    ]
    
    # Agrupar por RUBRICA (mesmo formato de group_tickets_by_category: [{"name": str, "value": int}, ...])
    grouped = defaultdict(int)
    for item in filtered:
        rubrica = item.get("RUBRICA") or "Sem rubrica"
        grouped[str(rubrica)] += 1
    
    result = [
        {"name": str(name), "value": int(value)}
        for name, value in grouped.items()
    ]
    return sorted(result, key=lambda x: x["value"], reverse=True)

# Retorna ações fechadas de campanha RA agrupadas por RUBRICA
def get_acoes_fechadas_campanha_RA(comercial_geral: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ações de clientes ANUNCIO_RA (motivo_encerramento=11, etc.) agrupadas por RUBRICA."""
    filtered = [
        c for c in comercial_geral
        if c.get("motivo_encerramento") == 11
        and c.get("STATUS") == 1
        and c.get("REAJUIZAMENTO") is not None
        and str(c.get("REAJUIZAMENTO", "")).lower() == "false"
        and c.get("CANAL_ATUAL") and str(c.get("CANAL_ATUAL", "")).upper() == "ANUNCIO"
    ]
    
    # Agrupar por RUBRICA
    grouped = defaultdict(int)
    for item in filtered:
        rubrica = item.get("RUBRICA") or "Sem rubrica"
        grouped[str(rubrica)] += 1
    
    result = [
        {"name": name, "value": value}
        for name, value in grouped.items()
    ]
    return sorted(result, key=lambda x: x["value"], reverse=True)

# Retorna ações fechadas de indicação agrupadas por RUBRICA
def get_acoes_fechadas_indicacao(comercial_geral: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ações de clientes INDICAÇÃO (motivo_encerramento=11, etc.) agrupadas por RUBRICA."""
    filtered = [
        c for c in comercial_geral
        if c.get("motivo_encerramento") == 11
        and c.get("STATUS") == 1
        and c.get("REAJUIZAMENTO") is not None
        and str(c.get("REAJUIZAMENTO", "")).lower() == "false"
        and c.get("CANAL_ATUAL") and str(c.get("CANAL_ATUAL", "")).upper() == "INDICAÇÃO"
    ]
    
    # Agrupar por RUBRICA
    grouped = defaultdict(int)
    for item in filtered:
        rubrica = item.get("RUBRICA") or "Sem rubrica"
        grouped[str(rubrica)] += 1
    
    result = [
        {"name": name, "value": value}
        for name, value in grouped.items()
    ]
    return sorted(result, key=lambda x: x["value"], reverse=True)

# Retorna ações fechadas de retorno agrupadas por RUBRICA
def get_acoes_fechadas_retorno(comercial_geral: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ações de clientes RETORNO (motivo_encerramento=11, etc.) agrupadas por RUBRICA."""
    filtered = [
        c for c in comercial_geral
        if c.get("motivo_encerramento") == 11
        and c.get("STATUS") == 1
        and c.get("REAJUIZAMENTO") is not None
        and str(c.get("REAJUIZAMENTO", "")).lower() == "false"
        and c.get("CANAL_ATUAL") and str(c.get("CANAL_ATUAL", "")).upper() == "RETORNO"
    ]

    # Agrupar por RUBRICA
    grouped = defaultdict(int)
    for item in filtered:
        rubrica = item.get("RUBRICA") or "Sem rubrica"
        grouped[str(rubrica)] += 1
    
    result = [
        {"name": name, "value": value}
        for name, value in grouped.items()
    ]
    return sorted(result, key=lambda x: x["value"], reverse=True)

# Retorna ações fechadas de Resgate agrupadas por RUBRICA
def get_acoes_fechadas_resgate(comercial_geral: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ações de clientes RESGATE (motivo_encerramento=11, etc.) agrupadas por RUBRICA."""
    filtered = [
        c for c in comercial_geral
        if c.get("motivo_encerramento") == 11
        and c.get("STATUS") == 1
        and c.get("REAJUIZAMENTO") is not None
        and str(c.get("REAJUIZAMENTO", "")).lower() == "false"
        and c.get("CANAL_ATUAL") and str(c.get("CANAL_ATUAL", "")).upper() == "RESGATE"
    ]
    # Agrupar por RUBRICA
    grouped = defaultdict(int)
    for item in filtered:
        rubrica = item.get("RUBRICA") or "Sem rubrica"
        grouped[str(rubrica)] += 1
    
    result = [
        {"name": name, "value": value}
        for name, value in grouped.items()
    ]
    return sorted(result, key=lambda x: x["value"], reverse=True)

# Retorna ações fechadas de Redes Sociais agrupadas por RUBRICA
def get_acoes_fechadas_redes_sociais(comercial_geral: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ações de clientes REDES SOCIAIS (motivo_encerramento=11, etc.) agrupadas por RUBRICA."""
    filtered = [
        c for c in comercial_geral
        if c.get("motivo_encerramento") == 11
        and c.get("STATUS") == 1
        and c.get("REAJUIZAMENTO") is not None
        and str(c.get("REAJUIZAMENTO", "")).lower() == "false"
        and c.get("CANAL_ATUAL") and str(c.get("CANAL_ATUAL", "")).upper() in ["REDES SOCIAIS", "INSTAGRAM", "GOOGLE", "FACEBOOK", "YOUTUBE"]
    ]
    
    # Agrupar por RUBRICA
    grouped = defaultdict(int)
    for item in filtered:
        rubrica = item.get("RUBRICA") or "Sem rubrica"
        grouped[str(rubrica)] += 1
    
    result = [
        {"name": name, "value": value}
        for name, value in grouped.items()
    ]
    return sorted(result, key=lambda x: x["value"], reverse=True)

# Retorna as ações fechadas de Site agrupadas por RUBRICA
def get_acoes_fechadas_site(comercial_geral: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ações de clientes SITE (motivo_encerramento=11, etc.) agrupadas por RUBRICA."""
    filtered = [
        c for c in comercial_geral
        if c.get("motivo_encerramento") == 11
        and c.get("STATUS") == 1
        and c.get("REAJUIZAMENTO") is not None
        and str(c.get("REAJUIZAMENTO", "")).lower() == "false"
        and c.get("CANAL_ATUAL") and str(c.get("CANAL_ATUAL", "")).upper() == "SITE"
    ]
    
    # Agrupar por RUBRICA
    grouped = defaultdict(int)
    for item in filtered:
        rubrica = item.get("RUBRICA") or "Sem rubrica"
        grouped[str(rubrica)] += 1
    
    result = [
        {"name": name, "value": value}
        for name, value in grouped.items()
    ]
    return sorted(result, key=lambda x: x["value"], reverse=True)

# Retorna o total de ações fechadas agrupadas por RUBRICA (soma de todos os canais, mesmo formato das outras)
def get_total_acoes_fechadas_por_rubrica(comercial_geral: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Soma ações fechadas por rubrica de todos os canais (NG, RA, indicação, retorno, resgate, redes sociais, site). Mesmo formato: [{"name": rubrica, "value": total}, ...]."""
    listas = [
        get_acoes_fechadas_campanha_NG(comercial_geral),
        get_acoes_fechadas_campanha_RA(comercial_geral),
        get_acoes_fechadas_indicacao(comercial_geral),
        get_acoes_fechadas_retorno(comercial_geral),
        get_acoes_fechadas_resgate(comercial_geral),
        get_acoes_fechadas_redes_sociais(comercial_geral),
        get_acoes_fechadas_site(comercial_geral),
    ]
    grouped = defaultdict(int)
    for lista in listas:
        for item in lista:
            name = item.get("name") or "Sem rubrica"
            value = item.get("value") or 0
            grouped[str(name)] += int(value)
    result = [
        {"name": str(name), "value": int(value)}
        for name, value in grouped.items()
    ]
    return sorted(result, key=lambda x: x["value"], reverse=True)


def get_taxa_aproveitamento(comercial_geral: List[Dict[str, Any]]) -> float:
    acoes_fechadas = get_acoes_fechadas(comercial_geral)
    clientes_todos = get_clientes_todos(comercial_geral)
    
    # Evitar divisão por zero
    if clientes_todos == 0:
        return 0.0
    
    # Calcular taxa em porcentagem
    taxa = (acoes_fechadas / clientes_todos)
    return round(taxa, 2)


# -----------------------------------------------------------------------------
# 4 - Funções de comparativos
# -----------------------------------------------------------------------------

def _resolver_periodos_comparativo(
    from_date: Optional[date],
    to_date: Optional[date],
) -> tuple[date, date, date, date]:
    """Retorna (início_atual, fim_atual, início_anterior, fim_anterior).

    O período anterior é o mesmo período um mês civil antes (ex.: 01/08-20/08 ->
    01/07-20/07), delegando para o util compartilhado usado por todos os dashboards.
    """
    return resolver_periodo_comparativo(from_date, to_date)


def _comparativo_variacao_percentual(
    comercial_geral: List[Dict[str, Any]],
    all_comercial_geral: Optional[List[Dict[str, Any]]],
    from_date: Optional[date],
    to_date: Optional[date],
    metrica_fn: Callable[[List[Dict[str, Any]]], float],
    *,
    round_digits: int = 2,
) -> float:
    dados_para_busca = all_comercial_geral if all_comercial_geral is not None else comercial_geral
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        _resolver_periodos_comparativo(from_date, to_date)
    )

    valor_atual = metrica_fn(
        _filter_by_date_range(comercial_geral, data_inicio_atual, data_fim_atual)
    )
    valor_anterior = metrica_fn(
        _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)
    )

    if valor_anterior == 0:
        return 0.0

    variacao = ((valor_atual - valor_anterior) / valor_anterior) * 100
    return round(variacao, round_digits)


def _valor_periodo_anterior(
    comercial_geral: List[Dict[str, Any]],
    all_comercial_geral: Optional[List[Dict[str, Any]]],
    from_date: Optional[date],
    to_date: Optional[date],
    metrica_fn: Callable[[List[Dict[str, Any]]], float],
) -> float:
    """
    Valor absoluto da métrica no período anterior (mesmo recorte de calendário
    usado por ``_comparativo_variacao_percentual``).

    Necessário porque o Estratégico Geral combina NG+LA+RJ somando os valores
    absolutos de cada escritório antes de calcular UM percentual combinado —
    nunca somando os percentuais de cada escritório entre si (matematicamente
    inválido: dois +30% de bases diferentes não fazem um +60% combinado).
    """
    dados_para_busca = all_comercial_geral if all_comercial_geral is not None else comercial_geral
    _, _, data_inicio_anterior, data_fim_anterior = _resolver_periodos_comparativo(from_date, to_date)
    return metrica_fn(
        _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)
    )


def get_clientes_todos_periodo_anterior(
    comercial_geral: List[Dict[str, Any]],
    all_comercial_geral: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    return _valor_periodo_anterior(
        comercial_geral, all_comercial_geral, from_date, to_date, get_clientes_todos
    )


def get_acoes_fechadas_periodo_anterior(
    comercial_geral: List[Dict[str, Any]],
    all_comercial_geral: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    return _valor_periodo_anterior(
        comercial_geral, all_comercial_geral, from_date, to_date, get_acoes_fechadas
    )


def get_comparativo_clientes_campanha_NG(
    comercial_geral: List[Dict[str, Any]],
    all_comercial_geral: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    return _comparativo_variacao_percentual(
        comercial_geral, all_comercial_geral, from_date, to_date, get_clientes_campanha_NG
    )


def get_comparativo_clientes_campanha_RA(
    comercial_geral: List[Dict[str, Any]],
    all_comercial_geral: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    return _comparativo_variacao_percentual(
        comercial_geral, all_comercial_geral, from_date, to_date, get_clientes_campanha_RA
    )


def get_comparativo_clientes_redes_sociais(
    comercial_geral: List[Dict[str, Any]],
    all_comercial_geral: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    return _comparativo_variacao_percentual(
        comercial_geral, all_comercial_geral, from_date, to_date, get_clientes_redes_sociais
    )


def get_comparativo_clientes_indicacao(
    comercial_geral: List[Dict[str, Any]],
    all_comercial_geral: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    return _comparativo_variacao_percentual(
        comercial_geral, all_comercial_geral, from_date, to_date, get_clientes_indicacao
    )


def get_comparativo_clientes_retorno(
    comercial_geral: List[Dict[str, Any]],
    all_comercial_geral: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    return _comparativo_variacao_percentual(
        comercial_geral, all_comercial_geral, from_date, to_date, get_clientes_retorno
    )


def get_comparativo_clientes_resgate(
    comercial_geral: List[Dict[str, Any]],
    all_comercial_geral: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    return _comparativo_variacao_percentual(
        comercial_geral, all_comercial_geral, from_date, to_date, get_clientes_resgate
    )


def get_comparativo_clientes_parceiros_externos(
    comercial_geral: List[Dict[str, Any]],
    all_comercial_geral: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    return _comparativo_variacao_percentual(
        comercial_geral,
        all_comercial_geral,
        from_date,
        to_date,
        get_clientes_parceiros_externos,
    )


def get_comparativo_clientes_site(
    comercial_geral: List[Dict[str, Any]],
    all_comercial_geral: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    return _comparativo_variacao_percentual(
        comercial_geral, all_comercial_geral, from_date, to_date, get_clientes_site
    )


def get_comparativo_clientes_todos(
    comercial_geral: List[Dict[str, Any]],
    all_comercial_geral: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    return _comparativo_variacao_percentual(
        comercial_geral,
        all_comercial_geral,
        from_date,
        to_date,
        get_clientes_todos,
        round_digits=1,
    )


def get_comparativo_acoes_fechadas(
    comercial_geral: List[Dict[str, Any]],
    all_comercial_geral: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    return _comparativo_variacao_percentual(
        comercial_geral, all_comercial_geral, from_date, to_date, get_acoes_fechadas
    )


def get_comparativo_clientes_cancelados(
    comercial_geral: List[Dict[str, Any]],
    all_comercial_geral: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    return _comparativo_variacao_percentual(
        comercial_geral, all_comercial_geral, from_date, to_date, get_clientes_cancelados
    )


def get_comparativo_taxa_aproveitamento(
    comercial_geral: List[Dict[str, Any]],
    all_comercial_geral: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    return _comparativo_variacao_percentual(
        comercial_geral, all_comercial_geral, from_date, to_date, get_taxa_aproveitamento
    )


# -----------------------------------------------------------------------------
# 5 - Funções por atendente
# -----------------------------------------------------------------------------

# Agrupa ações fechadas por atendente
def group_acoes_fechadas_por_atendente(comercial_geral: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa ações fechadas por atendente usando os mesmos critérios de get_acoes_fechadas (só atendentes ativos)."""
    filtered = [
        c for c in comercial_geral
        if _is_atendente_ativo(c)
        and c.get("motivo_encerramento") == 11
        and c.get("STATUS") != 2
        and c.get("REAJUIZAMENTO") is not None
        and str(c.get("REAJUIZAMENTO", "")).lower() == "false"
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
def group_acoes_fechadas_diariamente(comercial_geral: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa ações fechadas do dia atual por atendente (só atendentes ativos)."""
    from datetime import date as date_type, datetime as datetime_type

    hoje = date.today()
    filtered = []
    for c in comercial_geral:
        if (not _is_atendente_ativo(c)):
            continue
        if (c.get("motivo_encerramento") == 11
            and c.get("STATUS") != 2
            and c.get("REAJUIZAMENTO") is not None
            and str(c.get("REAJUIZAMENTO", "")).lower() == "false"):

            data = c.get("ASSINATURA") or c.get("assinatura")
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
def group_contratos_fechados_diariamente_por_atendente(comercial_geral: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa contratos fechados do dia atual por atendente (só atendentes ativos)."""
    from datetime import date as date_type, datetime as datetime_type

    hoje = date.today()
    filtered = []
    for c in comercial_geral:
        if not _is_atendente_ativo(c):
            continue
        if c.get("motivo_encerramento") == 11:
            data = c.get("ASSINATURA") or c.get("assinatura")
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

def _converter_valor(valor_raw: any) -> float:
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


def _is_acao_fechada(row: Dict[str, Any]) -> bool:
    """
    Critérios base de "ação fechada" usados no painel comercial.
    Mantém a mesma regra de `get_acoes_fechadas` para evitar divergência.
    """
    return (
        row.get("motivo_encerramento") == 11
        and row.get("STATUS") != 2
        and row.get("REAJUIZAMENTO") is not None
        and str(row.get("REAJUIZAMENTO", "")).lower() == "false"
    )


def get_acoes_fechadas_registros(
    comercial_geral: List[Dict[str, Any]],
    *,
    excluir_uf_rj: bool = False,
) -> List[Dict[str, Any]]:
    """
    Retorna os registros (linhas) de ações fechadas.

    Útil quando além da quantidade você precisa dos campos por ação (ex.: `VALOR_AM`).
    """
    filtered = [c for c in comercial_geral if _is_acao_fechada(c)]
    if excluir_uf_rj:
        filtered = [c for c in filtered if str(c.get("UF", "")).upper() != "RJ"]
    return filtered


def get_comissao_base_por_acao(comercial_geral: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Lista a comissão base calculada por ação (mesmo universo que `get_acoes_fechadas` / cartão).

    Cada ação fechada pode ter `VALOR_AM` diferente; por isso o cálculo é por linha.
    """
    acoes = get_acoes_fechadas_registros(comercial_geral)
    itens: List[Dict[str, Any]] = []
    for item in acoes:
        valor_am = _converter_valor(item.get("VALOR_AM"))
        itens.append(
            {
                "ID_ACTION": item.get("ID_ACTION"),
                "RUBRICA": item.get("RUBRICA"),
                "UF": item.get("UF"),
                "VALOR_AM": valor_am,
                "COMISSAO_BASE": round(valor_am, 2),
            }
        )
    return itens


def get_comissao_base_por_rubrica(comercial_geral: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Soma a comissão base agrupada por RUBRICA (alinhada a `get_comissao_base_por_acao`).
    Formato compatível com outros agrupamentos: [{"name": <rubrica>, "value": <total>}]
    """
    grouped: Dict[str, float] = defaultdict(float)
    for item in get_comissao_base_por_acao(comercial_geral):
        rubrica = item.get("RUBRICA") or "Sem rubrica"
        grouped[str(rubrica)] += float(item.get("COMISSAO_BASE") or 0.0)

    result = [{"name": name, "value": round(value, 2)} for name, value in grouped.items()]
    return sorted(result, key=lambda x: x["value"], reverse=True)


def get_rubricas_total_tabela(comercial_geral: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Tabela "RUBRICAS TOTAL": por rubrica, AÇÕES (ações fechadas, mesmo critério do cartão),
    VALOR_AM (unitário vindo do banco) e TOTAL (soma da comissão base por linha,
    alinhada a `get_comissao_base_por_acao` / `get_comissao_base`).

    Quando todas as linhas da rubrica têm o mesmo VALOR_AM, TOTAL = ACOES × VALOR_AM.
    """
    por_acao = get_comissao_base_por_acao(comercial_geral)
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


def get_comissao_base(comercial_geral: List[Dict[str, Any]]) -> float:
    """
    Calcula a comissão base: para cada ação fechada (mesmo universo que `get_acoes_fechadas`),
    multiplica 1 (a ação) pelo VALOR_AM da sua rubrica e soma tudo.
    """
    total = 0.0
    for item in get_acoes_fechadas_registros(comercial_geral):
        total += _converter_valor(item.get("VALOR_AM"))
    return round(total, 2)


def get_comercial_comissionamento_por_atendente(
    comercial_geral: List[Dict[str, Any]],
    protocolos: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Relatório por atendente: ações e comissão base alinhados a `get_comissao_base_por_acao`.

    O **valor_fm** (1,00–4,00) vem do valor de causa protocolado **daquele atendente**
    (`get_valor_causa_protocolo_novo_por_atendente` + mesma escada de `get_fator_multiplicador_para_atingido`).
    Quem não tem protocolo no período usa atingido 0 → FM 1,0.

    **comissao_com_fm** = comissão_base × valor_fm do atendente; AM/PA e PB repartem esse valor
    na mesma proporção do pool global (PB% e AM/PA% de `get_proporcionais_am_pa_pb_sobre_comissao_com_fm`).

    Campos: atendente, acoes, comissao_base, valor_fm, proporcional_am_pa, proporcional_pb, comissao_com_fm.
    """
    from app.analyses.NG.protocolo import (
        get_comissao_com_fm,
        get_fator_multiplicador_para_atingido,
        get_proporcionais_am_pa_pb_sobre_comissao_com_fm,
        get_valor_causa_protocolo_novo_por_atendente,
    )

    acoes_regs = get_acoes_fechadas_registros(comercial_geral)
    por_atendente: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"acoes": 0, "comissao_base": 0.0})
    for item in acoes_regs:
        nome = item.get("ATENDENTE") or "Sem atendente"
        chave = _formatar_nome_atendente(str(nome).strip())
        por_atendente[chave]["acoes"] += 1
        por_atendente[chave]["comissao_base"] += _converter_valor(item.get("VALOR_AM"))

    pool = float(get_comissao_com_fm(protocolos, comercial_geral) or 0.0)
    _, prop_pb_total = get_proporcionais_am_pa_pb_sobre_comissao_com_fm(
        protocolos, pool
    )
    prop_pb_total = float(prop_pb_total or 0.0)
    frac_pb = (prop_pb_total / pool) if pool > 0 else 0.0

    valor_causa_por_atendente = get_valor_causa_protocolo_novo_por_atendente(protocolos)

    linhas: List[Dict[str, Any]] = []
    for atendente, agg in por_atendente.items():
        cb = round(float(agg["comissao_base"]), 2)
        n_acoes = int(agg["acoes"])
        atingido_att = float(valor_causa_por_atendente.get(atendente, 0.0) or 0.0)
        fm_att = float(get_fator_multiplicador_para_atingido(atingido_att))
        valor_fm = round(fm_att, 2)
        comissao_com_fm = round(cb * fm_att, 2)
        proporcional_pb = round(comissao_com_fm * frac_pb, 2)
        proporcional_am_pa = round(comissao_com_fm - proporcional_pb, 2)
        linhas.append({
            "atendente": atendente,
            "acoes": n_acoes,
            "comissao_base": cb,
            "valor_fm": valor_fm,
            "proporcional_am_pa": proporcional_am_pa,
            "proporcional_pb": proporcional_pb,
            "comissao_com_fm": comissao_com_fm,
        })

    linhas.sort(key=lambda x: (-x["comissao_com_fm"], str(x["atendente"])))
    return linhas