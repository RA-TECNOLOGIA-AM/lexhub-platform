# Análises do dashboard de publicações (LexFlow) — LAADV

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from statistics import mean
from typing import Any, Callable, Dict, List, Literal, Optional, Union

from app.analyses.common import conversao  # V2: conversões dos valores do banco num módulo só
from app.analyses.common import tempo  # V2: média/mediana de tempo num módulo só
from app.utils import parse_date_from_db


# -----------------------------------------------------------------------------
# Constantes — nomes de colunas do banco
# -----------------------------------------------------------------------------

_COL_DISPONIBILIZACAO = "DATA_DISPONIBILIZACAO"
_COL_CONCLUSAO        = "DATA_CONCLUSAO"
_COL_STATUS           = "STATUS"
_COL_LEITOR           = "LEITOR"
_COL_RESPONSAVEL      = "RESPONSAVEL"
_COL_MATERIA          = "MATERIA"
_COL_DOCUMENTO        = "DOCUMENTO"
_COL_TRIBUNAL         = "TRIBUNAL"
_COL_ORGAO            = "ORGAO"
_COL_COMARCA          = "COMARCA"
_COL_ID_PROCESSO      = "ID_PROCESSO"

# Colunas dos agendamentos (query agendamentos_todos_setores_LA).
_COL_AG_PROCESSO_ID   = "processo_id"
_COL_AG_DATA_CRIACAO  = "DATA_HORA_CRIACAO"
_COL_AG_ATIVIDADE     = "ATIVIDADE"
_COL_AG_SETOR         = "SETOR"

# Status elegíveis para a métrica de publicações pendentes no dashboard LA.
_STATUS_PENDENTE_METRICA_LA = frozenset({"visualizado", "não visualizado"})


# -----------------------------------------------------------------------------
# Helpers internos
# -----------------------------------------------------------------------------

def _col(row: Dict[str, Any], name: str) -> Any:
    return row.get(name) or row.get(name.lower())


_to_date = conversao.para_data  # V2: era uma cópia local (app/analyses/common/conversao.py)


def _get_date(row: Dict[str, Any], col_name: str) -> Optional[date]:
    """Atalho para _to_date(_col(row, col_name)) — usado em toda leitura de data."""
    return _to_date(_col(row, col_name))


def _status_normalizado(row: Dict[str, Any]) -> str:
    s = _col(row, _COL_STATUS)
    if s is None:
        return ""
    return str(s).strip().lower()


def _is_cumprido(row: Dict[str, Any]) -> bool:
    return _status_normalizado(row) == "cumprido"


def _conta_como_pendente_publicacao_LA(row: Dict[str, Any]) -> bool:
    """Só entra na métrica de pendentes com status Visualizado ou Não visualizado."""
    return _status_normalizado(row) in _STATUS_PENDENTE_METRICA_LA


def _in_interval(
    d: date,
    from_date: Optional[date],
    to_date: Optional[date],
) -> bool:
    if from_date and to_date:
        return from_date <= d <= to_date
    if from_date:
        return d >= from_date
    if to_date:
        return d <= to_date
    return True


def _formatar_nome(nome_completo: str) -> str:
    """Extrai apenas o primeiro e segundo nome do leitor ou responsável."""
    if not nome_completo or nome_completo == "Sem funcionario":
        return nome_completo
    partes = nome_completo.strip().split()
    if len(partes) == 1:
        return partes[0].upper()
    return " ".join(partes[:2]).upper()


def _rotulo_leitor(row: Dict[str, Any]) -> str:
    """
    Rótulo para agrupar/filtrar por funcionário: leitor designado, se houver;
    caso contrário o responsável (ex.: cumprimento em lote no LexFlow costuma
    não preencher ``LEITOR``, mas mantém ``RESPONSAVEL``).
    """
    raw = _col(row, _COL_LEITOR)
    if raw is not None and str(raw).strip():
        return _formatar_nome(str(raw).strip())
    raw_resp = _col(row, _COL_RESPONSAVEL)
    if raw_resp is not None and str(raw_resp).strip():
        return _formatar_nome(str(raw_resp).strip())
    return _formatar_nome("SEM LEITOR")


def _label_caixa_alta(value: Any, default: str) -> str:
    """Rótulo para gráficos: `default` já em maiúsculas; valores preenchidos viram `.upper()`."""
    if value is None:
        return default
    s = str(value).strip()
    return default if not s else s.upper()


