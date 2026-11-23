# Dashboard Julgados Acórdãos — Escritório NG (id_escritorio_assinante = 20)
#
# A query `julgados` (queries.py) é compartilhada entre escritórios, sem filtro
# de escritório no SQL. O recorte para NG é feito aqui via `_base_julgados_NG`,
# para permitir reuso do mesmo dado por outros escritórios (LA, etc.) no futuro.
#
# Espelha `julgados_sentenca.py` (1º Grau), trocando ``DATA_SENTENCA`` por
# ``DATA_ACORDAO``, ``ID_1G``/``JUIZ_1G`` por ``ID_2G``/``RELATOR_2G`` — mesma
# query (`julgados`), mesmos processos, eixo temporal e status de 2º grau.

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Optional

from app.analyses.common import tempo  # V2: média/mediana de tempo num módulo só
from app.utils import parse_date_from_db, resolver_periodo_comparativo
from app.analyses.common import matriz_julgamento as mj
from app.analyses.common.julgados_agravo import eh_processo_agravo, numero_processo

# =============================================================================
# Constantes
# =============================================================================

ID_ESCRITORIO_NG = 20

_COL_ID_ESCRITORIO = "ID_ESCRITORIO"
_COL_ID_2G = "ID_2G"
_COL_STATUS_2G = "STATUS_2G"
_COL_DATA_ACORDAO = "DATA_ACORDAO"
_COL_DATA_AJUIZAMENTO = "DATA_AJUIZAMENTO"
_COL_RELATOR_2G = "RELATOR_2G"
_COL_MATERIA = "MATERIA"
_COL_COMPETENCIA = "COMPETENCIA"
_COL_COMARCA = "COMARCA"
_COL_UF = "UF"
_COL_MOTIVO_STATUS_2G = "MOTIVO_STATUS_2G"
_COL_VALOR_CAUSA_ACORDAO = "VALOR_CAUSA_ACORDO"

_SEM_MATERIA = "Sem matéria"
_SEM_COMPETENCIA = "Sem competência"
_SEM_COMARCA = "Sem comarca"
_SEM_MOTIVO_EXTINCAO = "Não informado"
_SEM_ANO_AJUIZAMENTO = "Sem data de ajuizamento"

_MONTH_NAMES = (
    "jan", "fev", "mar", "abr", "mai", "jun",
    "jul", "ago", "set", "out", "nov", "dez",
)

_RESULTADO_FAV = "fav"
_RESULTADO_DES = "des"
_RESULTADO_OUTROS = "outros"

# Mérito 2G (esquema novo, ``acordao_merito_segundo_grau`` — ver
# ``app.analyses.common.matriz_julgamento``). ACORDO HOMOLOGADO não tem mais
# equivalente de mérito (eixo próprio, fora de escopo) — processos só com esse
# status antigo deixam de contar como "Procedentes" e passam a cair em "Não
# classificados". SENTENÇA ANULADA (id novo 8) também não é procedente/
# improcedente/extinto — continua em "Não classificados", agora corretamente
# (antes dependia do ID antigo 22 não estar em nenhum dos 3 conjuntos).
_IDS_2G_PROCEDENTE: frozenset[int] = frozenset({
    mj.ID_MERITO_PROCEDENTE_COM_PE, mj.ID_MERITO_PROCEDENTE_SEM_PE,
    mj.ID_MERITO_PARC_PROCEDENTE_COM_PE, mj.ID_MERITO_PARC_PROCEDENTE_SEM_PE,
})
_IDS_2G_IMPROCEDENTE: frozenset[int] = frozenset({
    mj.ID_MERITO_IMPROCEDENTE, mj.ID_MERITO_IMPROCEDENTE_PRESCRICAO,
})
_IDS_2G_EXTINTO: frozenset[int] = frozenset({mj.ID_MERITO_EXTINTO_SEM_MERITO})


# =============================================================================
# Utilitários
# =============================================================================

def _to_int(value: Any) -> Optional[int]:
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


def _get_id_2g(item: dict[str, Any]) -> Optional[int]:
    """ID de mérito 2G: usa a coluna nova quando presente, senão traduz o status antigo por nome."""
    novo = _to_int(item.get("ID_ACORDAO_MERITO_2G") or item.get("id_acordao_merito_grau2"))
    status_antigo = item.get(_COL_STATUS_2G) or item.get("status_2g")
    return mj.resolver_id_merito_2g(novo, status_antigo)


def _get_data_acordao(item: dict[str, Any]) -> Optional[date]:
    return _to_date(item.get(_COL_DATA_ACORDAO) or item.get("data_acordao"))


def _get_data_sentenca(item: dict[str, Any]) -> Optional[date]:
    return _to_date(item.get("DATA_SENTENCA") or item.get("data_sentenca"))


def _get_data_embargos_acordao(item: dict[str, Any]) -> Optional[date]:
    return _to_date(item.get("ACORDAO_EMBARGOS") or item.get("acordao_embargos"))


def _get_resultado_embargos_acordao(item: dict[str, Any]) -> Optional[str]:
    """Status Resultante dos embargos (acórdãos), pela matriz ``mj.classificar_status_embargos``:
    mérito vigente ANTES dos embargos (``ID_ACORDAO_MERITO_2G_PRE_EMBARGOS``, do ``processo_audit``) x resultado
    lançado (``STATUS_ACORDAO_EMBARGOS``). Com data de embargo e sem resultado lançado: "Sem
    resultado lançado" (sem estimativa). ``None`` se não há data de embargo nem resultado lançado."""
    id_pre = _to_int(item.get("ID_ACORDAO_MERITO_2G_PRE_EMBARGOS"))
    if id_pre is None:
        id_pre = _get_id_2g(item)
    oficial = mj.classificar_status_embargos(id_pre, item.get("STATUS_ACORDAO_EMBARGOS"))
    if oficial is not None:
        return oficial
    if _get_data_embargos_acordao(item) is None:
        return None
    return mj.STATUS_EMBARGO_SEM_RESULTADO


def _get_data_ajuizamento(item: dict[str, Any]) -> Optional[date]:
    return _to_date(item.get(_COL_DATA_AJUIZAMENTO) or item.get("data_ajuizamento"))


def _get_ano_ajuizamento(item: dict[str, Any]) -> str:
    ajuizamento = _get_data_ajuizamento(item)
    return str(ajuizamento.year) if ajuizamento else _SEM_ANO_AJUIZAMENTO


