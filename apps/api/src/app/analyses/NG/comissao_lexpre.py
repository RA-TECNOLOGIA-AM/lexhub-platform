# Análises de comissão do Comercial (banco lexpre)
#
# Réplica das medidas de comissão do dashboard Comercial NG legado
# (comercial_geral.get_comissao_base + protocolo.get_fator_multiplicador /
# get_comissao_com_fm / get_proporcionais_am_pa_pb_sobre_comissao_com_fm),
# adaptadas à base lexpre (public.atendimento + public.demandas).
#
# A Comissão Base depende de VALOR_AM (valor de comissão fixo por rubrica),
# cadastrado em juridico.rubricas.valor_AM no banco `ng`. O equivalente no lexpre
# é public.rubricas.valor_rubrica, adicionado em 04/09/2026 (47 de 65 rubricas
# preenchidas até então — as sem valor cadastrado somam R$0, via
# `_converter_valor(None)`) e exposto na query `comercial_lexpre_NG` (queries.py)
# como "VALOR_AM".
#
# IMPORTANTE — rubrica "reunida" (pacote): o pacote em si normalmente NÃO tem
# VALOR_AM cadastrado (ex.: "RUBRICAS_BRADESCO" tem valor_rubrica NULL) — quem
# carrega a comissão são as rubricas ASSOCIADAS (ex.: "SEGURO" R$1,00, "CESTA"
# R$3,00 dentro desse pacote). Por isso, ao expandir uma demanda de pacote em um
# componente por associada (`_expandir_ids_para_contagem`, usado só para
# CONTAGEM), a comissão de cada componente usa o VALOR_AM da PRÓPRIA associada
# (`_valor_am_por_componente` + `mapa_valor_associada`), nunca o do pacote —
# senão todo componente contaria R$0.
#
# IMPORTANTE — desconto por cancelamento tardio (04/09/2026): uma demanda pode
# gerar comissão em um período (assinada/fechada) e só ser cancelada no período
# seguinte, depois de a comissão daquele período já ter sido paga. Nesse caso, o
# valor já pago precisa ser descontado da comissão do período em que o
# cancelamento efetivamente aconteceu — ver `get_desconto_cancelamentos_periodo_anterior`
# (fonte: `public.audit_log`, evento "demanda.cancelada") e
# `get_comissao_com_fm_liquida`.
from typing import Any, Dict, List, Optional, Tuple
from datetime import date
from collections import defaultdict

from app.analyses.NG.comercial_lexpre import (
    _is_assinado,
    _to_date,
    _expandir_ids_para_contagem,
    _valor_am_por_componente,
    _row_pertence_canal,
    _formatar_nome_atendente,
    STATUS_DEMANDA_CANCELADO_ID,
)
from app.analyses.NG.protocolo_lexpre import (
    _demanda_valida,
    _converter_valor,
    get_valor_causa_protocolado,
    get_valor_causa_protocolado_por_atendente,
)


def get_comissao_base(
    rows: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    mapa_reunidas: Optional[Dict[int, List[str]]] = None,
    mapa_valor_associada: Optional[Dict[str, float]] = None,
) -> float:
    """
    Comissão base = soma do VALOR_AM das ações fechadas no período — mesmo recorte de
    `comercial_lexpre.get_acoes_fechadas` (demandas não canceladas, de atendimentos
    assinados, por DATA_ASSINATURA), expandida por rubrica reunida (cada componente
    usa seu próprio VALOR_AM, não o do pacote — ver `_valor_am_por_componente`).
    """
    total = 0.0
    for row in rows or []:
        if not _is_assinado(row):
            continue
        if row.get("ID_DEMANDA") is None:
            continue
        if row.get("STATUS_DEMANDA_ID") == STATUS_DEMANDA_CANCELADO_ID:
            continue
        data_assinatura = _to_date(row.get("DATA_ASSINATURA"))
        if not data_assinatura:
            continue
        if from_date and data_assinatura < from_date:
            continue
        if to_date and data_assinatura > to_date:
            continue
        for _sub_id, nome in _expandir_ids_para_contagem(row, mapa_reunidas):
            total += _valor_am_por_componente(row, nome, mapa_valor_associada)
    return round(total, 2)


