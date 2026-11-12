"""Análises de Perfil de Clientes / Marketing — banco NG.

Fonte: perfil_clientes_NG (actions com motivo_encerramento = 11, i.e. clientes assinados)

Todas as métricas são calculadas sobre o total de linhas da query (equivalente ao
DAX `TOTAL_CLIENTES = COUNTROWS(perfil_clientes_NG)` usado como base no Power BI),
sem deduplicação por cliente.
"""
from datetime import date
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from app.utils import parse_date_from_db
from app.analyses.NG.protocolo import _converter_valor_causa, get_valor_causa_protocolo_novo


def _calc_idade(nascimento: Any) -> Optional[int]:
    d = parse_date_from_db(nascimento)
    if not d:
        return None
    hoje = date.today()
    idade = hoje.year - d.year - ((hoje.month, hoje.day) < (d.month, d.day))
    return idade if 0 <= idade <= 120 else None


def _faixa_etaria(idade: int) -> str:
    if idade < 18:
        return "< 18"
    if idade <= 24:
        return "18-24"
    if idade <= 34:
        return "25-34"
    if idade <= 44:
        return "35-44"
    return "45+"


def _contagem(
    rows: List[Dict[str, Any]],
    campo: str,
    *,
    incluir_vazios: bool = False,
    rotulo_vazio: str = "Não informado",
) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for r in rows:
        val = r.get(campo)
        nome = str(val).strip() if val is not None else ""
        if not nome:
            if not incluir_vazios:
                continue
            nome = rotulo_vazio
        counts[nome] = counts.get(nome, 0) + 1
    return counts


def _to_chart(counts: Dict[str, int]) -> List[Dict[str, Any]]:
    return [
        {"name": k, "value": v}
        for k, v in sorted(counts.items(), key=lambda x: x[1], reverse=True)
    ]


# ─── Métricas escalares ───────────────────────────────────────────────────────

def get_total_clientes(rows: List[Dict[str, Any]]) -> int:
    """TOTAL_CLIENTES = COUNTROWS(perfil_clientes_NG)."""
    return len(rows)


def get_media_idade(rows: List[Dict[str, Any]]) -> float:
    idades = [
        i for i in (_calc_idade(r.get("DATA_NASCIMENTO")) for r in rows)
        if i is not None
    ]
    return round(sum(idades) / len(idades), 2) if idades else 0.0


def get_marketing_ng_stats(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "marketing_ng_total_clientes": get_total_clientes(rows),
        "marketing_ng_media_idade": get_media_idade(rows),
    }


def _is_truthy(val: Any) -> bool:
    if isinstance(val, bool):
        return val
    if val is None:
        return False
    return str(val).strip().lower() in ("true", "t", "1", "sim", "yes")


