# Dashboard Julgados Sentenças — Escritório RJ / LAADV RJ (id_escritorio_assinante = 27)
#
# Réplica de `LA/julgados_sentenca_LA.py` (06/11/2026): mesma lógica e regras (inclusive
# exclusão de agravos), só troca o escritório 21 -> 27.
#
# A query `julgados` (queries.py) é compartilhada entre escritórios, sem filtro
# de escritório no SQL. O recorte para RJ é feito aqui via `_base_julgados_RJ`,
# mesma query e joins usados pelo módulo NG (`julgados_sentenca.py`).

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Optional

from app.analyses.common import julgados  # V2: leitores e agrupamentos dos Julgados num módulo só
from app.analyses.common import conversao  # V2: conversões dos valores do banco num módulo só
from app.analyses.common import periodo  # V2: período e variação vs período anterior num módulo só
from app.analyses.common import memo  # V2: cache por pedido (a mesma conta uma vez por pedido)
from app.analyses.common import tempo  # V2: média/mediana de tempo num módulo só
from app.utils import parse_date_from_db, resolver_periodo_comparativo
from app.analyses.common import matriz_julgamento as mj
from app.analyses.common.julgados_agravo import eh_processo_agravo, numero_processo

# =============================================================================
# Constantes
# =============================================================================

ID_ESCRITORIO_RJ = 27

_COL_ID_ESCRITORIO = "ID_ESCRITORIO"
_COL_ID_1G = "ID_1G"
_COL_STATUS_1G = "STATUS_1G"
_COL_STATUS_2G = "STATUS_2G"
_COL_DATA_AJUIZAMENTO = "DATA_AJUIZAMENTO"
_COL_DATA_SENTENCA = "DATA_SENTENCA"
_COL_JUIZ_1G = "JUIZ_1G"
_COL_MATERIA = "MATERIA"
_COL_COMPETENCIA = "COMPETENCIA"
_COL_COMARCA = "COMARCA"
_COL_UF = "UF"
_COL_MOTIVO_STATUS_1G = "MOTIVO_STATUS_1G"
_COL_VALOR_CAUSA_SENTENCA = "VALOR_CAUSA_SENTENCA"

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

# Mérito 1G (esquema novo, ``sentenca_merito_primeiro_grau`` — ver
# ``app.analyses.common.matriz_julgamento``). ACORDO HOMOLOGADO não tem mais
# equivalente de mérito (eixo próprio, fora de escopo) — processos só com esse
# status antigo deixam de contar como "Procedentes" nesta migração.
_IDS_1G_PROCEDENTE: frozenset[int] = frozenset({
    mj.ID_MERITO_PROCEDENTE_COM_PE, mj.ID_MERITO_PROCEDENTE_SEM_PE,
    mj.ID_MERITO_PARC_PROCEDENTE_COM_PE, mj.ID_MERITO_PARC_PROCEDENTE_SEM_PE,
})
_IDS_1G_IMPROCEDENTE: frozenset[int] = frozenset({
    mj.ID_MERITO_IMPROCEDENTE, mj.ID_MERITO_IMPROCEDENTE_PRESCRICAO,
})
_IDS_1G_EXTINTO: frozenset[int] = frozenset({mj.ID_MERITO_EXTINTO_SEM_MERITO})


# =============================================================================
# Utilitários
# =============================================================================

_to_int = conversao.para_inteiro  # V2: era uma cópia local (app/analyses/common/conversao.py)


_to_date = conversao.para_data  # V2: era uma cópia local (app/analyses/common/conversao.py)


_data_no_periodo = periodo.no_periodo  # V2: era uma cópia local (app/analyses/common/periodo.py)


def _get_id_1g(item: dict[str, Any]) -> Optional[int]:
    """ID de mérito 1G: usa a coluna nova quando presente, senão traduz o status antigo por nome."""
    novo = _to_int(item.get("ID_SENTENCA_MERITO_1G") or item.get("id_sentenca_merito_grau1"))
    status_antigo = item.get(_COL_STATUS_1G) or item.get("status_1g")
    return mj.resolver_id_merito_1g(novo, status_antigo)


_get_id_2g = julgados.id_2g  # V2: app/analyses/common/julgados.py


def _get_data_sentenca(item: dict[str, Any]) -> Optional[date]:
    return _to_date(item.get(_COL_DATA_SENTENCA) or item.get("data_sentenca"))


_get_data_ajuizamento = julgados.data_ajuizamento  # V2: app/analyses/common/julgados.py


def _get_data_embargos_sentenca(item: dict[str, Any]) -> Optional[date]:
    return _to_date(item.get("SENTENCA_EMBARGOS") or item.get("sentenca_embargos"))


def _get_resultado_embargos_sentenca(item: dict[str, Any]) -> Optional[str]:
    """Status Resultante dos embargos (sentenças), pela matriz ``mj.classificar_status_embargos``:
    mérito vigente ANTES dos embargos (``ID_SENTENCA_MERITO_1G_PRE_EMBARGOS``, do ``processo_audit``) x resultado
    lançado (``STATUS_SENTENCA_EMBARGOS``). Com data de embargo e sem resultado lançado: "Sem
    resultado lançado" (sem estimativa). ``None`` se não há data de embargo nem resultado lançado."""
    id_pre = _to_int(item.get("ID_SENTENCA_MERITO_1G_PRE_EMBARGOS"))
    if id_pre is None:
        id_pre = _get_id_1g(item)
    oficial = mj.classificar_status_embargos(id_pre, item.get("STATUS_SENTENCA_EMBARGOS"))
    if oficial is not None:
        return oficial
    if _get_data_embargos_sentenca(item) is None:
        return None
    return mj.STATUS_EMBARGO_SEM_RESULTADO


_get_ano_ajuizamento = julgados.ano_ajuizamento  # V2: app/analyses/common/julgados.py


_to_float = julgados.para_float  # V2: app/analyses/common/julgados.py


