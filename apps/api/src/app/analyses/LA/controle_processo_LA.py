"""
Análises do controle de processos (LexFlow) — escritório LAADV AM (ID_ESCRITORIO=21).

Este módulo trabalha em cima do payload retornado pela query `controle_processo`
definida em `app/queries.py` e assume que o dado de entrada é uma lista de dicts
(linhas do banco já serializadas), como nos demais módulos de `app/analyses`.
"""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.analyses.common import periodo  # V2: período e variação vs período anterior num módulo só
from app.analyses.common import memo  # V2: cache por pedido (a mesma conta uma vez por pedido)
from app.analyses.common import tempo  # V2: média/mediana de tempo num módulo só
from app.utils import ordem_mes  # V2: séries mês a mês em ordem cronológica
from app.utils import parse_date_from_db, parse_datetime_from_db, resolver_periodo_comparativo
from app.analyses.common import matriz_julgamento as mj

_ID_ESCRITORIO_LA = 21

# LexFlow `fase.id` — alinhado ao cadastro do banco (controle_processo)
_ID_FASE_INICIAL_LA = 25
_ID_FASE_RECURSAL_LA = 8
_ID_FASE_EXECUCAO_LA = 12
_ID_FASE_TRANSITO_JULGADO = 11
_ID_FASE_ARQUVADO_IMPROCEDENTE = 28
_ID_FASE_ARQUVADO_PROCEDENTE = 27

# Extintos com/sem mérito (1G e 2G) e taxa de provimento agora usam a Matriz de
# Julgamento (``app.analyses.common.matriz_julgamento``), que resolve o mérito a
# partir das colunas novas (``id_sentenca_merito_grau1``/``id_acordao_merito_grau2``)
# com fallback nos status antigos por nome — ver ``_get_id_merito_1g``/``_get_id_merito_2g``.

_COL_ID_ESCRITORIO = "ID_ESCRITORIO"
# Query `controle_processo`: p.id_situacao AS "ID_SITUACAO" — LexFlow ``public.situacao``
_COL_ID_SITUACAO = "ID_SITUACAO"
# public.situacao: 1=ATIVO, 2=ARQUIVADO, 6=SUSPENSO/SOBRESTADO. A query já restringe a (1, 6).
_ID_SITUACAO_ATIVO_LA = 1
_ID_SITUACAO_SUSPENSO_SOBRESTADO_LA = 6
# Query `controle_processo`: p.id_status_grau1 AS "ID_1G"
_COL_ID_1G = "ID_1G"
# Query `controle_processo`: spg.nome AS "STATUS_1G"
_COL_STATUS_1G = "STATUS_1G"
# Query `controle_processo`: p.id_status_grau2 AS "ID_2G"
_COL_ID_2G = "ID_2G"
# Query `controle_processo`: ssg.nome AS "STATUS_2G"
_COL_STATUS_2G = "STATUS_2G"
_COL_ID_FASE = "ID_FASE"
_COL_FASE = "FASE"
_COL_SUBFASE = "SUBFASE"
# Query `controle_processo`: p.valor_causa as "VALOR_DE_CAUSA" — única fonte de valor monetário
# usada neste módulo (mesmo em cartões de sentença/acórdão/execução, que antes usavam colunas
# próprias como VALOR_CAUSA_SENTENCA/VALOR_CAUSA_ACORDO/VALOR_CAUSA_EXECUCAO).
_COL_VALOR_CAUSA = "VALOR_DE_CAUSA"
# Exceção: painel "Extintos · 2º Grau" do Recursal usa especificamente o valor de causa do
# acórdão (não o valor de causa inicial), a pedido do escritório — ver funções
# ``*_valor_acordao_LA`` mais abaixo. Controle de Processos continua em ``_COL_VALOR_CAUSA``.
_COL_VALOR_CAUSA_ACORDO = "VALOR_CAUSA_ACORDO"
# CTE `fases_log` na query `controle_processo`
_COL_DT_ENTRADA_INICIAL = "DT_ENTRADA_INICIAL"
_COL_DT_SAIDA_INICIAL = "DT_SAIDA_INICIAL"
_COL_DT_ENTRADA_RECURSAL = "DT_ENTRADA_RECURSAL"
_COL_DT_SAIDA_RECURSAL = "DT_SAIDA_RECURSAL"
_COL_DT_ENTRADA_EXECUCAO = "DT_ENTRADA_EXECUCAO"
_COL_DT_SAIDA_EXECUCAO = "DT_SAIDA_EXECUCAO"
# Flags derivadas de ``log_fase_processual`` na query ``controle_processo`` (CTE ``fases_log``)
_COL_LOG_TEVE_SUBFASE_INICIAL_INDEFERIDA = "LOG_TEVE_SUBFASE_INICIAL_INDEFERIDA"
_COL_LOG_TEVE_SUBFASE_RECURSO_NAO_PROVIDO = "LOG_TEVE_SUBFASE_RECURSO_NAO_PROVIDO"

# Data “real” de entrada na fase inicial (melhor proxy para início do fluxo)
_COL_DATA_AJUIZAMENTO = "DATA_AJUIZAMENTO"
# Query `controle_processo`: p.sentenca AS "DATA_SENTENCA"
_COL_DATA_SENTENCA = "DATA_SENTENCA"
# Query `controle_processo`: p.acordao_data AS "DATA_ACORDAO"
_COL_DATA_ACORDAO = "DATA_ACORDAO"
# Query `controle_processo`: p.transito_julgado AS "DATA_TRANSITO_JULGADO"
_COL_DATA_TRANSITO_JULGADO = "DATA_TRANSITO_JULGADO"

_SEM_FASE = "SEM FASE"
_SEM_SUBFASE = "SEM SUBFASE"

_MONTH_NAMES_LA = [
    "jan", "fev", "mar", "abr", "mai", "jun",
    "jul", "ago", "set", "out", "nov", "dez",
]


def _col(row: Dict[str, Any], name: str) -> Any:
    """Compat: algumas rotas podem enviar chaves em lowercase."""
    return row.get(name) or row.get(name.lower())


def _normalizar_chave_fase_LA(value: str) -> str:
    """
    Normaliza fase para comparação/filtro (alinha UI ↔ banco).

    - Maiúsculas
    - Remove acentos
    - Remove pontuação comum (ex.: "." em "AG.")
    - Colapsa espaços
    """
    s = str(value).strip().upper()
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"[^A-Z0-9\s]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _rotulo_fase_grafico_LA(row: Dict[str, Any]) -> str:
    """Rótulo exibido nos gráficos/filtros de fase (maiúsculas, preserva acentos do banco)."""
    raw = _col(row, _COL_FASE)
    if raw is None or not str(raw).strip():
        return _SEM_FASE
    return str(raw).strip().upper()


def _rotulo_subfase_grafico_LA(row: Dict[str, Any]) -> str:
    """Rótulo exibido nos gráficos de subfase (maiúsculas, preserva texto do banco)."""
    raw = _col(row, _COL_SUBFASE)
    if raw is None or not str(raw).strip():
        return _SEM_SUBFASE
    return str(raw).strip().upper()


def _truthy_flag_LA(value: Any) -> bool:
    """Compat para booleanos vindos do Postgres/cache (bool, string, 0/1)."""
    if value is True:
        return True
    if value is False or value is None:
        return False
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value != 0
    s = str(value).strip().lower()
    if s in ("true", "t", "1", "yes", "y"):
        return True
    return False


def _to_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    try:
        s = str(value).strip()
        if not s:
            return None
        return int(float(s))  # cobre "21", "21.0"
    except (ValueError, TypeError):
        return None


