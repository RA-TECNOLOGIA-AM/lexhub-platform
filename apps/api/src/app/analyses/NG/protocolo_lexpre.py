# Análises e processamento de dados de PROTOCOLO NG (banco lexpre)
#
# Fonte: mesma query "comercial_lexpre_NG" (queries.py) usada por comercial_lexpre.py —
# public.atendimento + public.demandas do banco `lexpre`. Este módulo cobre a Seção 03
# da página Comercial (LexPre): "Protocolos e valor de causa", que só ganha dados de
# fato quando a demanda é protocolada (``data_protocolo`` preenchida) dentro do lexpre.
#
# "Fila de Demandas no Pré-Protocolo" classifica cada demanda (não cancelada) em um
# de 6 estágios, a partir de ``demandas.setor_id`` (public.setores) e ``data_protocolo``:
#   - Protocolado: data_protocolo preenchida (independente do setor atual).
#   - Não Protocolado: setor = Protocolo, ainda sem data_protocolo.
#   - Não Confeccionado: setor = Peticionamento.
#   - Pendências: setor = Pendências.
#   - Triagem: setor = Triagem.
#   - Não Organizado: setor = Organização de Documentos, Comercial, ou sem setor
#     definido (demanda em rascunho).
#
# "por atendente" usa o campo ATENDENTE do atendimento (mesmo da Seção 02) — o
# ``demandas.funcionario_responsavel`` aponta para IDs que não existem em
# ``public.funcionario`` nos dados atuais (não confiável ainda).

from typing import Any, Dict, List, Optional
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal

from app.utils import parse_date_from_db, resolver_periodo_comparativo
from app.analyses.NG.comercial_lexpre import _expandir_ids_para_contagem

# "Cancelado" em public.status (lexpre) — mesma constante de comercial_lexpre.py.
STATUS_DEMANDA_CANCELADO_ID = 10

# "Assinado" em public.status (lexpre) — mesma constante/regra de `_is_assinado`
# em comercial_lexpre.py (duplicada aqui pelo mesmo motivo: módulo autocontido).
STATUS_ASSINADO_ID = 6

# "Aguardando Despacho Inicial" — status que marca a demanda como efetivamente
# protocolada e resolvida, mesma constante/critério de
# `protocolo_setor_lexpre.STATUS_AG_DESPACHO_INICIAL_ID` (duplicada aqui pelo
# mesmo motivo: módulo autocontido). Status é global/compartilhado entre
# escritórios (public.status não tem bloco por escritório como public.setores),
# então não precisa virar set. Usado por `get_protocolados`/
# `get_valor_causa_protocolado` (30/09/2026): só ter DATA_PROTOCOLO preenchida
# não basta — uma demanda pode protocolar, ser devolvida e cair de novo em
# Protocolo depois (represada, sem nova saída) sem que DATA_PROTOCOLO seja
# limpa; exigir o status terminal fecha esse buraco e alinha com o critério já
# usado pelo dashboard Protocolo LexPre (`_is_protocolado`).
STATUS_AG_DESPACHO_INICIAL_ID = 13

# public.setores (lexpre) — cada escritório tem seu próprio bloco de ids pro mesmo
# setor lógico (link real: setores.operacao_id -> operacao.escritorio_id). Cada
# constante abaixo é a UNIÃO dos ids desse setor em todos os escritórios com
# dashboard lexpre até agora (NGAM=1, LAAM=2 — este módulo alimenta
# `get_bucket_fila_pre_protocolo`, já usado pelo Comercial LexPre LA via
# `get_valor_causa_por_atendente`, então precisa reconhecer os ids do LAAM
# também). A atribuição de escritório de uma linha vem SEMPRE da coluna
# ESCRITORIO_ID, nunca do valor de SETOR_ID em si — por isso a comparação é por
# pertencimento (in). Ver o mesmo ajuste em org_doc_lexpre.py, 24/09/2026.
#   Setor            NGAM   LAAM
#   Pendências          2     10
#   Peticionamento      4     12
#   Protocolo           5     13
#   Triagem             6      9
SETOR_PENDENCIAS_IDS = {2, 10}
SETOR_PETICIONAMENTO_IDS = {4, 12}
SETOR_PROTOCOLO_IDS = {5, 13}
SETOR_TRIAGEM_IDS = {6, 9}