def _get_valor_causa_sentenca(item: dict[str, Any]) -> float:
    """Valor de causa INICIAL do processo (o protocolado, ``processo.valor_causa`` — sincronizado
    automaticamente do protocolo). Por decisão de negócio, não usa ``processo.valor_causa_vs``
    (campo separado por grau: majoritariamente vazio/zerado e, quando preenchido, diverge do valor
    inicial em ~93% dos casos — validado ao vivo no banco em 29/09/2026)."""
    return _to_float(item.get(_COL_VALOR_CAUSA_SENTENCA) or item.get("valor_causa"))


def _normalizar_nome_juiz(value: Any) -> str:
    nome = str(value or "").strip()
    if not nome or nome.lower() in {"none", "null", "-", "n/a"}:
        return ""
    return nome


def _get_juiz_1g(item: dict[str, Any]) -> str:
    """Nome do juiz (1G): campo de texto livre ``processo.juiz_1g`` (via ``JUIZ_1G``
    na query). Por decisão de negócio, o cadastro normalizado
    (``juiz_primeiro_grau``) não é usado aqui — o texto livre é a fonte oficial."""
    return _normalizar_nome_juiz(item.get(_COL_JUIZ_1G))


_get_materia = julgados.materia  # V2: app/analyses/common/julgados.py


_get_competencia = julgados.competencia  # V2: app/analyses/common/julgados.py


_get_comarca = julgados.comarca  # V2: app/analyses/common/julgados.py


_get_uf = julgados.uf  # V2: app/analyses/common/julgados.py


def _get_motivo_extincao(item: dict[str, Any]) -> str:
    nome = str(item.get(_COL_MOTIVO_STATUS_1G) or item.get("motivo_status_1g") or "").strip()
    return nome if nome else _SEM_MOTIVO_EXTINCAO


_iniciais_nome = julgados.iniciais_nome  # V2: app/analyses/common/julgados.py


def _classificar_resultado_1g_julgados(id_1g: Optional[int]) -> Optional[str]:
    if id_1g in _IDS_1G_PROCEDENTE:
        return _RESULTADO_FAV
    if id_1g in _IDS_1G_IMPROCEDENTE:
        return _RESULTADO_DES
    if id_1g in _IDS_1G_EXTINTO:
        return _RESULTADO_OUTROS
    return None


# =============================================================================
# Filtros interativos cumulativos (matéria, juiz, comarca, competência, categoria)
# =============================================================================

CATEGORIA_PROCEDENTE = "procedente"
CATEGORIA_IMPROCEDENTE = "improcedente"
CATEGORIA_EXTINTO = "extinto"

CATEGORIAS_1G_VALIDAS_JULGADOS_RJ: frozenset[str] = frozenset(
    {CATEGORIA_PROCEDENTE, CATEGORIA_IMPROCEDENTE, CATEGORIA_EXTINTO}
)

_RESULTADO_PARA_CATEGORIA: dict[str, str] = {
    _RESULTADO_FAV: CATEGORIA_PROCEDENTE,
    _RESULTADO_DES: CATEGORIA_IMPROCEDENTE,
    _RESULTADO_OUTROS: CATEGORIA_EXTINTO,
}


def _get_categoria_1g_julgados(item: dict[str, Any]) -> Optional[str]:
    resultado = _classificar_resultado_1g_julgados(_get_id_1g(item))
    return _RESULTADO_PARA_CATEGORIA.get(resultado) if resultado else None


_valor_em_conjunto_filtro_julgados = julgados.valor_em_conjunto  # V2: app/analyses/common/julgados.py


@dataclass(frozen=True)
class JulgadosSentencaFiltrosRJ:
    """Filtros cumulativos (AND entre dimensões, OR dentro de cada uma) sobre sentenças Julgados."""

    materias: Optional[frozenset[str]] = None
    juizes: Optional[frozenset[str]] = None
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
            or self.juizes
            or self.comarcas
            or self.competencias
            or self.categorias
            or self.ufs
            or self.motivos_extincao
            or self.anos_ajuizamento
            or self.resultados_embargos
        )


def _sentenca_match_filtros_julgados_RJ(
    item: dict[str, Any],
    filtros: JulgadosSentencaFiltrosRJ,
) -> bool:
    if filtros.materias is not None and not _valor_em_conjunto_filtro_julgados(
        _get_materia(item), filtros.materias
    ):
        return False
    if filtros.juizes is not None:
        juiz = _get_juiz_1g(item)
        if not juiz or not _valor_em_conjunto_filtro_julgados(juiz, filtros.juizes):
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
        categoria = _get_categoria_1g_julgados(item)
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
        resultado = _get_resultado_embargos_sentenca(item)
        if resultado is None or not _valor_em_conjunto_filtro_julgados(resultado, filtros.resultados_embargos):
            return False
    return True


def filtrar_sentencas_julgados_RJ(
    processos: list[dict[str, Any]],
    filtros: Optional[JulgadosSentencaFiltrosRJ],
) -> list[dict[str, Any]]:
    """Restringe processos aos filtros interativos (matéria/juiz/comarca/competência/categoria)."""
    if filtros is None or not filtros.ativo():
        return processos
    return [item for item in processos if _sentenca_match_filtros_julgados_RJ(item, filtros)]


# =============================================================================
# Base por escritório
# =============================================================================