def _converter_valor_causa(valor_causa: Any) -> float:
    if valor_causa is None:
        return 0.0
    try:
        if isinstance(valor_causa, Decimal):
            return float(valor_causa)
        if isinstance(valor_causa, (int, float)):
            return float(valor_causa)
        if isinstance(valor_causa, str):
            valor_limpo = valor_causa.strip().replace(",", ".")
            valor_limpo = "".join(c for c in valor_limpo if c.isdigit() or c == ".")
            if valor_limpo:
                return float(valor_limpo)
            return 0.0
        return float(str(valor_causa).replace(",", "."))
    except (ValueError, TypeError, AttributeError):
        return 0.0


def _parse_data_controle_LA(value: Any) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return parse_date_from_db(value)


def _parse_datetime_controle_LA(value: Any) -> Optional[datetime]:
    """Data/hora para cálculo de permanência: preserva horário quando existir no payload."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, time.min)
    return parse_datetime_from_db(value)


def _data_sentenca_no_intervalo_LA(
    row: Dict[str, Any],
    from_date: Optional[date],
    to_date: Optional[date],
) -> bool:
    """
    Se não há intervalo, não restringe por ``DATA_SENTENCA``.
    Caso contrário, exige data de sentença válida e contida no intervalo (igual ``_in_range`` em
    ``dashboard_routes``).
    """
    if not from_date and not to_date:
        return True
    d = _parse_data_controle_LA(_col(row, _COL_DATA_SENTENCA))
    if d is None:
        return False
    if from_date and to_date:
        return from_date <= d <= to_date
    if from_date:
        return d >= from_date
    return d <= to_date


def _data_acordao_no_intervalo_LA(
    row: Dict[str, Any],
    from_date: Optional[date],
    to_date: Optional[date],
) -> bool:
    """Mesmo critério de ``_data_sentenca_no_intervalo_LA``, para ``DATA_ACORDAO``."""
    if not from_date and not to_date:
        return True
    d = _parse_data_controle_LA(_col(row, _COL_DATA_ACORDAO))
    if d is None:
        return False
    if from_date and to_date:
        return from_date <= d <= to_date
    if from_date:
        return d >= from_date
    return d <= to_date


def _data_transito_julgado_no_intervalo_LA(
    row: Dict[str, Any],
    from_date: Optional[date],
    to_date: Optional[date],
) -> bool:
    """Mesmo critério de ``_data_sentenca_no_intervalo_LA``, para ``DATA_TRANSITO_JULGADO``."""
    if not from_date and not to_date:
        return True
    d = _parse_data_controle_LA(_col(row, _COL_DATA_TRANSITO_JULGADO))
    if d is None:
        return False
    if from_date and to_date:
        return from_date <= d <= to_date
    if from_date:
        return d >= from_date
    return d <= to_date


def _col_data_no_intervalo_LA(
    row: Dict[str, Any],
    col: str,
    from_date: Optional[date],
    to_date: Optional[date],
) -> bool:
    """Sem intervalo, não restringe. Caso contrário exige data válida em ``col`` dentro do intervalo."""
    if not from_date and not to_date:
        return True
    d = _parse_data_controle_LA(_col(row, col))
    if d is None:
        return False
    if from_date and to_date:
        return from_date <= d <= to_date
    if from_date:
        return d >= from_date
    return d <= to_date


def _duracao_dias_entrada_saida_LA(
    row: Dict[str, Any],
    col_entrada: str,
    col_saida: str,
) -> Optional[float]:
    """
    Dias entre saída e entrada do setor (``saída - entrada``), com fração quando há horário.
    Mesma regra para fase inicial, recursal e execução. Apenas ``date`` no payload implica meia-noite.
    Retorna ``None`` se faltar data, parse falhar ou saída for anterior à entrada.
    """
    entrada = _parse_datetime_controle_LA(_col(row, col_entrada))
    saida = _parse_datetime_controle_LA(_col(row, col_saida))
    if entrada is None or saida is None:
        return None
    segundos = (saida - entrada).total_seconds()
    if segundos < 0:
        return None
    return float(segundos / 86400.0)


@memo.por_pedido()
def _duracoes_permanencia_LA(
    controle_processo: List[Dict[str, Any]],
    col_entrada: str,
    col_saida: str,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
):
    """V2 (app.analyses.common.tempo): dias (com fração) entre a entrada e a saída da fase, com a mesma regra
    de `_duracao_dias_entrada_saida_LA` (0 entra, negativo fica fora), amostrados pela data da SAÍDA no
    período. Usado pela média, pela mediana e pela série mês a mês."""
    return tempo.duracoes(
        _base_controle_processo_LA(controle_processo),
        lambda p: _parse_datetime_controle_LA(_col(p, col_entrada)),
        lambda p: _parse_datetime_controle_LA(_col(p, col_saida)),
        de=from_date,
        ate=to_date,
        data_periodo=lambda p: _parse_data_controle_LA(_col(p, col_saida)),
        unidade="dias_fracao",
        aceita_zero=True,
    )


def _media_dias_permanencia_setor_LA(
    controle_processo: List[Dict[str, Any]],
    col_entrada: str,
    col_saida: str,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """
    Média de dias (entrada → saída), amostrada pelos processos cuja SAÍDA da fase
    caiu no período informado (não pela entrada/ajuizamento).
    """
    return tempo.media(_duracoes_permanencia_LA(controle_processo, col_entrada, col_saida, from_date, to_date))


def _mediana_dias_permanencia_setor_LA(
    controle_processo: List[Dict[str, Any]],
    col_entrada: str,
    col_saida: str,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """
    Mediana de dias (entrada → saída), amostrada pelos processos cuja SAÍDA da fase
    caiu no período informado (não pela entrada/ajuizamento).
    """
    return tempo.mediana(_duracoes_permanencia_LA(controle_processo, col_entrada, col_saida, from_date, to_date))


# -----------------------------------------------------------------------------
# 1 - Função auxiliar base (todas as outras devem partir daqui)
# -----------------------------------------------------------------------------
@memo.por_pedido()
def _base_controle_processo_LA(controle_processo: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Base do dashboard LA: mantém apenas linhas cujo ID_ESCRITORIO == 21.

    Use esta função como primeira etapa de qualquer análise/agrupamento para
    garantir consistência entre métricas e gráficos. Utilizando a DATA_AJUIZAMENTO como filtro.
    """
    base: List[Dict[str, Any]] = []
    for row in controle_processo:
        if _to_int(_col(row, _COL_ID_ESCRITORIO)) == _ID_ESCRITORIO_LA:
            base.append(row)
    return base


@memo.por_pedido()
def _filtrar_controle_processo_por_id_fase_LA(
    controle_processo: List[Dict[str, Any]],
    id_fase: int,
) -> List[Dict[str, Any]]:
    processos = _base_controle_processo_LA(controle_processo)
    return [p for p in processos if _to_int(_col(p, _COL_ID_FASE)) == id_fase]