# Chaves ASCII (para a API/Pydantic) — os rótulos em pt-BR exibidos no funil
# ("Pendências", "Triagem", "Não Organizado", "Não Confeccionado", "Não Protocolado",
# "Protocolado") ficam por conta do front, que já sabe montar a legenda do gráfico.
BUCKETS_FILA_PRE_PROTOCOLO_ORDENADOS: tuple[str, ...] = (
    "pendencias",
    "triagem",
    "nao_organizado",
    "nao_confeccionado",
    "nao_protocolado",
    "protocolado",
)


def _formatar_nome_atendente(nome_completo: Any) -> str:
    """Primeiro nome do atendente — mesmo critério dos outros dashboards comerciais."""
    if not nome_completo or not str(nome_completo).strip():
        return "Sem atendente"
    return str(nome_completo).strip().split()[0]


def _converter_valor(valor_raw: Any) -> float:
    """Converte um valor monetário (string ou numérico) para float."""
    if valor_raw is None:
        return 0.0

    if isinstance(valor_raw, (int, float, Decimal)):
        return float(valor_raw)

    valor_str = str(valor_raw).strip()
    if not valor_str:
        return 0.0

    valor_str = (
        valor_str.replace("R$", "")
        .replace(" ", "")  # NBSP
        .replace(" ", "")
        .strip()
    )

    if "," in valor_str and "." in valor_str:
        valor_str = valor_str.replace(".", "").replace(",", ".")
    elif "," in valor_str and "." not in valor_str:
        valor_str = valor_str.replace(",", ".")

    try:
        return float(valor_str)
    except (ValueError, TypeError):
        return 0.0


def _to_date(raw: Any) -> Optional[date]:
    if not raw:
        return None
    parsed = parse_date_from_db(raw)
    if isinstance(parsed, datetime):
        return parsed.date()
    if isinstance(parsed, date):
        return parsed
    return None


def _to_datetime(raw: Any) -> Optional[datetime]:
    """Como `_to_date`, mas preserva hora/minuto — necessário para tempo médio até o protocolo."""
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw
    if isinstance(raw, date):
        return datetime.combine(raw, datetime.min.time())
    parsed_date = _to_date(raw)
    if parsed_date is None:
        return None
    return datetime.combine(parsed_date, datetime.min.time())


def _is_assinado(row: Dict[str, Any]) -> bool:
    """Cliente assinou — mesma regra de `comercial_lexpre._is_assinado` (ver lá o porquê; motivo_id não entra no critério)."""
    if row.get("STATUS_ID") != STATUS_ASSINADO_ID:
        return False
    return bool(row.get("DATA_ASSINATURA"))


def _demanda_valida(row: Dict[str, Any]) -> bool:
    """
    Demanda não cancelada de um atendimento assinado — só essas contam na Seção 03.

    Sem o filtro de assinatura, demandas em rascunho de atendimentos que ainda nem
    fecharam contrato (``status_id`` "Em assinatura", sem ``data_assinatura``) também
    entrariam na fila, inflando a contagem além do que as atendentes realmente fecharam.
    """
    return (
        row.get("ID_DEMANDA") is not None
        and row.get("STATUS_DEMANDA_ID") != STATUS_DEMANDA_CANCELADO_ID
        and _is_assinado(row)
    )


def _is_protocolado_terminal(row: Dict[str, Any]) -> bool:
    """
    Demanda atingiu (e mantém) o status "Aguardando Despacho Inicial" — mesmo
    critério de `protocolo_setor_lexpre._is_protocolado`. Usado por
    `get_protocolados`/`get_valor_causa_protocolado` além de `DATA_PROTOCOLO`
    preenchida: uma demanda pode ter protocolado no passado e depois voltar a
    cair em Protocolo (represada de novo, sem status terminal) sem que
    DATA_PROTOCOLO seja limpa — sem essa checagem ela continuaria contando como
    "protocolada" aqui mesmo já não sendo mais, divergindo do dashboard
    Protocolo LexPre.
    """
    return row.get("STATUS_DEMANDA_ID") == STATUS_AG_DESPACHO_INICIAL_ID