def _to_float(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _get_valor_causa_acordao(item: dict[str, Any]) -> float:
    """Valor de causa INICIAL do processo (o protocolado, ``processo.valor_causa`` — sincronizado
    automaticamente do protocolo). Por decisão de negócio, não usa ``processo.valor_causa_va``
    (campo separado por grau: majoritariamente vazio/zerado e, quando preenchido, diverge do valor
    inicial em ~93% dos casos — validado ao vivo no banco em 29/09/2026)."""
    return _to_float(item.get(_COL_VALOR_CAUSA_ACORDAO) or item.get("valor_causa"))


def _normalizar_nome_relator(value: Any) -> str:
    nome = str(value or "").strip()
    if not nome or nome.lower() in {"none", "null", "-", "n/a"}:
        return ""
    return nome


def _get_relator_2g(item: dict[str, Any]) -> str:
    """Nome do relator (2G): campo de texto livre ``processo.relator_2g`` (via
    ``RELATOR_2G`` na query). Por decisão de negócio, o cadastro normalizado
    (``relator_segundo_grau``) não é usado aqui — o texto livre é a fonte oficial."""
    return _normalizar_nome_relator(item.get(_COL_RELATOR_2G))


def _get_materia(item: dict[str, Any]) -> str:
    nome = str(item.get(_COL_MATERIA) or item.get("materia") or "").strip()
    return nome if nome else _SEM_MATERIA


def _get_competencia(item: dict[str, Any]) -> str:
    nome = str(item.get(_COL_COMPETENCIA) or item.get("competencia") or "").strip()
    return nome if nome else _SEM_COMPETENCIA


def _get_comarca(item: dict[str, Any]) -> str:
    nome = str(item.get(_COL_COMARCA) or item.get("comarca") or "").strip()
    return nome if nome else _SEM_COMARCA


def _get_uf(item: dict[str, Any]) -> str:
    return str(item.get(_COL_UF) or item.get("uf") or "").strip().upper()


def _get_motivo_extincao(item: dict[str, Any]) -> str:
    nome = str(item.get(_COL_MOTIVO_STATUS_2G) or item.get("motivo_status_2g") or "").strip()
    return nome if nome else _SEM_MOTIVO_EXTINCAO


def _iniciais_nome(nome: str) -> str:
    partes = [p for p in nome.split() if p]
    if not partes:
        return "—"
    if len(partes) == 1:
        return partes[0][:2].upper()
    return f"{partes[0][0]}{partes[1][0]}".upper()


def _classificar_resultado_2g_julgados(id_2g: Optional[int]) -> Optional[str]:
    if id_2g in _IDS_2G_PROCEDENTE:
        return _RESULTADO_FAV
    if id_2g in _IDS_2G_IMPROCEDENTE:
        return _RESULTADO_DES
    if id_2g in _IDS_2G_EXTINTO:
        return _RESULTADO_OUTROS
    return None


# =============================================================================
# Filtros interativos cumulativos (matéria, relator, comarca, competência, categoria, UF)
# =============================================================================

CATEGORIA_PROCEDENTE = "procedente"
CATEGORIA_IMPROCEDENTE = "improcedente"
CATEGORIA_EXTINTO = "extinto"

CATEGORIAS_2G_VALIDAS_JULGADOS_NG: frozenset[str] = frozenset(
    {CATEGORIA_PROCEDENTE, CATEGORIA_IMPROCEDENTE, CATEGORIA_EXTINTO}
)

_RESULTADO_PARA_CATEGORIA: dict[str, str] = {
    _RESULTADO_FAV: CATEGORIA_PROCEDENTE,
    _RESULTADO_DES: CATEGORIA_IMPROCEDENTE,
    _RESULTADO_OUTROS: CATEGORIA_EXTINTO,
}


def _get_categoria_2g_julgados(item: dict[str, Any]) -> Optional[str]:
    resultado = _classificar_resultado_2g_julgados(_get_id_2g(item))
    return _RESULTADO_PARA_CATEGORIA.get(resultado) if resultado else None


def _valor_em_conjunto_filtro_julgados(valor: str, conjunto: Optional[frozenset[str]]) -> bool:
    if not conjunto:
        return True
    chave = valor.casefold()
    return any(chave == v.casefold() for v in conjunto)


@dataclass(frozen=True)
class JulgadosAcordaoFiltros:
    """Filtros cumulativos (AND entre dimensões, OR dentro de cada uma) sobre acórdãos Julgados."""

    materias: Optional[frozenset[str]] = None
    relatores: Optional[frozenset[str]] = None
    comarcas: Optional[frozenset[str]] = None
    competencias: Optional[frozenset[str]] = None
    categorias: Optional[frozenset[str]] = None
    ufs: Optional[frozenset[str]] = None
    motivos_extincao: Optional[frozenset[str]] = None
    anos_ajuizamento: Optional[frozenset[str]] = None
    resultados_embargos: Optional[frozenset[str]] = None

    def ativo(self) -> bool:
        return bool(
            self.materias
            or self.relatores
            or self.comarcas
            or self.competencias
            or self.categorias
            or self.ufs
            or self.motivos_extincao
            or self.anos_ajuizamento
            or self.resultados_embargos
        )


def _acordao_match_filtros_julgados_NG(
    item: dict[str, Any],
    filtros: JulgadosAcordaoFiltros,
) -> bool:
    if filtros.materias is not None and not _valor_em_conjunto_filtro_julgados(
        _get_materia(item), filtros.materias
    ):
        return False
    if filtros.relatores is not None:
        relator = _get_relator_2g(item)
        if not relator or not _valor_em_conjunto_filtro_julgados(relator, filtros.relatores):
            return False
    if filtros.comarcas is not None and not _valor_em_conjunto_filtro_julgados(
        _get_comarca(item), filtros.comarcas
    ):
        return False
    if filtros.competencias is not None and not _valor_em_conjunto_filtro_julgados(
        _get_competencia(item), filtros.competencias
    ):
        return False
    if filtros.categorias is not None:
        categoria = _get_categoria_2g_julgados(item)
        if categoria is None or not _valor_em_conjunto_filtro_julgados(categoria, filtros.categorias):
            return False
    if filtros.ufs is not None:
        uf = _get_uf(item)
        if not uf or not _valor_em_conjunto_filtro_julgados(uf, filtros.ufs):
            return False
    if filtros.motivos_extincao is not None and not _valor_em_conjunto_filtro_julgados(
        _get_motivo_extincao(item), filtros.motivos_extincao
    ):
        return False
    if filtros.anos_ajuizamento is not None and not _valor_em_conjunto_filtro_julgados(
        _get_ano_ajuizamento(item), filtros.anos_ajuizamento
    ):
        return False
    if filtros.resultados_embargos is not None:
        resultado = _get_resultado_embargos_acordao(item)
        if resultado is None or not _valor_em_conjunto_filtro_julgados(resultado, filtros.resultados_embargos):
            return False
    return True


def filtrar_acordaos_julgados_NG(
    processos: list[dict[str, Any]],
    filtros: Optional[JulgadosAcordaoFiltros],
) -> list[dict[str, Any]]:
    """Restringe processos aos filtros interativos (matéria/relator/comarca/competência/categoria/UF)."""
    if filtros is None or not filtros.ativo():
        return processos
    return [item for item in processos if _acordao_match_filtros_julgados_NG(item, filtros)]


# =============================================================================
# Base por escritório
# =============================================================================

def _base_julgados_NG(processos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Base padrão das análises Julgados NG: ``ID_ESCRITORIO`` == 20, sem agravos
    (ver :func:`~app.analyses.common.julgados_agravo.eh_processo_agravo`)."""
    return [
        item
        for item in processos
        if _to_int(item.get(_COL_ID_ESCRITORIO) or item.get("id_escritorio_assinante"))
        == ID_ESCRITORIO_NG
        and not eh_processo_agravo(numero_processo(item))
    ]


def _filtrar_acordao_no_periodo(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    return [
        row for row in processos
        if _data_no_periodo(_get_data_acordao(row), from_date, to_date)
    ]


def _filtrar_embargos_acordao_no_periodo(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Acórdãos embargados cujo embargo cai no período — eixo é a data do acórdão de embargos
    (``ACORDAO_EMBARGOS``), não ``DATA_ACORDAO``: o acórdão original costuma ser de meses antes.
    Sem período, todos os embargados (inclusive com resultado lançado e sem data de embargo)."""
    if from_date is None and to_date is None:
        return [row for row in processos if _get_resultado_embargos_acordao(row) is not None]
    return [
        row for row in processos
        if _data_no_periodo(_get_data_embargos_acordao(row), from_date, to_date)
    ]


def _contar_acordao_por_categoria(
    processos: list[dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
    categoria: Optional[frozenset[int]],
) -> int:
    """Conta acórdãos no período; ``categoria=None`` conta o total (sem filtro de ID_2G)."""
    acordaos = _filtrar_acordao_no_periodo(processos, from_date, to_date)
    if categoria is None:
        return len(acordaos)
    return sum(1 for row in acordaos if _get_id_2g(row) in categoria)


# =============================================================================
# KPIs de Acórdão (2º Grau)
# =============================================================================

def _contar_acordao_nao_classificados_NG(
    processos: list[dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> int:
    """Acórdãos no período cujo ID_2G não cai em Procedente/Improcedente/Extinto
    (ex.: sentença anulada, encerrado 1G, ou sem status lançado)."""
    total = _contar_acordao_por_categoria(processos, from_date, to_date, None)
    classificados = sum(
        _contar_acordao_por_categoria(processos, from_date, to_date, categoria)
        for categoria in (_IDS_2G_PROCEDENTE, _IDS_2G_IMPROCEDENTE, _IDS_2G_EXTINTO)
    )
    return total - classificados


def _valor_acordao_acordaos_procedentes_NG(
    processos: list[dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> float:
    """Soma de VALOR_ACORDAO (valor fixado no acórdão, ``processo.valor_causa_va``) dos acórdãos
    procedentes do período — mesmo número da coluna "Valor do Acórdão" do relatório."""
    total = 0.0
    for row in _filtrar_acordao_no_periodo(processos, from_date, to_date):
        if _get_id_2g(row) not in _IDS_2G_PROCEDENTE:
            continue
        try:
            total += float(row.get("VALOR_ACORDAO") or 0)
        except (TypeError, ValueError):
            continue
    return round(total, 2)


def _valor_causa_acordaos_procedentes_NG(
    processos: list[dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> float:
    """Soma de VALOR_CAUSA_ACORDO (valor de causa inicial, ``processo.valor_causa``) dos acórdãos procedentes do período."""
    acordaos = _filtrar_acordao_no_periodo(processos, from_date, to_date)
    return round(
        sum(
            _get_valor_causa_acordao(row)
            for row in acordaos
            if _get_id_2g(row) in _IDS_2G_PROCEDENTE
        ),
        2,
    )


def _contar_acordao_embargados_NG(
    processos: list[dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> int:
    """Acórdãos com embargo no período (eixo: data do acórdão de embargos)."""
    acordaos = _filtrar_embargos_acordao_no_periodo(processos, from_date, to_date)
    return sum(1 for row in acordaos if _get_resultado_embargos_acordao(row) is not None)


def _contar_acordao_revertidos_NG(
    processos: list[dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> int:
    """Acórdãos com embargo no período revertidos a favor ("Revertido Ganho", resultado oficial)."""
    acordaos = _filtrar_embargos_acordao_no_periodo(processos, from_date, to_date)
    alvo = {mj.STATUS_EMBARGO_REVERTIDO_GANHO}
    return sum(1 for row in acordaos if _get_resultado_embargos_acordao(row) in alvo)


def _tempo_medio_dias_acordao_NG(
    processos: list[dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> Optional[float]:
    """Média de dias entre DATA_SENTENCA (1G) e DATA_ACORDAO, para acórdãos do período com ambas
    as datas válidas (acórdão >= sentença)."""
    dias = tempo.duracoes(_filtrar_acordao_no_periodo(processos, from_date, to_date), _get_data_sentenca, _get_data_acordao, aceita_zero=True)
    return tempo.media(dias, casas=1, vazio=None)


def _tempo_medio_dias_embargos_acordao_NG(
    processos: list[dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> Optional[float]:
    """Média de dias entre DATA_ACORDAO e a data do acórdão de embargos (ACORDAO_EMBARGOS), no mesmo
    recorte da pizza "Resultado dos embargos" (embargo com data no período), só com as duas datas
    válidas e embargo >= acórdão."""
    dias = tempo.duracoes(_filtrar_embargos_acordao_no_periodo(processos, from_date, to_date), _get_data_acordao, _get_data_embargos_acordao, aceita_zero=True)
    return tempo.media(dias, casas=1, vazio=None)


def get_kpis_acordao_julgados_NG(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> dict[str, int]:
    """
    KPIs de acórdãos (2º Grau) do escritório NG no período (eixo: DATA_ACORDAO).

    - **Total**: processos com acórdão proferido no período.
    - **Procedentes**: ``ID_2G`` em qualquer variação de procedência (total ou
      parcial, com ou sem proveito econômico, incluindo acordo homologado).
    - **Improcedentes**: somente ``ID_2G`` = IMPROCEDENTE.
    - **Extintos**: ``ID_2G`` = extinção sem mérito.
    - **Não classificados**: ``ID_2G`` fora dessas 3 categorias (sentença
      anulada, encerrado 1G, ou sem status lançado).
    - **Tempo médio (dias)**: média entre DATA_SENTENCA (1G) e DATA_ACORDAO.
    - **Valor dos acórdãos procedentes**: soma de VALOR_CAUSA_ACORDO só dos procedentes.
    """
    base = _base_julgados_NG(processos)
    return {
        "julgados_acordao_total_NG": _contar_acordao_por_categoria(base, from_date, to_date, None),
        "julgados_acordao_procedentes_NG": _contar_acordao_por_categoria(base, from_date, to_date, _IDS_2G_PROCEDENTE),
        "julgados_acordao_improcedentes_NG": _contar_acordao_por_categoria(base, from_date, to_date, _IDS_2G_IMPROCEDENTE),
        "julgados_acordao_extintos_NG": _contar_acordao_por_categoria(base, from_date, to_date, _IDS_2G_EXTINTO),
        "julgados_acordao_nao_classificados_NG": _contar_acordao_nao_classificados_NG(base, from_date, to_date),
        "julgados_acordao_tempo_medio_dias_NG": _tempo_medio_dias_acordao_NG(base, from_date, to_date),
        "julgados_acordao_embargos_tempo_medio_dias_NG": _tempo_medio_dias_embargos_acordao_NG(base, from_date, to_date),
        "julgados_acordao_valor_procedentes_NG": _valor_causa_acordaos_procedentes_NG(base, from_date, to_date),
        "julgados_acordao_valor_fixado_procedentes_NG": _valor_acordao_acordaos_procedentes_NG(base, from_date, to_date),
        "julgados_acordao_embargados_NG": _contar_acordao_embargados_NG(base, from_date, to_date),
        "julgados_acordao_revertidos_NG": _contar_acordao_revertidos_NG(base, from_date, to_date),
    }


# =============================================================================
# Comparativos (mesmo padrão de analyses/NG/comercial_geral.py)
# =============================================================================

def _resolver_periodos_comparativo_julgados_NG(
    from_date: Optional[date],
    to_date: Optional[date],
) -> tuple[date, date, date, date]:
    """Retorna (início_atual, fim_atual, início_anterior, fim_anterior).

    O período anterior é o mesmo período um mês civil antes (ex.: 01/08-20/08 ->
    01/07-20/07).
    """
    return resolver_periodo_comparativo(from_date, to_date)


def _comparativo_variacao_percentual_julgados_NG(
    processos_ng: list[dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
    categoria: Optional[frozenset[int]],
) -> float:
    inicio_atual, fim_atual, inicio_anterior, fim_anterior = (
        _resolver_periodos_comparativo_julgados_NG(from_date, to_date)
    )
    valor_atual = _contar_acordao_por_categoria(processos_ng, inicio_atual, fim_atual, categoria)
    valor_anterior = _contar_acordao_por_categoria(processos_ng, inicio_anterior, fim_anterior, categoria)

    if valor_anterior == 0:
        return 0.0

    variacao = ((valor_atual - valor_anterior) / valor_anterior) * 100
    return round(variacao, 2)


def _comparativo_variacao_percentual_nao_classificados_julgados_NG(
    processos_ng: list[dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> float:
    inicio_atual, fim_atual, inicio_anterior, fim_anterior = (
        _resolver_periodos_comparativo_julgados_NG(from_date, to_date)
    )
    valor_atual = _contar_acordao_nao_classificados_NG(processos_ng, inicio_atual, fim_atual)
    valor_anterior = _contar_acordao_nao_classificados_NG(processos_ng, inicio_anterior, fim_anterior)

    if valor_anterior == 0:
        return 0.0

    variacao = ((valor_atual - valor_anterior) / valor_anterior) * 100
    return round(variacao, 2)


def _comparativo_variacao_percentual_valor_fixado_acordao_julgados_NG(
    processos: list[dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> float:
    inicio_atual, fim_atual, inicio_anterior, fim_anterior = (
        _resolver_periodos_comparativo_julgados_NG(from_date, to_date)
    )
    valor_atual = _valor_acordao_acordaos_procedentes_NG(processos, inicio_atual, fim_atual)
    valor_anterior = _valor_acordao_acordaos_procedentes_NG(processos, inicio_anterior, fim_anterior)

    if not valor_anterior:
        return 0.0

    variacao = ((valor_atual - valor_anterior) / valor_anterior) * 100
    return round(variacao, 2)


def _comparativo_variacao_percentual_valor_acordao_julgados_NG(
    processos: list[dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> float:
    inicio_atual, fim_atual, inicio_anterior, fim_anterior = (
        _resolver_periodos_comparativo_julgados_NG(from_date, to_date)
    )
    valor_atual = _valor_causa_acordaos_procedentes_NG(processos, inicio_atual, fim_atual)
    valor_anterior = _valor_causa_acordaos_procedentes_NG(processos, inicio_anterior, fim_anterior)

    if not valor_anterior:
        return 0.0

    variacao = ((valor_atual - valor_anterior) / valor_anterior) * 100
    return round(variacao, 2)


def _comparativo_variacao_percentual_embargados_julgados_NG(
    processos: list[dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> float:
    inicio_atual, fim_atual, inicio_anterior, fim_anterior = (
        _resolver_periodos_comparativo_julgados_NG(from_date, to_date)
    )
    valor_atual = _contar_acordao_embargados_NG(processos, inicio_atual, fim_atual)
    valor_anterior = _contar_acordao_embargados_NG(processos, inicio_anterior, fim_anterior)

    if not valor_anterior:
        return 0.0

    variacao = ((valor_atual - valor_anterior) / valor_anterior) * 100
    return round(variacao, 2)


def _comparativo_variacao_percentual_revertidos_julgados_NG(
    processos: list[dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> float:
    inicio_atual, fim_atual, inicio_anterior, fim_anterior = (
        _resolver_periodos_comparativo_julgados_NG(from_date, to_date)
    )
    valor_atual = _contar_acordao_revertidos_NG(processos, inicio_atual, fim_atual)
    valor_anterior = _contar_acordao_revertidos_NG(processos, inicio_anterior, fim_anterior)

    if not valor_anterior:
        return 0.0

    variacao = ((valor_atual - valor_anterior) / valor_anterior) * 100
    return round(variacao, 2)


def _comparativo_variacao_percentual_tempo_medio_acordao_julgados_NG(
    processos: list[dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> float:
    inicio_atual, fim_atual, inicio_anterior, fim_anterior = (
        _resolver_periodos_comparativo_julgados_NG(from_date, to_date)
    )
    valor_atual = _tempo_medio_dias_acordao_NG(processos, inicio_atual, fim_atual)
    valor_anterior = _tempo_medio_dias_acordao_NG(processos, inicio_anterior, fim_anterior)

    if valor_atual is None or not valor_anterior:
        return 0.0
    return tempo.variacao_percentual(valor_atual, valor_anterior)


def get_comparativos_acordao_julgados_NG(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> dict[str, float]:
    """Variação % de cada card de Acórdão vs período anterior de mesma duração."""
    base = _base_julgados_NG(processos)
    return {
        "comparativo_julgados_acordao_total_NG": _comparativo_variacao_percentual_julgados_NG(
            base, from_date, to_date, None
        ),
        "comparativo_julgados_acordao_procedentes_NG": _comparativo_variacao_percentual_julgados_NG(
            base, from_date, to_date, _IDS_2G_PROCEDENTE
        ),
        "comparativo_julgados_acordao_improcedentes_NG": _comparativo_variacao_percentual_julgados_NG(
            base, from_date, to_date, _IDS_2G_IMPROCEDENTE
        ),
        "comparativo_julgados_acordao_extintos_NG": _comparativo_variacao_percentual_julgados_NG(
            base, from_date, to_date, _IDS_2G_EXTINTO
        ),
        "comparativo_julgados_acordao_nao_classificados_NG": _comparativo_variacao_percentual_nao_classificados_julgados_NG(
            base, from_date, to_date
        ),
        "comparativo_julgados_acordao_tempo_medio_dias_NG": _comparativo_variacao_percentual_tempo_medio_acordao_julgados_NG(
            base, from_date, to_date
        ),
        "comparativo_julgados_acordao_valor_fixado_procedentes_NG": _comparativo_variacao_percentual_valor_fixado_acordao_julgados_NG(
            base, from_date, to_date
        ),
        "comparativo_julgados_acordao_valor_procedentes_NG": _comparativo_variacao_percentual_valor_acordao_julgados_NG(
            base, from_date, to_date
        ),
        "comparativo_julgados_acordao_embargados_NG": _comparativo_variacao_percentual_embargados_julgados_NG(
            base, from_date, to_date
        ),
        "comparativo_julgados_acordao_revertidos_NG": _comparativo_variacao_percentual_revertidos_julgados_NG(
            base, from_date, to_date
        ),
    }


# =============================================================================
# Ranking de relatores (2G): Procedentes / Improcedentes / Extintos
# =============================================================================

def get_ranking_relatores_acordao_julgados_NG(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Ranking de relatores (2G) pelos acórdãos do período: taxa de procedência e
    distribuição Procedentes / Improcedentes / Extintos.

    Acórdãos com ``ID_2G`` fora dessas 3 categorias (não classificáveis) não
    entram na contagem — mesmo critério de `recurso_NG.filtrar_por_relator_2g_recurso_NG`.
    """
    base = _base_julgados_NG(processos)
    acordaos = _filtrar_acordao_no_periodo(base, from_date, to_date)

    acc: dict[str, dict[str, Any]] = {}
    for item in acordaos:
        nome = _get_relator_2g(item)
        if not nome:
            continue
        resultado = _classificar_resultado_2g_julgados(_get_id_2g(item))
        if resultado is None:
            continue
        chave = nome.casefold()
        if chave not in acc:
            acc[chave] = {"name": nome, _RESULTADO_FAV: 0, _RESULTADO_DES: 0, _RESULTADO_OUTROS: 0}
        acc[chave][resultado] += 1

    linhas: list[dict[str, Any]] = []
    for row in acc.values():
        fav = int(row[_RESULTADO_FAV])
        des = int(row[_RESULTADO_DES])
        outros = int(row[_RESULTADO_OUTROS])
        total = fav + des + outros
        if total <= 0:
            continue
        linhas.append({
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
        })

    linhas.sort(
        key=lambda x: (
            -float(x.get("taxa_sucesso") or 0),
            -int(x.get("total_casos") or 0),
            str(x.get("name") or ""),
        )
    )
    return linhas


# =============================================================================
# Distribuição por matéria / competência / comarca
# =============================================================================

def _agrupar_por_campo(
    itens_base: list[dict[str, Any]],
    obter_campo: Any,
) -> list[dict[str, Any]]:
    grouped: dict[str, int] = defaultdict(int)
    for item in itens_base:
        grouped[obter_campo(item)] += 1
    total = float(sum(grouped.values()))
    itens: list[dict[str, Any]] = []
    for nome, qtd in grouped.items():
        itens.append({
            "name": nome,
            "value": float(qtd),
            "percent": round(100.0 * float(qtd) / total, 1) if total > 0 else 0.0,
        })
    return sorted(itens, key=lambda x: float(x["value"]), reverse=True)


def _group_acordao_por_campo_julgados_NG(
    processos: list[dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
    obter_campo: Any,
) -> list[dict[str, Any]]:
    """Distribuição dos acórdãos do período por um campo qualquer (``percent`` soma 100%)."""
    base = _base_julgados_NG(processos)
    acordaos = _filtrar_acordao_no_periodo(base, from_date, to_date)
    return _agrupar_por_campo(acordaos, obter_campo)


def group_acordao_por_materia_julgados_NG(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Distribuição dos acórdãos do período por matéria (``percent`` soma 100%)."""
    return _group_acordao_por_campo_julgados_NG(processos, from_date, to_date, _get_materia)


def group_acordao_por_competencia_julgados_NG(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Distribuição dos acórdãos do período por competência (``percent`` soma 100%)."""
    return _group_acordao_por_campo_julgados_NG(processos, from_date, to_date, _get_competencia)


def group_acordao_por_comarca_julgados_NG(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Distribuição dos acórdãos do período por comarca (``percent`` soma 100%)."""
    return _group_acordao_por_campo_julgados_NG(processos, from_date, to_date, _get_comarca)


def group_acordao_por_motivo_extincao_julgados_NG(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Distribuição dos acórdãos extintos do período por motivo da extinção (``percent`` soma 100%)."""
    base = _base_julgados_NG(processos)
    acordaos = _filtrar_acordao_no_periodo(base, from_date, to_date)
    extintos = [row for row in acordaos if _get_id_2g(row) in _IDS_2G_EXTINTO]
    return _agrupar_por_campo(extintos, _get_motivo_extincao)


# =============================================================================
# Estudo das Improcedências — Acórdão (11/11/2026). Mesma montagem do estudo da
# Sentença: estoque (sem ``from_date``/``to_date``) ou entrada (``DATA_ACORDAO``
# no período); comarca (qtd + valor de causa inicial + UF + tempo médio), motivo
# informado no 2G, ranking de relatores e quantos subiram ao STJ/STF (subfase).
# =============================================================================

def _acordaos_improcedentes_no_escopo_NG(
    processos: list[dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> list[dict[str, Any]]:
    """Acórdãos improcedentes (``ID_2G`` improcedente) no escopo informado."""
    base = _base_julgados_NG(processos)
    acordaos = _filtrar_acordao_no_periodo(base, from_date, to_date)
    return [row for row in acordaos if _get_id_2g(row) in _IDS_2G_IMPROCEDENTE]


def _uf_por_comarca_julgados_acordao_NG(processos: list[dict[str, Any]]) -> dict[str, str]:
    """UF mais frequente por comarca (histórico completo do escritório) — para o mapa multi-UF."""
    contagem: defaultdict[str, defaultdict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in _base_julgados_NG(processos):
        uf = _get_uf(row)
        if uf:
            contagem[_get_comarca(row)][uf] += 1
    return {nome: max(por_uf.items(), key=lambda kv: kv[1])[0] for nome, por_uf in contagem.items()}


def _tempo_medio_dias_por_comarca_acordao_NG(processos: list[dict[str, Any]]) -> dict[str, float]:
    """Média de dias entre a sentença e o acórdão, por comarca — histórico completo do escritório,
    independente de categoria e do escopo (mesma métrica do card "Tempo médio" do Acórdão)."""
    por_comarca = tempo.duracoes_por_grupo(
        _base_julgados_NG(processos), _get_data_sentenca, _get_data_acordao, lambda row, _fim: _get_comarca(row), aceita_zero=True
    )
    return {nome: tempo.media(dias, casas=1) for nome, dias in por_comarca.items()}


def group_acordao_improcedentes_por_comarca_julgados_NG(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Acórdãos improcedentes do escopo por comarca (qtd, valor de causa inicial, UF, tempo médio)."""
    improcedentes = _acordaos_improcedentes_no_escopo_NG(processos, from_date, to_date)
    uf_por_comarca = _uf_por_comarca_julgados_acordao_NG(processos)
    tempo_medio = _tempo_medio_dias_por_comarca_acordao_NG(processos)
    contagem: defaultdict[str, int] = defaultdict(int)
    valores: defaultdict[str, float] = defaultdict(float)
    for row in improcedentes:
        comarca = _get_comarca(row)
        contagem[comarca] += 1
        valores[comarca] += _get_valor_causa_acordao(row)
    total = float(sum(contagem.values()))
    itens = [
        {
            "name": nome,
            "value": float(qtd),
            "percent": round(100.0 * float(qtd) / total, 1) if total > 0 else 0.0,
            "valor_causa": round(valores.get(nome, 0.0), 2),
            "uf": uf_por_comarca.get(nome),
            "tempo_medio_dias": tempo_medio.get(nome),
        }
        for nome, qtd in contagem.items()
    ]
    return sorted(itens, key=lambda x: float(x["value"]), reverse=True)


def group_acordao_por_motivo_improcedencia_julgados_NG(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Acórdãos improcedentes do escopo por motivo informado no 2G (``MOTIVO_STATUS_2G``)."""
    improcedentes = _acordaos_improcedentes_no_escopo_NG(processos, from_date, to_date)
    return _agrupar_por_campo(improcedentes, _get_motivo_extincao)


def get_ranking_relatores_improcedencia_julgados_NG(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Ranking de relatores (2G) pela quantidade de acórdãos improcedentes (sem relator não entra)."""
    improcedentes = _acordaos_improcedentes_no_escopo_NG(processos, from_date, to_date)
    return _agrupar_por_campo([row for row in improcedentes if _get_relator_2g(row)], _get_relator_2g)


def get_improcedencia_acordao_totais_julgados_NG(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> dict[str, Any]:
    """Total de acórdãos improcedentes e soma do valor de causa inicial no escopo."""
    improcedentes = _acordaos_improcedentes_no_escopo_NG(processos, from_date, to_date)
    return {
        "total": len(improcedentes),
        "valor_causa": round(sum(_get_valor_causa_acordao(row) for row in improcedentes), 2),
    }


# Subfases (``status_processual``) de subida ao tribunal superior no NG.
ID_SUBFASE_RECURSO_ESPECIAL_STJ = 151       # AG ELABORAÇÃO RECURSO ESPECIAL
ID_SUBFASE_RECURSO_EXTRAORDINARIO_STF = 152  # AG ELABORAÇÃO RECURSO EXTRAORDINÁRIO


def _tribunal_superior_por_subfase(item: dict[str, Any]) -> Optional[str]:
    """"STJ" quando a subfase atual é a 151 (Recurso Especial); "STF" quando é a 152 (Recurso
    Extraordinário); ``None`` caso contrário. Pelo id, não pelo nome da subfase."""
    id_subfase = _to_int(item.get("ID_SUBFASE") or item.get("id_status_processual"))
    if id_subfase == ID_SUBFASE_RECURSO_ESPECIAL_STJ:
        return "STJ"
    if id_subfase == ID_SUBFASE_RECURSO_EXTRAORDINARIO_STF:
        return "STF"
    return None


def get_improcedencia_acordao_tribunal_superior_julgados_NG(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> dict[str, int]:
    """Acórdãos improcedentes do escopo que subiram ao STJ (Recurso Especial) ou ao STF (Recurso
    Extraordinário), pela subfase ATUAL do processo. Improcedente no 2G ou sobe ou é arquivado."""
    improcedentes = _acordaos_improcedentes_no_escopo_NG(processos, from_date, to_date)
    contagem = {"STJ": 0, "STF": 0}
    for row in improcedentes:
        tribunal = _tribunal_superior_por_subfase(row)
        if tribunal:
            contagem[tribunal] += 1
    return {"stj": contagem["STJ"], "stf": contagem["STF"]}


def get_total_acordaos_julgados_NG(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """Total de acórdãos (todas as categorias) no escopo — denominador do "a cada 10"."""
    return len(_filtrar_acordao_no_periodo(_base_julgados_NG(processos), from_date, to_date))


def group_acordao_por_ano_ajuizamento_julgados_NG(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Total de acórdãos do período (todos, sem filtro de categoria), agrupados pelo
    ano de ajuizamento (DATA_AJUIZAMENTO) do processo — quantidade (``value``) e
    soma do valor de causa do acórdão (``valor_causa``) por ano.
    """
    base = _base_julgados_NG(processos)
    acordaos = _filtrar_acordao_no_periodo(base, from_date, to_date)

    contagem: defaultdict[str, int] = defaultdict(int)
    valores: defaultdict[str, float] = defaultdict(float)
    for row in acordaos:
        ano = _get_ano_ajuizamento(row)
        contagem[ano] += 1
        valores[ano] += _get_valor_causa_acordao(row)

    return sorted(
        [
            {"name": nome, "value": qtd, "valor_causa": round(valores.get(nome, 0.0), 2)}
            for nome, qtd in contagem.items()
        ],
        key=lambda x: x["name"],
    )


def group_acordao_embargos_resultado_julgados_NG(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Distribuição dos acórdãos com embargo no período (eixo: data do acórdão de embargos) por Status Resultante dos embargos
    (ordem fixa de ``mj.STATUS_EMBARGO_ORDEM``, zeros incluídos) — ver ``_get_resultado_embargos_acordao``."""
    base = _base_julgados_NG(processos)
    status = [
        resultado
        for row in _filtrar_embargos_acordao_no_periodo(base, from_date, to_date)
        if (resultado := _get_resultado_embargos_acordao(row)) is not None
    ]
    return mj.agrupar_status_embargos(status)


# =============================================================================
# Histórico de acórdãos por mês e categoria — sem filtro de data, para o
# gráfico "Acórdãos mês a mês" (uma série por categoria; ano filtrado no front)
# =============================================================================

def _group_acordao_por_mes_categoria_NG(
    processos: list[dict[str, Any]],
    categoria: Optional[frozenset[int]],
) -> list[dict[str, Any]]:
    """Total de acórdãos por mês (histórico completo), opcionalmente restrito a uma categoria de ``ID_2G``."""
    base = _base_julgados_NG(processos)
    grouped: dict[str, dict[str, Any]] = {}

    for row in base:
        d = _get_data_acordao(row)
        if not d:
            continue
        if categoria is not None and _get_id_2g(row) not in categoria:
            continue
        month_key = f"{d.year}-{d.month:02d}"
        if month_key not in grouped:
            month_name = f"{_MONTH_NAMES[d.month - 1]} {d.year}"
            grouped[month_key] = {"name": month_name, "value": 0, "sort_key": month_key}
        grouped[month_key]["value"] += 1

    return [
        {"name": item["name"], "value": item["value"]}
        for item in sorted(grouped.values(), key=lambda x: x["sort_key"])
    ]


def group_julgados_acordao_procedentes_por_mes_NG(
    processos: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Acórdãos procedentes por mês (histórico completo do escritório NG)."""
    return _group_acordao_por_mes_categoria_NG(processos, _IDS_2G_PROCEDENTE)


def group_julgados_acordao_improcedentes_por_mes_NG(
    processos: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Acórdãos improcedentes por mês (histórico completo do escritório NG)."""
    return _group_acordao_por_mes_categoria_NG(processos, _IDS_2G_IMPROCEDENTE)


def group_julgados_acordao_extintos_por_mes_NG(
    processos: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Acórdãos extintos por mês (histórico completo do escritório NG)."""
    return _group_acordao_por_mes_categoria_NG(processos, _IDS_2G_EXTINTO)


# =============================================================================
# Opções de UF (para o filtro ao lado do seletor de período)
# =============================================================================

def get_opcoes_uf_julgados_acordao_NG(processos: list[dict[str, Any]]) -> list[str]:
    """UFs distintas presentes no escritório NG (histórico completo, sem filtros)."""
    base = _base_julgados_NG(processos)
    ufs = {_get_uf(item) for item in base if _get_uf(item)}
    return sorted(ufs)


# =============================================================================
# Acórdãos com campos vazios (relator / matéria / comarca / competência / UF)
# =============================================================================

_IDS_MERITO_COM_PE: frozenset[int] = frozenset({mj.ID_MERITO_PROCEDENTE_COM_PE, mj.ID_MERITO_PARC_PROCEDENTE_COM_PE})


def _falta_valor_pe_acordao(row: dict[str, Any]) -> bool:
    """Mérito com proveito econômico (procedente ou parcialmente procedente) sem o valor da acórdão
    (``VALOR_ACORDAO``) — vazio ou zero."""
    if _get_id_2g(row) not in _IDS_MERITO_COM_PE:
        return False
    valor = row.get("VALOR_ACORDAO")
    try:
        return valor is None or float(valor) <= 0
    except (TypeError, ValueError):
        return True


def _merito_sem_data_acordao(row: dict[str, Any]) -> bool:
    """Mérito 2G lançado mas sem data do acórdão (vazia ou inválida) — fica fora de todas as
    contagens do dashboard, que usam ``DATA_ACORDAO`` como eixo."""
    return _get_id_2g(row) is not None and _get_data_acordao(row) is None


def _data_sem_merito_acordao(row: dict[str, Any]) -> bool:
    """Data do acórdão lançada mas sem mérito 2G — entra no total, mas cai em "Não classificados"."""
    return _get_data_acordao(row) is not None and _get_id_2g(row) is None


def get_julgados_acordao_campos_vazios_NG(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> dict[str, int]:
    """Quantidade de acórdãos do período sem relator/matéria/comarca/competência/UF preenchidos."""
    base = _base_julgados_NG(processos)
    acordaos = _filtrar_acordao_no_periodo(base, from_date, to_date)

    sem_relator = sum(1 for row in acordaos if not _get_relator_2g(row))
    sem_materia = sum(1 for row in acordaos if _get_materia(row) == _SEM_MATERIA)
    sem_comarca = sum(1 for row in acordaos if _get_comarca(row) == _SEM_COMARCA)
    sem_competencia = sum(1 for row in acordaos if _get_competencia(row) == _SEM_COMPETENCIA)
    sem_uf = sum(1 for row in acordaos if not _get_uf(row))
    sem_valor_pe = sum(1 for row in acordaos if _falta_valor_pe_acordao(row))
    # Fora do eixo de data (06/11/2026): processos que não entram em nenhuma contagem do
    # dashboard por inconsistência entre mérito e data do acórdão.
    merito_sem_data = sum(1 for row in base if _merito_sem_data_acordao(row))
    data_sem_merito = sum(1 for row in base if _data_sem_merito_acordao(row))

    return {
        "julgados_acordao_sem_relator_NG": sem_relator,
        "julgados_acordao_sem_materia_NG": sem_materia,
        "julgados_acordao_sem_comarca_NG": sem_comarca,
        "julgados_acordao_sem_competencia_NG": sem_competencia,
        "julgados_acordao_sem_uf_NG": sem_uf,
        "julgados_acordao_sem_valor_pe_NG": sem_valor_pe,
        "julgados_acordao_merito_sem_data_NG": merito_sem_data,
        "julgados_acordao_data_sem_merito_NG": data_sem_merito,
    }


def get_julgados_acordao_dados_faltando_NG(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Acórdãos do período com relator/matéria/comarca/competência/UF faltando —
    número do processo + campo faltando (alimenta o alerta clicável do dashboard)."""
    base = _base_julgados_NG(processos)
    acordaos = _filtrar_acordao_no_periodo(base, from_date, to_date)

    def _numero(row: dict[str, Any]) -> str:
        return str(row.get("NUMERO_PROCESSO") or row.get("numero_processo") or "").strip()

    itens: list[dict[str, Any]] = []
    for row in acordaos:
        numero = _numero(row)
        if not _get_relator_2g(row):
            itens.append({"numero_processo": numero, "campo": "Relator"})
        if _get_materia(row) == _SEM_MATERIA:
            itens.append({"numero_processo": numero, "campo": "Matéria"})
        if _get_comarca(row) == _SEM_COMARCA:
            itens.append({"numero_processo": numero, "campo": "Comarca"})
        if _get_competencia(row) == _SEM_COMPETENCIA:
            itens.append({"numero_processo": numero, "campo": "Competência"})
        if not _get_uf(row):
            itens.append({"numero_processo": numero, "campo": "UF"})
        if _falta_valor_pe_acordao(row):
            itens.append({"numero_processo": numero, "campo": "Valor do acórdão"})
    for row in base:
        if _merito_sem_data_acordao(row):
            itens.append({"numero_processo": _numero(row), "campo": "Data do acórdão (mérito lançado)"})
        elif _data_sem_merito_acordao(row):
            itens.append({"numero_processo": _numero(row), "campo": "Mérito do acórdão (data lançada)"})
    return itens


# =============================================================================
# Lista de acórdãos (tabela): Nº processo, fase, subfase, status 2G, UF, relator, data
# =============================================================================

def _get_fase(item: dict[str, Any]) -> str:
    nome = str(item.get("FASE") or item.get("fase") or "").strip()
    return nome if nome else "—"


def _get_subfase(item: dict[str, Any]) -> str:
    nome = str(item.get("SUBFASE") or item.get("subfase") or "").strip()
    return nome if nome else "—"


def _get_status_2g(item: dict[str, Any]) -> str:
    nome = str(item.get("STATUS_2G") or item.get("status_2g") or "").strip()
    return nome if nome else "—"


def _get_status_embargos_acordao(item: dict[str, Any]) -> str:
    """Status oficial do acórdão de embargos (``STATUS_ACORDAO_EMBARGOS``) — campo real da
    query, preenchido parcialmente desde out/2026 (ver seção "Embargos e reversão" da documentação)."""
    nome = str(item.get("STATUS_ACORDAO_EMBARGOS") or item.get("status_acordao_embargos") or "").strip()
    return nome if nome else "—"


def _get_numero_processo(item: dict[str, Any]) -> str:
    numero = str(item.get("NUMERO_PROCESSO") or item.get("numero_processo") or "").strip()
    return numero if numero else "—"


def list_acordaos_julgados_NG(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Lista de acórdãos do período para a tabela: nº processo, fase, subfase, status 2G, UF, relator,
    data, status do acórdão de embargos (oficial, preenchimento parcial) e data do acórdão de embargos."""
    base = _base_julgados_NG(processos)
    acordaos = _filtrar_acordao_no_periodo(base, from_date, to_date)

    itens: list[dict[str, Any]] = []
    for row in acordaos:
        ag_id = _to_int(row.get("ID") or row.get("id"))
        data_acordao = _get_data_acordao(row)
        data_embargos = _get_data_embargos_acordao(row)
        uf = _get_uf(row)
        relator = _get_relator_2g(row)
        itens.append({
            "id": ag_id,
            "numero_processo": _get_numero_processo(row),
            "fase": _get_fase(row),
            "subfase": _get_subfase(row),
            "status_2g": _get_status_2g(row),
            "uf": uf if uf else "—",
            "relator": relator if relator else "—",
            "data_acordao": data_acordao.isoformat() if data_acordao else None,
            "status_acordao_embargos": _get_status_embargos_acordao(row),
            "data_acordao_embargos": data_embargos.isoformat() if data_embargos else None,
        })

    com_data = sorted(
        (i for i in itens if i["data_acordao"]),
        key=lambda i: i["data_acordao"],
        reverse=True,
    )
    sem_data = [i for i in itens if not i["data_acordao"]]
    return com_data + sem_data
