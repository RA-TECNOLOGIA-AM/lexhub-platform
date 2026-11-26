from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Dict, Any, Optional
from collections import defaultdict
import statistics
from decimal import Decimal

from app.analyses.NG.protocolo import _converter_valor_causa
from app.analyses.LA.controle_processo_LA import _construir_segmentos_subfase_LA
# from app.analyses.LA.controle_processo_LA import _base_controle_processo_LA
from app.utils import parse_date_from_db

_MONTH_NAMES = [
    "jan", "fev", "mar", "abr", "mai", "jun",
    "jul", "ago", "set", "out", "nov", "dez"
]
_ID_FASE_INICIAL_LA = 25
_ID_FASE_RECURSAL_LA = 8
_ID_FASE_EXECUCAO_LA = 12

# Função que retorna a quantidade de processos da Fase Inicial e suas Subfases.
_COL_ESCRITORIO = "ESCRITORIO"
_COL_UF = "UF"
_COL_AREA_ATUACAO = "AREA_ATUACAO"
_COL_ID_FASE = "ID_FASE"
_COL_SUBFASE = "SUBFASE"
_COL_COMARCA = "COMARCA"
_COL_VALOR_CAUSA = "VALOR_DE_CAUSA"
_COL_VALOR_CAUSA_SENTENCA = "VALOR_CAUSA_SENTENCA"
_COL_DATA_SENTENCA = "DATA_SENTENCA"
_COL_VALOR_CAUSA_EXECUCAO = "VALOR_CAUSA_EXECUCAO"
_COL_DATA_AJUIZAMENTO = "DATA_AJUIZAMENTO"
_COL_DT_ENTRADA_RECURSAL = "DT_ENTRADA_RECURSAL"
_COL_DT_ENTRADA_EXECUCAO = "DT_ENTRADA_EXECUCAO"
_COL_DATA_EXECUCAO = "DATA_EXECUCAO"
_COL_TEM_ETIQUETA_ACORDO = "TEM_ETIQUETA_ACORDO"
_COL_VALOR_ALCADA_FINAL = "VALOR_ALCADA_FINAL"
_SEM_SUBFASE = "SEM SUBFASE"
_SEM_COMARCA = "Sem comarca"

# Data de entrada na fase, por ``ID_FASE`` — usada para filtrar por período
# quando o dashboard pede "data que o processo entrou naquela fase". Na
# Inicial, a entrada é a data da distribuição do processo — campo
# ``DATA_AJUIZAMENTO`` (fonte: ``p.distribuicao``); não usar o log de fase
# (``DT_ENTRADA_INICIAL``), que é menos confiável.
_COL_DATA_ENTRADA_POR_FASE = {
    _ID_FASE_INICIAL_LA: _COL_DATA_AJUIZAMENTO,
    _ID_FASE_RECURSAL_LA: _COL_DT_ENTRADA_RECURSAL,
    _ID_FASE_EXECUCAO_LA: _COL_DT_ENTRADA_EXECUCAO,
}


def _col(row: Dict[str, Any], name: str) -> Any:
    """Compatibilidade para payloads com chaves em maiúsculo ou minúsculo."""
    if name in row and row[name] is not None:
        return row[name]
    return row.get(name.lower())


def _to_int(value: Any) -> Optional[int]:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    try:
        value_str = str(value).strip()
        if not value_str:
            return None
        return int(float(value_str))
    except (TypeError, ValueError):
        return None


def _to_date_estrategico_geral(value: Any) -> Optional[date]:
    if value is None:
        return None
    parsed = parse_date_from_db(value)
    if isinstance(parsed, datetime):
        return parsed.date()
    if isinstance(parsed, date):
        return parsed
    return None