def get_fator_multiplicador_para_atingido(atingido: float) -> float:
    """
    FM (1,0 a 4,0) a partir do valor de causa protocolado (atingido) — mesma escada
    do dashboard Comercial NG legado.

    Começa a contar a partir de R$2,5M em valor de causa protocolado, e trava em 4.0
    a partir de R$4M.
    """
    a = float(atingido or 0.0)
    if a > 4_000_000:
        return 4.0
    if 2_500_000 <= a <= 4_000_000:
        return a / 1_000_000
    return 1.0


def get_fator_multiplicador(
    rows: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """FM baseado no valor de causa protocolado no período — mesma fonte do card "Valor de Causa Protocolado"."""
    atingido = get_valor_causa_protocolado(rows, from_date, to_date)
    return get_fator_multiplicador_para_atingido(atingido)


def _get_valor_por_estado(
    rows: List[Dict[str, Any]],
    ufs: set,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """
    Soma o valor de causa das demandas protocoladas no período nos UFs informados —
    mesmo recorte de `protocolo_lexpre.get_valor_causa_protocolado`, mais o filtro de
    UF (vindo de customer.uf).

    O lexpre ainda não modela "status DISTRIBUÍDO" nem "reajuizamento" (diferente do
    banco ng, onde `get_valor_por_estado_am_pa`/`_pb` filtram por esses dois campos) —
    aqui o filtro é o mesmo de "protocolado no período", que já é o equivalente lexpre
    mais próximo.
    """
    ufs_norm = {str(u).strip().upper() for u in ufs}
    vistos: set = set()
    total = 0.0
    for row in rows or []:
        if not _demanda_valida(row):
            continue
        if str(row.get("UF") or "").strip().upper() not in ufs_norm:
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
        total += _converter_valor(row.get("VALOR_CAUSA"))
    return total


def get_comissao_com_fm(
    rows: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    mapa_reunidas: Optional[Dict[int, List[str]]] = None,
    mapa_valor_associada: Optional[Dict[str, float]] = None,
) -> float:
    """Pool de comissão após o fator: COMISSAO_BASE (período) × FATOR_MULTIPLICADOR (valor de causa protocolado)."""
    fm = get_fator_multiplicador(rows, from_date, to_date)
    base = get_comissao_base(rows, from_date, to_date, mapa_reunidas, mapa_valor_associada)
    return round(fm * base, 2)


def get_rubricas_total_tabela(
    rows: List[Dict[str, Any]],
    canal: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    mapa_reunidas: Optional[Dict[int, List[str]]] = None,
    mapa_valor_associada: Optional[Dict[str, float]] = None,
) -> List[Dict[str, Any]]:
    """
    Tabela "Valor das Rubricas": por rubrica (ou componente de rubrica reunida),
    quantidade de ações fechadas no período, VALOR_AM unitário e TOTAL (soma do
    VALOR_AM por ação) — mesmo recorte e mesma expansão de reunidas de
    `get_comissao_base` (cada componente usa seu próprio VALOR_AM, não o do
    pacote — ver `_valor_am_por_componente`), agrupado por rubrica em vez de
    somado no total geral, e opcionalmente restrito a um canal de origem (mesmo
    critério de `get_acoes_fechadas_por_rubrica`). Espelha
    `comercial_geral.get_rubricas_total_tabela` (banco `ng`).
    """
    grouped: Dict[str, Dict[str, Any]] = {}
    for row in rows or []:
        if not _is_assinado(row):
            continue
        if row.get("ID_DEMANDA") is None:
            continue
        if row.get("STATUS_DEMANDA_ID") == STATUS_DEMANDA_CANCELADO_ID:
            continue
        if canal is not None and not _row_pertence_canal(row, canal):
            continue
        data_assinatura = _to_date(row.get("DATA_ASSINATURA"))
        if not data_assinatura:
            continue
        if from_date and data_assinatura < from_date:
            continue
        if to_date and data_assinatura > to_date:
            continue
        for _sub_id, nome in _expandir_ids_para_contagem(row, mapa_reunidas):
            item = grouped.setdefault(nome, {"acoes": 0, "total": 0.0})
            item["acoes"] += 1
            item["total"] += _valor_am_por_componente(row, nome, mapa_valor_associada)

    linhas: List[Dict[str, Any]] = []
    for rubrica, item in grouped.items():
        acoes = int(item["acoes"])
        total = round(item["total"], 2)
        valor_am = round(total / acoes, 2) if acoes > 0 else 0.0
        linhas.append({"rubrica": rubrica, "acoes": acoes, "valor_am": valor_am, "total": total})
    linhas.sort(key=lambda x: (-x["acoes"], str(x["rubrica"])))
    return linhas


def _desconto_cancelamentos_por_atendente(
    rows: List[Dict[str, Any]],
    cancelamentos: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    mapa_reunidas: Optional[Dict[int, List[str]]] = None,
    mapa_valor_associada: Optional[Dict[str, float]] = None,
) -> Dict[str, float]:
    """
    Desconto de comissão por cancelamento tardio (ver `get_desconto_cancelamentos_periodo_anterior`),
    agrupado por ATENDENTE (dono da demanda cancelada) — base de
    `get_desconto_cancelamentos_periodo_anterior` (soma de todos os atendentes) e da
    coluna "Desconto" de `get_comissionamento_por_atendente`.

    Sem `from_date`/`to_date` definidos, retorna vazio (sem desconto — ver função acima).
    """
    if not from_date or not to_date:
        return {}

    por_demanda: Dict[Any, Dict[str, Any]] = {}
    for row in rows or []:
        id_demanda = row.get("ID_DEMANDA")
        if id_demanda is None or id_demanda in por_demanda:
            continue
        por_demanda[id_demanda] = row

    resultado: Dict[str, float] = defaultdict(float)
    for cancelamento in cancelamentos or []:
        data_cancelamento = _to_date(cancelamento.get("DATA_CANCELAMENTO"))
        if not data_cancelamento:
            continue
        if data_cancelamento < from_date or data_cancelamento > to_date:
            continue
        row = por_demanda.get(cancelamento.get("ID_DEMANDA"))
        if row is None or not _is_assinado(row):
            continue
        data_assinatura = _to_date(row.get("DATA_ASSINATURA"))
        if not data_assinatura or data_assinatura >= from_date:
            continue
        nome = _formatar_nome_atendente(row.get("ATENDENTE"))
        for _sub_id, nome_componente in _expandir_ids_para_contagem(row, mapa_reunidas):
            resultado[nome] += _valor_am_por_componente(row, nome_componente, mapa_valor_associada)
    return {nome: round(valor, 2) for nome, valor in resultado.items()}


def get_desconto_cancelamentos_periodo_anterior(
    rows: List[Dict[str, Any]],
    cancelamentos: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    mapa_reunidas: Optional[Dict[int, List[str]]] = None,
    mapa_valor_associada: Optional[Dict[str, float]] = None,
) -> float:
    """
    Desconto de comissão por cancelamento tardio: soma o VALOR_AM de demandas cuja
    comissão já foi contabilizada em um período ANTERIOR (DATA_ASSINATURA antes de
    `from_date`) mas que foram canceladas DENTRO do período atual (`public.audit_log`,
    acao = "demanda.cancelada", entre `from_date` e `to_date`) — o valor já
    considerado pago precisa ser descontado da comissão do período em que o
    cancelamento aconteceu, não do período em que foi originalmente pago (que já
    fechou). Mesma expansão de rubrica reunida de `get_comissao_base` (cada
    componente pelo seu próprio VALOR_AM).

    Sem `from_date`/`to_date` definidos (ex.: dashboard sem período selecionado) não
    há como distinguir "período anterior" de "período atual" — retorna 0 (sem
    desconto).
    """
    por_atendente = _desconto_cancelamentos_por_atendente(
        rows, cancelamentos, from_date, to_date, mapa_reunidas, mapa_valor_associada
    )
    return round(sum(por_atendente.values()), 2)


def get_comissao_com_fm_liquida(
    rows: List[Dict[str, Any]],
    cancelamentos: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    mapa_reunidas: Optional[Dict[int, List[str]]] = None,
    mapa_valor_associada: Optional[Dict[str, float]] = None,
) -> float:
    """
    `get_comissao_com_fm` já líquida do desconto de cancelamentos tardios (ver
    `get_desconto_cancelamentos_periodo_anterior`) — o desconto é o valor cheio já
    recebido pela demanda, subtraído DEPOIS do FM (não deve sofrer o FM do período
    atual, que pode ser diferente do FM vigente quando a comissão foi paga de fato).
    """
    bruta = get_comissao_com_fm(rows, from_date, to_date, mapa_reunidas, mapa_valor_associada)
    desconto = get_desconto_cancelamentos_periodo_anterior(
        rows, cancelamentos, from_date, to_date, mapa_reunidas, mapa_valor_associada
    )
    return round(bruta - desconto, 2)


def get_comissionamento_por_atendente(
    rows: List[Dict[str, Any]],
    cancelamentos: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    mapa_reunidas: Optional[Dict[int, List[str]]] = None,
    mapa_valor_associada: Optional[Dict[str, float]] = None,
) -> List[Dict[str, Any]]:
    """
    Relatório por atendente — réplica de
    `comercial_geral.get_comercial_comissionamento_por_atendente` (banco `ng`), adaptada
    ao lexpre: ações e comissão base do atendente (mesmo recorte/expansão de reunidas de
    `get_comissao_base`); **valor_fm** (1,00-4,00) a partir do valor de causa protocolado
    DAQUELE atendente (`get_valor_causa_protocolado_por_atendente` + mesma escada de
    `get_fator_multiplicador_para_atingido` — quem não protocolou nada no período usa
    atingido 0 → FM 1,0); **comissao_com_fm** = comissao_base × valor_fm; AM/PA e PB
    repartem esse valor na mesma proporção do pool global.

    **desconto_cancelamentos** (04/09/2026): valor já comissionado ao atendente em um
    período anterior, mas cuja demanda foi cancelada dentro deste período (ver
    `_desconto_cancelamentos_por_atendente`) — coluna adicional em relação ao legado,
    mostrando o desconto atribuído a cada atendente (0 quando não há desconto).

    Campos: atendente, acoes, comissao_base, valor_fm, proporcional_am_pa,
    proporcional_pb, comissao_com_fm, desconto_cancelamentos.
    """
    por_atendente: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"acoes": 0, "comissao_base": 0.0})
    vistos: set = set()
    for row in rows or []:
        if not _is_assinado(row):
            continue
        if row.get("ID_DEMANDA") is None:
            continue
        if row.get("STATUS_DEMANDA_ID") == STATUS_DEMANDA_CANCELADO_ID:
            continue
        data_assinatura = _to_date(row.get("DATA_ASSINATURA"))
        if not data_assinatura:
            continue
        if from_date and data_assinatura < from_date:
            continue
        if to_date and data_assinatura > to_date:
            continue
        nome = _formatar_nome_atendente(row.get("ATENDENTE"))
        for sub_id, componente in _expandir_ids_para_contagem(row, mapa_reunidas):
            if sub_id in vistos:
                continue
            vistos.add(sub_id)
            por_atendente[nome]["acoes"] += 1
            por_atendente[nome]["comissao_base"] += _valor_am_por_componente(row, componente, mapa_valor_associada)

    pool = get_comissao_com_fm(rows, from_date, to_date, mapa_reunidas, mapa_valor_associada)
    _, prop_pb_total = get_proporcionais_am_pa_pb_sobre_comissao_com_fm(rows, pool, from_date, to_date)
    prop_pb_total = float(prop_pb_total or 0.0)
    frac_pb = (prop_pb_total / pool) if pool > 0 else 0.0

    valor_causa_por_atendente = get_valor_causa_protocolado_por_atendente(rows, from_date, to_date)
    desconto_por_atendente = _desconto_cancelamentos_por_atendente(
        rows, cancelamentos, from_date, to_date, mapa_reunidas, mapa_valor_associada
    )

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
            "desconto_cancelamentos": round(desconto_por_atendente.get(atendente, 0.0), 2),
        })

    linhas.sort(key=lambda x: (-x["comissao_com_fm"], str(x["atendente"])))
    return linhas


def get_proporcionais_am_pa_pb_sobre_comissao_com_fm(
    rows: List[Dict[str, Any]],
    comissao_com_fm: float,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> Tuple[float, float]:
    """
    Reparte o pool `comissao_com_fm` entre os cartões AM/PA e PB com soma exata ao
    total — mesma lógica do dashboard Comercial NG legado. A fatia de PB é
    proporcional ao valor de causa protocolado na PB sobre o valor de causa total do
    período; AM/PA absorve o restante do pool (demais UFs).
    """
    pool = float(comissao_com_fm or 0.0)
    if pool <= 0:
        return 0.0, 0.0
    valor_total = get_valor_causa_protocolado(rows, from_date, to_date)
    if valor_total <= 0:
        return round(pool, 2), 0.0

    v_pb = _get_valor_por_estado(rows, {"PB"}, from_date, to_date)
    proporcional_pb = round((v_pb / valor_total) * pool, 2)
    proporcional_pb = max(0.0, min(proporcional_pb, pool))
    proporcional_am_pa = round(pool - proporcional_pb, 2)
    return proporcional_am_pa, proporcional_pb