def _rotulo_materia_LA(row: Dict[str, Any]) -> str:
    return _label_caixa_alta(_col(row, _COL_MATERIA), "SEM MATERIA")


def _rotulo_documento_LA(row: Dict[str, Any]) -> str:
    return _label_caixa_alta(_col(row, _COL_DOCUMENTO), "DOCUMENTO")


def _rotulo_tribunal_LA(row: Dict[str, Any]) -> str:
    return _label_caixa_alta(_col(row, _COL_TRIBUNAL), "SEM TRIBUNAL")


def _rotulo_orgao_LA(row: Dict[str, Any]) -> str:
    return _label_caixa_alta(_col(row, _COL_ORGAO), "SEM ORGAO")


def _normalizar_filtro_dimensao_LA(valor: Optional[str]) -> Optional[str]:
    """Valor da UI ou do banco → comparação com rótulos em maiúsculas."""
    if valor is None or not str(valor).strip():
        return None
    return str(valor).strip().upper()


def _cumprida_mesmo_dia(row: Dict[str, Any], dia: Optional[date] = None) -> bool:
    """
    True se a publicação foi cumprida com DATA_DISPONIBILIZACAO == DATA_CONCLUSAO.
    Quando `dia` é informado, exige também que ambas as datas sejam iguais a ele.
    """
    if not _is_cumprido(row):
        return False
    d_disp = _get_date(row, _COL_DISPONIBILIZACAO)
    d_conc = _get_date(row, _COL_CONCLUSAO)
    if d_disp is None or d_conc is None or d_disp != d_conc:
        return False
    return dia is None or d_disp == dia


def _agrupar_por_rotulo(
    publicacoes: List[Dict[str, Any]],
    fn_rotulo: Callable[[Dict[str, Any]], str],
) -> List[Dict[str, Any]]:
    """Agrupa publicações contando ocorrências por rótulo calculado via fn_rotulo."""
    grouped: Dict[str, int] = defaultdict(int)
    for p in publicacoes:
        grouped[fn_rotulo(p)] += 1
    return [{"name": k, "value": v} for k, v in sorted(grouped.items())]


def _filtrar_por_rotulo(
    publicacoes: List[Dict[str, Any]],
    valor: Optional[Union[str, List[str]]],
    fn_rotulo: Callable[[Dict[str, Any]], str],
) -> List[Dict[str, Any]]:
    """
    Filtra publicações cujo rótulo (calculado via fn_rotulo) coincide com valor.
    Se valor for None ou vazio, devolve cópia da lista sem filtrar.
    """
    valores = valor if isinstance(valor, (list, tuple, set)) else [valor]
    alvos = {a for a in (_normalizar_filtro_dimensao_LA(v) for v in valores) if a is not None}
    if not alvos:
        return list(publicacoes)
    return [p for p in publicacoes if fn_rotulo(p) in alvos]


# -----------------------------------------------------------------------------
# Filtros por leitor e por dimensão
# -----------------------------------------------------------------------------

def filter_publicacoes_por_leitor_LA(
    publicacoes: List[Dict[str, Any]],
    leitor: Optional[Union[str, List[str]]] = None,
) -> List[Dict[str, Any]]:
    """
    Restringe a lista às publicações de um único leitor.

    O critério de identidade é o mesmo de :func:`_rotulo_leitor` (leitor, ou
    responsável se leitor vazio; primeiro + segundo nome em maiúsculas; ou
    ``SEM LEITOR``). O parâmetro ``leitor`` pode
    ser o nome completo vindo do banco ou já no formato dos gráficos — é
    normalizado com :func:`_formatar_nome` antes da comparação.

    Para analisar só aquele leitor, encadeie antes das demais funções deste
    módulo, por exemplo::

        base = filter_publicacoes_por_leitor_LA(publicacoes, "Maria Silva")
        group_publicacoes_por_tribunal_LA(base)

    Se ``leitor`` for ``None`` ou string vazia, devolve uma cópia da lista
    original (sem filtro).
    """
    nomes = leitor if isinstance(leitor, (list, tuple, set)) else [leitor]
    alvos = {_formatar_nome(str(n).strip()) for n in nomes if n is not None and str(n).strip()}
    if not alvos:
        return list(publicacoes)
    return [p for p in publicacoes if _rotulo_leitor(p) in alvos]