@memo.por_pedido()
def _base_julgados_RJ(processos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Base padrão das análises Julgados RJ: ``ID_ESCRITORIO`` == 27, sem agravos
    (ver :func:`~app.analyses.common.julgados_agravo.eh_processo_agravo`)."""
    return julgados.base(processos, ID_ESCRITORIO_RJ)


@memo.por_pedido()
def _filtrar_sentenca_no_periodo(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    return [
        row for row in processos
        if _data_no_periodo(_get_data_sentenca(row), from_date, to_date)
    ]


@memo.por_pedido()
def _filtrar_embargos_sentenca_no_periodo(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Sentenças embargadas cujo embargo cai no período — eixo é a data da sentença de embargos
    (``SENTENCA_EMBARGOS``), não ``DATA_SENTENCA``: a sentença original costuma ser de meses antes.
    Sem período, todas as embargadas (inclusive com resultado lançado e sem data de embargo)."""
    if from_date is None and to_date is None:
        return [row for row in processos if _get_resultado_embargos_sentenca(row) is not None]
    return [
        row for row in processos
        if _data_no_periodo(_get_data_embargos_sentenca(row), from_date, to_date)
    ]


def _contar_sentenca_por_categoria(
    processos: list[dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
    categoria: Optional[frozenset[int]],
) -> int:
    """Conta sentenças no período; ``categoria=None`` conta o total (sem filtro de ID_1G)."""
    sentencas = _filtrar_sentenca_no_periodo(processos, from_date, to_date)
    if categoria is None:
        return len(sentencas)
    return sum(1 for row in sentencas if _get_id_1g(row) in categoria)


# =============================================================================
# KPIs de Sentença (1º Grau)
# =============================================================================

def _tempo_medio_dias_sentenca_RJ(
    processos: list[dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> Optional[float]:
    """Média de dias entre DATA_AJUIZAMENTO (distribuição) e DATA_SENTENCA, para
    sentenças do período com ambas as datas válidas (sentença >= ajuizamento)."""
    sentencas = _filtrar_sentenca_no_periodo(processos, from_date, to_date)
    dias = tempo.duracoes(sentencas, _get_data_ajuizamento, _get_data_sentenca, aceita_zero=True)
    return tempo.media(dias, casas=1, vazio=None)


def _valor_causa_sentencas_procedentes_RJ(
    processos: list[dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> float:
    """Soma de VALOR_CAUSA_SENTENCA (valor de causa inicial, ``processo.valor_causa``) das sentenças procedentes do período."""
    sentencas = _filtrar_sentenca_no_periodo(processos, from_date, to_date)
    return round(
        sum(
            _get_valor_causa_sentenca(row)
            for row in sentencas
            if _get_id_1g(row) in _IDS_1G_PROCEDENTE
        ),
        2,
    )


def _contar_sentenca_embargados_RJ(
    processos: list[dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> int:
    """Sentenças com embargo no período (eixo: data da sentença de embargos)."""
    sentencas = _filtrar_embargos_sentenca_no_periodo(processos, from_date, to_date)
    return sum(1 for row in sentencas if _get_resultado_embargos_sentenca(row) is not None)


def _contar_sentenca_revertidos_RJ(
    processos: list[dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> int:
    """Sentenças com embargo no período revertidas a favor ("Revertido Ganho", resultado oficial)."""
    sentencas = _filtrar_embargos_sentenca_no_periodo(processos, from_date, to_date)
    alvo = {mj.STATUS_EMBARGO_REVERTIDO_GANHO}
    return sum(1 for row in sentencas if _get_resultado_embargos_sentenca(row) in alvo)


def _tempo_medio_dias_embargos_sentenca_RJ(
    processos: list[dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> Optional[float]:
    """Média de dias entre DATA_SENTENCA e a data da sentença de embargos (SENTENCA_EMBARGOS), no mesmo
    recorte da pizza "Resultado dos embargos" (embargo com data no período), só com as duas datas
    válidas e embargo >= sentença."""
    dias = tempo.duracoes(_filtrar_embargos_sentenca_no_periodo(processos, from_date, to_date), _get_data_sentenca, _get_data_embargos_sentenca, aceita_zero=True)
    return tempo.media(dias, casas=1, vazio=None)


def get_kpis_sentenca_julgados_RJ(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> dict[str, int]:
    """
    KPIs de sentenças (1º Grau) do escritório RJ no período (eixo: DATA_SENTENCA).

    - **Total**: processos com sentença proferida no período.
    - **Procedentes**: ``ID_1G`` em qualquer variação de procedência (total ou
      parcial, com ou sem proveito econômico).
    - **Improcedentes**: somente ``ID_1G`` = IMPROCEDENTE.
    - **Extintos**: ``ID_1G`` = extinção sem mérito.
    - **Tempo médio (dias)**: média entre DATA_AJUIZAMENTO e DATA_SENTENCA.
    - **Valor das sentenças procedentes**: soma de VALOR_CAUSA_SENTENCA só das procedentes.
    """
    base = _base_julgados_RJ(processos)
    return {
        "julgados_sentenca_total_RJ": _contar_sentenca_por_categoria(base, from_date, to_date, None),
        "julgados_sentenca_procedentes_RJ": _contar_sentenca_por_categoria(base, from_date, to_date, _IDS_1G_PROCEDENTE),
        "julgados_sentenca_improcedentes_RJ": _contar_sentenca_por_categoria(base, from_date, to_date, _IDS_1G_IMPROCEDENTE),
        "julgados_sentenca_extintos_RJ": _contar_sentenca_por_categoria(base, from_date, to_date, _IDS_1G_EXTINTO),
        "julgados_sentenca_tempo_medio_dias_RJ": _tempo_medio_dias_sentenca_RJ(base, from_date, to_date),
        "julgados_sentenca_embargos_tempo_medio_dias_RJ": _tempo_medio_dias_embargos_sentenca_RJ(base, from_date, to_date),
        "julgados_sentenca_valor_procedentes_RJ": _valor_causa_sentencas_procedentes_RJ(base, from_date, to_date),
        "julgados_sentenca_embargados_RJ": _contar_sentenca_embargados_RJ(base, from_date, to_date),
        "julgados_sentenca_revertidos_RJ": _contar_sentenca_revertidos_RJ(base, from_date, to_date),
    }


# =============================================================================
# Comparativos (mesmo padrão de analyses/NG/comercial_geral.py)
# =============================================================================

_resolver_periodos_comparativo_julgados_RJ = julgados.resolver_periodos_comparativo  # V2: app/analyses/common/julgados.py


def _comparativo_variacao_percentual_julgados_RJ(
    processos_ng: list[dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
    categoria: Optional[frozenset[int]],
) -> float:
    inicio_atual, fim_atual, inicio_anterior, fim_anterior = (
        _resolver_periodos_comparativo_julgados_RJ(from_date, to_date)
    )
    valor_atual = _contar_sentenca_por_categoria(processos_ng, inicio_atual, fim_atual, categoria)
    valor_anterior = _contar_sentenca_por_categoria(processos_ng, inicio_anterior, fim_anterior, categoria)

    return periodo.variacao_percentual(valor_atual, valor_anterior)


def _comparativo_variacao_percentual_tempo_medio_sentenca_julgados_RJ(
    processos: list[dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> float:
    inicio_atual, fim_atual, inicio_anterior, fim_anterior = (
        _resolver_periodos_comparativo_julgados_RJ(from_date, to_date)
    )
    valor_atual = _tempo_medio_dias_sentenca_RJ(processos, inicio_atual, fim_atual)
    valor_anterior = _tempo_medio_dias_sentenca_RJ(processos, inicio_anterior, fim_anterior)

    if valor_atual is None or not valor_anterior:
        return 0.0
    return periodo.variacao_percentual(valor_atual, valor_anterior)


def _comparativo_variacao_percentual_valor_sentenca_julgados_RJ(
    processos: list[dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> float:
    inicio_atual, fim_atual, inicio_anterior, fim_anterior = (
        _resolver_periodos_comparativo_julgados_RJ(from_date, to_date)
    )
    valor_atual = _valor_causa_sentencas_procedentes_RJ(processos, inicio_atual, fim_atual)
    valor_anterior = _valor_causa_sentencas_procedentes_RJ(processos, inicio_anterior, fim_anterior)

    return periodo.variacao_percentual(valor_atual, valor_anterior)


def _comparativo_variacao_percentual_embargados_julgados_RJ(
    processos: list[dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> float:
    inicio_atual, fim_atual, inicio_anterior, fim_anterior = (
        _resolver_periodos_comparativo_julgados_RJ(from_date, to_date)
    )
    valor_atual = _contar_sentenca_embargados_RJ(processos, inicio_atual, fim_atual)
    valor_anterior = _contar_sentenca_embargados_RJ(processos, inicio_anterior, fim_anterior)

    return periodo.variacao_percentual(valor_atual, valor_anterior)


def _comparativo_variacao_percentual_revertidos_julgados_RJ(
    processos: list[dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> float:
    inicio_atual, fim_atual, inicio_anterior, fim_anterior = (
        _resolver_periodos_comparativo_julgados_RJ(from_date, to_date)
    )
    valor_atual = _contar_sentenca_revertidos_RJ(processos, inicio_atual, fim_atual)
    valor_anterior = _contar_sentenca_revertidos_RJ(processos, inicio_anterior, fim_anterior)

    return periodo.variacao_percentual(valor_atual, valor_anterior)


def get_comparativos_sentenca_julgados_RJ(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> dict[str, float]:
    """Variação % de cada card de Sentença vs período anterior de mesma duração."""
    base = _base_julgados_RJ(processos)
    return {
        "comparativo_julgados_sentenca_total_RJ": _comparativo_variacao_percentual_julgados_RJ(
            base, from_date, to_date, None
        ),
        "comparativo_julgados_sentenca_procedentes_RJ": _comparativo_variacao_percentual_julgados_RJ(
            base, from_date, to_date, _IDS_1G_PROCEDENTE
        ),
        "comparativo_julgados_sentenca_improcedentes_RJ": _comparativo_variacao_percentual_julgados_RJ(
            base, from_date, to_date, _IDS_1G_IMPROCEDENTE
        ),
        "comparativo_julgados_sentenca_extintos_RJ": _comparativo_variacao_percentual_julgados_RJ(
            base, from_date, to_date, _IDS_1G_EXTINTO
        ),
        "comparativo_julgados_sentenca_tempo_medio_dias_RJ": _comparativo_variacao_percentual_tempo_medio_sentenca_julgados_RJ(
            base, from_date, to_date
        ),
        "comparativo_julgados_sentenca_valor_procedentes_RJ": _comparativo_variacao_percentual_valor_sentenca_julgados_RJ(
            base, from_date, to_date
        ),
        "comparativo_julgados_sentenca_embargados_RJ": _comparativo_variacao_percentual_embargados_julgados_RJ(
            base, from_date, to_date
        ),
        "comparativo_julgados_sentenca_revertidos_RJ": _comparativo_variacao_percentual_revertidos_julgados_RJ(
            base, from_date, to_date
        ),
    }


# =============================================================================
# Ranking de juízes (1G): Procedentes / Improcedentes / Extintos
# =============================================================================

def get_ranking_juizes_sentenca_julgados_RJ(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Ranking de juízes (1G) pelas sentenças do período: taxa de procedência e
    distribuição Procedentes / Improcedentes / Extintos.

    Sentenças com ``ID_1G`` fora dessas 3 categorias (não classificáveis) não
    entram na contagem — mesmo critério de `recurso_RJ.filtrar_por_juiz_1g_recurso_RJ`.
    """
    base = _base_julgados_RJ(processos)
    sentencas = _filtrar_sentenca_no_periodo(base, from_date, to_date)

    acc: dict[str, dict[str, Any]] = {}
    for item in sentencas:
        nome = _get_juiz_1g(item)
        if not nome:
            continue
        resultado = _classificar_resultado_1g_julgados(_get_id_1g(item))
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

_agrupar_por_campo = julgados.agrupar_por_campo  # V2: app/analyses/common/julgados.py


def _group_sentenca_por_campo_julgados_RJ(
    processos: list[dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
    obter_campo: Any,
) -> list[dict[str, Any]]:
    """Distribuição das sentenças do período por um campo qualquer (``percent`` soma 100%)."""
    base = _base_julgados_RJ(processos)
    sentencas = _filtrar_sentenca_no_periodo(base, from_date, to_date)
    return _agrupar_por_campo(sentencas, obter_campo)


def group_sentenca_por_materia_julgados_RJ(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Distribuição das sentenças do período por matéria (``percent`` soma 100%)."""
    return _group_sentenca_por_campo_julgados_RJ(processos, from_date, to_date, _get_materia)


def group_sentenca_por_competencia_julgados_RJ(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Distribuição das sentenças do período por competência (``percent`` soma 100%)."""
    return _group_sentenca_por_campo_julgados_RJ(processos, from_date, to_date, _get_competencia)


def group_sentenca_por_comarca_julgados_RJ(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Distribuição das sentenças do período por comarca (``percent`` soma 100%)."""
    return _group_sentenca_por_campo_julgados_RJ(processos, from_date, to_date, _get_comarca)


def _sentencas_extintas_no_escopo_RJ(
    processos: list[dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> list[dict[str, Any]]:
    """Sentenças extintas (``ID_1G`` = extinção sem mérito) no escopo informado: quando
    ``from_date``/``to_date`` são ``None``, não há filtro de data (estoque = toda a base já
    sentenciada); quando informados, restringe a ``DATA_SENTENCA`` no intervalo (entrada no período)."""
    base = _base_julgados_RJ(processos)
    sentencas = _filtrar_sentenca_no_periodo(base, from_date, to_date)
    return [row for row in sentencas if _get_id_1g(row) in _IDS_1G_EXTINTO]


def group_sentenca_por_motivo_extincao_julgados_RJ(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Distribuição das sentenças **extintas** do escopo por motivo da extinção
    (``percent`` soma 100%). Motivo é preenchido pelo colaborador no sistema no
    momento em que o processo é marcado como extinto (``ID_1G`` = extinção sem
    mérito); sentenças extintas sem motivo preenchido entram em "Não informado".
    Sem ``from_date``/``to_date`` retorna o estoque (toda a base); com datas, só o período.
    """
    extintas = _sentencas_extintas_no_escopo_RJ(processos, from_date, to_date)
    return _agrupar_por_campo(extintas, _get_motivo_extincao)


def _uf_por_comarca_julgados_RJ(processos: list[dict[str, Any]]) -> dict[str, str]:
    """
    UF mais frequente associada a cada comarca (histórico completo do escritório RJ, sem filtro
    de data) — usada para casar cada comarca com o estado certo no mapa coroplético (uma comarca
    nunca existe em mais de um estado, mas o nome sozinho não garante isso ao cruzar com a malha
    de municípios do IBGE).
    """
    base = _base_julgados_RJ(processos)
    contagem: defaultdict[str, defaultdict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in base:
        uf = _get_uf(row)
        if not uf:
            continue
        contagem[_get_comarca(row)][uf] += 1
    return {
        nome: max(por_uf.items(), key=lambda kv: kv[1])[0]
        for nome, por_uf in contagem.items()
    }


def _tempo_medio_dias_por_comarca_julgados_RJ(processos: list[dict[str, Any]]) -> dict[str, float]:
    """
    Média de dias entre DATA_AJUIZAMENTO e DATA_SENTENCA, por comarca — calculada sobre o
    histórico completo do escritório RJ (:func:`_base_julgados_RJ`, todas as sentenças com ambas
    as datas válidas, independente de categoria ou período), mesmo padrão de
    :func:`~app.analyses.NG.execucao.group_execucao_por_comarca`: é fixa por comarca e não muda
    com o escopo estoque/entrada da seção "Estudos de Extinção" — serve de referência estável de
    "quanto tempo uma sentença dessa comarca costuma levar".
    """
    por_comarca = tempo.duracoes_por_grupo(
        _base_julgados_RJ(processos), _get_data_ajuizamento, _get_data_sentenca, lambda row, _fim: _get_comarca(row), aceita_zero=True
    )
    return {nome: tempo.media(dias, casas=1) for nome, dias in por_comarca.items()}


def group_sentenca_extintas_por_comarca_julgados_RJ(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Distribuição das sentenças extintas do escopo por comarca — quantidade (``value``) e soma do
    valor de causa da sentença (``valor_causa``) por comarca, mais a UF mais frequente da comarca
    (``uf``, para o mapa coroplético) e o tempo médio em dias entre ajuizamento e sentença da
    comarca (``tempo_medio_dias``, ver :func:`_tempo_medio_dias_por_comarca_julgados_RJ`; ``None``
    quando a comarca não tem nenhuma sentença com as duas datas preenchidas). Sem
    ``from_date``/``to_date`` retorna o estoque (toda a base); com datas, só o período. Seção
    "Estudos de Extinção".
    """
    extintas = _sentencas_extintas_no_escopo_RJ(processos, from_date, to_date)
    uf_por_comarca = _uf_por_comarca_julgados_RJ(processos)
    tempo_medio_por_comarca = _tempo_medio_dias_por_comarca_julgados_RJ(processos)
    contagem: defaultdict[str, int] = defaultdict(int)
    valores: defaultdict[str, float] = defaultdict(float)
    for row in extintas:
        comarca = _get_comarca(row)
        contagem[comarca] += 1
        valores[comarca] += _get_valor_causa_sentenca(row)
    total = float(sum(contagem.values()))
    itens = [
        {
            "name": nome,
            "value": float(qtd),
            "percent": round(100.0 * float(qtd) / total, 1) if total > 0 else 0.0,
            "valor_causa": round(valores.get(nome, 0.0), 2),
            "uf": uf_por_comarca.get(nome),
            "tempo_medio_dias": tempo_medio_por_comarca.get(nome),
        }
        for nome, qtd in contagem.items()
    ]
    return sorted(itens, key=lambda x: float(x["value"]), reverse=True)


def get_ranking_juizes_extincao_julgados_RJ(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Ranking de juízes (1G) pela quantidade de sentenças extintas no escopo (``percent`` soma 100%).
    Sem ``from_date``/``to_date`` retorna o estoque (toda a base); com datas, só o período. Sentenças
    extintas sem juiz preenchido não entram na contagem. Seção "Estudos de Extinção".
    """
    extintas = _sentencas_extintas_no_escopo_RJ(processos, from_date, to_date)
    com_juiz = [row for row in extintas if _get_juiz_1g(row)]
    return _agrupar_por_campo(com_juiz, _get_juiz_1g)


def get_extincao_totais_julgados_RJ(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> dict[str, Any]:
    """Total de sentenças extintas e soma do valor de causa, no escopo informado (sem
    ``from_date``/``to_date`` = estoque; com datas = só o período). Seção "Estudos de Extinção"."""
    extintas = _sentencas_extintas_no_escopo_RJ(processos, from_date, to_date)
    valor = round(sum(_get_valor_causa_sentenca(row) for row in extintas), 2)
    return {"total": len(extintas), "valor_causa": valor}


def get_total_sentencas_julgados_RJ(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """Total de sentenças (todas as categorias, com ou sem mérito classificável) no escopo
    informado — sem ``from_date``/``to_date`` = estoque; com datas = só o período. Usado na
    proporção "a cada X processos julgados, Y são extintos" da seção "Estudos de Extinção"."""
    base = _base_julgados_RJ(processos)
    return len(_filtrar_sentenca_no_periodo(base, from_date, to_date))


def get_extincao_revertida_2g_julgados_RJ(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """
    Quantas sentenças extintas em 1G (no escopo informado) têm o acórdão de MESMO processo em
    2G com mérito "Sentença Anulada" (``mj.ID_MERITO_SENTENCA_ANULADA``, exclusivo do 2G) —
    indício de extinção revertida na instância recursal: quando a sentença é extinta em 1G, o
    processo sobe para 2G tentando reverter, e "Sentença Anulada" é o resultado que anula a
    extinção. A query `julgados` traz 1G e 2G na mesma linha (mesmo processo), então não precisa
    de cruzamento — só ler `ID_ACORDAO_MERITO_2G` da mesma linha da sentença extinta. Conta sobre
    o total de extintas (denominador inclui as que ainda não têm acórdão julgado em 2G). Seção
    "Estudos de Extinção".
    """
    extintas = _sentencas_extintas_no_escopo_RJ(processos, from_date, to_date)
    return sum(1 for row in extintas if _get_id_2g(row) == mj.ID_MERITO_SENTENCA_ANULADA)


# =============================================================================
# Estudo das Improcedências (11/11/2026) — mesma montagem do "Estudos de Extinção",
# trocando a categoria para improcedente (``_IDS_1G_IMPROCEDENTE``). Escopo igual:
# sem ``from_date``/``to_date`` = estoque (toda a base sentenciada); com datas = entrada.
# =============================================================================

def _sentencas_improcedentes_no_escopo_RJ(
    processos: list[dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> list[dict[str, Any]]:
    """Sentenças improcedentes (``ID_1G`` improcedente) no escopo informado."""
    base = _base_julgados_RJ(processos)
    sentencas = _filtrar_sentenca_no_periodo(base, from_date, to_date)
    return [row for row in sentencas if _get_id_1g(row) in _IDS_1G_IMPROCEDENTE]


def group_sentenca_por_motivo_improcedencia_julgados_RJ(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Improcedentes do escopo por motivo informado no 1G (mesmo campo ``MOTIVO_STATUS_1G``
    do motivo da extinção; vazio cai em "Não informado")."""
    improcedentes = _sentencas_improcedentes_no_escopo_RJ(processos, from_date, to_date)
    return _agrupar_por_campo(improcedentes, _get_motivo_extincao)


def group_sentenca_improcedentes_por_comarca_julgados_RJ(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Improcedentes do escopo por comarca — quantidade, soma do valor de causa inicial, UF da
    comarca e tempo médio ajuizamento→sentença da comarca (mesmo formato do mapa de extinções)."""
    improcedentes = _sentencas_improcedentes_no_escopo_RJ(processos, from_date, to_date)
    uf_por_comarca = _uf_por_comarca_julgados_RJ(processos)
    tempo_medio_por_comarca = _tempo_medio_dias_por_comarca_julgados_RJ(processos)
    contagem: defaultdict[str, int] = defaultdict(int)
    valores: defaultdict[str, float] = defaultdict(float)
    for row in improcedentes:
        comarca = _get_comarca(row)
        contagem[comarca] += 1
        valores[comarca] += _get_valor_causa_sentenca(row)
    total = float(sum(contagem.values()))
    itens = [
        {
            "name": nome,
            "value": float(qtd),
            "percent": round(100.0 * float(qtd) / total, 1) if total > 0 else 0.0,
            "valor_causa": round(valores.get(nome, 0.0), 2),
            "uf": uf_por_comarca.get(nome),
            "tempo_medio_dias": tempo_medio_por_comarca.get(nome),
        }
        for nome, qtd in contagem.items()
    ]
    return sorted(itens, key=lambda x: float(x["value"]), reverse=True)


def get_ranking_juizes_improcedencia_julgados_RJ(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Ranking de juízes (1G) pela quantidade de improcedências no escopo (sem juiz não entra)."""
    improcedentes = _sentencas_improcedentes_no_escopo_RJ(processos, from_date, to_date)
    return _agrupar_por_campo([row for row in improcedentes if _get_juiz_1g(row)], _get_juiz_1g)


def get_improcedencia_totais_julgados_RJ(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> dict[str, Any]:
    """Total de improcedências e soma do valor de causa inicial no escopo."""
    improcedentes = _sentencas_improcedentes_no_escopo_RJ(processos, from_date, to_date)
    valor = round(sum(_get_valor_causa_sentenca(row) for row in improcedentes), 2)
    return {"total": len(improcedentes), "valor_causa": valor}


def get_improcedencia_revertida_2g_julgados_RJ(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """Improcedentes em 1G (no escopo) cujo acórdão do MESMO processo em 2G é procedente ou
    parcialmente procedente (com ou sem proveito econômico) — improcedência revertida no recurso.
    "Sentença Anulada" não entra (anula, mas não decide a favor). Denominador = todas as
    improcedentes do escopo, inclusive as ainda sem acórdão."""
    improcedentes = _sentencas_improcedentes_no_escopo_RJ(processos, from_date, to_date)
    return sum(1 for row in improcedentes if _get_id_2g(row) in _IDS_1G_PROCEDENTE)


def group_sentenca_por_ano_ajuizamento_julgados_RJ(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """
    Total de sentenças do período (todas, sem filtro de categoria), agrupadas pelo
    ano de ajuizamento (DATA_AJUIZAMENTO) do processo — quantidade (``value``) e
    soma do valor de causa da sentença (``valor_causa``) por ano.
    """
    base = _base_julgados_RJ(processos)
    sentencas = _filtrar_sentenca_no_periodo(base, from_date, to_date)

    contagem: defaultdict[str, int] = defaultdict(int)
    valores: defaultdict[str, float] = defaultdict(float)
    for row in sentencas:
        ano = _get_ano_ajuizamento(row)
        contagem[ano] += 1
        valores[ano] += _get_valor_causa_sentenca(row)

    return sorted(
        [
            {"name": nome, "value": qtd, "valor_causa": round(valores.get(nome, 0.0), 2)}
            for nome, qtd in contagem.items()
        ],
        key=lambda x: x["name"],
    )


def group_sentenca_embargos_resultado_julgados_RJ(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Distribuição das sentenças com embargo no período (eixo: data da sentença de embargos) por Status Resultante dos embargos
    (ordem fixa de ``mj.STATUS_EMBARGO_ORDEM``, zeros incluídos) — ver ``_get_resultado_embargos_sentenca``."""
    base = _base_julgados_RJ(processos)
    status = [
        resultado
        for row in _filtrar_embargos_sentenca_no_periodo(base, from_date, to_date)
        if (resultado := _get_resultado_embargos_sentenca(row)) is not None
    ]
    return mj.agrupar_status_embargos(status)


# =============================================================================
# Histórico de sentenças por mês e categoria — sem filtro de data, para o
# gráfico "Sentenças mês a mês" (uma série por categoria; ano filtrado no front)
# =============================================================================

def _group_sentenca_por_mes_categoria_RJ(
    processos: list[dict[str, Any]],
    categoria: Optional[frozenset[int]],
) -> list[dict[str, Any]]:
    """Total de sentenças por mês (histórico completo), opcionalmente restrito a uma categoria de ``ID_1G``."""
    base = _base_julgados_RJ(processos)
    grouped: dict[str, dict[str, Any]] = {}

    for row in base:
        d = _get_data_sentenca(row)
        if not d:
            continue
        if categoria is not None and _get_id_1g(row) not in categoria:
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


def group_julgados_sentenca_procedentes_por_mes_RJ(
    processos: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Sentenças procedentes por mês (histórico completo do escritório RJ)."""
    return _group_sentenca_por_mes_categoria_RJ(processos, _IDS_1G_PROCEDENTE)


def group_julgados_sentenca_improcedentes_por_mes_RJ(
    processos: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Sentenças improcedentes por mês (histórico completo do escritório RJ)."""
    return _group_sentenca_por_mes_categoria_RJ(processos, _IDS_1G_IMPROCEDENTE)


def group_julgados_sentenca_extintos_por_mes_RJ(
    processos: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Sentenças extintas por mês (histórico completo do escritório RJ)."""
    return _group_sentenca_por_mes_categoria_RJ(processos, _IDS_1G_EXTINTO)


# =============================================================================
# Opções de UF (para o filtro ao lado do seletor de período)
# =============================================================================

def get_opcoes_uf_julgados_RJ(processos: list[dict[str, Any]]) -> list[str]:
    """UFs distintas presentes no escritório RJ (histórico completo, sem filtros)."""
    base = _base_julgados_RJ(processos)
    ufs = {_get_uf(item) for item in base if _get_uf(item)}
    return sorted(ufs)


def get_opcoes_comarca_julgados_RJ(processos: list[dict[str, Any]]) -> list[str]:
    """Comarcas distintas (não vazias) presentes na base do escritório RJ, em ordem alfabética —
    usadas como universo conhecido pelo mapa coroplético (distingue "zero no filtro" de "fora da base")."""
    base = _base_julgados_RJ(processos)
    comarcas = {_get_comarca(item) for item in base}
    comarcas.discard(_SEM_COMARCA)
    return sorted(comarcas)


# =============================================================================
# Sentenças com campos vazios (juiz / matéria / comarca / competência / UF)
# =============================================================================

_IDS_MERITO_COM_PE: frozenset[int] = frozenset({mj.ID_MERITO_PROCEDENTE_COM_PE, mj.ID_MERITO_PARC_PROCEDENTE_COM_PE})


def _falta_valor_pe_sentenca(row: dict[str, Any]) -> bool:
    """Mérito com proveito econômico (procedente ou parcialmente procedente) sem o valor da sentença
    (``VALOR_SENTENCA``) — vazio ou zero."""
    if _get_id_1g(row) not in _IDS_MERITO_COM_PE:
        return False
    valor = row.get("VALOR_SENTENCA")
    try:
        return valor is None or float(valor) <= 0
    except (TypeError, ValueError):
        return True


def _merito_sem_data_sentenca(row: dict[str, Any]) -> bool:
    """Mérito 1G lançado mas sem data da sentença (vazia ou inválida) — fica fora de todas as
    contagens do dashboard, que usam ``DATA_SENTENCA`` como eixo."""
    return _get_id_1g(row) is not None and _get_data_sentenca(row) is None


def _data_sem_merito_sentenca(row: dict[str, Any]) -> bool:
    """Data da sentença lançada mas sem mérito 1G — entra no total, mas não é classificada."""
    return _get_data_sentenca(row) is not None and _get_id_1g(row) is None


def get_julgados_sentenca_campos_vazios_RJ(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> dict[str, int]:
    """Quantidade de sentenças do período sem juiz/matéria/comarca/competência/UF preenchidos."""
    base = _base_julgados_RJ(processos)
    sentencas = _filtrar_sentenca_no_periodo(base, from_date, to_date)

    sem_juiz = sum(1 for row in sentencas if not _get_juiz_1g(row))
    sem_materia = sum(1 for row in sentencas if _get_materia(row) == _SEM_MATERIA)
    sem_comarca = sum(1 for row in sentencas if _get_comarca(row) == _SEM_COMARCA)
    sem_competencia = sum(1 for row in sentencas if _get_competencia(row) == _SEM_COMPETENCIA)
    sem_uf = sum(1 for row in sentencas if not _get_uf(row))
    sem_valor_pe = sum(1 for row in sentencas if _falta_valor_pe_sentenca(row))
    # Fora do eixo de data (10/11/2026): processos que não entram em nenhuma contagem do
    # dashboard por inconsistência entre mérito e data da sentença.
    merito_sem_data = sum(1 for row in base if _merito_sem_data_sentenca(row))
    data_sem_merito = sum(1 for row in base if _data_sem_merito_sentenca(row))

    return {
        "julgados_sentenca_sem_juiz_RJ": sem_juiz,
        "julgados_sentenca_sem_materia_RJ": sem_materia,
        "julgados_sentenca_sem_comarca_RJ": sem_comarca,
        "julgados_sentenca_sem_competencia_RJ": sem_competencia,
        "julgados_sentenca_sem_uf_RJ": sem_uf,
        "julgados_sentenca_sem_valor_pe_RJ": sem_valor_pe,
        "julgados_sentenca_merito_sem_data_RJ": merito_sem_data,
        "julgados_sentenca_data_sem_merito_RJ": data_sem_merito,
    }


def get_julgados_sentenca_dados_faltando_RJ(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Sentenças do período com juiz/matéria/comarca/competência/UF faltando —
    número do processo + campo faltando (alimenta o alerta clicável do dashboard)."""
    base = _base_julgados_RJ(processos)
    sentencas = _filtrar_sentenca_no_periodo(base, from_date, to_date)

    def _numero(row: dict[str, Any]) -> str:
        return str(row.get("NUMERO_PROCESSO") or row.get("numero_processo") or "").strip()

    itens: list[dict[str, Any]] = []
    for row in sentencas:
        numero = _numero(row)
        if not _get_juiz_1g(row):
            itens.append({"numero_processo": numero, "campo": "Juiz"})
        if _get_materia(row) == _SEM_MATERIA:
            itens.append({"numero_processo": numero, "campo": "Matéria"})
        if _get_comarca(row) == _SEM_COMARCA:
            itens.append({"numero_processo": numero, "campo": "Comarca"})
        if _get_competencia(row) == _SEM_COMPETENCIA:
            itens.append({"numero_processo": numero, "campo": "Competência"})
        if not _get_uf(row):
            itens.append({"numero_processo": numero, "campo": "UF"})
        if _falta_valor_pe_sentenca(row):
            itens.append({"numero_processo": numero, "campo": "Valor da sentença"})
    for row in base:
        if _merito_sem_data_sentenca(row):
            itens.append({"numero_processo": _numero(row), "campo": "Data da sentença (mérito lançado)"})
        elif _data_sem_merito_sentenca(row):
            itens.append({"numero_processo": _numero(row), "campo": "Mérito da sentença (data lançada)"})
    return itens


# =============================================================================
# Lista de sentenças (tabela): Nº processo, fase, subfase, status 1G, UF, juiz, data
# =============================================================================

_get_fase = julgados.fase  # V2: app/analyses/common/julgados.py


_get_subfase = julgados.subfase  # V2: app/analyses/common/julgados.py


def _get_status_1g(item: dict[str, Any]) -> str:
    nome = str(item.get("STATUS_1G") or item.get("status_1g") or "").strip()
    return nome if nome else "—"


def _get_status_embargos_sentenca(item: dict[str, Any]) -> str:
    """Status oficial da sentença de embargos (``STATUS_SENTENCA_EMBARGOS``) — campo real da
    query, preenchido parcialmente desde out/2026 (ver seção "Embargos e reversão" da documentação)."""
    nome = str(item.get("STATUS_SENTENCA_EMBARGOS") or item.get("status_sentenca_embargos") or "").strip()
    return nome if nome else "—"


_get_numero_processo = julgados.numero_processo_linha  # V2: app/analyses/common/julgados.py


def list_sentencas_julgados_RJ(
    processos: list[dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[dict[str, Any]]:
    """Lista de sentenças do período para a tabela: nº processo, fase, subfase, status 1G, UF, juiz, data,
    status da sentença de embargos (oficial, preenchimento parcial) e data da sentença de embargos."""
    base = _base_julgados_RJ(processos)
    sentencas = _filtrar_sentenca_no_periodo(base, from_date, to_date)

    itens: list[dict[str, Any]] = []
    for row in sentencas:
        ag_id = _to_int(row.get("ID") or row.get("id"))
        data_sentenca = _get_data_sentenca(row)
        data_embargos = _get_data_embargos_sentenca(row)
        uf = _get_uf(row)
        juiz = _get_juiz_1g(row)
        itens.append({
            "id": ag_id,
            "numero_processo": _get_numero_processo(row),
            "fase": _get_fase(row),
            "subfase": _get_subfase(row),
            "status_1g": _get_status_1g(row),
            "uf": uf if uf else "—",
            "juiz": juiz if juiz else "—",
            "data_sentenca": data_sentenca.isoformat() if data_sentenca else None,
            "status_sentenca_embargos": _get_status_embargos_sentenca(row),
            "data_sentenca_embargos": data_embargos.isoformat() if data_embargos else None,
        })

    com_data = sorted(
        (i for i in itens if i["data_sentenca"]),
        key=lambda i: i["data_sentenca"],
        reverse=True,
    )
    sem_data = [i for i in itens if not i["data_sentenca"]]
    return com_data + sem_data