def _data_no_periodo_estrategico_geral(
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


def _rotulo_subfase(row: Dict[str, Any]) -> str:
    raw = _col(row, _COL_SUBFASE)
    if raw is None or not str(raw).strip():
        return _SEM_SUBFASE
    return str(raw).strip().upper()


@dataclass(frozen=True)
class EstrategicoGeralFiltros:
    """Filtros cumulativos do dashboard estratégico geral (jurídico)."""

    escritorios: frozenset[str] | None = None
    comarcas: frozenset[str] | None = None
    # NGAM/NGPA/NGPB compartilham o mesmo ``id_escritorio_assinante`` (razão
    # social "Nicolas Gomes") — só o campo UF do processo diferencia os três
    # estados. Restringe apenas os processos desse escritório à(s) UF(s)
    # informada(s); processos de outros escritórios (LA) não são afetados
    # (ver ``filter_controle_processo_por_ufs_geral``).
    ufs: frozenset[str] | None = None
    areas_atuacao: frozenset[str] | None = None
    # Só afeta este dashboard (fonte lexflow) — Comercial/Protocolo não têm
    # conceito de "situação" (vêm de ng/laadv) e são tratados como sempre ativos,
    # independente do que for selecionado aqui. Sem valor, usa o escopo padrão
    # histórico (ver ``_SITUACOES_GERAL_PADRAO``).
    situacoes: frozenset[str] | None = None

    def ativo(self) -> bool:
        return (
            bool(self.escritorios)
            or bool(self.comarcas)
            or bool(self.ufs)
            or bool(self.areas_atuacao)
            or bool(self.situacoes)
        )


# ``public.processo`` (lexflow) é multi-tenant — outras queries do mesmo banco
# (ex.: "julgados", "log_subfase_processual") deixam explícito que o recorte
# por escritório é responsabilidade de cada análise. Sem essa whitelist, o
# Jurídico Geral soma processos de escritórios que não pertencem a este
# produto (NG/LA), inflando "Fase Inicial" acima de "Protocolados".
_ESCRITORIOS_GERAL_CONHECIDOS: frozenset[str] = frozenset(
    {
        "Nicolas Gomes",
        "Luis Albert AM",
        "Luis Albert RJ",
    }
)

_NICOLAS_GOMES_ESCRITORIO = "NICOLAS GOMES"


def filter_controle_processo_por_escritorios_geral(
    controle_processo: List[Dict[str, Any]],
    escritorios: frozenset[str] | None = None,
) -> List[Dict[str, Any]]:
    """
    Filtra os processos pelos nomes dos escritórios (coluna ``ESCRITORIO``).

    Se ``escritorios`` não for informado ou estiver vazio, retorna a lista original.
    """
    if not escritorios:
        return list(controle_processo)

    alvos = {str(e).strip().upper() for e in escritorios if str(e).strip()}
    if not alvos:
        return list(controle_processo)

    return [
        processo
        for processo in controle_processo
        if str(_col(processo, _COL_ESCRITORIO) or "").strip().upper() in alvos
    ]


def filter_controle_processo_por_escritorio_geral(
    controle_processo: List[Dict[str, Any]],
    escritorio: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Filtra os processos pelo nome do escritório vindo da coluna ``ESCRITORIO``.

    Se ``escritorio`` não for informado, retorna a lista original.
    """
    if escritorio is None or not str(escritorio).strip():
        return list(controle_processo)

    return filter_controle_processo_por_escritorios_geral(
        controle_processo,
        frozenset({str(escritorio).strip()}),
    )


def filter_controle_processo_por_ufs_geral(
    controle_processo: List[Dict[str, Any]],
    ufs: frozenset[str] | None = None,
) -> List[Dict[str, Any]]:
    """
    Restringe os processos do escritório "Nicolas Gomes" (NG) à(s) UF(s)
    informada(s) — NGAM/NGPA/NGPB compartilham o mesmo ``id_escritorio_assinante``
    (razão social "Nicolas Gomes"), então só o campo ``UF`` do processo
    diferencia os três. Processos de outros escritórios (LA) não são afetados.
    """
    if not ufs:
        return list(controle_processo)

    alvos = {str(u).strip().upper() for u in ufs if str(u).strip()}
    if not alvos:
        return list(controle_processo)

    resultado = []
    for processo in controle_processo:
        escritorio = str(_col(processo, _COL_ESCRITORIO) or "").strip().upper()
        if escritorio != _NICOLAS_GOMES_ESCRITORIO:
            resultado.append(processo)
            continue
        if str(_col(processo, _COL_UF) or "").strip().upper() in alvos:
            resultado.append(processo)

    return resultado


def deduplicar_controle_processo_geral(
    controle_processo: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Remove linhas duplicadas do mesmo processo (mesmo ``ID``).

    A query de ``controle_processo`` faz ``LEFT JOIN`` com ``adverso_processo``/
    ``pessoa`` para trazer a parte adversa — processos com mais de um adverso
    geram uma linha por adverso, inflando as contagens e somas de valor por
    fase/subfase/comarca. Mantém a primeira ocorrência de cada ``ID``; linhas
    sem ``ID`` legível são mantidas (não há chave para deduplicar).
    """
    vistos: set[int] = set()
    resultado: List[Dict[str, Any]] = []
    for processo in controle_processo:
        pid = _to_int(_col(processo, "ID"))
        if pid is None:
            resultado.append(processo)
            continue
        if pid in vistos:
            continue
        vistos.add(pid)
        resultado.append(processo)
    return resultado


def filter_controle_processo_por_comarcas_geral(
    controle_processo: List[Dict[str, Any]],
    comarcas: frozenset[str] | None = None,
) -> List[Dict[str, Any]]:
    """
    Filtra os processos pelos nomes das comarcas (coluna ``COMARCA``).

    Se ``comarcas`` não for informado ou estiver vazio, retorna a lista original.
    """
    if not comarcas:
        return list(controle_processo)

    alvos = {str(c).strip().upper() for c in comarcas if str(c).strip()}
    if not alvos:
        return list(controle_processo)

    return [
        processo
        for processo in controle_processo
        if (str(_col(processo, _COL_COMARCA) or "").strip() or _SEM_COMARCA).upper() in alvos
    ]


def filter_controle_processo_por_areas_atuacao_geral(
    controle_processo: List[Dict[str, Any]],
    areas_atuacao: frozenset[str] | None = None,
) -> List[Dict[str, Any]]:
    """
    Filtra os processos pelos nomes das áreas de atuação (coluna ``AREA_ATUACAO``,
    resolvida via JOIN com ``public.area_atuacao`` no LexFlow).

    Se ``areas_atuacao`` não for informado ou estiver vazio, retorna a lista original.
    """
    if not areas_atuacao:
        return list(controle_processo)

    alvos = {str(a).strip().upper() for a in areas_atuacao if str(a).strip()}
    if not alvos:
        return list(controle_processo)

    return [
        processo
        for processo in controle_processo
        if str(_col(processo, _COL_AREA_ATUACAO) or "").strip().upper() in alvos
    ]


_COL_ID_SITUACAO = "ID_SITUACAO"

# ``public.situacao`` (lexflow) — só 3 valores cadastrados hoje.
_SITUACAO_ATIVO_ID = 1
_SITUACAO_ARQUIVADO_ID = 2
_SITUACAO_SUSPENSO_ID = 6

_SITUACAO_LABEL_POR_ID: dict[int, str] = {
    _SITUACAO_ATIVO_ID: "ATIVO",
    _SITUACAO_ARQUIVADO_ID: "ARQUIVADO",
    _SITUACAO_SUSPENSO_ID: "SUSPENSO/SOBRESTADO",
}
_SITUACAO_ID_POR_LABEL: dict[str, int] = {v: k for k, v in _SITUACAO_LABEL_POR_ID.items()}

# Escopo padrão quando o usuário não escolhe uma situação explicitamente —
# todas as situações cadastradas (ATIVO + ARQUIVADO + SUSPENSO/SOBRESTADO).
_SITUACOES_GERAL_PADRAO: frozenset[int] = frozenset(_SITUACAO_LABEL_POR_ID.keys())


def filter_controle_processo_por_situacoes_geral(
    controle_processo: List[Dict[str, Any]],
    situacoes: frozenset[str] | None = None,
) -> List[Dict[str, Any]]:
    """
    Filtra os processos pela situação (coluna ``ID_SITUACAO``: ATIVO, ARQUIVADO,
    SUSPENSO/SOBRESTADO).

    Sem filtro explícito (ou só com rótulos desconhecidos), conta todas as
    situações — inclusive arquivados — já que o dataset de origem
    (``controle_processo_todas_situacoes``) só traz essas 3.
    """
    alvos_id: frozenset[int] = _SITUACOES_GERAL_PADRAO
    if situacoes:
        resolvidos = {
            _SITUACAO_ID_POR_LABEL[str(s).strip().upper()]
            for s in situacoes
            if str(s).strip().upper() in _SITUACAO_ID_POR_LABEL
        }
        if resolvidos:
            alvos_id = frozenset(resolvidos)

    return [
        processo
        for processo in controle_processo
        if _to_int(_col(processo, _COL_ID_SITUACAO)) in alvos_id
    ]


def get_opcoes_filtros_estrategico_geral(
    controle_processo: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Opções de escritório/comarca para o painel de filtros."""
    escritorios: set[str] = set()
    comarcas: set[str] = set()
    for processo in controle_processo:
        raw = _col(processo, _COL_ESCRITORIO)
        if raw and str(raw).strip():
            escritorios.add(str(raw).strip())
        raw_comarca = _col(processo, _COL_COMARCA)
        if raw_comarca and str(raw_comarca).strip():
            comarcas.add(str(raw_comarca).strip())
    return {
        "escritorios": sorted(escritorios, key=lambda x: x.casefold()),
        "comarcas": sorted(comarcas, key=lambda x: x.casefold()),
    }

# -----------------------------------------------------------------------------
# 1 - Agrupamento de dados do juridico geral
# -----------------------------------------------------------------------------
_COL_LOG_ID_PROCESSO = "ID_PROCESSO"


def _tempo_medio_dias_por_subfase_geral(
    log_subfase: List[Dict[str, Any]],
    id_fase: int,
    processo_ids: Optional[frozenset] = None,
) -> Dict[str, float]:
    """
    Tempo médio (dias) de permanência em cada subfase da fase informada
    (``id_fase``), estimado a partir do histórico de ``log_fase_processual``
    (ver ``_construir_segmentos_subfase_LA`` para a metodologia e limitações).

    Restrito aos processos que sobraram após o filtro de escritório
    (``processo_ids``), quando informado — garante que o tempo médio respeite
    o mesmo filtro de escritório já aplicado ao gráfico de quantidade/valor.
    """
    base = log_subfase
    if processo_ids is not None:
        base = [
            row
            for row in base
            if _to_int(_col(row, _COL_LOG_ID_PROCESSO)) in processo_ids
        ]

    segmentos = _construir_segmentos_subfase_LA(base)

    agregados: Dict[str, Dict[str, float]] = defaultdict(
        lambda: {"soma_dias": 0.0, "qtd": 0.0}
    )
    for seg in segmentos:
        if seg.get("id_fase") != id_fase:
            continue
        agregados[seg["subfase"]]["soma_dias"] += seg["duracao_dias"]
        agregados[seg["subfase"]]["qtd"] += 1.0

    return {
        nome: round(v["soma_dias"] / v["qtd"], 2)
        for nome, v in agregados.items()
        if v["qtd"] > 0
    }


def _group_processos_por_subfase_na_fase_geral(
    controle_processo: List[Dict[str, Any]],
    id_fase: int,
    valor_causa_col: str,
    tempo_medio_por_subfase: Optional[Dict[str, float]] = None,
    data_entrada_col: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    valor_sentenca_col: Optional[str] = None,
    data_sentenca_col: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    ``valor_sentenca_col``/``data_sentenca_col``: o valor da sentença tem seu
    PRÓPRIO recorte de data (``data_sentenca_col``, ex.: ``DATA_SENTENCA``) —
    independente do ``data_entrada_col`` usado pra quantidade/valor de causa
    (ex.: ``DT_ENTRADA_RECURSAL``). Um processo pode ter entrado no Recursal
    fora do período mas recebido a sentença dentro dele (ou vice-versa), então
    as duas contagens não têm por que coincidir. Sem ``data_sentenca_col``,
    cai no comportamento antigo (mesmo gate de ``data_entrada_col``).
    """
    grouped: Dict[str, Dict[str, float]] = defaultdict(
        lambda: {"quantidade": 0.0, "valor_causa": 0.0, "valor_sentenca": 0.0}
    )

    filtrar_por_data = data_entrada_col is not None and (from_date is not None or to_date is not None)
    filtrar_sentenca_por_data = data_sentenca_col is not None and (from_date is not None or to_date is not None)

    for processo in controle_processo:
        if _to_int(_col(processo, _COL_ID_FASE)) != id_fase:
            continue

        entra_no_periodo = True
        if filtrar_por_data:
            data_entrada = _to_date_estrategico_geral(_col(processo, data_entrada_col))
            entra_no_periodo = _data_no_periodo_estrategico_geral(data_entrada, from_date, to_date)

        subfase = _rotulo_subfase(processo)

        if entra_no_periodo:
            grouped[subfase]["quantidade"] += 1.0
            grouped[subfase]["valor_causa"] += _converter_valor_causa(
                _col(processo, valor_causa_col)
            )

        if valor_sentenca_col:
            if data_sentenca_col:
                sentenca_no_periodo = True
                if filtrar_sentenca_por_data:
                    data_sentenca = _to_date_estrategico_geral(_col(processo, data_sentenca_col))
                    sentenca_no_periodo = _data_no_periodo_estrategico_geral(
                        data_sentenca, from_date, to_date
                    )
            else:
                sentenca_no_periodo = entra_no_periodo
            if sentenca_no_periodo:
                grouped[subfase]["valor_sentenca"] += _converter_valor_causa(
                    _col(processo, valor_sentenca_col)
                )

    total_processos = int(sum(item["quantidade"] for item in grouped.values()))

    subfases = []
    for subfase, item in grouped.items():
        quantidade = int(item["quantidade"])
        percent = (
            round((quantidade / total_processos) * 100, 2)
            if total_processos
            else 0.0
        )
        subfases.append(
            {
                "name": subfase,
                "value": quantidade,
                "valor_causa": round(item["valor_causa"], 2),
                "percent": percent,
                "tempo_medio_dias": (
                    tempo_medio_por_subfase.get(subfase)
                    if tempo_medio_por_subfase
                    else None
                ),
                **(
                    {"valor_sentenca": round(item["valor_sentenca"], 2)}
                    if valor_sentenca_col
                    else {}
                ),
            }
        )

    return sorted(subfases, key=lambda item: item["value"], reverse=True)


def get_processos_fase_inicial_por_subfase_geral(
    controle_processo: List[Dict[str, Any]],
    log_subfase: Optional[List[Dict[str, Any]]] = None,
    processo_ids: Optional[frozenset] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """
    Retorna a quantidade e o valor da causa dos processos na fase INICIAL,
    agrupados por subfase no formato de chart.

    ``name`` = rótulo, ``value`` = quantidade, ``valor_causa`` = soma do valor
    da causa da subfase, ``percent`` = participação dentro da fase inicial e
    ``tempo_medio_dias`` = tempo médio de permanência na subfase (quando
    ``log_subfase`` for informado).

    Quando ``from_date``/``to_date`` são informados, restringe aos processos
    cuja ``DATA_AJUIZAMENTO`` (data da distribuição do processo, entrada na
    fase Inicial) está no período.
    """
    tempo_medio = (
        _tempo_medio_dias_por_subfase_geral(log_subfase, _ID_FASE_INICIAL_LA, processo_ids)
        if log_subfase
        else None
    )
    return _group_processos_por_subfase_na_fase_geral(
        controle_processo,
        _ID_FASE_INICIAL_LA,
        _COL_VALOR_CAUSA,
        tempo_medio_por_subfase=tempo_medio,
        data_entrada_col=_COL_DATA_AJUIZAMENTO,
        from_date=from_date,
        to_date=to_date,
    )


def get_processos_fase_recursal_por_subfase_geral(
    controle_processo: List[Dict[str, Any]],
    log_subfase: Optional[List[Dict[str, Any]]] = None,
    processo_ids: Optional[frozenset] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """
    Retorna a quantidade, o valor da causa (``VALOR_DE_CAUSA``) e o valor da
    sentença (``VALOR_CAUSA_SENTENCA``) dos processos na fase RECURSAL,
    agrupados por subfase no formato de chart.

    Quando ``from_date``/``to_date`` são informados, restringe a
    quantidade/valor de causa aos processos cuja ``DT_ENTRADA_RECURSAL``
    (data em que o processo entrou na fase Recursal) está no período. O valor
    da sentença usa seu PRÓPRIO recorte — ``DATA_SENTENCA`` no período — já
    que a sentença pode sair num momento diferente da entrada no Recursal.
    """
    tempo_medio = (
        _tempo_medio_dias_por_subfase_geral(log_subfase, _ID_FASE_RECURSAL_LA, processo_ids)
        if log_subfase
        else None
    )
    return _group_processos_por_subfase_na_fase_geral(
        controle_processo,
        _ID_FASE_RECURSAL_LA,
        _COL_VALOR_CAUSA,
        tempo_medio_por_subfase=tempo_medio,
        data_entrada_col=_COL_DT_ENTRADA_RECURSAL,
        from_date=from_date,
        to_date=to_date,
        valor_sentenca_col=_COL_VALOR_CAUSA_SENTENCA,
        data_sentenca_col=_COL_DATA_SENTENCA,
    )


def get_valor_sentenca_total_periodo_geral(
    controle_processo: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """
    Soma do valor da sentença (``VALOR_CAUSA_SENTENCA``) de QUALQUER processo
    cuja ``DATA_SENTENCA`` caia no período — independente da fase ATUAL do
    processo (Inicial, Recursal, Execução, etc.).

    Usado pelo total do card "Recursal — Valor Causa" (secundário "Valor
    sentença") do Estratégico Geral, pra bater com o dashboard "Julgados
    Sentenças" — que também não restringe por fase atual, só pela data da
    sentença. Bem diferente da tabela "Recursal por subfase"
    (``get_processos_fase_recursal_por_subfase_geral``), que soma só
    sentenças de processos ATUALMENTE na fase Recursal: muita sentença sai
    com o processo ainda na Inicial (sem recurso apresentado ainda), então os
    dois números divergem por desenho — não é inconsistência.
    """
    total = 0.0
    for processo in controle_processo:
        data_sentenca = _to_date_estrategico_geral(_col(processo, _COL_DATA_SENTENCA))
        if not _data_no_periodo_estrategico_geral(data_sentenca, from_date, to_date):
            continue
        total += _converter_valor_causa(_col(processo, _COL_VALOR_CAUSA_SENTENCA))
    return round(total, 2)


def _vias_execucao_no_periodo_geral(
    processo: Dict[str, Any],
    from_date: Optional[date],
    to_date: Optional[date],
) -> tuple[bool, bool]:
    """
    Um processo "entra em execução" por uma de duas vias — retorna
    ``(via_fase, via_acordo)``, cada uma já resolvida contra o período:

    (a) via judicial formal — ``ID_FASE`` = 12, pela ``DT_ENTRADA_EXECUCAO`` do log; ou
    (b) via Acordo — processo com a etiqueta ``ACORDO`` (``TEM_ETIQUETA_ACORDO``),
        pela ``DATA_EXECUCAO`` do processo (a fase judicial pode migrar depois,
        inclusive para uma fase própria de Acordo fora de 12; a etiqueta é o
        marcador estável, não o ``ID_FASE``).

    As duas vias não são mutuamente exclusivas na base (um processo pode ter
    ``ID_FASE`` = 12 e a etiqueta Acordo ao mesmo tempo) — por isso o chamador
    deve tratar a inclusão do processo como ``via_fase or via_acordo`` (não uma
    soma), evitando contar o mesmo processo duas vezes na quantidade.
    """
    tem_fase = _to_int(_col(processo, _COL_ID_FASE)) == _ID_FASE_EXECUCAO_LA
    tem_etiqueta_acordo = bool(_col(processo, _COL_TEM_ETIQUETA_ACORDO))

    if not tem_fase and not tem_etiqueta_acordo:
        return False, False

    if from_date is None and to_date is None:
        return tem_fase, tem_etiqueta_acordo

    via_fase = tem_fase and _data_no_periodo_estrategico_geral(
        _to_date_estrategico_geral(_col(processo, _COL_DT_ENTRADA_EXECUCAO)),
        from_date,
        to_date,
    )
    via_acordo = tem_etiqueta_acordo and _data_no_periodo_estrategico_geral(
        _to_date_estrategico_geral(_col(processo, _COL_DATA_EXECUCAO)),
        from_date,
        to_date,
    )
    return via_fase, via_acordo


def get_processos_fase_execucao_por_subfase_geral(
    controle_processo: List[Dict[str, Any]],
    log_subfase: Optional[List[Dict[str, Any]]] = None,
    processo_ids: Optional[frozenset] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """
    Retorna a quantidade, o valor da causa (``VALOR_DE_CAUSA``) e o valor de
    execução dos processos que entraram em EXECUÇÃO, agrupados por subfase no
    formato de chart.

    "Entrar em execução" cobre as duas vias possíveis — ver
    ``_vias_execucao_no_periodo_geral``. O valor de execução usa a coluna
    própria de cada via: ``VALOR_CAUSA_EXECUCAO`` na via judicial (``ID_FASE``
    = 12) e ``VALOR_ALCADA_FINAL`` na via Acordo (esse é o valor que de fato
    "entra" na fase de execução para os processos de Acordo — já usado com
    esse papel na Fase de Acordos). Quando ``from_date``/``to_date`` são
    informados, cada via usa sua própria data de entrada (``DT_ENTRADA_EXECUCAO``
    ou ``DATA_EXECUCAO``).
    """
    tempo_medio = (
        _tempo_medio_dias_por_subfase_geral(log_subfase, _ID_FASE_EXECUCAO_LA, processo_ids)
        if log_subfase
        else None
    )

    grouped: Dict[str, Dict[str, float]] = defaultdict(
        lambda: {"quantidade": 0.0, "valor_causa": 0.0, "valor_execucao": 0.0}
    )
    for processo in controle_processo:
        via_fase, via_acordo = _vias_execucao_no_periodo_geral(processo, from_date, to_date)
        if not via_fase and not via_acordo:
            continue

        subfase = _rotulo_subfase(processo)
        grouped[subfase]["quantidade"] += 1.0
        grouped[subfase]["valor_causa"] += _converter_valor_causa(
            _col(processo, _COL_VALOR_CAUSA)
        )
        if via_fase:
            grouped[subfase]["valor_execucao"] += _converter_valor_causa(
                _col(processo, _COL_VALOR_CAUSA_EXECUCAO)
            )
        if via_acordo:
            grouped[subfase]["valor_execucao"] += _converter_valor_causa(
                _col(processo, _COL_VALOR_ALCADA_FINAL)
            )

    total_processos = int(sum(item["quantidade"] for item in grouped.values()))

    subfases = []
    for subfase, item in grouped.items():
        quantidade = int(item["quantidade"])
        percent = (
            round((quantidade / total_processos) * 100, 2)
            if total_processos
            else 0.0
        )
        subfases.append(
            {
                "name": subfase,
                "value": quantidade,
                "valor_causa": round(item["valor_causa"], 2),
                "valor_execucao": round(item["valor_execucao"], 2),
                "percent": percent,
                "tempo_medio_dias": (
                    tempo_medio.get(subfase) if tempo_medio else None
                ),
            }
        )

    return sorted(subfases, key=lambda item: item["value"], reverse=True)


_ID_FASE_EXECUCAO_ACORDO_GERAL = 30
_COL_NUMERO_PROCESSO = "NUMERO_PROCESSO"
_COL_VALOR_EXECUCAO_RAW = "VALOR_EXECUCAO"
_COL_VALOR_REMANESCENTE = "VALOR_REMANESCENTE"
_COL_DATA_COMPENSACAO_ALVARA_INCONTROVERSO = "DATA_COMPENSACAO_ALVARA_INCONTROVERSO"
_COL_DATA_ACORDO_FECHADO = "DATA_ACORDO_FECHADO"
# Valor de causa nas queries `execucao_LA`/`execucao_acordos_NG` — coluna
# "VALOR_CAUSA" (sem "DE"), diferente de `_COL_VALOR_CAUSA` ("VALOR_DE_CAUSA",
# usada por `controle_processo`). Só existe no dataset de condenação — o de
# acordos não tem essa coluna.
_COL_VALOR_CAUSA_EXECUCAO_ORIGEM = "VALOR_CAUSA"


def _dedupe_por_numero_processo_geral(
    rows: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Unicidade por ``NUMERO_PROCESSO`` — mesmo critério usado pelos dashboards
    dedicados de Execução (``_base_execucao``/``_base_execucao_acordos``),
    evitando contar a mesma linha mais de uma vez.
    """
    vistos: set[Any] = set()
    resultado: List[Dict[str, Any]] = []
    for row in rows:
        chave = _col(row, _COL_NUMERO_PROCESSO) or _col(row, "ID") or _col(row, "id")
        if chave is not None:
            if chave in vistos:
                continue
            vistos.add(chave)
        resultado.append(row)
    return resultado


def _valor_execucao_em_aberto_geral(processo: Dict[str, Any]) -> float:
    """
    Valor ainda em aberto na Execução: ``VALOR_REMANESCENTE`` quando o alvará
    do incontroverso já foi compensado (``DATA_COMPENSACAO_ALVARA_INCONTROVERSO``
    preenchida), ou ``VALOR_EXECUCAO`` cheio caso contrário — mesmo critério do
    dashboard dedicado de Execução Condenação.
    """
    data_compensacao = _col(processo, _COL_DATA_COMPENSACAO_ALVARA_INCONTROVERSO)
    if data_compensacao is not None and str(data_compensacao).strip():
        valor = _col(processo, _COL_VALOR_REMANESCENTE)
    else:
        valor = _col(processo, _COL_VALOR_EXECUCAO_RAW)
    return _converter_valor_causa(valor)


def _execucao_condenacao_acordos_populacoes_geral(
    execucao_condenacao: List[Dict[str, Any]],
    execucao_acordos: List[Dict[str, Any]],
    escritorios: Optional[frozenset] = None,
    ufs: Optional[frozenset] = None,
    areas_atuacao: Optional[frozenset] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    População compartilhada entre ``get_execucao_condenacao_acordos_combinado_geral``
    (total dos cards) e ``get_execucao_condenacao_acordos_por_subfase_geral``
    (quebra por subfase) — mesma definição usada pelos dashboards dedicados de
    Execução (Condenação NG/LA + Acordos NG), com a MESMA troca de modo que
    esses dashboards fazem conforme período informado ou não:

    - Condenação (``ID_FASE`` = 12), excluindo processos com etiqueta Acordo —
      as duas vias são mutuamente exclusivas aqui (diferente de
      ``_vias_execucao_no_periodo_geral``, usada pela tabela antiga).
    - Acordos: etiqueta Acordo OU ``DATA_ACORDO_FECHADO`` preenchida (base).

    Sem período (``Jurídico Fixo``): estoque atual pras duas vias —
    Condenação ``ID_FASE`` = 12 e ``ID_SITUACAO`` = ATIVO; Acordos
    ``ID_FASE`` = 30. Mesmo critério de ``_filtrar_em_execucao``/
    ``_filtrar_em_execucao_acordos`` nos dashboards dedicados.

    Com período (``Jurídico Avanço nas Fases``): ENTRADA no período pras duas
    vias, sem exigir fase atual — Condenação por ``DATA_EXECUCAO`` (mesmo
    critério de ``_filtrar_entrada_execucao_no_periodo``); Acordos por
    etiqueta Acordo (obrigatória, não basta ``DATA_ACORDO_FECHADO``) +
    ``DATA_EXECUCAO`` no intervalo (mesmo critério de
    ``_filtrar_entrada_execucao_acordos_no_periodo``) — bate com o card
    "Valor em Execução"/"Total em Execução" (modo Entrada) do dashboard
    dedicado, não com "Valor/Total EM Execução" (estoque, sem período).

    Retorna ``(condenacao_estoque, condenacao_processos, acordos_processos)``:
    ``condenacao_estoque`` é sempre o estoque atual da condenação (usado só
    pro valor "estoque", quando não há período); ``condenacao_processos``/
    ``acordos_processos`` já refletem o modo (estoque ou entrada) certo pra
    quantidade E valor desse período.
    """
    escritorios_alvo = escritorios or _ESCRITORIOS_GERAL_CONHECIDOS
    sem_periodo = from_date is None or to_date is None

    condenacao = filter_controle_processo_por_escritorios_geral(execucao_condenacao, escritorios_alvo)
    condenacao = filter_controle_processo_por_ufs_geral(condenacao, ufs)
    condenacao = filter_controle_processo_por_areas_atuacao_geral(condenacao, areas_atuacao)
    condenacao = [p for p in condenacao if not _col(p, _COL_TEM_ETIQUETA_ACORDO)]
    condenacao = _dedupe_por_numero_processo_geral(condenacao)

    acordos = filter_controle_processo_por_escritorios_geral(execucao_acordos, escritorios_alvo)
    acordos = filter_controle_processo_por_ufs_geral(acordos, ufs)
    acordos = filter_controle_processo_por_areas_atuacao_geral(acordos, areas_atuacao)
    acordos = [
        p for p in acordos
        if bool(_col(p, _COL_TEM_ETIQUETA_ACORDO)) or _col(p, _COL_DATA_ACORDO_FECHADO) is not None
    ]
    acordos = _dedupe_por_numero_processo_geral(acordos)

    condenacao_estoque = [
        p for p in condenacao
        if _to_int(_col(p, _COL_ID_FASE)) == _ID_FASE_EXECUCAO_LA
        and _to_int(_col(p, _COL_ID_SITUACAO)) == _SITUACAO_ATIVO_ID
    ]

    if sem_periodo:
        condenacao_processos = condenacao_estoque
        acordos_processos = [
            p for p in acordos
            if _to_int(_col(p, _COL_ID_FASE)) == _ID_FASE_EXECUCAO_ACORDO_GERAL
        ]
    else:
        condenacao_processos = [
            p for p in condenacao
            if _data_no_periodo_estrategico_geral(
                _to_date_estrategico_geral(_col(p, _COL_DATA_EXECUCAO)),
                from_date,
                to_date,
            )
        ]
        acordos_processos = [
            p for p in acordos
            if bool(_col(p, _COL_TEM_ETIQUETA_ACORDO))
            and _data_no_periodo_estrategico_geral(
                _to_date_estrategico_geral(_col(p, _COL_DATA_EXECUCAO)),
                from_date,
                to_date,
            )
        ]

    return condenacao_estoque, condenacao_processos, acordos_processos


def get_execucao_condenacao_acordos_combinado_geral(
    execucao_condenacao: List[Dict[str, Any]],
    execucao_acordos: List[Dict[str, Any]],
    escritorios: Optional[frozenset] = None,
    ufs: Optional[frozenset] = None,
    areas_atuacao: Optional[frozenset] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> Dict[str, float]:
    """
    Quantidade e valor "em execução" com a MESMA definição usada pelos
    dashboards dedicados de Execução (Condenação NG/LA + Acordos NG), para os
    cards "Execução — Processos"/"Valor execução" do Estratégico Geral baterem
    com os de lá — inclusive trocando de card conforme o período:

    - Sem período (``Jurídico Fixo``): valor = estoque atual das duas vias —
      Condenação via ``_valor_execucao_em_aberto_geral`` (desconta o
      incontroverso já compensado), Acordos via ``VALOR_ALCADA_FINAL`` — bate
      com "Valor/Total EM Execução" do dashboard dedicado.
    - Com período (``Jurídico Avanço nas Fases``): valor = entrada no período,
      valor CHEIO (sem desconto) das duas vias — bate com "Valor em
      Execução"/"Total em Execução" (modo Entrada) do dashboard dedicado.

    ``valor_causa`` soma ``VALOR_CAUSA`` (a própria coluna de valor de causa
    da query de Execução, presente só do lado Condenação — Acordos não tem
    essa coluna) da MESMA população usada pra quantidade/valor acima.

    Ver ``_execucao_condenacao_acordos_populacoes_geral`` para a definição de
    população completa (e a troca de modo estoque/entrada).
    """
    condenacao_estoque, condenacao_processos, acordos_processos = _execucao_condenacao_acordos_populacoes_geral(
        execucao_condenacao, execucao_acordos, escritorios, ufs, areas_atuacao, from_date, to_date
    )
    sem_periodo = from_date is None or to_date is None

    if sem_periodo:
        valor_condenacao = sum(_valor_execucao_em_aberto_geral(p) for p in condenacao_estoque)
    else:
        valor_condenacao = sum(
            _converter_valor_causa(_col(p, _COL_VALOR_EXECUCAO_RAW)) for p in condenacao_processos
        )
    valor_acordos = sum(
        _converter_valor_causa(_col(p, _COL_VALOR_ALCADA_FINAL)) for p in acordos_processos
    )

    valor_causa = sum(
        _converter_valor_causa(_col(p, _COL_VALOR_CAUSA_EXECUCAO_ORIGEM)) for p in condenacao_processos
    ) + sum(
        _converter_valor_causa(_col(p, _COL_VALOR_CAUSA_EXECUCAO_ORIGEM)) for p in acordos_processos
    )

    return {
        "processos": len(condenacao_processos) + len(acordos_processos),
        "valor_execucao": round(valor_condenacao + valor_acordos, 2),
        "valor_causa": round(valor_causa, 2),
    }


def get_execucao_condenacao_acordos_por_subfase_geral(
    execucao_condenacao: List[Dict[str, Any]],
    execucao_acordos: List[Dict[str, Any]],
    escritorios: Optional[frozenset] = None,
    ufs: Optional[frozenset] = None,
    areas_atuacao: Optional[frozenset] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """
    Quebra por subfase da MESMA população combinada de
    ``get_execucao_condenacao_acordos_combinado_geral`` — pra alimentar o
    gráfico "Execução por subfases" batendo com o total do card (antes, essa
    tabela vinha de ``get_processos_fase_execucao_por_subfase_geral``, com
    uma definição mais ampla que não batia com o card).

    Quantidade e valor por subfase usam a MESMA população/modo do total —
    estoque atual sem período, entrada no período com período (ver
    ``_execucao_condenacao_acordos_populacoes_geral``/
    ``get_execucao_condenacao_acordos_combinado_geral``).
    """
    condenacao_estoque, condenacao_processos, acordos_processos = _execucao_condenacao_acordos_populacoes_geral(
        execucao_condenacao, execucao_acordos, escritorios, ufs, areas_atuacao, from_date, to_date
    )
    sem_periodo = from_date is None or to_date is None

    grouped: Dict[str, Dict[str, float]] = defaultdict(
        lambda: {"quantidade": 0.0, "valor_execucao": 0.0}
    )

    for processo in condenacao_processos:
        grouped[_rotulo_subfase(processo)]["quantidade"] += 1.0
    if sem_periodo:
        for processo in condenacao_estoque:
            grouped[_rotulo_subfase(processo)]["valor_execucao"] += _valor_execucao_em_aberto_geral(processo)
    else:
        for processo in condenacao_processos:
            grouped[_rotulo_subfase(processo)]["valor_execucao"] += _converter_valor_causa(
                _col(processo, _COL_VALOR_EXECUCAO_RAW)
            )
    for processo in acordos_processos:
        subfase = _rotulo_subfase(processo)
        grouped[subfase]["quantidade"] += 1.0
        grouped[subfase]["valor_execucao"] += _converter_valor_causa(
            _col(processo, _COL_VALOR_ALCADA_FINAL)
        )

    total_processos = int(sum(item["quantidade"] for item in grouped.values()))
    subfases = []
    for subfase, item in grouped.items():
        quantidade = int(item["quantidade"])
        percent = (
            round((quantidade / total_processos) * 100, 2)
            if total_processos
            else 0.0
        )
        subfases.append(
            {
                "name": subfase,
                "value": quantidade,
                "valor_execucao": round(item["valor_execucao"], 2),
                "percent": percent,
            }
        )
    return sorted(subfases, key=lambda item: item["value"], reverse=True)


# -----------------------------------------------------------------------------
# 2 - Processos do Jurídico (Inicial + Recursal + Execução) por comarca
# -----------------------------------------------------------------------------

_IDS_FASE_JURIDICO_GERAL = frozenset({_ID_FASE_INICIAL_LA, _ID_FASE_RECURSAL_LA, _ID_FASE_EXECUCAO_LA})


def get_processos_juridico_por_comarca_geral(
    controle_processo: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """
    Distribuição por comarca de todos os processos do Jurídico (fases Inicial,
    Recursal e Execução). Sem ``from_date``/``to_date``, independente de data
    (``percent`` soma 100%).

    Quando o período é informado, cada processo é filtrado pela data em que
    entrou na sua própria fase (``DATA_AJUIZAMENTO``/``DT_ENTRADA_RECURSAL``/
    ``DT_ENTRADA_EXECUCAO``, conforme o ``ID_FASE`` da linha).
    """
    filtrar_por_data = from_date is not None or to_date is not None
    grouped: Dict[str, int] = defaultdict(int)
    # V2: valor de causa e UF de cada comarca, para o mapa de comarcas do Estratégico (a v1 só contava).
    valor_por_comarca: Dict[str, float] = defaultdict(float)
    ufs_por_comarca: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in controle_processo:
        id_fase = _to_int(_col(row, _COL_ID_FASE))
        if id_fase not in _IDS_FASE_JURIDICO_GERAL:
            continue
        if filtrar_por_data:
            data_entrada_col = _COL_DATA_ENTRADA_POR_FASE.get(id_fase)
            data_entrada = (
                _to_date_estrategico_geral(_col(row, data_entrada_col))
                if data_entrada_col
                else None
            )
            if not _data_no_periodo_estrategico_geral(data_entrada, from_date, to_date):
                continue
        comarca = str(_col(row, _COL_COMARCA) or "").strip() or _SEM_COMARCA
        grouped[comarca] += 1
        # V2: (ver acima) soma o valor de causa e conta a UF do processo na comarca.
        valor_por_comarca[comarca] += _converter_valor_causa(_col(row, _COL_VALOR_CAUSA))
        uf = str(_col(row, _COL_UF) or "").strip().upper()
        if uf:
            ufs_por_comarca[comarca][uf] += 1

    total = float(sum(grouped.values()))
    itens = [
        {
            "name": nome,
            "value": float(qtd),
            "percent": round(100.0 * float(qtd) / total, 1) if total > 0 else 0.0,
            # V2: (ver acima) a UF mais comum dos processos da comarca e o valor de causa somado.
            "uf": max(ufs_por_comarca[nome].items(), key=lambda kv: (kv[1], kv[0]))[0]
            if ufs_por_comarca.get(nome)
            else None,
            "valor_causa": round(valor_por_comarca[nome], 2),
        }
        for nome, qtd in grouped.items()
    ]
    return sorted(itens, key=lambda x: float(x["value"]), reverse=True)