def filter_publicacoes_por_materia_LA(
    publicacoes: List[Dict[str, Any]],
    materia: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Restringe às publicações cuja matéria coincide com o rótulo dos gráficos.

    ``materia`` pode vir do banco ou do ``name`` retornado por
    :func:`group_publicacoes_por_materia_LA` (ex.: ``SEM MATERIA``).
    Se ``None`` ou vazio, devolve cópia da lista sem filtrar.
    """
    return _filtrar_por_rotulo(publicacoes, materia, _rotulo_materia_LA)


def filter_publicacoes_por_documento_LA(
    publicacoes: List[Dict[str, Any]],
    documento: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Por tipo de documento (coluna ``DOCUMENTO``), alinhado a
    :func:`group_publicacoes_por_tipo_documento_LA`.
    """
    return _filtrar_por_rotulo(publicacoes, documento, _rotulo_documento_LA)


def filter_publicacoes_por_tribunal_LA(
    publicacoes: List[Dict[str, Any]],
    tribunal: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Por tribunal, mesmo critério de :func:`group_publicacoes_por_tribunal_LA`."""
    return _filtrar_por_rotulo(publicacoes, tribunal, _rotulo_tribunal_LA)


def filter_publicacoes_por_orgao_LA(
    publicacoes: List[Dict[str, Any]],
    orgao: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Por órgão, mesmo critério de :func:`group_publicacoes_por_orgao_LA`."""
    return _filtrar_por_rotulo(publicacoes, orgao, _rotulo_orgao_LA)


# -----------------------------------------------------------------------------
# 1 - Funções que vão nos cartões de informações do dashboard
# -----------------------------------------------------------------------------

def get_publicacoes_recebidas_periodo_LA(
    publicacoes: List[Dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> int:
    """Contagem por DATA_DISPONIBILIZACAO dentro do intervalo."""
    return sum(
        1 for p in publicacoes
        if (d := _get_date(p, _COL_DISPONIBILIZACAO)) is not None
        and _in_interval(d, from_date, to_date)
    )


def filter_publicacoes_recebidas_no_periodo_LA(
    publicacoes: List[Dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> List[Dict[str, Any]]:
    """
    Publicações cuja DATA_DISPONIBILIZACAO está no intervalo — mesma regra de
    get_publicacoes_recebidas_periodo_LA. Usado nos gráficos (matéria, tribunal, etc.)
    para alinhar ao filtro de período da UI.
    """
    return [
        p for p in publicacoes
        if (d := _get_date(p, _COL_DISPONIBILIZACAO)) is not None
        and _in_interval(d, from_date, to_date)
    ]


def filter_publicacoes_tratadas_no_periodo_LA(
    publicacoes: List[Dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> List[Dict[str, Any]]:
    """
    Publicações cumpridas cuja DATA_CONCLUSAO está no intervalo — mesma regra de
    get_publicacoes_tratadas_periodo_LA. Usado para alinhar agrupamentos "por leitor"
    de cumpridas ao card "Cumpridas no período" (base = conclusão, não chegada).
    """
    return [
        p for p in publicacoes
        if _is_cumprido(p)
        and (d := _get_date(p, _COL_CONCLUSAO)) is not None
        and _in_interval(d, from_date, to_date)
    ]


def get_publicacoes_tratadas_periodo_LA(
    publicacoes: List[Dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> int:
    """Status cumprido; referência de data: DATA_CONCLUSAO."""
    return sum(
        1 for p in publicacoes
        if _is_cumprido(p)
        and (d := _get_date(p, _COL_CONCLUSAO)) is not None
        and _in_interval(d, from_date, to_date)
    )


def resolve_dia_referencia_fim_periodo_LA(
    from_date: Optional[date],
    to_date: Optional[date],
) -> date:
    """
    Último dia do intervalo da UI (em geral o `to` da query: ex. início do mês até hoje).
    Se não houver `to`, usa `from`; se não houver nenhum, data atual do servidor.
    """
    if to_date is not None:
        return to_date
    if from_date is not None:
        return from_date
    return date.today()


def get_publicacoes_tratadas_no_dia_LA(
    publicacoes: List[Dict[str, Any]],
    dia: date,
) -> int:
    """Cumpridas com DATA_CONCLUSAO no dia civil `dia`."""
    return sum(
        1 for p in publicacoes
        if _is_cumprido(p)
        and _get_date(p, _COL_CONCLUSAO) == dia
    )


def get_publicacoes_recebidas_no_dia_LA(
    publicacoes: List[Dict[str, Any]],
    dia: date,
) -> int:
    """Registros cuja DATA_DISPONIBILIZACAO cai no dia civil `dia` (chegaram nesse dia)."""
    return sum(
        1 for p in publicacoes
        if _get_date(p, _COL_DISPONIBILIZACAO) == dia
    )


def get_publicacoes_cumpridas_mesmo_dia_chegada_no_dia_LA(
    publicacoes: List[Dict[str, Any]],
    dia: date,
) -> int:
    """
    Cumpridas com disponibilização e conclusão no mesmo dia civil `dia`
    (chegaram e foram cumpridas nesse dia).
    """
    return sum(1 for p in publicacoes if _cumprida_mesmo_dia(p, dia))


def get_publicacoes_com_data_disponibilizacao_LA(
    publicacoes: List[Dict[str, Any]],
) -> int:
    """
    Quantidade com DATA_DISPONIBILIZACAO preenchida ("chegaram" — base do %).
    Não usa filtro de período da página.
    """
    return sum(
        1 for p in publicacoes
        if _get_date(p, _COL_DISPONIBILIZACAO) is not None
    )


def get_publicacoes_cumpridas_mesmo_dia_chegada_LA(
    publicacoes: List[Dict[str, Any]],
) -> int:
    """
    Cumpridas cuja DATA_CONCLUSAO é o mesmo dia civil que DATA_DISPONIBILIZACAO.
    Independente do intervalo selecionado no dashboard.
    """
    return sum(1 for p in publicacoes if _cumprida_mesmo_dia(p))


def get_pct_tratadas_mesmo_dia_publicacoes_LA(
    publicacoes: List[Dict[str, Any]],
    dia_referencia: date,
) -> Optional[float]:
    """
    Taxa no dia de referência (último dia do período, ex. hoje):
    (cumpridas no mesmo dia da chegada nesse dia) / (publicações que chegaram nesse dia) * 100.
    Ex.: chegaram 274 e 274 cumpridas no mesmo dia → 100%.
    """
    denom = get_publicacoes_recebidas_no_dia_LA(publicacoes, dia_referencia)
    if denom == 0:
        return None
    num = get_publicacoes_cumpridas_mesmo_dia_chegada_no_dia_LA(publicacoes, dia_referencia)
    return round(100.0 * num / denom, 2)


def get_publicacoes_pendentes_LA(publicacoes: List[Dict[str, Any]]) -> int:
    """Backlog atual: apenas status Visualizado ou Não visualizado."""
    return sum(1 for p in publicacoes if _conta_como_pendente_publicacao_LA(p))


def get_media_tempo_tratamento_publicacoes_LA(
    publicacoes: List[Dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> Optional[float]:
    """
    Média em dias entre DATA_DISPONIBILIZACAO e DATA_CONCLUSAO,
    apenas para cumpridas com DATA_CONCLUSAO no intervalo.
    """
    dias = tempo.duracoes(
        [p for p in publicacoes if _is_cumprido(p)],
        lambda p: _get_date(p, _COL_DISPONIBILIZACAO),
        lambda p: _get_date(p, _COL_CONCLUSAO),
        de=from_date,
        ate=to_date,
        aceita_zero=True,
    )
    return tempo.media(dias, casas=None, vazio=None)


def get_publicacoes_pendentes_zeradas_no_periodo_LA(
    publicacoes: List[Dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> int:
    """
    Quantas vezes o estoque de pendentes (chegou por DATA_DISPONIBILIZACAO e ainda não
    tinha sido cumprida até aquele dia) chegou a zero dentro do intervalo — cada
    transição de >0 para 0 conta como uma vez; dias consecutivos zerados não repetem
    a contagem. Publicações fora do escopo de "pendente" hoje (ex.: cancelada) contam
    apenas se cumpridas, com base na sua própria DATA_CONCLUSAO.
    """
    if from_date is None or to_date is None or from_date > to_date:
        return 0

    delta: Dict[date, int] = defaultdict(int)
    for p in publicacoes:
        chegada = _get_date(p, _COL_DISPONIBILIZACAO)
        if chegada is None:
            continue
        delta[chegada] += 1
        if _is_cumprido(p):
            conclusao = _get_date(p, _COL_CONCLUSAO)
            if conclusao is not None:
                delta[conclusao] -= 1
        # Não cumprida: nunca "fecha" — contribui ao estoque indefinidamente a partir da chegada.

    if not delta:
        return 0

    estoque = sum(v for d, v in delta.items() if d < from_date)
    estava_zerado = estoque <= 0
    zeradas = 0
    dia = from_date
    while dia <= to_date:
        estoque += delta.get(dia, 0)
        zerado_agora = estoque <= 0
        if zerado_agora and not estava_zerado:
            zeradas += 1
        estava_zerado = zerado_agora
        dia += timedelta(days=1)

    return zeradas


def group_publicacoes_recebidas_por_dia_LA(
    publicacoes: List[Dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> List[Dict[str, Any]]:
    grouped: Dict[str, int] = defaultdict(int)
    for p in publicacoes:
        d = _get_date(p, _COL_DISPONIBILIZACAO)
        if d is None or not _in_interval(d, from_date, to_date):
            continue
        grouped[d.strftime("%Y-%m-%d")] += 1
    return [{"name": dia, "value": count} for dia, count in sorted(grouped.items())]


def group_publicacoes_tratadas_por_dia_LA(
    publicacoes: List[Dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> List[Dict[str, Any]]:
    grouped: Dict[str, int] = defaultdict(int)
    for p in publicacoes:
        if not _is_cumprido(p):
            continue
        d = _get_date(p, _COL_CONCLUSAO)
        if d is None or not _in_interval(d, from_date, to_date):
            continue
        grouped[d.strftime("%Y-%m-%d")] += 1
    return [{"name": dia, "value": count} for dia, count in sorted(grouped.items())]


# -----------------------------------------------------------------------------
# 2 - Agrupando dados para os gráficos
# -----------------------------------------------------------------------------

def group_publicacoes_por_tribunal_LA(publicacoes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return _agrupar_por_rotulo(publicacoes, _rotulo_tribunal_LA)


def group_publicacoes_por_tipo_documento_LA(publicacoes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return _agrupar_por_rotulo(publicacoes, _rotulo_documento_LA)


def group_publicacoes_por_materia_LA(publicacoes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return _agrupar_por_rotulo(publicacoes, _rotulo_materia_LA)


def group_publicacoes_por_orgao_LA(publicacoes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return _agrupar_por_rotulo(publicacoes, _rotulo_orgao_LA)


def group_publicacoes_por_comarca_LA(publicacoes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    fn_rotulo = lambda p: _label_caixa_alta(p.get(_COL_COMARCA), "SEM COMARCA")
    return _agrupar_por_rotulo(publicacoes, fn_rotulo)


# -----------------------------------------------------------------------------
# 3 - Funções por Funcionário (Leitor e Responsável)
# -----------------------------------------------------------------------------

def group_publicacoes_cumprido_por_leitor_LA(
    publicacoes: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Por leitor, contagem apenas de publicações com status cumprido."""
    cumpridas = [p for p in publicacoes if _is_cumprido(p)]
    return _agrupar_por_rotulo(cumpridas, _rotulo_leitor)


def group_publicacoes_pendentes_por_leitor_LA(
    publicacoes: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Por leitor, contagem de publicações pendentes (apenas Visualizado ou Não visualizado).
    No dashboard, deve ser chamada com a base completa — sem filtrar por período de recebimento.
    """
    pendentes = [p for p in publicacoes if _conta_como_pendente_publicacao_LA(p)]
    return _agrupar_por_rotulo(pendentes, _rotulo_leitor)


def group_publicacoes_pendentes_por_dias_atraso_LA(
    publicacoes: List[Dict[str, Any]],
    *,
    data_referencia: Optional[date] = None,
    modo_atraso: Literal["desde_mais_antiga", "ate_referencia"] = "desde_mais_antiga",
) -> List[Dict[str, Any]]:
    """
    Somente publicações pendentes (status Visualizado ou Não visualizado).

    **desde_mais_antiga** (equivalente ao Power BI com ``DATA`` = DATA_DISPONIBILIZACAO
    da linha e ``DATA DA MAIS ANTIGA`` = menor DATA_DISPONIBILIZACAO entre os pendentes):

    ``ATRASO_EM_DIAS = DATEDIFF([DATA DA MAIS ANTIGA], [DATA], DAY)``
    → dias = (DATA_DISPONIBILIZACAO da publicação − data mais antiga). A publicação
    mais antiga fica com 0; as demais medem o afastamento em dias na linha do tempo
    das chegadas.

    **ate_referencia**: dias em calendário até o dia da análise —
    ``(data_referencia ou hoje) − DATA_DISPONIBILIZACAO`` (mínimo 0).

    Retorno: pontos ``name`` = dias (string), ``value`` = quantidade agregada.
    Linhas sem DATA_DISPONIBILIZACAO são ignoradas.
    """
    datas_chegada: List[date] = []
    for p in publicacoes:
        if not _conta_como_pendente_publicacao_LA(p):
            continue
        d_chegada = _get_date(p, _COL_DISPONIBILIZACAO)
        if d_chegada is None:
            continue
        datas_chegada.append(d_chegada)

    if not datas_chegada:
        return []

    data_mais_antiga = min(datas_chegada)
    ref = data_referencia if data_referencia is not None else date.today()

    buckets: Dict[int, int] = defaultdict(int)
    for d_chegada in datas_chegada:
        if modo_atraso == "desde_mais_antiga":
            dias = (d_chegada - data_mais_antiga).days
        else:
            dias = max((ref - d_chegada).days, 0)
        buckets[dias] += 1

    return [{"name": str(d), "value": c} for d, c in sorted(buckets.items())]


# -----------------------------------------------------------------------------
# 4 - Agendamento criado após a finalização da publicação (qualquer setor)
# -----------------------------------------------------------------------------

def _agendamentos_por_processo_LA(
    agendamentos: List[Dict[str, Any]],
) -> Dict[Any, List[Dict[str, Any]]]:
    """Agrupa agendamentos por processo (ID_PROCESSO), ordenados por data de criação (mais antigo primeiro)."""
    por_processo: Dict[Any, List[Dict[str, Any]]] = defaultdict(list)
    for ag in agendamentos:
        pid = _col(ag, _COL_AG_PROCESSO_ID)
        if pid is None:
            continue
        por_processo[pid].append(ag)
    for lista in por_processo.values():
        lista.sort(key=lambda ag: _get_date(ag, _COL_AG_DATA_CRIACAO) or date.max)
    return por_processo


def _agendamento_apos_finalizacao_LA(
    publicacao: Dict[str, Any],
    agendamentos_por_processo: Dict[Any, List[Dict[str, Any]]],
) -> Optional[Dict[str, Any]]:
    """
    Primeiro agendamento (qualquer setor) do mesmo processo com DATA_HORA_CRIACAO no
    mesmo dia ou depois da DATA_CONCLUSAO da publicação. ``None`` se a publicação não
    tiver DATA_CONCLUSAO/ID_PROCESSO ou nenhum agendamento elegível existir.
    """
    d_conclusao = _get_date(publicacao, _COL_CONCLUSAO)
    if d_conclusao is None:
        return None
    id_processo = _col(publicacao, _COL_ID_PROCESSO)
    if id_processo is None:
        return None
    for ag in agendamentos_por_processo.get(id_processo, []):
        d_criacao = _get_date(ag, _COL_AG_DATA_CRIACAO)
        if d_criacao is not None and d_criacao >= d_conclusao:
            return ag
    return None


def build_publicacoes_agendamento_apos_finalizacao_LA(
    publicacoes: List[Dict[str, Any]],
    agendamentos: List[Dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> tuple[int, int, List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Entre as publicações cumpridas com DATA_CONCLUSAO no intervalo: quantas têm um
    agendamento (qualquer setor, mesmo processo) criado a partir da conclusão, quantas
    não têm, o nome (ATIVIDADE) desses agendamentos agrupado para o gráfico "por
    atividade", e o setor de destino (SETOR) agrupado para o gráfico "por setor".
    """
    por_processo = _agendamentos_por_processo_LA(agendamentos)
    com_agendamento = 0
    sem_agendamento = 0
    grouped_atividade: Dict[str, int] = defaultdict(int)
    grouped_setor: Dict[str, int] = defaultdict(int)
    for p in publicacoes:
        if not _is_cumprido(p):
            continue
        d = _get_date(p, _COL_CONCLUSAO)
        if d is None or not _in_interval(d, from_date, to_date):
            continue
        ag = _agendamento_apos_finalizacao_LA(p, por_processo)
        if ag is None:
            sem_agendamento += 1
            continue
        com_agendamento += 1
        nome = _label_caixa_alta(_col(ag, _COL_AG_ATIVIDADE), "SEM ATIVIDADE")
        grouped_atividade[nome] += 1
        setor = _label_caixa_alta(_col(ag, _COL_AG_SETOR), "SEM SETOR")
        grouped_setor[setor] += 1

    por_atividade = sorted(
        ({"name": k, "value": v} for k, v in grouped_atividade.items()),
        key=lambda x: x["value"],
        reverse=True,
    )
    por_setor = sorted(
        ({"name": k, "value": v} for k, v in grouped_setor.items()),
        key=lambda x: x["value"],
        reverse=True,
    )
    return com_agendamento, sem_agendamento, por_atividade, por_setor


def filter_publicacoes_por_atividade_agendamento_LA(
    publicacoes: List[Dict[str, Any]],
    agendamentos: List[Dict[str, Any]],
    atividade: Optional[str],
    from_date: Optional[date],
    to_date: Optional[date],
) -> List[Dict[str, Any]]:
    """
    Restringe às publicações cumpridas no intervalo cujo agendamento (qualquer setor,
    criado a partir da DATA_CONCLUSAO) tem ATIVIDADE igual a `atividade` — mesmo
    critério de :func:`build_publicacoes_agendamento_apos_finalizacao_LA`.
    Se `atividade` for None ou vazio, devolve cópia da lista original (sem filtro).
    """
    alvo = _normalizar_filtro_dimensao_LA(atividade)
    if alvo is None:
        return list(publicacoes)
    por_processo = _agendamentos_por_processo_LA(agendamentos)
    out: List[Dict[str, Any]] = []
    for p in publicacoes:
        if not _is_cumprido(p):
            continue
        d = _get_date(p, _COL_CONCLUSAO)
        if d is None or not _in_interval(d, from_date, to_date):
            continue
        ag = _agendamento_apos_finalizacao_LA(p, por_processo)
        if ag is None:
            continue
        nome = _label_caixa_alta(_col(ag, _COL_AG_ATIVIDADE), "SEM ATIVIDADE")
        if nome == alvo:
            out.append(p)
    return out


def filter_publicacoes_por_setor_agendamento_LA(
    publicacoes: List[Dict[str, Any]],
    agendamentos: List[Dict[str, Any]],
    setor: Optional[str],
    from_date: Optional[date],
    to_date: Optional[date],
) -> List[Dict[str, Any]]:
    """
    Restringe às publicações cumpridas no intervalo cujo agendamento (criado a partir
    da DATA_CONCLUSAO) tem SETOR igual a `setor` — mesmo critério de
    :func:`build_publicacoes_agendamento_apos_finalizacao_LA`.
    Se `setor` for None ou vazio, devolve cópia da lista original (sem filtro).
    """
    alvo = _normalizar_filtro_dimensao_LA(setor)
    if alvo is None:
        return list(publicacoes)
    por_processo = _agendamentos_por_processo_LA(agendamentos)
    out: List[Dict[str, Any]] = []
    for p in publicacoes:
        if not _is_cumprido(p):
            continue
        d = _get_date(p, _COL_CONCLUSAO)
        if d is None or not _in_interval(d, from_date, to_date):
            continue
        ag = _agendamento_apos_finalizacao_LA(p, por_processo)
        if ag is None:
            continue
        setor_nome = _label_caixa_alta(_col(ag, _COL_AG_SETOR), "SEM SETOR")
        if setor_nome == alvo:
            out.append(p)
    return out


def filter_publicacoes_por_status_agendamento_LA(
    publicacoes: List[Dict[str, Any]],
    agendamentos: List[Dict[str, Any]],
    status: Optional[str],
    from_date: Optional[date],
    to_date: Optional[date],
) -> List[Dict[str, Any]]:
    """
    Restringe às publicações cumpridas no intervalo conforme `status`:
    ``"com"`` → só as que geraram agendamento (qualquer setor) após a conclusão;
    ``"sem"`` → só as que não geraram nenhum. Qualquer outro valor devolve cópia
    da lista original (sem filtro).
    """
    alvo = str(status).strip().lower() if status else ""
    if alvo not in ("com", "sem"):
        return list(publicacoes)
    por_processo = _agendamentos_por_processo_LA(agendamentos)
    out: List[Dict[str, Any]] = []
    for p in publicacoes:
        if not _is_cumprido(p):
            continue
        d = _get_date(p, _COL_CONCLUSAO)
        if d is None or not _in_interval(d, from_date, to_date):
            continue
        tem_agendamento = _agendamento_apos_finalizacao_LA(p, por_processo) is not None
        if (alvo == "com") == tem_agendamento:
            out.append(p)
    return out


# -----------------------------------------------------------------------------
# 5 - Lista de publicações (tabela "Lista de tarefas" do dashboard)
# -----------------------------------------------------------------------------

def list_publicacoes_LA(
    publicacoes: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Uma linha por publicação, no formato de linha de tarefa (mesmo componente usado
    por agendamentos). Sem PRAZO real — publicação não tem prazo, o campo fica vazio.
    ``descricao`` = tipo de documento; ``operacao`` (subtítulo) = matéria;
    ``pessoa_setor`` = tribunal - órgão.
    """
    itens: List[Dict[str, Any]] = []
    for p in publicacoes:
        pub_id = _col(p, "id")
        try:
            pub_id_int = int(pub_id)
        except (TypeError, ValueError):
            continue
        criado = _get_date(p, _COL_DISPONIBILIZACAO)
        status = str(_col(p, _COL_STATUS) or "").strip() or "—"
        itens.append({
            "id": pub_id_int,
            "status": status,
            "descricao": _rotulo_documento_LA(p),
            "pessoa_setor": f"{_rotulo_tribunal_LA(p)} - {_rotulo_orgao_LA(p)}",
            "funcionario": _rotulo_leitor(p),
            "atividade": _rotulo_materia_LA(p),
            "prazo": None,
            "concluida": _is_cumprido(p),
            "criado_em": criado.isoformat() if criado else None,
            "operacao": _rotulo_materia_LA(p),
        })
    return itens


# -----------------------------------------------------------------------------
# 6 - Comissionamento por funcionário (leitor)
# -----------------------------------------------------------------------------

# Valores unitários do modelo de cálculo (item 6 do documento de comissionamento):
# certa = lida corretamente e com agendamento correto; errada = lida e com agendamento errado.
_VALOR_UNITARIO_CERTA_LA = Decimal("0.20")
_VALOR_UNITARIO_ERRADA_LA = Decimal("0.50")


def get_publicacoes_comissionamento_por_funcionario_LA(
    publicacoes: List[Dict[str, Any]],
    agendamentos: List[Dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> List[Dict[str, Any]]:
    """
    Comissão mensal por funcionário (leitor):
    ``(Nº de publicações certas × R$0,20) − (Nº de publicações erradas × R$0,50)``.

    "Certa" = publicação cumprida no intervalo com agendamento (qualquer setor) criado
    a partir da conclusão, no mesmo processo; "errada" = cumprida no intervalo sem
    nenhum agendamento posterior — mesmo critério de
    :func:`build_publicacoes_agendamento_apos_finalizacao_LA`.
    """
    por_processo = _agendamentos_por_processo_LA(agendamentos)
    contagem: Dict[str, Dict[str, int]] = defaultdict(lambda: {"certas": 0, "erradas": 0})
    for p in publicacoes:
        if not _is_cumprido(p):
            continue
        d = _get_date(p, _COL_CONCLUSAO)
        if d is None or not _in_interval(d, from_date, to_date):
            continue
        nome = _rotulo_leitor(p)
        if _agendamento_apos_finalizacao_LA(p, por_processo) is not None:
            contagem[nome]["certas"] += 1
        else:
            contagem[nome]["erradas"] += 1

    linhas: List[Dict[str, Any]] = []
    for nome, c in contagem.items():
        qtd_certas = c["certas"]
        qtd_erradas = c["erradas"]
        qtd_lidas = qtd_certas + qtd_erradas
        valor_base = (Decimal(qtd_certas) * _VALOR_UNITARIO_CERTA_LA).quantize(Decimal("0.01"))
        valor_penalidade = (Decimal(qtd_erradas) * _VALOR_UNITARIO_ERRADA_LA).quantize(Decimal("0.01"))
        comissao = (valor_base - valor_penalidade).quantize(Decimal("0.01"))
        linhas.append({
            "funcionario": nome,
            "qtd_lidas": qtd_lidas,
            "qtd_certas": qtd_certas,
            "qtd_erradas": qtd_erradas,
            "valor_certa": float(_VALOR_UNITARIO_CERTA_LA),
            "valor_errada": float(_VALOR_UNITARIO_ERRADA_LA),
            "comissao": float(comissao),
        })
    linhas.sort(key=lambda x: (-x["comissao"], x["funcionario"]))
    return linhas