def _normalizar_materia(raw: Any) -> str:
    """Rubrica já vem normalizada do lexpre (sem o sufixo livre do banco `ng`) — mesma implementação de `protocolo_setor_lexpre._normalizar_materia`."""
    s = str(raw or "").strip()
    return s if s else "Sem matéria"


def _valor_causa_protocolado(row: Dict[str, Any]) -> float:
    """
    Valor de causa de uma demanda protocolada — matéria ANP usa DANO_MORAL em vez
    de VALOR_CAUSA, mesmo critério de `protocolo_setor_lexpre.get_valor_causa_protocolado`.
    A query do Comercial (`comercial_lexpre_NG`) chama a rubrica de "RUBRICA", não
    "MATERIA" (mesma coluna de origem, `public.rubricas.nome`, só com alias
    diferente entre as duas queries).
    """
    materia = _normalizar_materia(row.get("RUBRICA")).upper()
    valor_raw = row.get("DANO_MORAL") if materia == "ANP" else row.get("VALOR_CAUSA")
    return _converter_valor(valor_raw)


def _comparativo_variacao_percentual(
    from_date: Optional[date],
    to_date: Optional[date],
    metrica_fn,
) -> float:
    """Variação percentual de ``metrica_fn(inicio, fim)`` no período vs. o mesmo recorte um mês civil antes."""
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )
    valor_atual = metrica_fn(data_inicio_atual, data_fim_atual)
    valor_anterior = metrica_fn(data_inicio_anterior, data_fim_anterior)
    if valor_anterior == 0:
        return 0.0
    return round(((valor_atual - valor_anterior) / valor_anterior) * 100, 2)


# -----------------------------------------------------------------------------
# 1 - KPIs (filtrados por DATA_PROTOCOLO no período)
# -----------------------------------------------------------------------------

def get_protocolados(
    protocolo_lexpre: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    mapa_reunidas: Optional[Dict[int, List[str]]] = None,
) -> int:
    """
    Demandas (não canceladas) protocoladas no período, deduplicadas por ID_DEMANDA.

    Com ``mapa_reunidas`` (ver ``comercial_lexpre.build_mapa_rubricas_reunidas``),
    demandas de rubrica "reunida" contam uma vez por componente ativo — mesmo
    critério de "Ações Fechadas"/Ranking, consistente em todo o dashboard Comercial.

    Exige também o status terminal (`_is_protocolado_terminal`, 30/09/2026) — uma
    demanda com DATA_PROTOCOLO preenchida mas devolvida e represada de novo em
    Protocolo não conta mais aqui, alinhado ao critério do dashboard Protocolo LexPre.
    """
    vistos: set = set()
    for row in protocolo_lexpre or []:
        if not _demanda_valida(row) or not _is_protocolado_terminal(row):
            continue
        data_protocolo = _to_date(row.get("DATA_PROTOCOLO"))
        if not data_protocolo:
            continue
        if from_date and data_protocolo < from_date:
            continue
        if to_date and data_protocolo > to_date:
            continue
        for sub_id, _nome in _expandir_ids_para_contagem(row, mapa_reunidas):
            vistos.add(sub_id)
    return len(vistos)