def filtrar_triados(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """TRIADOS = CALCULATE(COUNTROWS(perfil_clientes_NG), RESP_TRIAGEM? = TRUE())."""
    return [r for r in rows if _is_truthy(r.get("RESP_TRIAGEM?"))]


# ─── Agrupamentos / gráficos ──────────────────────────────────────────────────

def group_faixa_etaria(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    counts: Dict[str, int] = {}
    for r in rows:
        idade = _calc_idade(r.get("DATA_NASCIMENTO"))
        if idade is None:
            continue
        faixa = _faixa_etaria(idade)
        counts[faixa] = counts.get(faixa, 0) + 1
    return _to_chart(counts)


def group_genero(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return _to_chart(_contagem(rows, "GENERO"))


def group_origem(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Canal de aquisição do cliente (usado no gráfico em cascata de Origem)."""
    return _to_chart(_contagem(rows, "CANAL_AQUISICAO"))


def group_ocupacao(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return _to_chart(_contagem(rows, "OCUPACAO"))


def group_tipo_trafego(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return _to_chart(_contagem(rows, "TIPO_TRAFEGO"))


def group_dispositivo(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return _to_chart(_contagem(rows, "DISPOSITIVO"))


def group_prospeccao(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return _to_chart(_contagem(rows, "PROPECCAO"))


def group_faixa_salarial(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Distribuição por faixa de média salarial mensal (usado no funil de Média Salarial).

    MEDIA_MENSAL é uma resposta categórica do formulário (ex.: "Até 2.500",
    "De 2.500 a 5.000", ...), não um valor numérico livre — por isso é agrupado
    como texto, do mesmo jeito que OCUPACAO/DISPOSITIVO/etc. Clientes sem resposta
    entram na categoria "Não informado" para bater com TOTAL_CLIENTES = COUNTROWS.
    """
    return _to_chart(_contagem(rows, "MEDIA_MENSAL", incluir_vazios=True))


def group_tipo_residencia(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return _to_chart(_contagem(rows, "TIPO_RESIDENCIA", incluir_vazios=True))


def group_pessoas_dependentes(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """PESSOAS_DEPENDENTES também é uma resposta categórica do formulário (ex.: "2 pessoas")."""
    return _to_chart(_contagem(rows, "PESSOAS_DEPENDENTES", incluir_vazios=True))


# ─── Facebook Ads ─────────────────────────────────────────────────────────────

def _parse_numero(valor_raw: Any) -> Optional[float]:
    """Converte número/Decimal ou string pt-BR/en-US (ex.: "1.500,00") para float."""
    if valor_raw is None:
        return None
    if isinstance(valor_raw, (int, float)):
        return float(valor_raw)
    valor_str = str(valor_raw).strip().replace("R$", "").replace(" ", "").replace(" ", "")
    if not valor_str:
        return None
    if "," in valor_str and "." in valor_str:
        valor_str = valor_str.replace(".", "").replace(",", ".")
    elif "," in valor_str:
        valor_str = valor_str.replace(",", ".")
    try:
        return float(valor_str)
    except (ValueError, TypeError):
        return None


def _sum_int(rows: List[Dict[str, Any]], campo: str) -> int:
    total = 0
    for r in rows:
        val = _parse_numero(r.get(campo))
        if val is None:
            continue
        total += int(round(val))
    return total


def _sum_float(rows: List[Dict[str, Any]], campo: str) -> float:
    total = 0.0
    for r in rows:
        val = _parse_numero(r.get(campo))
        if val is None:
            continue
        total += val
    return total


def get_facebook_ads_stats(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """CLIQUES/PAGEVIEW/LEADS = SUM('facebook_ads'[cliques_no_link/landing_page_view/leads])."""
    return {
        "marketing_ng_facebook_cliques": _sum_int(rows, "cliques_no_link"),
        "marketing_ng_facebook_pageview": _sum_int(rows, "landing_page_view"),
        "marketing_ng_facebook_leads": _sum_int(rows, "leads"),
    }


def group_investimento_cliques_leads(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Investimento (valor_gasto), cliques (cliques_no_link) e leads por dia (facebook_ads[date])."""
    por_dia: Dict[Any, Dict[str, float]] = {}
    for r in rows:
        dia = parse_date_from_db(r.get("date"))
        if dia is None:
            continue
        bucket = por_dia.setdefault(dia, {"investimento": 0.0, "cliques": 0.0, "leads": 0.0})
        investimento = _parse_numero(r.get("valor_gasto"))
        if investimento is not None:
            bucket["investimento"] += investimento
        cliques = _parse_numero(r.get("cliques_no_link"))
        if cliques is not None:
            bucket["cliques"] += cliques
        leads = _parse_numero(r.get("leads"))
        if leads is not None:
            bucket["leads"] += leads

    return [
        {
            "name": dia.strftime("%d/%m"),
            "investimento": round(bucket["investimento"], 2),
            "cliques": int(round(bucket["cliques"])),
            "leads": int(round(bucket["leads"])),
        }
        for dia, bucket in sorted(por_dia.items())
    ]


# ─── CAC / ROAS (Facebook Ads × pipeline comercial × protocolo) ──────────────
# QTD_CLIENTES_CAMPANHA/INDICAÇÃO vêm de actions_NG_2 (chave "actions"),
# VALOR_CAUSA_PROTOCOLO vem de setor_protocolo (chave "protocolos"), cruzado
# por ID_ACTION com os clientes fechados (MOTIVO_ENCERRAMENTO = 11) de canal
# de campanha. Como facebook_ads ainda não tem filtro de data confirmado,
# essas métricas usam os dados de actions/protocolos SEM filtro de período,
# para não misturar um numerador "todo o histórico" (valor gasto) com um
# denominador restrito ao período selecionado.

_CANAIS_CAMPANHA = {"ANUNCIO", "ANUNCIO_NG"}


def _canal_atual(row: Dict[str, Any]) -> str:
    return str(row.get("CANAL_ATUAL") or "").strip().upper()


def _action_ids_fechados_por_canal(rows: List[Dict[str, Any]], canais: Set[str]) -> Set[Any]:
    return {
        r.get("ID_ACTION")
        for r in rows
        if r.get("MOTIVO_ENCERRAMENTO") == 11 and _canal_atual(r) in canais
    }


def get_qtd_clientes_campanha(actions_rows: List[Dict[str, Any]]) -> int:
    """QTD_CLIENTES_CAMPANHA = DISTINCTCOUNT(ID_ACTION) onde MOTIVO_ENCERRAMENTO = 11
    e CANAL_ATUAL em {ANUNCIO, ANUNCIO_NG}."""
    return len(_action_ids_fechados_por_canal(actions_rows, _CANAIS_CAMPANHA))


def get_qtd_clientes_indicacao(actions_rows: List[Dict[str, Any]]) -> int:
    """QTD_CLIENTES_INDICAÇÃO = DISTINCTCOUNT(ID_ACTION) onde MOTIVO_ENCERRAMENTO = 11
    e CANAL_ATUAL = INDICAÇÃO."""
    return len(_action_ids_fechados_por_canal(actions_rows, {"INDICAÇÃO"}))


def get_valor_causa_protocolo_campanha(
    protocolos_rows: List[Dict[str, Any]],
    actions_rows: List[Dict[str, Any]],
) -> float:
    """VALOR_CAUSA_PROTOCOLO_CAMPANHA: mesma lógica de get_valor_causa_protocolo_novo
    (STATUS DISTRIBUÍDO/PROTOCOLADO, REAJUIZAMENTO = FALSE, ANP usa DANO_MORAL),
    restrito a ID_ACTION de cliente fechado (MOTIVO_ENCERRAMENTO = 11) de canal
    de campanha (ANUNCIO/ANUNCIO_NG).
    """
    action_ids = _action_ids_fechados_por_canal(actions_rows, _CANAIS_CAMPANHA)
    total = 0.0
    for p in protocolos_rows:
        if p.get("ID_ACTION") not in action_ids:
            continue

        status_ok = p.get("STATUS") and str(p.get("STATUS", "")).upper() in ["DISTRIBUÍDO", "PROTOCOLADO"]
        reajuizamento_ok = (
            str(p.get("REAJUIZAMENTO", "")).upper() == "FALSE" or
            p.get("REAJUIZAMENTO") is False
        )
        if not (status_ok and reajuizamento_ok):
            continue

        materia = str(p.get("MATERIA") or "").strip().upper()
        if materia == "ANP":
            valor_causa = p.get("DANO_MORAL")
        else:
            valor_causa = p.get("VALOR_DA_CAUSA") or p.get("VALOR_CAUSA")

        if valor_causa is None:
            continue

        valor_convertido = _converter_valor_causa(valor_causa)
        if valor_convertido > 0:
            total += valor_convertido
    return total


def _divide(numerador: float, denominador: float) -> float:
    return numerador / denominador if denominador else 0.0


def get_marketing_ng_cac_roas_stats(
    facebook_ads_rows: List[Dict[str, Any]],
    actions_rows: List[Dict[str, Any]],
    protocolos_rows: List[Dict[str, Any]],
) -> Dict[str, Any]:
    valor_gasto = _sum_float(facebook_ads_rows, "valor_gasto")
    qtd_campanha = get_qtd_clientes_campanha(actions_rows)
    qtd_indicacao = get_qtd_clientes_indicacao(actions_rows)
    valor_causa_campanha = get_valor_causa_protocolo_campanha(protocolos_rows, actions_rows)
    valor_causa_geral = get_valor_causa_protocolo_novo(protocolos_rows)

    return {
        "marketing_ng_facebook_valor_gasto": valor_gasto,
        "marketing_ng_facebook_cac_campanha": _divide(valor_gasto, qtd_campanha),
        "marketing_ng_facebook_cac_geral": _divide(valor_gasto, qtd_campanha + qtd_indicacao),
        "marketing_ng_facebook_roas_campanha": _divide(valor_causa_campanha, valor_gasto),
        "marketing_ng_facebook_roas_geral": _divide(valor_causa_geral, valor_gasto),
    }


# ─── Funil de pipeline (actions_NG_2) ─────────────────────────────────────────
# Cada etapa tem uma coluna própria em action_status marcando quando o cliente
# passou por ela (data ou flag booleana, ex.: "respondeu_onboarding"). Como
# clientes podem pular etapas, a ordem do funil é fixa (não ordenada por
# valor) — a contagem por etapa não é necessariamente decrescente.

_FUNIL_PIPELINE_ETAPAS = [
    ("ONBOARDING", "onboarding"),
    ("RESP. ONBOARDING", "respondeu_onboarding"),
    ("ETAPA 1", "data_etapa1"),
    ("RESP. ETAPA 1", "respondeu_etapa1"),
    ("ETAPA 2", "data_etapa2"),
    ("RESP. ETAPA 2", "respondeu_etapa2"),
    ("ETAPA 3", "data_etapa3"),
    ("RESP. ETAPA 3", "respondeu_etapa3"),
    ("EM ASSINATURA", "contrato_criado_em"),
]


def _passou_etapa(valor: Any) -> bool:
    """Etapa concluída se houver timestamp (não nulo) ou flag booleana verdadeira."""
    if valor is None:
        return False
    if isinstance(valor, bool):
        return valor
    return True


def group_funil_pipeline(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Funil de progressão pelo pipeline comercial (query actions_NG_2).

    A etapa final (ASSINADO) usa MOTIVO_ENCERRAMENTO = 11 — a mesma regra de
    "cliente fechado" usada em TOTAL_CLIENTES/TRIADOS — em vez de uma coluna
    de data específica.
    """
    resultado = [
        {"name": nome, "value": sum(1 for r in rows if _passou_etapa(r.get(campo)))}
        for nome, campo in _FUNIL_PIPELINE_ETAPAS
    ]
    resultado.append({
        "name": "ASSINADO",
        "value": sum(1 for r in rows if r.get("MOTIVO_ENCERRAMENTO") == 11),
    })
    return resultado


# ─── Analise_thiago (métricas RA / NG por canal_aquisicao) ───────────────────
# Fonte: query Analise_thiago. Métricas de protocolo usam SAIDA_PROTOCO como
# eixo de data (equivalente ao USERELATIONSHIP com calendario[DATA] no DAX).

_MOTIVO_ENCERRAMENTO_FECHADO = 11


def _canal_aquisicao(row: Dict[str, Any]) -> str:
    v = row.get("CANAL_AQUISICAO") or row.get("canal_aquisicao")
    return str(v or "").strip().upper()


def _motivo_encerramento(row: Dict[str, Any]) -> Any:
    if row.get("MOTIVO_ENCERRAMENTO") is not None:
        return row.get("MOTIVO_ENCERRAMENTO")
    return row.get("motivo_encerramento")


def _action_ids_fechados_por_canal_aquisicao(
    rows: List[Dict[str, Any]],
    canal: str,
) -> Set[Any]:
    canal_alvo = str(canal or "").strip().upper()
    return {
        r.get("ID_ACTION")
        for r in rows
        if _motivo_encerramento(r) == _MOTIVO_ENCERRAMENTO_FECHADO
        and _canal_aquisicao(r) == canal_alvo
        and r.get("ID_ACTION") is not None
    }


def get_qtd_clientes_campanha_ra(rows: List[Dict[str, Any]]) -> int:
    """QTD_CLIENTES_CAMPANHA_RA = DISTINCTCOUNT(ID_ACTION) com motivo_encerramento = 11
    e canal_aquisicao = ANUNCIO (Analise_thiago)."""
    return len(_action_ids_fechados_por_canal_aquisicao(rows, "ANUNCIO"))


def get_qtd_clientes_campanha_ng(rows: List[Dict[str, Any]]) -> int:
    """QTD_CLIENTES_CAMPANHA_NG = DISTINCTCOUNT(ID_ACTION) com motivo_encerramento = 11
    e canal_aquisicao = ANUNCIO_NG (Analise_thiago)."""
    return len(_action_ids_fechados_por_canal_aquisicao(rows, "ANUNCIO_NG"))


def _action_ids_por_canal_aquisicao(
    rows: List[Dict[str, Any]],
    canal: str,
) -> Set[Any]:
    canal_alvo = str(canal or "").strip().upper()
    return {
        r.get("ID_ACTION")
        for r in rows
        if _canal_aquisicao(r) == canal_alvo and r.get("ID_ACTION") is not None
    }


def get_total_leads_campanha_ra(rows: List[Dict[str, Any]]) -> int:
    """Total de leads RA = DISTINCTCOUNT(ID_ACTION) com canal_aquisicao = ANUNCIO."""
    return len(_action_ids_por_canal_aquisicao(rows, "ANUNCIO"))


def get_total_leads_campanha_ng(rows: List[Dict[str, Any]]) -> int:
    """Total de leads NG = DISTINCTCOUNT(ID_ACTION) com canal_aquisicao = ANUNCIO_NG."""
    return len(_action_ids_por_canal_aquisicao(rows, "ANUNCIO_NG"))


def get_conversao_campanha_ra(rows: List[Dict[str, Any]]) -> float:
    """Conversão RA = QTD_CLIENTES_CAMPANHA_RA / total de leads RA (em %)."""
    leads = get_total_leads_campanha_ra(rows)
    if not leads:
        return 0.0
    clientes = get_qtd_clientes_campanha_ra(rows)
    return round((clientes / leads) * 100, 2)


def get_conversao_campanha_ng(rows: List[Dict[str, Any]]) -> float:
    """Conversão NG = QTD_CLIENTES_CAMPANHA_NG / total de leads NG (em %)."""
    leads = get_total_leads_campanha_ng(rows)
    if not leads:
        return 0.0
    clientes = get_qtd_clientes_campanha_ng(rows)
    return round((clientes / leads) * 100, 2)


def _status_protocolo_resolvido(row: Dict[str, Any]) -> bool:
    status = str(row.get("STATUS_PROTOCOLO") or "").strip().upper()
    return status in {"DISTRIBUÍDO", "PROTOCOLADO"}


def _reajuizamento_false(row: Dict[str, Any]) -> bool:
    val = row.get("REAJUIZAMENTO")
    return val is False or str(val or "").strip().upper() == "FALSE"


def _saida_protocolo_preenchida(row: Dict[str, Any]) -> bool:
    raw = row.get("SAIDA_PROTOCO")
    if raw is None:
        return False
    return str(raw).strip() != ""


def _filtrar_por_saida_protocolo(
    rows: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    if not from_date and not to_date:
        return rows

    filtradas: List[Dict[str, Any]] = []
    for row in rows:
        saida = parse_date_from_db(row.get("SAIDA_PROTOCO"))
        if saida is None:
            continue
        if from_date and to_date:
            if from_date <= saida <= to_date:
                filtradas.append(row)
        elif from_date and saida >= from_date:
            filtradas.append(row)
        elif to_date and saida <= to_date:
            filtradas.append(row)
    return filtradas


def _protocolo_resolvido_saida_por_canal(
    rows: List[Dict[str, Any]],
    canal: str,
    *,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    exigir_saida_preenchida: bool = False,
) -> int:
    canal_alvo = str(canal or "").strip().upper()
    total = 0
    for row in _filtrar_por_saida_protocolo(rows, from_date, to_date):
        if _canal_aquisicao(row) != canal_alvo:
            continue
        if not _status_protocolo_resolvido(row):
            continue
        if not _reajuizamento_false(row):
            continue
        if exigir_saida_preenchida and not _saida_protocolo_preenchida(row):
            continue
        total += 1
    return total


def get_protocolo_resolvido_saida_ra(
    rows: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """PROTOCOLO_RESOLVIDO_SAIDA_RA = COUNTROWS com STATUS_PROTOCOLO em
    {DISTRIBUÍDO, PROTOCOLADO}, REAJUIZAMENTO = False, canal_aquisicao = ANUNCIO
    e SAIDA_PROTOCO preenchida; filtro opcional por data de SAIDA_PROTOCO."""
    return _protocolo_resolvido_saida_por_canal(
        rows,
        "ANUNCIO",
        from_date=from_date,
        to_date=to_date,
        exigir_saida_preenchida=True,
    )


def get_protocolo_resolvido_saida_ng(
    rows: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """PROTOCOLO_RESOLVIDO_SAIDA_NG = COUNTROWS com STATUS_PROTOCOLO em
    {DISTRIBUÍDO, PROTOCOLADO}, REAJUIZAMENTO = False, canal_aquisicao = ANUNCIO_NG;
    filtro opcional por data de SAIDA_PROTOCO."""
    return _protocolo_resolvido_saida_por_canal(
        rows,
        "ANUNCIO_NG",
        from_date=from_date,
        to_date=to_date,
    )


def _valor_causa_row_analise_thiago(row: Dict[str, Any]) -> float:
    rubrica = str(row.get("RUBRICA") or "").strip().upper()
    if rubrica == "ANP":
        valor = row.get("DANO_MORAL")
    else:
        valor = row.get("VALOR_DA_CAUSA")
    return _converter_valor_causa(valor)


def _valor_causa_protocolo_por_canal(
    rows: List[Dict[str, Any]],
    canal: str,
    *,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    canal_alvo = str(canal or "").strip().upper()
    total = 0.0
    for row in _filtrar_por_saida_protocolo(rows, from_date, to_date):
        if _canal_aquisicao(row) != canal_alvo:
            continue
        if not _status_protocolo_resolvido(row):
            continue
        if not _reajuizamento_false(row):
            continue
        valor = _valor_causa_row_analise_thiago(row)
        if valor > 0:
            total += valor
    return total


def get_valor_causa_protocolo_ra(
    rows: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """VALOR_CAUSA_PROTOCOLO_RA = SUMX com IF(RUBRICA = ANP, DANO_MORAL, VALOR_DA_CAUSA),
    STATUS_PROTOCOLO em {DISTRIBUÍDO, PROTOCOLADO}, REAJUIZAMENTO = False,
    canal_aquisicao = ANUNCIO; filtro opcional por SAIDA_PROTOCO."""
    return _valor_causa_protocolo_por_canal(
        rows,
        "ANUNCIO",
        from_date=from_date,
        to_date=to_date,
    )


def get_valor_causa_protocolo_ng(
    rows: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """VALOR_CAUSA_PROTOCOLO_NG = SUMX com IF(RUBRICA = ANP, DANO_MORAL, VALOR_DA_CAUSA),
    STATUS_PROTOCOLO em {DISTRIBUÍDO, PROTOCOLADO}, REAJUIZAMENTO = False,
    canal_aquisicao = ANUNCIO_NG; filtro opcional por SAIDA_PROTOCO."""
    return _valor_causa_protocolo_por_canal(
        rows,
        "ANUNCIO_NG",
        from_date=from_date,
        to_date=to_date,
    )


def _filtrar_por_assinatura(
    rows: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    if not from_date and not to_date:
        return rows

    filtradas: List[Dict[str, Any]] = []
    for row in rows:
        assinatura = parse_date_from_db(row.get("ASSINATURA"))
        if assinatura is None:
            continue
        if from_date and to_date:
            if from_date <= assinatura <= to_date:
                filtradas.append(row)
        elif from_date and assinatura >= from_date:
            filtradas.append(row)
        elif to_date and assinatura <= to_date:
            filtradas.append(row)
    return filtradas


def _acoes_por_canal(
    rows: List[Dict[str, Any]],
    canal: str,
    *,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    canal_alvo = str(canal or "").strip().upper()
    total = 0
    for row in _filtrar_por_assinatura(rows, from_date, to_date):
        if _motivo_encerramento(row) != _MOTIVO_ENCERRAMENTO_FECHADO:
            continue
        if row.get("STATUS") == 2:
            continue
        if not _reajuizamento_false(row):
            continue
        if _canal_aquisicao(row) != canal_alvo:
            continue
        total += 1
    return total


def get_acoes_ng(
    rows: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """ACOES_NG = COUNTROWS(Analise_thiago) com motivo_encerramento = 11,
    STATUS <> 2, REAJUIZAMENTO = False, canal_aquisicao = ANUNCIO_NG;
    filtro opcional por ASSINATURA (data de fechamento do cliente)."""
    return _acoes_por_canal(rows, "ANUNCIO_NG", from_date=from_date, to_date=to_date)


def get_acoes_ra(
    rows: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """ACOES_RA = COUNTROWS(Analise_thiago) com motivo_encerramento = 11,
    STATUS <> 2, REAJUIZAMENTO = False, canal_aquisicao = ANUNCIO;
    filtro opcional por ASSINATURA (data de fechamento do cliente)."""
    return _acoes_por_canal(rows, "ANUNCIO", from_date=from_date, to_date=to_date)


def get_ticket_medio_ng(valor_causa_ng: float, acoes_ng: int) -> float:
    """TICKET_MEDIO_NG = VALOR_CAUSA_PROTOCOLO_NG / ACOES_NG."""
    return round(valor_causa_ng / acoes_ng, 2) if acoes_ng else 0.0


def get_ticket_medio_ra(valor_causa_ra: float, acoes_ra: int) -> float:
    """TICKET_MEDIO_RA = VALOR_CAUSA_PROTOCOLO_RA / ACOES_RA."""
    return round(valor_causa_ra / acoes_ra, 2) if acoes_ra else 0.0


def group_rubrica_campanha(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Quantidade de clientes de campanha (RA/NG) por RUBRICA.

    Mesma população de QTD_CLIENTES_CAMPANHA_RA/NG (motivo_encerramento = 11,
    canal_aquisicao ANUNCIO/ANUNCIO_NG), agrupada por RUBRICA (tipo de caso) —
    usada no gráfico de barras horizontais empilhadas (RA laranja, NG azul).
    """
    counts: Dict[str, Dict[str, int]] = {}
    for r in rows:
        if _motivo_encerramento(r) != _MOTIVO_ENCERRAMENTO_FECHADO:
            continue
        canal = _canal_aquisicao(r)
        if canal == "ANUNCIO":
            chave = "ra"
        elif canal == "ANUNCIO_NG":
            chave = "ng"
        else:
            continue
        rubrica = str(r.get("RUBRICA") or "").strip() or "Não informado"
        bucket = counts.setdefault(rubrica, {"ra": 0, "ng": 0})
        bucket[chave] += 1

    itens = [{"name": rubrica, "ra": v["ra"], "ng": v["ng"]} for rubrica, v in counts.items()]
    itens.sort(key=lambda x: x["ra"] + x["ng"], reverse=True)
    return itens


def group_rubrica_protocolado(
    rows: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """Quantidade de rubricas já protocoladas (RA/NG), agrupadas por RUBRICA.

    Mesma população de PROTOCOLO_RESOLVIDO_SAIDA_RA/NG (STATUS_PROTOCOLO em
    {DISTRIBUÍDO, PROTOCOLADO}, REAJUIZAMENTO = False, filtrado por SAIDA_PROTOCO
    no período; RA exige também SAIDA_PROTOCO preenchida) — soma por canal bate
    exatamente com os totais dos cards Protocolados RA/NG.
    """
    counts: Dict[str, Dict[str, int]] = {}
    for row in _filtrar_por_saida_protocolo(rows, from_date, to_date):
        if not _status_protocolo_resolvido(row):
            continue
        if not _reajuizamento_false(row):
            continue

        canal = _canal_aquisicao(row)
        if canal == "ANUNCIO":
            if not _saida_protocolo_preenchida(row):
                continue
            chave = "ra"
        elif canal == "ANUNCIO_NG":
            chave = "ng"
        else:
            continue

        rubrica = str(row.get("RUBRICA") or "").strip() or "Não informado"
        bucket = counts.setdefault(rubrica, {"ra": 0, "ng": 0})
        bucket[chave] += 1

    itens = [{"name": rubrica, "ra": v["ra"], "ng": v["ng"]} for rubrica, v in counts.items()]
    itens.sort(key=lambda x: x["ra"] + x["ng"], reverse=True)
    return itens


# ─── Totais gerais (sem filtro de canal) — donuts RA x NG x Total ────────────

def get_qtd_clientes_campanha_total(rows: List[Dict[str, Any]]) -> int:
    """QTD_CLIENTES_CAMPANHAAAAA = DISTINCTCOUNT(ID_ACTION) com motivo_encerramento
    = 11, sem filtro de canal_aquisicao."""
    ids = {
        r.get("ID_ACTION")
        for r in rows
        if _motivo_encerramento(r) == _MOTIVO_ENCERRAMENTO_FECHADO and r.get("ID_ACTION") is not None
    }
    return len(ids)


def get_protocolo_resolvido_saida_total(
    rows: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """PROTOCOLO_RESOLVIDO_SAIDA_TOTAL = COUNTROWS(Analise_thiago) com
    STATUS_PROTOCOLO em {DISTRIBUÍDO, PROTOCOLADO}, REAJUIZAMENTO = False e
    SAIDA_PROTOCO não vazia (implícito em _filtrar_por_saida_protocolo), sem
    filtro de canal; filtro opcional por SAIDA_PROTOCO no período."""
    total = 0
    for row in _filtrar_por_saida_protocolo(rows, from_date, to_date):
        if not _status_protocolo_resolvido(row):
            continue
        if not _reajuizamento_false(row):
            continue
        total += 1
    return total


def get_valor_causa_protocolo_total(
    rows: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """VALOR_CAUSA_PROTOCOLO_TOTAL = SUM(VALOR_DA_CAUSA) com STATUS_PROTOCOLO em
    {DISTRIBUÍDO, PROTOCOLADO}, REAJUIZAMENTO = False, sem filtro de canal e sem
    a substituição RUBRICA=ANP -> DANO_MORAL (a DAX soma VALOR_DA_CAUSA puro);
    filtro opcional por SAIDA_PROTOCO no período."""
    total = 0.0
    for row in _filtrar_por_saida_protocolo(rows, from_date, to_date):
        if not _status_protocolo_resolvido(row):
            continue
        if not _reajuizamento_false(row):
            continue
        valor = _converter_valor_causa(row.get("VALOR_DA_CAUSA"))
        if valor > 0:
            total += valor
    return total


def group_total_clientes_campanha(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Donut RA x NG x Total de clientes de campanha (mesma coorte ASSINATURA
    já usada nos cards Campanha RA/NG)."""
    return [
        {"name": "RA", "value": get_qtd_clientes_campanha_ra(rows)},
        {"name": "NG", "value": get_qtd_clientes_campanha_ng(rows)},
        {"name": "Total", "value": get_qtd_clientes_campanha_total(rows)},
    ]


def group_protocolo_resolvido_total(
    rows: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """Donut RA x NG x Total de protocolos resolvidos (SAIDA_PROTOCO no período)."""
    return [
        {"name": "RA", "value": get_protocolo_resolvido_saida_ra(rows, from_date, to_date)},
        {"name": "NG", "value": get_protocolo_resolvido_saida_ng(rows, from_date, to_date)},
        {"name": "Total", "value": get_protocolo_resolvido_saida_total(rows, from_date, to_date)},
    ]


def group_valor_causa_total(
    rows: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """Donut RA x NG x Total de valor de causa protocolado (SAIDA_PROTOCO no período)."""
    return [
        {"name": "RA", "value": get_valor_causa_protocolo_ra(rows, from_date, to_date)},
        {"name": "NG", "value": get_valor_causa_protocolo_ng(rows, from_date, to_date)},
        {"name": "Total", "value": get_valor_causa_protocolo_total(rows, from_date, to_date)},
    ]


def get_total_trackeamento(rows: List[Dict[str, Any]]) -> int:
    """Total de linhas do trackeamento_NG_2 (filtrado por DATA_TRACKEAMENTO)."""
    return len(rows)


def filtrar_fechados_trackeamento(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """TOTAL_FECHADOS = linhas do trackeamento_NG_2 com MOTIVO_ENCERRAMENTO = 11
    e ASSINADO_EM não nulo (sem USERELATIONSHIP na DAX, filtra pela relação
    principal DATA_TRACKEAMENTO, já aplicada por quem chama esta função)."""
    return [
        r for r in rows
        if _motivo_encerramento(r) == _MOTIVO_ENCERRAMENTO_FECHADO and r.get("ASSINADO_EM") is not None
    ]


def get_processos_assinados_trackeamento(rows: List[Dict[str, Any]]) -> int:
    return len(filtrar_fechados_trackeamento(rows))


def _categoria_criativo(row: Dict[str, Any]) -> str:
    """Padroniza POSICIONAMENTO em Stories / Reels / Feed (restante -> (Em branco))."""
    pos = str(row.get("POSICIONAMENTO") or "").strip().lower()
    if "stor" in pos:
        return "Stories"
    if "reel" in pos:
        return "Reels"
    if "feed" in pos:
        return "Feed"
    return "(Em branco)"


def _posicionamento_padronizado(row: Dict[str, Any]) -> str:
    """Padroniza POSICIONAMENTO na plataforma: Facebook, Instagram, Bio, AN, Threads."""
    pos = str(row.get("POSICIONAMENTO") or "").strip().lower()
    if not pos:
        return "(Em branco)"
    if "facebook" in pos or "messenger" in pos:
        return "Facebook"
    if "instagram" in pos:
        return "Instagram"
    if "bio" in pos or "escritorio" in pos:
        return "Bio"
    if pos == "an":
        return "AN"
    if "thread" in pos:
        return "Threads"
    return "Outros"


def group_categoria_criativo(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    counts: Dict[str, int] = {}
    for r in rows:
        k = _categoria_criativo(r)
        counts[k] = counts.get(k, 0) + 1
    return _to_chart(counts)


def group_posicionamento_padronizado(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    counts: Dict[str, int] = {}
    for r in rows:
        k = _posicionamento_padronizado(r)
        counts[k] = counts.get(k, 0) + 1
    return _to_chart(counts)


def group_canal_aquisicao_trackeamento(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    counts: Dict[str, int] = {}
    for r in rows:
        k = _canal_aquisicao(r) or "(Em branco)"
        counts[k] = counts.get(k, 0) + 1
    return _to_chart(counts)


def group_campanha_trackeamento(rows: List[Dict[str, Any]], top_n: int = 10) -> List[Dict[str, Any]]:
    counts: Dict[str, int] = {}
    for r in rows:
        k = str(r.get("NOME_CAMPANHA") or "").strip() or "(Em branco)"
        counts[k] = counts.get(k, 0) + 1
    return _to_chart(counts)[:top_n]


def filtrar_canal_aquisicao(rows: List[Dict[str, Any]], canal: str) -> List[Dict[str, Any]]:
    canal_alvo = str(canal or "").strip().upper()
    return [r for r in rows if _canal_aquisicao(r) == canal_alvo]


def group_conjunto_trackeamento(rows: List[Dict[str, Any]], top_n: int = 10) -> List[Dict[str, Any]]:
    counts: Dict[str, int] = {}
    for r in rows:
        k = str(r.get("NOME_CONJUNTO") or "").strip() or "(Em branco)"
        counts[k] = counts.get(k, 0) + 1
    return _to_chart(counts)[:top_n]


def group_criativo_trackeamento(rows: List[Dict[str, Any]], top_n: int = 10) -> List[Dict[str, Any]]:
    counts: Dict[str, int] = {}
    for r in rows:
        k = str(r.get("CRIATIVO") or "").strip() or "(Em branco)"
        counts[k] = counts.get(k, 0) + 1
    return _to_chart(counts)[:top_n]


# ─── Ind. Orgânico de MKT — NG (Analise_thiago, canais SITE/GOOGLE/INSTAGRAM/FACEBOOK) ──

_CANAIS_ORGANICO = ("SITE", "GOOGLE", "INSTAGRAM", "FACEBOOK")


def filtrar_canais_organico(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [r for r in rows if _canal_aquisicao(r) in _CANAIS_ORGANICO]


def get_leads_por_canal(rows: List[Dict[str, Any]], canal: str) -> int:
    """Total de leads (DISTINCTCOUNT ID_ACTION) de um canal_aquisicao específico."""
    return len(_action_ids_por_canal_aquisicao(rows, canal))


def get_total_leads_organico(rows: List[Dict[str, Any]]) -> int:
    """Total de leads dos 4 canais orgânicos (SITE, GOOGLE, INSTAGRAM, FACEBOOK)."""
    ids: Set[Any] = set()
    for canal in _CANAIS_ORGANICO:
        ids |= _action_ids_por_canal_aquisicao(rows, canal)
    return len(ids)


def get_qtd_clientes_organico(rows: List[Dict[str, Any]]) -> int:
    """Contratos orgânicos = DISTINCTCOUNT(ID_ACTION) com motivo_encerramento = 11,
    canal_aquisicao em {SITE, GOOGLE, INSTAGRAM, FACEBOOK} — mesma condição usada
    em QTD_CLIENTES_CAMPANHA_RA/NG, generalizada para os 4 canais orgânicos."""
    ids: Set[Any] = set()
    for canal in _CANAIS_ORGANICO:
        ids |= _action_ids_fechados_por_canal_aquisicao(rows, canal)
    return len(ids)


def get_acoes_organico(
    rows: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """Ações orgânicas — mesma condição de ACOES_RA/NG (motivo_encerramento = 11,
    STATUS <> 2, REAJUIZAMENTO = False, filtro por ASSINATURA), somada nos 4 canais
    orgânicos."""
    return sum(
        _acoes_por_canal(rows, canal, from_date=from_date, to_date=to_date)
        for canal in _CANAIS_ORGANICO
    )


def get_valor_causa_protocolo_organico(
    rows: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """Valor de causa protocolado orgânico — mesma condição de VALOR_CAUSA_PROTOCOLO_RA/NG,
    somada nos 4 canais orgânicos."""
    return sum(
        _valor_causa_protocolo_por_canal(rows, canal, from_date=from_date, to_date=to_date)
        for canal in _CANAIS_ORGANICO
    )


def group_rubrica_organico(
    rows: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    canal: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Rubricas das ações orgânicas (mesma condição de _acoes_por_canal), agrupadas
    por RUBRICA. Sem `canal`, agrega os 4 canais orgânicos (dropdown "TOTAL");
    com `canal`, restringe a um único canal (FACEBOOK/INSTAGRAM/SITE/GOOGLE)."""
    canais = (str(canal).strip().upper(),) if canal else _CANAIS_ORGANICO
    counts: Dict[str, int] = {}
    for row in _filtrar_por_assinatura(rows, from_date, to_date):
        if _motivo_encerramento(row) != _MOTIVO_ENCERRAMENTO_FECHADO:
            continue
        if row.get("STATUS") == 2:
            continue
        if not _reajuizamento_false(row):
            continue
        if _canal_aquisicao(row) not in canais:
            continue
        rubrica = str(row.get("RUBRICA") or "").strip() or "Não informado"
        counts[rubrica] = counts.get(rubrica, 0) + 1
    return _to_chart(counts)


def group_campanha_organico(rows: List[Dict[str, Any]], top_n: int = 10) -> List[Dict[str, Any]]:
    counts: Dict[str, int] = {}
    for r in rows:
        k = str(r.get("CAMPANHA") or "").strip() or "(Em branco)"
        counts[k] = counts.get(k, 0) + 1
    return _to_chart(counts)[:top_n]


# ─── Filtros interativos (drill-down por clique nos gráficos) ────────────────

def _extrair_faixa_etaria(row: Dict[str, Any]) -> Optional[str]:
    idade = _calc_idade(row.get("DATA_NASCIMENTO"))
    return _faixa_etaria(idade) if idade is not None else None


# Cada linha-base (clientes/perfil_clientes_NG, Analise_thiago, trackeamento_NG_2)
# tem seu próprio conjunto de colunas; uma dimensão sem entrada aqui simplesmente
# não filtra aquela linha-base (não existe, não quebra).
_FIELD_MAP_CLIENTES: Dict[str, Callable[[Dict[str, Any]], Optional[str]]] = {
    "faixa_etaria": _extrair_faixa_etaria,
    "canal_aquisicao": _canal_aquisicao,
    "genero": lambda r: r.get("GENERO"),
    "tipo_trafego": lambda r: r.get("TIPO_TRAFEGO"),
    "ocupacao": lambda r: r.get("OCUPACAO"),
    "dispositivo": lambda r: r.get("DISPOSITIVO"),
    "prospeccao": lambda r: r.get("PROPECCAO"),
    "tipo_residencia": lambda r: r.get("TIPO_RESIDENCIA"),
    "pessoas_dependentes": lambda r: r.get("PESSOAS_DEPENDENTES"),
}

_FIELD_MAP_ANALISE_THIAGO: Dict[str, Callable[[Dict[str, Any]], Optional[str]]] = {
    "rubrica": lambda r: r.get("RUBRICA"),
    "categoria": _categoria_criativo,
    "posicionamento": _posicionamento_padronizado,
    "conjunto": lambda r: r.get("NOME_CONJUNTO"),
    "criativo": lambda r: r.get("CRIATIVO"),
    "campanha": lambda r: r.get("CAMPANHA"),
    "canal_aquisicao": _canal_aquisicao,
}

_FIELD_MAP_TRACKEAMENTO: Dict[str, Callable[[Dict[str, Any]], Optional[str]]] = {
    "categoria": _categoria_criativo,
    "posicionamento": _posicionamento_padronizado,
    "conjunto": lambda r: r.get("NOME_CONJUNTO"),
    "criativo": lambda r: r.get("CRIATIVO"),
    "campanha": lambda r: r.get("NOME_CAMPANHA"),
    "canal_aquisicao": _canal_aquisicao,
}


def apply_selection_filters(
    rows: List[Dict[str, Any]],
    filters: List[Tuple[str, str]],
    field_map: Dict[str, Callable[[Dict[str, Any]], Optional[str]]],
) -> List[Dict[str, Any]]:
    """Filtra `rows` pelos pares (dimensão, valor) do drill-down interativo.

    Múltiplos valores na MESMA dimensão = OR (ex.: Instagram OU Facebook);
    dimensões DIFERENTES = AND (ex.: Gênero=Feminino E Categoria=Reels).
    Uma dimensão sem entrada em `field_map` é ignorada — a linha-base não tem
    aquele campo, então esse filtro simplesmente não a afeta.
    """
    if not filters:
        return rows
    by_dim: Dict[str, Set[str]] = {}
    for dim, value in filters:
        by_dim.setdefault(str(dim), set()).add(str(value).strip().upper())
    result = rows
    for dim, values in by_dim.items():
        extractor = field_map.get(dim)
        if extractor is None:
            continue
        result = [r for r in result if str(extractor(r) or "").strip().upper() in values]
    return result