@memo.por_pedido()
def _filtrar_controle_processo_log_inicial_indeferida_LA(
    controle_processo: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Processos cujo log registrou status 189 (INICIAL INDEFERIDA) na fase inicial (25)."""
    processos = _base_controle_processo_LA(controle_processo)
    return [p for p in processos if _truthy_flag_LA(_col(p, _COL_LOG_TEVE_SUBFASE_INICIAL_INDEFERIDA))]


@memo.por_pedido()
def _filtrar_controle_processo_log_recursal_nao_provido_LA(
    controle_processo: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Processos cujo log registrou status 190 (RECURSO NÃO PROVIDO) na fase recursal (8)."""
    processos = _base_controle_processo_LA(controle_processo)
    return [p for p in processos if _truthy_flag_LA(_col(p, _COL_LOG_TEVE_SUBFASE_RECURSO_NAO_PROVIDO))]


@memo.por_pedido()
def _filtrar_controle_processo_fase_transito_julgado_LA(
    controle_processo: List[Dict[str, Any]],
    *,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """
    Fase TRÂNSITO EM JULGADO (``ID_FASE`` = 11). Com intervalo, restringe por ``DATA_TRANSITO_JULGADO``.
    """
    processos = _base_controle_processo_LA(controle_processo)
    return [
        p
        for p in processos
        if _to_int(_col(p, _COL_ID_FASE)) == _ID_FASE_TRANSITO_JULGADO
        and _data_transito_julgado_no_intervalo_LA(p, from_date, to_date)
    ]


def _get_id_merito_1g(p: Dict[str, Any]) -> Optional[int]:
    """ID de mérito 1G: usa a coluna nova quando presente, senão traduz o status antigo."""
    novo = _to_int(_col(p, "ID_SENTENCA_MERITO_1G"))
    return mj.resolver_id_merito_1g(novo, _col(p, _COL_STATUS_1G))


def _get_id_merito_2g(p: Dict[str, Any]) -> Optional[int]:
    """ID de mérito 2G: usa a coluna nova quando presente, senão traduz o status antigo."""
    novo = _to_int(_col(p, "ID_ACORDAO_MERITO_2G"))
    return mj.resolver_id_merito_2g(novo, _col(p, _COL_STATUS_2G))


@memo.por_pedido()
def _filtrar_extintos_com_merito_LA(
    controle_processo: List[Dict[str, Any]],
    *,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """
    Linhas da base LA com mérito de 1º grau (todo valor exceto Extinto Sem Mérito).

    Com ``from_date`` / ``to_date``, mantém apenas registros cuja ``DATA_SENTENCA`` cai no
    intervalo (inclusivo quando ambas as datas existem).
    """
    processos = _base_controle_processo_LA(controle_processo)
    return [
        p
        for p in processos
        if mj.eh_extinto_com_merito_2g(_get_id_merito_1g(p))
        and _data_sentenca_no_intervalo_LA(p, from_date, to_date)
    ]


@memo.por_pedido()
def _filtrar_extintos_com_merito_2g_LA(
    controle_processo: List[Dict[str, Any]],
    *,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """
    Linhas da base LA com mérito de 2º grau (todo valor exceto Extinto Sem Mérito).

    Com ``from_date`` / ``to_date``, mantém apenas registros cuja ``DATA_ACORDAO`` cai no intervalo.
    """
    processos = _base_controle_processo_LA(controle_processo)
    return [
        p
        for p in processos
        if mj.eh_extinto_com_merito_2g(_get_id_merito_2g(p))
        and _data_acordao_no_intervalo_LA(p, from_date, to_date)
    ]


@memo.por_pedido()
def _filtrar_extintos_sem_merito_LA(
    controle_processo: List[Dict[str, Any]],
    *,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """
    Linhas da base LA cujo mérito de 1º grau é Extinto Sem Mérito.

    Com ``from_date`` / ``to_date``, restringe por ``DATA_SENTENCA`` (mesma lógica dos extintos com mérito).
    """
    processos = _base_controle_processo_LA(controle_processo)
    return [
        p
        for p in processos
        if mj.eh_extinto_sem_merito_2g(_get_id_merito_1g(p))
        and _data_sentenca_no_intervalo_LA(p, from_date, to_date)
    ]


@memo.por_pedido()
def _filtrar_extintos_sem_merito_2g_LA(
    controle_processo: List[Dict[str, Any]],
    *,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """
    Linhas da base LA cujo mérito de 2º grau é Extinto Sem Mérito.

    Com ``from_date`` / ``to_date``, restringe por ``DATA_ACORDAO``.
    """
    processos = _base_controle_processo_LA(controle_processo)
    return [
        p
        for p in processos
        if mj.eh_extinto_sem_merito_2g(_get_id_merito_2g(p))
        and _data_acordao_no_intervalo_LA(p, from_date, to_date)
    ]


# -----------------------------------------------------------------------------
# 2 - Totais gerais
# -----------------------------------------------------------------------------
def get_total_controle_processo_LA(controle_processo: List[Dict[str, Any]]) -> int:
    return len(_base_controle_processo_LA(controle_processo))


def get_total_controle_processo_fase_inicial_LA(controle_processo: List[Dict[str, Any]]) -> int:
    """Quantidade de processos na fase INICIAL (``ID_FASE`` = 25) após filtro do escritório LA."""
    return len(_filtrar_controle_processo_por_id_fase_LA(controle_processo, _ID_FASE_INICIAL_LA))


def get_total_controle_processo_log_inicial_indeferida_LA(controle_processo: List[Dict[str, Any]]) -> int:
    """Quantidade de processos que em algum momento ficaram com status 189 (INICIAL INDEFERIDA) na fase inicial."""
    return len(_filtrar_controle_processo_log_inicial_indeferida_LA(controle_processo))


def get_valor_causa_total_controle_processo_log_inicial_indeferida_LA(
    controle_processo: List[Dict[str, Any]],
) -> float:
    """Soma de ``VALOR_DE_CAUSA`` dos processos que em algum momento ficaram com status 189 (INICIAL INDEFERIDA)."""
    processos = _filtrar_controle_processo_log_inicial_indeferida_LA(controle_processo)
    return round(sum(_converter_valor_causa(_col(p, _COL_VALOR_CAUSA)) for p in processos), 2)


def get_total_controle_processo_log_recursal_nao_provido_LA(controle_processo: List[Dict[str, Any]]) -> int:
    """Quantidade de processos que em algum momento ficaram com status 190 (RECURSO NÃO PROVIDO) na fase recursal."""
    return len(_filtrar_controle_processo_log_recursal_nao_provido_LA(controle_processo))


def get_valor_causa_total_controle_processo_log_recursal_nao_provido_LA(
    controle_processo: List[Dict[str, Any]],
) -> float:
    """Soma de ``VALOR_DE_CAUSA`` dos processos que em algum momento ficaram com status 190 (RECURSO NÃO PROVIDO)."""
    processos = _filtrar_controle_processo_log_recursal_nao_provido_LA(controle_processo)
    return round(sum(_converter_valor_causa(_col(p, _COL_VALOR_CAUSA)) for p in processos), 2)


def get_valor_causa_total_controle_processo_fase_inicial_LA(
    controle_processo: List[Dict[str, Any]],
) -> float:
    """Soma de ``VALOR_DE_CAUSA`` dos processos na fase INICIAL (``ID_FASE`` = 25)."""
    processos = _filtrar_controle_processo_por_id_fase_LA(controle_processo, _ID_FASE_INICIAL_LA)
    return float(sum(_converter_valor_causa(_col(p, _COL_VALOR_CAUSA)) for p in processos))


def get_total_controle_processo_fase_recursal_LA(controle_processo: List[Dict[str, Any]]) -> int:
    """Quantidade de processos na fase RECURSAL (``ID_FASE`` = 8) após filtro do escritório LA."""
    return len(_filtrar_controle_processo_por_id_fase_LA(controle_processo, _ID_FASE_RECURSAL_LA))


def get_valor_causa_total_controle_processo_fase_recursal_LA(
    controle_processo: List[Dict[str, Any]],
) -> float:
    """Soma de ``VALOR_DE_CAUSA`` dos processos na fase RECURSAL (``ID_FASE`` = 8)."""
    processos = _filtrar_controle_processo_por_id_fase_LA(controle_processo, _ID_FASE_RECURSAL_LA)
    return float(sum(_converter_valor_causa(_col(p, _COL_VALOR_CAUSA)) for p in processos))


def get_total_controle_processo_fase_execucao_LA(controle_processo: List[Dict[str, Any]]) -> int:
    """Quantidade de processos na fase EXECUÇÃO (``ID_FASE`` = 12) após filtro do escritório LA."""
    return len(_filtrar_controle_processo_por_id_fase_LA(controle_processo, _ID_FASE_EXECUCAO_LA))


def get_valor_causa_execucao_total_controle_processo_fase_execucao_LA(
    controle_processo: List[Dict[str, Any]],
) -> float:
    """Soma de ``VALOR_DE_CAUSA`` dos processos na fase EXECUÇÃO (``ID_FASE`` = 12)."""
    processos = _filtrar_controle_processo_por_id_fase_LA(controle_processo, _ID_FASE_EXECUCAO_LA)
    return float(
        sum(_converter_valor_causa(_col(p, _COL_VALOR_CAUSA)) for p in processos)
    )


def get_total_controle_processo_fase_arquivado_procedente_LA(
    controle_processo: List[Dict[str, Any]],
) -> int:
    """Quantidade na fase ARQUIVADO PROCEDENTE (``ID_FASE`` = 27)."""
    return len(
        _filtrar_controle_processo_por_id_fase_LA(
            controle_processo, _ID_FASE_ARQUVADO_PROCEDENTE
        )
    )


def get_valor_causa_total_controle_processo_fase_arquivado_procedente_LA(
    controle_processo: List[Dict[str, Any]],
) -> float:
    """Soma de ``VALOR_DE_CAUSA`` na fase ARQUIVADO PROCEDENTE (``ID_FASE`` = 27)."""
    processos = _filtrar_controle_processo_por_id_fase_LA(
        controle_processo, _ID_FASE_ARQUVADO_PROCEDENTE
    )
    return float(sum(_converter_valor_causa(_col(p, _COL_VALOR_CAUSA)) for p in processos))


def get_total_controle_processo_fase_arquivado_improcedente_LA(
    controle_processo: List[Dict[str, Any]],
) -> int:
    """Quantidade na fase ARQUIVADO IMPROCEDENTE (``ID_FASE`` = 28)."""
    return len(
        _filtrar_controle_processo_por_id_fase_LA(
            controle_processo, _ID_FASE_ARQUVADO_IMPROCEDENTE
        )
    )


def get_valor_causa_total_controle_processo_fase_arquivado_improcedente_LA(
    controle_processo: List[Dict[str, Any]],
) -> float:
    """Soma de ``VALOR_DE_CAUSA`` na fase ARQUIVADO IMPROCEDENTE (``ID_FASE`` = 28)."""
    processos = _filtrar_controle_processo_por_id_fase_LA(
        controle_processo, _ID_FASE_ARQUVADO_IMPROCEDENTE
    )
    return float(sum(_converter_valor_causa(_col(p, _COL_VALOR_CAUSA)) for p in processos))


def get_total_controle_processo_fase_transito_julgado_LA(
    controle_processo: List[Dict[str, Any]],
    *,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """Quantidade na fase TRÂNSITO EM JULGADO (``ID_FASE`` = 11), opcionalmente por ``DATA_TRANSITO_JULGADO``."""
    return len(
        _filtrar_controle_processo_fase_transito_julgado_LA(
            controle_processo, from_date=from_date, to_date=to_date
        )
    )


def get_valor_causa_total_controle_processo_fase_transito_julgado_LA(
    controle_processo: List[Dict[str, Any]],
    *,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """Soma de ``VALOR_DE_CAUSA`` do recorte (``DATA_TRANSITO_JULGADO`` quando há intervalo)."""
    processos = _filtrar_controle_processo_fase_transito_julgado_LA(
        controle_processo, from_date=from_date, to_date=to_date
    )
    return float(sum(_converter_valor_causa(_col(p, _COL_VALOR_CAUSA)) for p in processos))


def get_total_extintos_com_merito_LA(
    controle_processo: List[Dict[str, Any]],
    *,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """Quantidade de processos com ``ID_1G`` em extintos com mérito (17, 19–23), opcionalmente por ``DATA_SENTENCA``."""
    return len(
        _filtrar_extintos_com_merito_LA(
            controle_processo, from_date=from_date, to_date=to_date
        )
    )


def get_valor_causa_total_extintos_com_merito_LA(
    controle_processo: List[Dict[str, Any]],
    *,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """Soma de ``VALOR_DE_CAUSA`` do mesmo recorte (``DATA_SENTENCA`` quando o intervalo é informado)."""
    processos = _filtrar_extintos_com_merito_LA(
        controle_processo, from_date=from_date, to_date=to_date
    )
    return float(sum(_converter_valor_causa(_col(p, _COL_VALOR_CAUSA)) for p in processos))


def get_extintos_com_merito_por_tipo_sentenca_LA(
    controle_processo: List[Dict[str, Any]],
    *,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """
    Breakdown de extintos com mérito (1º grau) por tipo de sentença.

    Agrupa o mesmo recorte de ``get_total_extintos_com_merito_LA`` (``ID_1G`` ∈ extintos com mérito e
    opcionalmente por ``DATA_SENTENCA``), retornando quantidade e soma de ``VALOR_DE_CAUSA``
    por (``ID_1G``, ``STATUS_1G``).
    """
    processos = _filtrar_extintos_com_merito_LA(
        controle_processo, from_date=from_date, to_date=to_date
    )

    def _label_from_status(id_1g: int, status_1g: str) -> str:
        s = str(status_1g or "").strip()
        if s:
            s_up = s.upper()
            if "SENTEN" in s_up:
                return s_up
            return f"SENTENÇA {s_up}"
        return mj.rotulo_merito(id_1g) or f"SENTENÇA TIPO {id_1g}"

    acc: Dict[tuple, Dict[str, Any]] = {}
    for p in processos:
        id_1g = _get_id_merito_1g(p)
        if id_1g is None:
            continue
        status_1g_raw = _col(p, _COL_STATUS_1G)
        status_1g = (str(status_1g_raw).strip() if status_1g_raw is not None else "") or ""
        label = _label_from_status(id_1g, status_1g)
        key = (id_1g,)

        if key not in acc:
            acc[key] = {
                "id_1g": id_1g,
                # Nome vindo do banco (spg.nome AS "STATUS_1G")
                "status_1g": status_1g,
                # Campos “prontos pra UI”
                "label": label,
                "tipo_sentenca": label,
                "quantidade": 0,
                "valor_causa": 0.0,
            }
        else:
            # Se a primeira linha veio sem nome e uma próxima veio com nome, atualiza.
            if not acc[key].get("status_1g") and status_1g:
                acc[key]["status_1g"] = status_1g
                new_label = _label_from_status(id_1g, status_1g)
                acc[key]["label"] = new_label
                acc[key]["tipo_sentenca"] = new_label

        acc[key]["quantidade"] += 1
        acc[key]["valor_causa"] += float(_converter_valor_causa(_col(p, _COL_VALOR_CAUSA)))

    items = list(acc.values())
    items.sort(
        key=lambda x: (
            -(int(x.get("quantidade") or 0)),
            str(x.get("label") or ""),
            int(x.get("id_1g") or 0),
        )
    )
    for it in items:
        it["valor_causa"] = round(float(it["valor_causa"]), 2)
    return items


def get_total_extintos_com_merito_2g_LA(
    controle_processo: List[Dict[str, Any]],
    *,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """Quantidade com ``ID_2G`` em extintos com mérito (17, 19–25), opcionalmente por ``DATA_ACORDAO``."""
    return len(
        _filtrar_extintos_com_merito_2g_LA(
            controle_processo, from_date=from_date, to_date=to_date
        )
    )


def get_valor_causa_total_extintos_com_merito_2g_LA(
    controle_processo: List[Dict[str, Any]],
    *,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """Soma de ``VALOR_DE_CAUSA`` do recorte 2º grau (``DATA_ACORDAO`` quando há intervalo)."""
    processos = _filtrar_extintos_com_merito_2g_LA(
        controle_processo, from_date=from_date, to_date=to_date
    )
    return float(sum(_converter_valor_causa(_col(p, _COL_VALOR_CAUSA)) for p in processos))


def get_valor_causa_acordao_total_extintos_com_merito_2g_LA(
    controle_processo: List[Dict[str, Any]],
    *,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """
    Soma de ``VALOR_CAUSA_ACORDO`` do recorte 2º grau (``DATA_ACORDAO`` quando há intervalo).

    Usado só pelo painel "Extintos · 2º Grau" do Recursal — diferente de
    :func:`get_valor_causa_total_extintos_com_merito_2g_LA` (usada pelo Controle
    de Processos), que soma ``VALOR_DE_CAUSA`` (valor de causa inicial).
    """
    processos = _filtrar_extintos_com_merito_2g_LA(
        controle_processo, from_date=from_date, to_date=to_date
    )
    return float(sum(_converter_valor_causa(_col(p, _COL_VALOR_CAUSA_ACORDO)) for p in processos))


def get_extintos_com_merito_2g_por_tipo_sentenca_LA(
    controle_processo: List[Dict[str, Any]],
    *,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """
    Breakdown de extintos com mérito (2º grau) por tipo de acórdão/status.

    Agrupa o mesmo recorte de ``get_total_extintos_com_merito_2g_LA`` (``ID_2G`` ∈ extintos com mérito e
    opcionalmente por ``DATA_ACORDAO``), retornando quantidade e soma de ``VALOR_DE_CAUSA``
    por ``ID_2G`` e incluindo o nome vindo da query em ``STATUS_2G``.
    """
    processos = _filtrar_extintos_com_merito_2g_LA(
        controle_processo, from_date=from_date, to_date=to_date
    )

    def _label_from_status(id_2g: int, status_2g: str) -> str:
        s = str(status_2g or "").strip()
        if s:
            s_up = s.upper()
            if "ACORD" in s_up:
                return s_up
            if "SENTEN" in s_up:
                return s_up
            # Mantém o mesmo padrão visual do 1º grau (prefixo)
            return f"{s_up}"
        return mj.rotulo_merito(id_2g) or f"ACÓRDÃO TIPO {id_2g}"

    acc: Dict[tuple, Dict[str, Any]] = {}
    for p in processos:
        id_2g = _get_id_merito_2g(p)
        if id_2g is None:
            continue

        status_2g_raw = _col(p, _COL_STATUS_2G)
        status_2g = (str(status_2g_raw).strip() if status_2g_raw is not None else "") or ""
        label = _label_from_status(id_2g, status_2g)
        key = (id_2g,)

        if key not in acc:
            acc[key] = {
                "id_2g": id_2g,
                "status_2g": status_2g,
                "label": label,
                "tipo_sentenca": label,
                "quantidade": 0,
                "valor_causa": 0.0,
            }
        else:
            if not acc[key].get("status_2g") and status_2g:
                acc[key]["status_2g"] = status_2g
                new_label = _label_from_status(id_2g, status_2g)
                acc[key]["label"] = new_label
                acc[key]["tipo_sentenca"] = new_label

        acc[key]["quantidade"] += 1
        acc[key]["valor_causa"] += float(_converter_valor_causa(_col(p, _COL_VALOR_CAUSA)))

    items = list(acc.values())
    items.sort(
        key=lambda x: (
            -(int(x.get("quantidade") or 0)),
            str(x.get("label") or ""),
            int(x.get("id_2g") or 0),
        )
    )
    for it in items:
        it["valor_causa"] = round(float(it["valor_causa"]), 2)
    return items


def get_extintos_com_merito_2g_por_tipo_sentenca_valor_acordao_LA(
    controle_processo: List[Dict[str, Any]],
    *,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """
    Mesmo recorte/agrupamento de :func:`get_extintos_com_merito_2g_por_tipo_sentenca_LA`,
    mas somando ``VALOR_CAUSA_ACORDO`` em vez de ``VALOR_DE_CAUSA`` — usado só pelo
    painel "Extintos · 2º Grau" do Recursal.
    """
    processos = _filtrar_extintos_com_merito_2g_LA(
        controle_processo, from_date=from_date, to_date=to_date
    )

    def _label_from_status(id_2g: int, status_2g: str) -> str:
        s = str(status_2g or "").strip()
        if s:
            s_up = s.upper()
            if "ACORD" in s_up:
                return s_up
            if "SENTEN" in s_up:
                return s_up
            return f"{s_up}"
        return mj.rotulo_merito(id_2g) or f"ACÓRDÃO TIPO {id_2g}"

    acc: Dict[tuple, Dict[str, Any]] = {}
    for p in processos:
        id_2g = _get_id_merito_2g(p)
        if id_2g is None:
            continue

        status_2g_raw = _col(p, _COL_STATUS_2G)
        status_2g = (str(status_2g_raw).strip() if status_2g_raw is not None else "") or ""
        label = _label_from_status(id_2g, status_2g)
        key = (id_2g,)

        if key not in acc:
            acc[key] = {
                "id_2g": id_2g,
                "status_2g": status_2g,
                "label": label,
                "tipo_sentenca": label,
                "quantidade": 0,
                "valor_causa": 0.0,
            }
        else:
            if not acc[key].get("status_2g") and status_2g:
                acc[key]["status_2g"] = status_2g
                new_label = _label_from_status(id_2g, status_2g)
                acc[key]["label"] = new_label
                acc[key]["tipo_sentenca"] = new_label

        acc[key]["quantidade"] += 1
        acc[key]["valor_causa"] += float(_converter_valor_causa(_col(p, _COL_VALOR_CAUSA_ACORDO)))

    items = list(acc.values())
    items.sort(
        key=lambda x: (
            -(int(x.get("quantidade") or 0)),
            str(x.get("label") or ""),
            int(x.get("id_2g") or 0),
        )
    )
    for it in items:
        it["valor_causa"] = round(float(it["valor_causa"]), 2)
    return items


def get_total_extintos_sem_merito_LA(
    controle_processo: List[Dict[str, Any]],
    *,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """Quantidade com ``ID_1G`` = 18, opcionalmente por ``DATA_SENTENCA``."""
    return len(
        _filtrar_extintos_sem_merito_LA(
            controle_processo, from_date=from_date, to_date=to_date
        )
    )


def get_valor_causa_total_extintos_sem_merito_LA(
    controle_processo: List[Dict[str, Any]],
    *,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """Soma de ``VALOR_DE_CAUSA`` do recorte (``DATA_SENTENCA`` quando há intervalo)."""
    processos = _filtrar_extintos_sem_merito_LA(
        controle_processo, from_date=from_date, to_date=to_date
    )
    return float(sum(_converter_valor_causa(_col(p, _COL_VALOR_CAUSA)) for p in processos))


def get_total_extintos_sem_merito_2g_LA(
    controle_processo: List[Dict[str, Any]],
    *,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """Quantidade com ``ID_2G`` em extintos sem mérito (8, 18), opcionalmente por ``DATA_ACORDAO``."""
    return len(
        _filtrar_extintos_sem_merito_2g_LA(
            controle_processo, from_date=from_date, to_date=to_date
        )
    )


def get_valor_causa_total_extintos_sem_merito_2g_LA(
    controle_processo: List[Dict[str, Any]],
    *,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """Soma de ``VALOR_DE_CAUSA`` do recorte 2º grau sem mérito (``DATA_ACORDAO`` quando há intervalo)."""
    processos = _filtrar_extintos_sem_merito_2g_LA(
        controle_processo, from_date=from_date, to_date=to_date
    )
    return float(sum(_converter_valor_causa(_col(p, _COL_VALOR_CAUSA)) for p in processos))


def get_valor_causa_acordao_total_extintos_sem_merito_2g_LA(
    controle_processo: List[Dict[str, Any]],
    *,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """
    Soma de ``VALOR_CAUSA_ACORDO`` do recorte 2º grau sem mérito (``DATA_ACORDAO``
    quando há intervalo) — usado só pelo painel "Extintos · 2º Grau" do Recursal.
    """
    processos = _filtrar_extintos_sem_merito_2g_LA(
        controle_processo, from_date=from_date, to_date=to_date
    )
    return float(sum(_converter_valor_causa(_col(p, _COL_VALOR_CAUSA_ACORDO)) for p in processos))


# -----------------------------------------------------------------------------
# Taxa de provimento (2º grau)
# -----------------------------------------------------------------------------


@memo.por_pedido()
def _filtrar_acordaos_2g_LA(
    controle_processo: List[Dict[str, Any]],
    *,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """Recorte de acórdãos 2G: extintos com mérito + extintos sem mérito."""
    return (
        _filtrar_extintos_com_merito_2g_LA(
            controle_processo, from_date=from_date, to_date=to_date
        )
        + _filtrar_extintos_sem_merito_2g_LA(
            controle_processo, from_date=from_date, to_date=to_date
        )
    )


def get_total_acordaos_2g_LA(
    controle_processo: List[Dict[str, Any]],
    *,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """Total de acórdãos 2G (extintos com mérito + extintos sem mérito)."""
    return get_total_extintos_com_merito_2g_LA(
        controle_processo, from_date=from_date, to_date=to_date
    ) + get_total_extintos_sem_merito_2g_LA(
        controle_processo, from_date=from_date, to_date=to_date
    )


def get_total_decisoes_positivas_taxa_provimento_2g_LA(
    controle_processo: List[Dict[str, Any]],
    *,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """
    Acórdãos 2G considerados positivos na taxa de provimento:

    PROCEDENTE / PARC. PROCEDENTE (COM ou SEM PE), SENTENÇA ANULADA e EXTINTOS SEM MÉRITO.
    """
    return sum(
        1
        for p in _filtrar_acordaos_2g_LA(
            controle_processo, from_date=from_date, to_date=to_date
        )
        if mj.eh_decisao_positiva_taxa_provimento_2g(_get_id_merito_2g(p))
    )


def get_total_decisoes_improcedentes_taxa_provimento_2g_LA(
    controle_processo: List[Dict[str, Any]],
    *,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """Acórdãos 2G improcedentes (único status negativo na taxa de provimento)."""
    return sum(
        1
        for p in _filtrar_acordaos_2g_LA(
            controle_processo, from_date=from_date, to_date=to_date
        )
        if mj.eh_decisao_improcedente_taxa_provimento_2g(_get_id_merito_2g(p))
    )


def get_taxa_provimento_2g_LA(
    controle_processo: List[Dict[str, Any]],
    *,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> Optional[float]:
    """
    Taxa de provimento = decisões positivas / total de acórdãos 2G × 100.

    Positivos: procedente, parcialmente procedente, sentença anulada e extintos sem mérito.
    Negativo (fora do numerador): improcedente. Total = extintos com mérito + sem mérito.
    """
    total = get_total_acordaos_2g_LA(
        controle_processo, from_date=from_date, to_date=to_date
    )
    if total == 0:
        return 0.0
    positivos = get_total_decisoes_positivas_taxa_provimento_2g_LA(
        controle_processo, from_date=from_date, to_date=to_date
    )
    return round((positivos / total) * 100, 2)


def get_media_tempo_dias_fase_inicial_LA(
    controle_processo: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """
    Tempo médio na fase INICIAL: média de ``DT_SAIDA_INICIAL - DATA_AJUIZAMENTO`` em dias
    (fração quando há horário nas colunas), amostrada pelos processos cuja saída da fase
    caiu no período informado. Só processos com par válido e saída não anterior à entrada.
    """
    return _media_dias_permanencia_setor_LA(
        controle_processo,
        _COL_DATA_AJUIZAMENTO,
        _COL_DT_SAIDA_INICIAL,
        from_date,
        to_date,
    )


def get_media_tempo_dias_fase_recursal_LA(
    controle_processo: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """Mesmo critério da inicial, para ``DT_ENTRADA_RECURSAL`` / ``DT_SAIDA_RECURSAL``."""
    return _media_dias_permanencia_setor_LA(
        controle_processo,
        _COL_DT_ENTRADA_RECURSAL,
        _COL_DT_SAIDA_RECURSAL,
        from_date,
        to_date,
    )


def get_media_tempo_dias_fase_execucao_LA(
    controle_processo: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """Mesmo critério da inicial, para ``DT_ENTRADA_EXECUCAO`` / ``DT_SAIDA_EXECUCAO``."""
    return _media_dias_permanencia_setor_LA(
        controle_processo,
        _COL_DT_ENTRADA_EXECUCAO,
        _COL_DT_SAIDA_EXECUCAO,
        from_date,
        to_date,
    )


def get_mediana_tempo_dias_fase_inicial_LA(
    controle_processo: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """
    Mediana na fase INICIAL: mediana de ``DT_SAIDA_INICIAL - DATA_AJUIZAMENTO`` em dias
    (fração quando há horário nas colunas), amostrada pelos processos cuja saída da fase
    caiu no período informado. Só processos com par válido e saída não anterior à entrada.
    """
    return _mediana_dias_permanencia_setor_LA(
        controle_processo,
        _COL_DATA_AJUIZAMENTO,
        _COL_DT_SAIDA_INICIAL,
        from_date,
        to_date,
    )


def get_mediana_tempo_dias_fase_recursal_LA(
    controle_processo: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """Mesmo critério da inicial, para ``DT_ENTRADA_RECURSAL`` / ``DT_SAIDA_RECURSAL``."""
    return _mediana_dias_permanencia_setor_LA(
        controle_processo,
        _COL_DT_ENTRADA_RECURSAL,
        _COL_DT_SAIDA_RECURSAL,
        from_date,
        to_date,
    )


def get_mediana_tempo_dias_fase_execucao_LA(
    controle_processo: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """Mesmo critério da inicial, para ``DT_ENTRADA_EXECUCAO`` / ``DT_SAIDA_EXECUCAO``."""
    return _mediana_dias_permanencia_setor_LA(
        controle_processo,
        _COL_DT_ENTRADA_EXECUCAO,
        _COL_DT_SAIDA_EXECUCAO,
        from_date,
        to_date,
    )


def _comparativo_percentual_LA(atual: float, anterior: float) -> float:
    return periodo.variacao_percentual(atual, anterior)


def get_comparativo_media_tempo_dias_fase_inicial_LA(
    controle_processo: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """Comparativo (%) da média de dias na fase INICIAL vs período anterior equivalente."""
    # V2: o período atual também passa pelo resolver (sem período: o mês corrente até hoje, como o
    # anterior); a v1 usava o from/to cru e, sem filtro, comparava o histórico inteiro com o mês anterior.
    inicio, fim, inicio_ant, fim_ant = resolver_periodo_comparativo(from_date, to_date)
    atual = get_media_tempo_dias_fase_inicial_LA(controle_processo, inicio, fim)
    anterior = get_media_tempo_dias_fase_inicial_LA(controle_processo, inicio_ant, fim_ant)
    return _comparativo_percentual_LA(atual, anterior)


def get_comparativo_media_tempo_dias_fase_recursal_LA(
    controle_processo: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """Comparativo (%) da média de dias na fase RECURSAL vs período anterior equivalente."""
    # V2: o período atual também passa pelo resolver (sem período: o mês corrente até hoje, como o
    # anterior); a v1 usava o from/to cru e, sem filtro, comparava o histórico inteiro com o mês anterior.
    inicio, fim, inicio_ant, fim_ant = resolver_periodo_comparativo(from_date, to_date)
    atual = get_media_tempo_dias_fase_recursal_LA(controle_processo, inicio, fim)
    anterior = get_media_tempo_dias_fase_recursal_LA(controle_processo, inicio_ant, fim_ant)
    return _comparativo_percentual_LA(atual, anterior)


def get_comparativo_media_tempo_dias_fase_execucao_LA(
    controle_processo: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """Comparativo (%) da média de dias na fase EXECUÇÃO vs período anterior equivalente."""
    # V2: o período atual também passa pelo resolver (sem período: o mês corrente até hoje, como o
    # anterior); a v1 usava o from/to cru e, sem filtro, comparava o histórico inteiro com o mês anterior.
    inicio, fim, inicio_ant, fim_ant = resolver_periodo_comparativo(from_date, to_date)
    atual = get_media_tempo_dias_fase_execucao_LA(controle_processo, inicio, fim)
    anterior = get_media_tempo_dias_fase_execucao_LA(controle_processo, inicio_ant, fim_ant)
    return _comparativo_percentual_LA(atual, anterior)


def get_comparativo_mediana_tempo_dias_fase_inicial_LA(
    controle_processo: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """Comparativo (%) da mediana de dias na fase INICIAL vs período anterior equivalente."""
    # V2: o período atual também passa pelo resolver (sem período: o mês corrente até hoje, como o
    # anterior); a v1 usava o from/to cru e, sem filtro, comparava o histórico inteiro com o mês anterior.
    inicio, fim, inicio_ant, fim_ant = resolver_periodo_comparativo(from_date, to_date)
    atual = get_mediana_tempo_dias_fase_inicial_LA(controle_processo, inicio, fim)
    anterior = get_mediana_tempo_dias_fase_inicial_LA(controle_processo, inicio_ant, fim_ant)
    return _comparativo_percentual_LA(atual, anterior)


def get_comparativo_mediana_tempo_dias_fase_recursal_LA(
    controle_processo: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """Comparativo (%) da mediana de dias na fase RECURSAL vs período anterior equivalente."""
    # V2: o período atual também passa pelo resolver (sem período: o mês corrente até hoje, como o
    # anterior); a v1 usava o from/to cru e, sem filtro, comparava o histórico inteiro com o mês anterior.
    inicio, fim, inicio_ant, fim_ant = resolver_periodo_comparativo(from_date, to_date)
    atual = get_mediana_tempo_dias_fase_recursal_LA(controle_processo, inicio, fim)
    anterior = get_mediana_tempo_dias_fase_recursal_LA(controle_processo, inicio_ant, fim_ant)
    return _comparativo_percentual_LA(atual, anterior)


def get_comparativo_mediana_tempo_dias_fase_execucao_LA(
    controle_processo: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """Comparativo (%) da mediana de dias na fase EXECUÇÃO vs período anterior equivalente."""
    # V2: o período atual também passa pelo resolver (sem período: o mês corrente até hoje, como o
    # anterior); a v1 usava o from/to cru e, sem filtro, comparava o histórico inteiro com o mês anterior.
    inicio, fim, inicio_ant, fim_ant = resolver_periodo_comparativo(from_date, to_date)
    atual = get_mediana_tempo_dias_fase_execucao_LA(controle_processo, inicio, fim)
    anterior = get_mediana_tempo_dias_fase_execucao_LA(controle_processo, inicio_ant, fim_ant)
    return _comparativo_percentual_LA(atual, anterior)


def _media_dias_permanencia_setor_por_mes_LA(
    controle_processo: List[Dict[str, Any]],
    col_entrada: str,
    col_saida: str,
) -> List[Dict[str, Any]]:
    """
    Série mensal (todo o histórico) da média de dias (entrada → saída), agrupada pelo
    mês/ano da SAÍDA da fase. Mesma regra de duração de `_media_dias_permanencia_setor_LA`,
    só que quebrada mês a mês em vez de um único agregado — usada para acompanhar a
    tendência do tempo médio ao longo dos meses.
    """
    def mes(p: Dict[str, Any], _saida: Any) -> Any:
        d = _parse_data_controle_LA(_col(p, col_saida))
        return f"{_MONTH_NAMES_LA[d.month - 1]} {d.year}" if d else tempo.FORA

    por_mes = tempo.duracoes_por_grupo(
        _base_controle_processo_LA(controle_processo),
        lambda p: _parse_datetime_controle_LA(_col(p, col_entrada)),
        lambda p: _parse_datetime_controle_LA(_col(p, col_saida)),
        mes,
        unidade="dias_fracao",
        aceita_zero=True,
    )
    result = [{"name": nome, "value": tempo.media(dias)} for nome, dias in por_mes.items()]
    return sorted(result, key=ordem_mes)


def get_media_tempo_dias_fase_inicial_por_mes_LA(
    controle_processo: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Série mensal da média de dias na fase INICIAL (todo o histórico, sem filtro de período)."""
    return _media_dias_permanencia_setor_por_mes_LA(
        controle_processo, _COL_DATA_AJUIZAMENTO, _COL_DT_SAIDA_INICIAL
    )


def get_media_tempo_dias_fase_recursal_por_mes_LA(
    controle_processo: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Série mensal da média de dias na fase RECURSAL (todo o histórico, sem filtro de período)."""
    return _media_dias_permanencia_setor_por_mes_LA(
        controle_processo, _COL_DT_ENTRADA_RECURSAL, _COL_DT_SAIDA_RECURSAL
    )


def get_media_tempo_dias_fase_execucao_por_mes_LA(
    controle_processo: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Série mensal da média de dias na fase EXECUÇÃO (todo o histórico, sem filtro de período)."""
    return _media_dias_permanencia_setor_por_mes_LA(
        controle_processo, _COL_DT_ENTRADA_EXECUCAO, _COL_DT_SAIDA_EXECUCAO
    )


# -----------------------------------------------------------------------------
# 3 - Filtros
# -----------------------------------------------------------------------------
def filter_controle_processo_por_situacao_LA(
    controle_processo: List[Dict[str, Any]],
    situacao: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Filtra por situação do processo (``ID_SITUACAO``, LexFlow ``public.situacao``).

    - ``None`` / ``"ambos"`` (padrão): ATIVO (1) e SUSPENSO/SOBRESTADO (6) — todo o
      escopo já trazido pela query ``controle_processo``.
    - ``"ativo"``: só ATIVO (1).
    - ``"suspenso"`` / ``"sobrestado"`` / ``"suspenso/sobrestado"``: só SUSPENSO/SOBRESTADO (6).

    Aplicar antes (ou depois, é indiferente) do filtro por escritório — são condições
    independentes sobre a mesma lista de processos.
    """
    alvo = (situacao or "ambos").strip().lower()
    if alvo == "ativo":
        ids_permitidos = {_ID_SITUACAO_ATIVO_LA}
    elif alvo in ("suspenso", "sobrestado", "suspenso/sobrestado"):
        ids_permitidos = {_ID_SITUACAO_SUSPENSO_SOBRESTADO_LA}
    else:
        ids_permitidos = {_ID_SITUACAO_ATIVO_LA, _ID_SITUACAO_SUSPENSO_SOBRESTADO_LA}

    return [
        p for p in controle_processo
        if _to_int(_col(p, _COL_ID_SITUACAO)) in ids_permitidos
    ]


def filter_controle_processo_por_fase_LA(
    controle_processo: List[Dict[str, Any]],
    fase: Optional[str],
) -> List[Dict[str, Any]]:
    """
    Filtra a base (ID_ESCRITORIO=21) por fase.

    A comparação usa normalização robusta (acentos/pontuação), então valores como
    ``INICIAL`` batem com variações comuns vindas do banco/UI.

    Para linhas sem fase, use ``fase="SEM FASE"`` (ou equivalente normalizado).
    """
    processos = _base_controle_processo_LA(controle_processo)
    if fase is None or not str(fase).strip():
        return processos

    alvo = _normalizar_chave_fase_LA(fase)
    if not alvo:
        return processos

    filtrados: List[Dict[str, Any]] = []
    for p in processos:
        rotulo = _rotulo_fase_grafico_LA(p)
        if rotulo == _SEM_FASE:
            if alvo == _normalizar_chave_fase_LA(_SEM_FASE):
                filtrados.append(p)
            continue

        chave = _normalizar_chave_fase_LA(rotulo)
        if chave == alvo:
            filtrados.append(p)

    return filtrados


# -----------------------------------------------------------------------------
# 4 - Agrupamentos (derivados da base)
# -----------------------------------------------------------------------------
def group_controle_processo_por_fase_LA(controle_processo: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    processos = _base_controle_processo_LA(controle_processo)

    grouped: Dict[str, int] = defaultdict(int)
    for p in processos:
        grouped[_rotulo_fase_grafico_LA(p)] += 1

    result = [{"name": name, "value": float(value)} for name, value in grouped.items()]
    result = sorted(result, key=lambda x: x["value"], reverse=True)
    # print("[group_controle_processo_por_fase_LA] enviando:", result)
    return result


def group_controle_processo_por_subfase_LA(controle_processo: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    processos = _base_controle_processo_LA(controle_processo)

    grouped: Dict[str, int] = defaultdict(int)
    for p in processos:
        grouped[_rotulo_subfase_grafico_LA(p)] += 1

    result = [{"name": name, "value": float(value)} for name, value in grouped.items()]
    result = sorted(result, key=lambda x: x["value"], reverse=True)
    # print("[group_controle_processo_por_subfase_LA] enviando:", result)
    return result


def group_controle_processo_por_subfase_na_fase_LA(
    controle_processo: List[Dict[str, Any]],
    fase: Optional[str],
) -> List[Dict[str, Any]]:
    """
    Agrupa por SUBFASE apenas dentro da FASE selecionada.

    - Se ``fase`` não for informada, retorna lista vazia (o gráfico depende da seleção).
    - ``percent`` é calculado sobre o total de processos **dentro da fase** (soma 100%).
    """
    if fase is None or not str(fase).strip():
        # print("[group_controle_processo_por_subfase_na_fase_LA] enviando:", {"fase": fase, "result": []})
        return []

    processos = filter_controle_processo_por_fase_LA(controle_processo, fase)
    grouped: Dict[str, Dict[str, float]] = defaultdict(lambda: {"count": 0.0, "valor_causa": 0.0})
    for p in processos:
        key = _rotulo_subfase_grafico_LA(p)
        grouped[key]["count"] += 1.0
        grouped[key]["valor_causa"] += float(_converter_valor_causa(_col(p, _COL_VALOR_CAUSA)))

    total_count = sum(v["count"] for v in grouped.values())
    items = [
        {
            "name": k,
            "value": float(v["count"]),
            "valor_causa": round(float(v["valor_causa"]), 2),
            "percent": None,
        }
        for k, v in grouped.items()
    ]
    if total_count > 0:
        for it in items:
            it["percent"] = round(100.0 * float(it["value"]) / float(total_count), 2)

    result = sorted(items, key=lambda x: x["value"], reverse=True)
    # print("[group_controle_processo_por_subfase_na_fase_LA] enviando:", {"fase": fase, "result": result})
    return result


# -----------------------------------------------------------------------------
# 5 - Tempo médio por subfase (log_fase_processual)
# -----------------------------------------------------------------------------
_COL_LOG_ID_PROCESSO = "ID_PROCESSO"
_COL_LOG_DATA = "DATA"


@memo.por_pedido()
def _base_log_subfase_LA(log_subfase: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Mantém apenas linhas do escritório LA (``ID_ESCRITORIO`` == 21)."""
    return [p for p in log_subfase if _to_int(_col(p, _COL_ID_ESCRITORIO)) == _ID_ESCRITORIO_LA]


def _construir_segmentos_subfase_LA(log_subfase: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Constrói, por processo, segmentos de permanência por subfase a partir do histórico
    cronológico de ``log_fase_processual``.

    Cada troca de valor de subfase fecha o segmento anterior (do instante em que o valor
    passou a vigorar até o instante em que aparece um valor diferente) e abre um novo
    segmento. Só segmentos fechados (com um valor seguinte diferente) entram no cálculo —
    o último segmento em aberto de cada processo (ainda não trocou de subfase) é
    descartado, pois não terminou.

    Limitação: o log só é gravado em transições de FASE; uma troca de subfase que ocorra
    sem sair da fase atual não gera uma linha própria, então o início do novo valor é
    aproximado pelo timestamp do primeiro log em que ele aparece — o que pode
    superestimar a duração do segmento anterior quando a troca real ocorreu antes.
    """
    por_processo: Dict[Any, List[Dict[str, Any]]] = defaultdict(list)
    for row in log_subfase:
        pid = _col(row, _COL_LOG_ID_PROCESSO)
        if pid is None:
            continue
        por_processo[pid].append(row)

    segmentos: List[Dict[str, Any]] = []
    for rows in por_processo.values():
        rows_validas: List[tuple] = []
        for r in rows:
            dt = _parse_datetime_controle_LA(_col(r, _COL_LOG_DATA))
            if dt is not None:
                rows_validas.append((dt, r))
        rows_validas.sort(key=lambda item: item[0])

        atual_subfase: Optional[str] = None
        atual_fase: Optional[str] = None
        atual_id_fase: Optional[int] = None
        atual_inicio = None
        for dt, row in rows_validas:
            subfase = _rotulo_subfase_grafico_LA(row)
            fase_rotulo = _rotulo_fase_grafico_LA(row)
            id_fase_row = _to_int(_col(row, _COL_ID_FASE))
            if atual_subfase is None:
                atual_subfase, atual_fase, atual_id_fase, atual_inicio = subfase, fase_rotulo, id_fase_row, dt
                continue
            if subfase != atual_subfase:
                duracao_dias = (dt - atual_inicio).total_seconds() / 86400.0
                if duracao_dias > 0:
                    segmentos.append(
                        {
                            "subfase": atual_subfase,
                            "fase": atual_fase,
                            "id_fase": atual_id_fase,
                            "duracao_dias": duracao_dias,
                        }
                    )
                atual_subfase, atual_fase, atual_id_fase, atual_inicio = subfase, fase_rotulo, id_fase_row, dt

    return segmentos


def get_tempo_medio_dias_por_subfase_LA(
    log_subfase: List[Dict[str, Any]],
    fase: Optional[str] = None,
    situacao: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Tempo médio (dias) de permanência em cada subfase da fase informada, estimado a
    partir do histórico de ``log_fase_processual`` (ver
    ``_construir_segmentos_subfase_LA`` para a metodologia e suas limitações).

    Sem filtro de período — mesmo escopo "todo o histórico" já usado pelo gráfico de
    subfases (``group_controle_processo_por_subfase_na_fase_LA``).
    """
    if fase is None or not str(fase).strip():
        return []

    base = _base_log_subfase_LA(log_subfase)
    base = filter_controle_processo_por_situacao_LA(base, situacao)
    segmentos = _construir_segmentos_subfase_LA(base)

    alvo_fase = _normalizar_chave_fase_LA(fase)
    agregados: Dict[str, Dict[str, float]] = defaultdict(lambda: {"soma_dias": 0.0, "qtd": 0.0})
    for seg in segmentos:
        if _normalizar_chave_fase_LA(seg["fase"]) != alvo_fase:
            continue
        agregados[seg["subfase"]]["soma_dias"] += seg["duracao_dias"]
        agregados[seg["subfase"]]["qtd"] += 1.0

    return [
        {"name": nome, "value": round(v["soma_dias"] / v["qtd"], 2)}
        for nome, v in agregados.items()
        if v["qtd"] > 0
    ]