def get_valor_causa_protocolado(
    protocolo_lexpre: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """
    Soma do valor de causa das demandas protocoladas no período (matéria ANP usa
    DANO_MORAL — ver `_valor_causa_protocolado`). Exige status terminal, mesmo
    critério de `get_protocolados` (30/09/2026).
    """
    vistos: set = set()
    total = 0.0
    for row in protocolo_lexpre or []:
        if not _demanda_valida(row) or not _is_protocolado_terminal(row):
            continue
        data_protocolo = _to_date(row.get("DATA_PROTOCOLO"))
        if not data_protocolo:
            continue
        if from_date and data_protocolo < from_date:
            continue
        if to_date and data_protocolo > to_date:
            continue
        id_demanda = row.get("ID_DEMANDA")
        if id_demanda is None or id_demanda in vistos:
            continue
        vistos.add(id_demanda)
        total += _valor_causa_protocolado(row)
    return round(total, 2)


def get_ticket_medio_protocolado(
    protocolo_lexpre: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    mapa_reunidas: Optional[Dict[int, List[str]]] = None,
) -> float:
    """
    Valor de causa médio por ação protocolada no período (valor de causa não é
    duplicado por componente — só o denominador usa a contagem expandida).
    """
    protocolados = get_protocolados(protocolo_lexpre, from_date, to_date, mapa_reunidas)
    if protocolados == 0:
        return 0.0
    valor_total = get_valor_causa_protocolado(protocolo_lexpre, from_date, to_date)
    return round(valor_total / protocolados, 2)


_MONTH_NAMES = [
    "jan", "fev", "mar", "abr", "mai", "jun",
    "jul", "ago", "set", "out", "nov", "dez"
]


def get_protocolados_periodo_anterior(
    protocolo_lexpre: List[Dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
    mapa_reunidas: Optional[Dict[int, List[str]]] = None,
) -> int:
    """
    Protocolados no MESMO recorte do "mês anterior" resolvido por
    ``resolver_periodo_comparativo`` — valor ABSOLUTO (não percentual), pro
    chamador combinar com outras fontes (ex.: legado ng/laadv) e só então
    calcular um único comparativo, em vez de somar percentuais de fontes
    diferentes (que dá resultado errado).
    """
    _, _, data_inicio_anterior, data_fim_anterior = resolver_periodo_comparativo(from_date, to_date)
    return get_protocolados(protocolo_lexpre, data_inicio_anterior, data_fim_anterior, mapa_reunidas)


def get_valor_causa_protocolado_periodo_anterior(
    protocolo_lexpre: List[Dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> float:
    """Mesmo critério de `get_protocolados_periodo_anterior`, para valor de causa protocolado."""
    _, _, data_inicio_anterior, data_fim_anterior = resolver_periodo_comparativo(from_date, to_date)
    return get_valor_causa_protocolado(protocolo_lexpre, data_inicio_anterior, data_fim_anterior)


def group_protocolados_por_mes(
    protocolo_lexpre: List[Dict[str, Any]],
    mapa_reunidas: Optional[Dict[int, List[str]]] = None,
) -> List[Dict[str, Any]]:
    """
    Agrupa Processos Protocolados (mesmo critério de `get_protocolados`) por
    mês, pra alimentar o gráfico de tendência "Protocolados por mês" no
    Estratégico Geral. Sem filtro de período — usa toda a história disponível.
    """
    nomes_mes: Dict[str, str] = {}
    ids_por_mes: Dict[str, set] = defaultdict(set)
    for row in protocolo_lexpre or []:
        if not _demanda_valida(row) or not _is_protocolado_terminal(row):
            continue
        data = _to_date(row.get("DATA_PROTOCOLO"))
        if not data:
            continue
        month_key = f"{data.year}-{data.month:02d}"
        nomes_mes.setdefault(month_key, f"{_MONTH_NAMES[data.month - 1]} {data.year}")
        for sub_id, _nome in _expandir_ids_para_contagem(row, mapa_reunidas):
            ids_por_mes[month_key].add(sub_id)
    return [
        {"name": nomes_mes[k], "value": len(v)}
        for k, v in sorted(ids_por_mes.items())
    ]


def group_protocolados_por_dia(
    protocolo_lexpre: List[Dict[str, Any]],
    mapa_reunidas: Optional[Dict[int, List[str]]] = None,
) -> List[Dict[str, Any]]:
    """Mesmo critério de `group_protocolados_por_mes`, granularidade diária (drilldown)."""
    ids_por_dia: Dict[str, set] = defaultdict(set)
    for row in protocolo_lexpre or []:
        if not _demanda_valida(row) or not _is_protocolado_terminal(row):
            continue
        data = _to_date(row.get("DATA_PROTOCOLO"))
        if not data:
            continue
        dia_key = data.strftime("%Y-%m-%d")
        for sub_id, _nome in _expandir_ids_para_contagem(row, mapa_reunidas):
            ids_por_dia[dia_key].add(sub_id)
    return [
        {"name": k, "value": len(v)}
        for k, v in sorted(ids_por_dia.items())
    ]


def group_valor_causa_protocolado_por_mes(protocolo_lexpre: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Agrupa o valor de causa protocolado (mesmo critério de
    `get_valor_causa_protocolado`) por mês, pra alimentar o gráfico "Valor de
    causa protocolado por mês" no Estratégico Geral.
    """
    grouped: Dict[str, Dict[str, Any]] = {}
    vistos_por_mes: Dict[str, set] = defaultdict(set)
    for row in protocolo_lexpre or []:
        if not _demanda_valida(row) or not _is_protocolado_terminal(row):
            continue
        data = _to_date(row.get("DATA_PROTOCOLO"))
        if not data:
            continue
        id_demanda = row.get("ID_DEMANDA")
        if id_demanda is None:
            continue
        month_key = f"{data.year}-{data.month:02d}"
        if month_key not in grouped:
            grouped[month_key] = {"name": f"{_MONTH_NAMES[data.month - 1]} {data.year}", "value": 0.0}
        if id_demanda in vistos_por_mes[month_key]:
            continue
        vistos_por_mes[month_key].add(id_demanda)
        grouped[month_key]["value"] += _valor_causa_protocolado(row)
    return [item for _, item in sorted(grouped.items(), key=lambda x: x[0])]


def group_valor_causa_protocolado_por_dia(protocolo_lexpre: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Mesmo critério de `group_valor_causa_protocolado_por_mes`, granularidade diária (drilldown)."""
    grouped: Dict[str, Dict[str, Any]] = {}
    vistos_por_dia: Dict[str, set] = defaultdict(set)
    for row in protocolo_lexpre or []:
        if not _demanda_valida(row) or not _is_protocolado_terminal(row):
            continue
        data = _to_date(row.get("DATA_PROTOCOLO"))
        if not data:
            continue
        id_demanda = row.get("ID_DEMANDA")
        if id_demanda is None:
            continue
        dia_key = data.strftime("%Y-%m-%d")
        if dia_key not in grouped:
            grouped[dia_key] = {"name": dia_key, "value": 0.0}
        if id_demanda in vistos_por_dia[dia_key]:
            continue
        vistos_por_dia[dia_key].add(id_demanda)
        grouped[dia_key]["value"] += _valor_causa_protocolado(row)
    return [item for _, item in sorted(grouped.items(), key=lambda x: x[0])]


def get_tempo_medio_ate_protocolo_horas(
    protocolo_lexpre: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    mapa_reunidas: Optional[Dict[int, List[str]]] = None,
) -> float:
    """
    Tempo médio (em horas) entre a assinatura do atendimento e o protocolo da demanda,
    para demandas protocoladas no período. A demanda não tem data própria de criação
    no lexpre, então a base de início usada é a DATA_ASSINATURA do atendimento.

    Com ``mapa_reunidas``, demandas de rubrica "reunida" entram no cálculo uma vez por
    componente ativo (o mesmo tempo repetido N vezes) — consistente com a contagem de
    "ações fechadas"/protocoladas no resto do dashboard.
    """
    vistos: set = set()
    horas: List[float] = []
    for row in protocolo_lexpre or []:
        if not _demanda_valida(row):
            continue
        data_protocolo_dia = _to_date(row.get("DATA_PROTOCOLO"))
        if not data_protocolo_dia:
            continue
        if from_date and data_protocolo_dia < from_date:
            continue
        if to_date and data_protocolo_dia > to_date:
            continue

        data_assinatura = _to_datetime(row.get("DATA_ASSINATURA"))
        data_protocolo = _to_datetime(row.get("DATA_PROTOCOLO"))
        if not data_assinatura or not data_protocolo:
            continue
        delta_horas = (data_protocolo - data_assinatura).total_seconds() / 3600
        if delta_horas < 0:
            continue

        for sub_id, _nome in _expandir_ids_para_contagem(row, mapa_reunidas):
            if sub_id in vistos:
                continue
            vistos.add(sub_id)
            horas.append(delta_horas)

    if not horas:
        return 0.0
    return round(sum(horas) / len(horas), 2)


def get_comparativo_protocolados(
    protocolo_lexpre: List[Dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
    mapa_reunidas: Optional[Dict[int, List[str]]] = None,
) -> float:
    return _comparativo_variacao_percentual(
        from_date, to_date, lambda a, b: get_protocolados(protocolo_lexpre, a, b, mapa_reunidas)
    )


def get_comparativo_valor_causa_protocolado(
    protocolo_lexpre: List[Dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
) -> float:
    return _comparativo_variacao_percentual(
        from_date, to_date, lambda a, b: get_valor_causa_protocolado(protocolo_lexpre, a, b)
    )


def get_comparativo_ticket_medio_protocolado(
    protocolo_lexpre: List[Dict[str, Any]],
    from_date: Optional[date],
    to_date: Optional[date],
    mapa_reunidas: Optional[Dict[int, List[str]]] = None,
) -> float:
    return _comparativo_variacao_percentual(
        from_date, to_date, lambda a, b: get_ticket_medio_protocolado(protocolo_lexpre, a, b, mapa_reunidas)
    )


# -----------------------------------------------------------------------------
# 2 - Fila de Demandas no Pré-Protocolo (foto atual, sem filtro de período)
# -----------------------------------------------------------------------------

def get_bucket_fila_pre_protocolo(row: Dict[str, Any]) -> Optional[str]:
    """Estágio da demanda no funil de pré-protocolo (chave ASCII) — ``None`` se cancelada/inválida."""
    if not _demanda_valida(row):
        return None
    if row.get("DATA_PROTOCOLO"):
        return "protocolado"
    setor_id = row.get("SETOR_ID")
    if setor_id in SETOR_PENDENCIAS_IDS:
        return "pendencias"
    if setor_id in SETOR_PETICIONAMENTO_IDS:
        return "nao_confeccionado"
    if setor_id in SETOR_PROTOCOLO_IDS:
        return "nao_protocolado"
    if setor_id in SETOR_TRIAGEM_IDS:
        return "triagem"
    return "nao_organizado"


def get_fila_pre_protocolo_por_atendente(
    protocolo_lexpre: List[Dict[str, Any]],
    mapa_reunidas: Optional[Dict[int, List[str]]] = None,
) -> List[Dict[str, Any]]:
    """
    Fila de demandas no pré-protocolo, por atendente e estágio — foto do estado atual
    (não filtra por período: é a fila de trabalho de agora, não algo que "aconteceu"
    numa janela de datas).

    Com ``mapa_reunidas``, demandas de rubrica "reunida" contam uma vez por componente
    ativo (todos no mesmo estágio da demanda-pacote) — mesmo critério de "Ações
    Fechadas"/Protocolados, consistente em todo o dashboard Comercial.

    Formato: ``[{"name": atendente, "total": n, "Pendências": n, "Não Organizado": n,
    "Não Confeccionado": n, "Não Protocolado": n, "Protocolado": n}, ...]``, ordenado
    por total decrescente.
    """
    contagem: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in protocolo_lexpre or []:
        bucket = get_bucket_fila_pre_protocolo(row)
        if bucket is None:
            continue
        nome = _formatar_nome_atendente(row.get("ATENDENTE"))
        peso = len(_expandir_ids_para_contagem(row, mapa_reunidas))
        contagem[nome][bucket] += peso

    resultado: List[Dict[str, Any]] = []
    for nome, buckets in contagem.items():
        total = sum(buckets.values())
        item: Dict[str, Any] = {"name": nome, "total": total}
        for bucket_nome in BUCKETS_FILA_PRE_PROTOCOLO_ORDENADOS:
            item[bucket_nome] = buckets.get(bucket_nome, 0)
        resultado.append(item)

    return sorted(resultado, key=lambda item: item["total"], reverse=True)


# -----------------------------------------------------------------------------
# 3 - Valor de Causa por atendente (Protocolado x Não Protocolado)
# -----------------------------------------------------------------------------

def get_valor_causa_por_atendente(
    protocolo_lexpre: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """
    Valor de causa das demandas por atendente, separado em protocolado e não
    protocolado ("protocolado" recortado por período, "não protocolado" é foto atual — ver abaixo). "Não protocolado" segue o critério de
    `get_fila_pre_protocolo_por_atendente`/`get_bucket_fila_pre_protocolo`: "não
    protocolado" exige que a demanda esteja de fato NO setor Protocolo agora
    (``SETOR_ID in SETOR_PROTOCOLO_IDS``, um id por escritório).

    Corrigido em 11/09/2026: antes classificava só pela presença de
    ``DATA_PROTOCOLO`` (sem checar o setor atual), então uma demanda devolvida do
    Protocolo para outro setor (Org Doc, Peticionamento, Pendências) sem nunca ter
    sido protocolada continuava contando o valor de causa como "não protocolado"
    — inflando o card mesmo depois de a demanda ter saído do Protocolo. Demandas em
    outros buckets (pendências, não confeccionado, não organizado, triagem) não
    entram em nenhuma das 2 barras — o card é especificamente sobre o que está
    represado NO Protocolo (não protocolado) vs. o que esse atendente já protocolou
    (protocolado, que continua contando mesmo depois de a demanda seguir para o
    próximo setor — só marca uma conquista já obtida, não onde ela está agora).

    Todo atendente com demanda ativa nesses 2 buckets aparece no resultado, mesmo
    com valor de causa ainda zerado (nenhuma demanda com ``valor_causa`` preenchido)
    — o gráfico não some, só mostra 0 até o valor existir.

    Corrigido em 01/10/2026: a barra "protocolado" agora respeita o período
    (``from_date``/``to_date``) e usa exatamente o critério de
    `get_valor_causa_protocolado_por_atendente` (DATA_PROTOCOLO no período, status
    terminal, ANP via DANO_MORAL) — mesma base do card "Valor de Causa Protocolado"
    e do FM da Comissão. Antes era foto de toda a história (ex.: Patricia em set/2026
    aparecia com R$3,136mi, somando protocolados de outubro, contra R$2,874mi no
    FM). A barra "não protocolado" continua foto do estado atual (o que está
    represado no Protocolo agora não tem data de protocolo pra recortar).

    Formato: ``[{"name": atendente, "protocolado": R$, "nao_protocolado": R$, "total": R$}, ...]``,
    ordenado por total decrescente.
    """
    valores: Dict[str, Dict[str, float]] = defaultdict(lambda: {"protocolado": 0.0, "nao_protocolado": 0.0})
    for row in protocolo_lexpre or []:
        if get_bucket_fila_pre_protocolo(row) != "nao_protocolado":
            continue
        nome = _formatar_nome_atendente(row.get("ATENDENTE"))
        entry = valores[nome]  # garante a entrada mesmo sem valor de causa ainda

        valor = _converter_valor(row.get("VALOR_CAUSA"))
        if valor <= 0:
            continue
        entry["nao_protocolado"] += valor

    for nome, valor in get_valor_causa_protocolado_por_atendente(protocolo_lexpre, from_date, to_date).items():
        valores[nome]["protocolado"] += valor

    resultado = [
        {
            "name": nome,
            "protocolado": round(v["protocolado"], 2),
            "nao_protocolado": round(v["nao_protocolado"], 2),
            "total": round(v["protocolado"] + v["nao_protocolado"], 2),
        }
        for nome, v in valores.items()
    ]
    return sorted(resultado, key=lambda item: item["total"], reverse=True)


def get_valor_causa_protocolado_por_atendente(
    protocolo_lexpre: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> Dict[str, float]:
    """
    Valor de causa protocolado no período (por ``DATA_PROTOCOLO``), por atendente —
    base do card "Meta por Atendente" (a diferença de `get_valor_causa_por_atendente`
    é que essa aqui recorta por período em vez de ser uma foto do estado atual).

    Exige status terminal (`_is_protocolado_terminal`) e usa DANO_MORAL pra matéria
    ANP (`_valor_causa_protocolado`) — mesmo critério de `get_valor_causa_protocolado`,
    propagado aqui em 30/09/2026 pra "Meta por Atendente" não divergir do Protocolo
    LexPre pelo mesmo motivo que "Protocolados"/"Valor de Causa Protocolado" divergiam.
    """
    vistos: set = set()
    valores: Dict[str, float] = defaultdict(float)
    for row in protocolo_lexpre or []:
        if not _demanda_valida(row) or not _is_protocolado_terminal(row):
            continue
        data_protocolo = _to_date(row.get("DATA_PROTOCOLO"))
        if not data_protocolo:
            continue
        if from_date and data_protocolo < from_date:
            continue
        if to_date and data_protocolo > to_date:
            continue
        id_demanda = row.get("ID_DEMANDA")
        if id_demanda is None or id_demanda in vistos:
            continue
        vistos.add(id_demanda)
        nome = _formatar_nome_atendente(row.get("ATENDENTE"))
        valores[nome] += _valor_causa_protocolado(row)

    return {nome: round(valor, 2) for nome, valor in valores.items()}


def get_linhas_valor_causa_protocolado(
    protocolo_lexpre: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """
    Uma linha por demanda protocolada no período — mesmo critério/dedup de
    `get_valor_causa_protocolado_por_atendente`, sem agregar por atendente. Base da
    aba "Valor Protocolado (FM)" do export da Comissão Comercial (LexPre): essas
    demandas são as que entram no Fator Multiplicador do período, não na Comissão
    Base (que é por DATA_ASSINATURA — aba principal do mesmo export).

    Caso real que motivou a aba (28/10/2026): uma demanda pode assinar num mês
    (conta pra Comissão Base daquele mês) e só protocolar no mês seguinte (conta só
    pro FM do mês seguinte, não pra Base) — demanda 957 da LAAM, assinada 30/09,
    protocolada 02/10: sem esta aba, ela não aparecia em nenhuma lista exportável
    referente a outubro, mesmo entrando certinho no Valor de Causa Protocolado e no
    FM daquele mês.
    """
    vistos: set = set()
    linhas: List[Dict[str, Any]] = []
    for row in protocolo_lexpre or []:
        if not _demanda_valida(row) or not _is_protocolado_terminal(row):
            continue
        data_protocolo = _to_date(row.get("DATA_PROTOCOLO"))
        if not data_protocolo:
            continue
        if from_date and data_protocolo < from_date:
            continue
        if to_date and data_protocolo > to_date:
            continue
        id_demanda = row.get("ID_DEMANDA")
        if id_demanda is None or id_demanda in vistos:
            continue
        vistos.add(id_demanda)
        linhas.append({
            "CLIENTE": row.get("CLIENTE"),
            "ATENDENTE": _formatar_nome_atendente(row.get("ATENDENTE")),
            "UF": row.get("UF"),
            "RUBRICA": _normalizar_materia(row.get("RUBRICA")),
            "VALOR_CAUSA_PROTOCOLADO": _valor_causa_protocolado(row),
            "NUMERO_PROCESSO": row.get("NUMERO_PROCESSO"),
            "DATA_PROTOCOLO": data_protocolo,
        })
    return linhas


def get_registros_para_meta_inteligente(
    protocolo_lexpre: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Adapta as demandas protocoladas (não canceladas, de atendimentos assinados) para
    o formato esperado por ``calcular_meta_inteligente_por_atendente``
    (app.analyses.NG.ml.meta_inteligente) — mesma função usada pelo card "Meta
    Inteligente por Atendente" do dashboard Comercial NG legado, que espera
    ``ATENDENTE``, ``SAIDA`` (data do protocolo) e ``VALOR_DA_CAUSA`` por registro.

    Deduplicado por ID_DEMANDA — uma linha por demanda protocolada.

    Exige status terminal (`_is_protocolado_terminal`) e usa DANO_MORAL pra matéria
    ANP (`_valor_causa_protocolado`) — mesmo critério de `get_valor_causa_protocolado`,
    propagado aqui em 30/09/2026 pelo mesmo motivo.
    """
    vistos: set = set()
    registros: List[Dict[str, Any]] = []
    for row in protocolo_lexpre or []:
        if not _demanda_valida(row) or not _is_protocolado_terminal(row):
            continue
        if not row.get("DATA_PROTOCOLO"):
            continue
        id_demanda = row.get("ID_DEMANDA")
        if id_demanda is None or id_demanda in vistos:
            continue
        vistos.add(id_demanda)
        registros.append({
            "ATENDENTE": _formatar_nome_atendente(row.get("ATENDENTE")),
            "SAIDA": row.get("DATA_PROTOCOLO"),
            "VALOR_DA_CAUSA": _valor_causa_protocolado(row),
        })
    return registros
