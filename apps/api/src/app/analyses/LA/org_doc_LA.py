# Funções de analises do setor de organização de documentos LA

from typing import List, Dict, Any, Optional, Union
from datetime import datetime, date
from collections import defaultdict
from decimal import Decimal
from app.utils import parse_date_from_db, resolver_periodo_comparativo
from app.analyses.LA.comercial_LA import _formatar_nome_atendente
from app.analyses.LA.protocolo_LA import _converter_valor_causa

# -----------------------------------------------------------------------------
# 1 - Funções auxiliares
# -----------------------------------------------------------------------------

# Filtra processos da organização de Documentos por intervalo de datas usando a coluna SAIDA.
def _filter_by_date_range(org_documentos: List[Dict[str, Any]], from_date: date, to_date: date) -> List[Dict[str, Any]]:
    """Filtra dados da organização de documentos por intervalo de datas usando a coluna SAIDA."""
    filtered = []
    for item in org_documentos:
        try:
            saida_str = item.get("SAIDA") or item.get("saida")
            if not saida_str:
                continue
            saida_date = parse_date_from_db(saida_str)
            if not saida_date:
                continue
            if isinstance(saida_date, datetime):
                saida_date = saida_date.date()
            elif not isinstance(saida_date, date):
                continue
            if from_date <= saida_date <= to_date:
                filtered.append(item)
        except (ValueError, AttributeError, TypeError):
            continue
    return filtered

# Normalizar a matéria.
def _normalizar_materia(raw: Any) -> str:
    """Extrai a matéria: apenas a parte antes do ' - ' (ex: 'BX_ANT_FIN - BANCO BRADESCO' -> 'BX_ANT_FIN')."""
    if raw is None or raw == "":
        return "Sem materia"
    s = str(raw).strip()
    if " - " in s:
        s = s.split(" - ", 1)[0].strip()
    return s if s else "Sem materia"

# Fução que retorna os processos resolvidos.
def _filtrar_organizados(org_documentos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filtra dados da organização de documentos por processos resolvidos."""
    return [
        item for item in org_documentos
        if item.get("STATUS") and str(item.get("STATUS", "")).upper() in ["PETICIONAMENTO", "PROTOCOLO", "CONCLUIDO"]
        and (
            str(item.get("REAJUIZAMENTO", "")).upper() == "FALSE" or
            item.get("REAJUIZAMENTO") is False
        )
    ]

# Fução que retorna os processos não resolvidos.
def _filtrar_nao_organizados(org_documentos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filtra dados da organização de documentos por processos não resolvidos."""
    return [
        item for item in org_documentos
        if item.get("STATUS") and str(item.get("STATUS", "")).upper() in ["ORG DOC"]
        and (
            str(item.get("REAJUIZAMENTO", "")).upper() == "FALSE" or
            item.get("REAJUIZAMENTO") is False
        )
    ]

# Formata o nome do funcionário.
def _formatar_nome_funcionario(nome_completo: str) -> str:
    if not nome_completo or nome_completo == "Sem funcionario":
        return nome_completo

    partes = nome_completo.strip().split()
    if len(partes) == 1:
        return partes[0].upper()
    return " ".join(partes[:2]).upper()


def filter_org_doc_LA_por_materia(
    org_documentos: List[Dict[str, Any]],
    materia: Optional[Union[str, List[str]]] = None,
) -> List[Dict[str, Any]]:
    """
    Mesmo critério de :func:`group_organizados_total_por_materia_LA` /
    ``group_nao_organizados_total_por_materia_LA`` (:func:`_normalizar_materia`).
    """
    valores = materia if isinstance(materia, (list, tuple, set)) else [materia]
    alvos = {_normalizar_materia(v) for v in valores if v is not None and str(v).strip()}
    if not alvos:
        return list(org_documentos)
    return [p for p in org_documentos if _normalizar_materia(p.get("MATERIA")) in alvos]


def filter_org_doc_LA_por_funcionario(
    org_documentos: List[Dict[str, Any]],
    funcionario: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Mesmo critério de :func:`group_organizados_por_funcionario_LA`
    (:func:`_formatar_nome_funcionario`, maiúsculas).
    """
    if funcionario is None or not str(funcionario).strip():
        return list(org_documentos)
    alvo = _formatar_nome_funcionario(str(funcionario).strip())
    return [
        p for p in org_documentos
        if _formatar_nome_funcionario(p.get("FUNCIONARIO")) == alvo
    ]


def filter_org_doc_LA_por_funcionarios(
    org_documentos: List[Dict[str, Any]],
    funcionarios: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Restringe aos registros de um ou mais funcionários LA (união — OR)."""
    if not funcionarios:
        return list(org_documentos)
    alvos = {
        _formatar_nome_funcionario(str(f).strip())
        for f in funcionarios
        if f is not None and str(f).strip()
    }
    if not alvos:
        return list(org_documentos)
    return [
        p for p in org_documentos
        if _formatar_nome_funcionario(p.get("FUNCIONARIO")) in alvos
    ]


def _normalizar_uf_org_doc_LA(raw: Any) -> str:
    """Normaliza a UF vinda do banco ou da query para comparação."""
    return str(raw or "").strip().upper()


def list_ufs_org_doc_LA(org_documentos: List[Dict[str, Any]]) -> List[str]:
    """Lista única de UFs disponíveis no recorte atual de org. documentos LA."""
    vistos: set[str] = set()
    saida: List[str] = []
    for row in org_documentos or []:
        uf = _normalizar_uf_org_doc_LA(row.get("UF") or row.get("uf"))
        if not uf or uf in vistos:
            continue
        vistos.add(uf)
        saida.append(uf)
    return sorted(saida)


def filter_org_doc_LA_por_uf(
    org_documentos: List[Dict[str, Any]],
    uf: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Restringe org. documentos LA aos registros de uma UF."""
    if uf is None or not str(uf).strip():
        return list(org_documentos)
    alvo = _normalizar_uf_org_doc_LA(uf)
    return [
        p for p in org_documentos
        if _normalizar_uf_org_doc_LA(p.get("UF") or p.get("uf")) == alvo
    ]


# -----------------------------------------------------------------------------
# 2 - Funções dos cartões de analises
# -----------------------------------------------------------------------------

# Retorna a quantidade de processos não organizados.
def get_nao_organizados_LA(organizados: List[Dict[str, Any]]) -> int:
    return len(_filtrar_nao_organizados(organizados))

# Retorna a quantidade de processos organizados.
def get_total_organizados_LA(organizados: List[Dict[str, Any]]) -> int:
    return len(_filtrar_organizados(organizados))

# Retorna a quantidade de processos organizados automaticamente.
def get_total_organizados_automaticamente_LA(organizados: List[Dict[str, Any]]) -> int:
    organizados_automaticamente = [
        p for p in organizados
        if p.get("STATUS") and str(p.get("STATUS", "")).upper() in ["PETICIONAMENTO", "PROTOCOLO", "CONCLUIDO"]
        and ( str(p.get("PET_AUTO", "")).upper() == "TRUE" or p.get("PET_AUTO") is True )
    ]
    return len(organizados_automaticamente)

# Retorna a quantidade de processos organizados manualmente.
def get_total_organizados_manualmente_LA(organizados: List[Dict[str, Any]]) -> int:
    organizados_manualmente = [
        p for p in organizados
        if p.get("STATUS") and str(p.get("STATUS", "")).upper() in ["PETICIONAMENTO", "PROTOCOLO", "CONCLUIDO"]
        and ( str(p.get("PET_AUTO", "")).upper() == "FALSE" or p.get("PET_AUTO") is False )
    ]
    return len(organizados_manualmente)

# Retorna a quantidade de processos que retornaram para o setor de pendencia.
def get_retorno_pendencia_LA(organizados: List[Dict[str, Any]]) -> int:
    retornos_pendencia = [
        p for p in organizados
        if p.get("STATUS") and str(p.get("STATUS", "")).upper() in ["PENDENCIA"]
    ]
    return len(retornos_pendencia)

# Retorna a quantidade de processos cancelados.
def get_cancelados_LA(organizados: List[Dict[str, Any]]) -> int:
    cancelados = [
        p for p in organizados
        if p.get("STATUS") and str(p.get("STATUS", "")).upper() in ["CANCELADO"]
    ]
    return len(cancelados)


# -----------------------------------------------------------------------------
# 3 - Funções agrupadas por atendente
# -----------------------------------------------------------------------------

# Retorna a quantidade de processos não organizados por atendente.
def get_nao_organizados_por_atendente_LA(org_documentos: List[Dict[str, Any]]) -> Dict[str, int]:
    """Retorna a quantidade de processos não organizados por atendente."""
    org_documentos = _filtrar_nao_organizados(org_documentos)
    atendente_counts = defaultdict(int)
    for p in org_documentos:
        atendente = p.get("ATENDENTE_COMERCIAL") or "Sem atendente"
        atendente_formatado = _formatar_nome_atendente(atendente)
        atendente_counts[atendente_formatado] += 1
    return dict(atendente_counts)

# -----------------------------------------------------------------------------
# 4 - Funções agrupadas por funcionário
# -----------------------------------------------------------------------------

# Agrupa processos não organizados por funcionário responsável.
def group_nao_organizados_por_funcionario_LA(org_documentos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa processos não organizados por funcionario responsavel."""
    nao_organizados = _filtrar_nao_organizados(org_documentos)
    grouped = defaultdict(int)
    for item in nao_organizados:
        funcionario = _formatar_nome_funcionario(item.get("FUNCIONARIO"))
        grouped[funcionario] += 1
    result = [
        {"name": name, "value": int(qtd)}
        for name, qtd in grouped.items()
    ]
    return sorted(result, key=lambda x: x["value"], reverse=True)

# Agrupa processos organizados por funcionário responsável.
def group_organizados_por_funcionario_LA(org_documentos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa processos organizados por funcionario responsavel."""
    organizados = _filtrar_organizados(org_documentos)
    grouped = defaultdict(int)
    for item in organizados:
        funcionario = _formatar_nome_funcionario(item.get("FUNCIONARIO"))
        grouped[funcionario] += 1
    result = [
        {"name": name, "value": int(qtd)}
        for name, qtd in grouped.items()
    ]
    return sorted(result, key=lambda x: x["value"], reverse=True)

# Retorna o valor de causa por funcionário.
def get_valor_causa_por_funcionario_LA(org_documentos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Retorna o valor de causa por funcionario."""
    organizados = _filtrar_organizados(org_documentos)
    grouped = defaultdict(lambda: {"total": 0, "valor": 0})
    for item in organizados:
        funcionario = _formatar_nome_funcionario(item.get("FUNCIONARIO"))
        materia = str(item.get("MATERIA") or "").strip().upper()
        valor_causa = item.get("DANO_MORAL") if materia == "ANP" else (item.get("VALOR_DA_CAUSA") or item.get("VALOR_CAUSA"))
        if valor_causa is None:
            continue
        valor_convertido = _converter_valor_causa(valor_causa)
        if valor_convertido <= 0:
            continue
        grouped[funcionario]["total"] += 1
        grouped[funcionario]["valor"] += valor_convertido
    sorted_items = sorted(grouped.items(), key=lambda x: x[1]["valor"], reverse=True)
    return [{"name": nome, "value": data["valor"]} for nome, data in sorted_items]


# R$ 0,60 por resolvido, proporcional ao valor de causa expresso em milhões.
_COMISSAO_POR_RESOLVIDO_MILHAO_LA = Decimal("0.60")
_MILHAO_LA = Decimal("1000000")


def get_comissionamento_por_funcionario_LA(org_documentos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Comissão = 0,60 × QTD de resolvidos × (valor de causa gerado / 1.000.000).

    Usa as mesmas bases de `group_organizados_por_funcionario_LA` e
    `get_valor_causa_por_funcionario_LA`.

    Retorna linhas com: funcionario, qtd_resolvidos, valor_causa_gerado, valor_comissao.
    """
    por_qtd = {r["name"]: int(r["value"]) for r in group_organizados_por_funcionario_LA(org_documentos)}
    por_valor = {r["name"]: float(r["value"]) for r in get_valor_causa_por_funcionario_LA(org_documentos)}
    nomes = sorted(set(por_qtd) | set(por_valor))

    linhas: List[Dict[str, Any]] = []
    for nome in nomes:
        qtd = por_qtd.get(nome, 0)
        valor_causa = por_valor.get(nome, 0.0)
        v = Decimal(str(valor_causa))
        q = Decimal(qtd)
        comissao = _COMISSAO_POR_RESOLVIDO_MILHAO_LA * q * (v / _MILHAO_LA)
        comissao_arred = float(comissao.quantize(Decimal("0.01")))
        linhas.append({
            "funcionario": nome,
            "qtd_resolvidos": qtd,
            "valor_causa_gerado": round(valor_causa, 2),
            "valor_comissao": comissao_arred,
        })

    linhas.sort(key=lambda x: (-x["valor_comissao"], x["funcionario"]))
    return linhas


# Retorna o tempo médio (em dias) para o processo ser resolvido no setor, de forma geral.
def get_media_tempo_resolvidos_LA(org_documentos: List[Dict[str, Any]]) -> float:
    duracoes = _extrair_duracoes_dias(org_documentos)

    if not duracoes:
        return 0.0

    return round(sum(duracoes) / len(duracoes), 2)
# Função auxiliar para extrair os dias
def _extrair_duracoes_dias(org_documentos: List[Dict[str, Any]]) -> List[float]:
    protocolos_agrupados = _filtrar_organizados(org_documentos)
    duracoes: List[float] = []

    for p in protocolos_agrupados:
        try:
            entrada_str = p.get("ENTRADA") or p.get("entrada")
            saida_str = p.get("SAIDA") or p.get("saida")

            if not entrada_str or not saida_str:
                continue

            entrada_date = parse_date_from_db(entrada_str)
            saida_date = parse_date_from_db(saida_str)

            if not entrada_date or not saida_date:
                continue

            if isinstance(entrada_date, datetime):
                entrada_date = entrada_date.date()
            if isinstance(saida_date, datetime):
                saida_date = saida_date.date()

            if not isinstance(entrada_date, date) or not isinstance(saida_date, date):
                continue

            duracao_dias = (saida_date - entrada_date).days
            if duracao_dias > 0:
                duracoes.append(float(duracao_dias))

        except (ValueError, AttributeError, TypeError):
            continue

    return duracoes

# Retorna a mediana do tempo (em dias) para o processo ser resolvido no setor, de forma geral.
def get_mediana_tempo_resolvidos_LA(org_documentos: List[Dict[str, Any]]) -> float:
    duracoes = _extrair_duracoes_dias(org_documentos)

    if not duracoes:
        return 0.0

    duracoes.sort()
    n = len(duracoes)

    if n % 2 == 1:
        mediana = duracoes[n // 2]
    else:
        mediana = (duracoes[n // 2 - 1] + duracoes[n // 2]) / 2.0

    return round(mediana, 2)

# Retorna a média de processos resolvidos por funcionário.
def get_media_resolvidos_por_funcionario_LA(org_documentos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Média de processos resolvidos por funcionario."""
    resolvidos = _filtrar_organizados(org_documentos)
    grouped = defaultdict(lambda: {"total": 0, "dias": set()})
    for item in resolvidos:
        funcionario = _formatar_nome_funcionario(item.get("FUNCIONARIO"))
        saida_str = item.get("SAIDA") or item.get("saida")
        if not saida_str:
            continue
        saida_date = parse_date_from_db(saida_str)
        if not saida_date:
            continue
        grouped[funcionario]["total"] += 1
        grouped[funcionario]["dias"].add(saida_date)
    result = []
    for funcionario, stats in grouped.items():
        total = stats["total"]
        dias = len(stats["dias"])
        if dias > 0:
            media = total / dias
            result.append({"name": funcionario, "value": round(media, 2)})
    return sorted(result, key=lambda x: x["value"], reverse=True)

# -----------------------------------------------------------------------------
# 5 - Funções agrupadas por matéria
# -----------------------------------------------------------------------------

# Agrupa processos resolvidos por matéria.
def group_organizados_total_por_materia_LA(org_documentos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa processos resolvidos por matéria."""
    resolvidos = _filtrar_organizados(org_documentos)
    grouped = defaultdict(int)
    for item in resolvidos:
        materia = _normalizar_materia(item.get("MATERIA"))
        grouped[materia] += 1
    result = [
        {"name": name, "value": int(qtd)}
        for name, qtd in grouped.items()
    ]
    return sorted(result, key=lambda x: x["value"], reverse=True)

# Agrupa processos não organizados por matéria.
def group_nao_organizados_total_por_materia_LA(org_documentos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    nao_organizados = _filtrar_nao_organizados(org_documentos)
    grouped = defaultdict(int)
    for item in nao_organizados:
        materia = _normalizar_materia(item.get("MATERIA"))
        grouped[materia] += 1
    result = [
        {"name": name, "value": int(qtd)}
        for name, qtd in grouped.items()
    ]
    return sorted(result, key=lambda x: x["value"], reverse=True)

# Agrupa processos resolvidos total por matéria.
def group_resolvidos_total_por_mes_LA(org_documentos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa processos resolvidos total por matéria."""
    resolvidos = _filtrar_organizados(org_documentos)
    grouped = {}
    for item in resolvidos:
        try:
            saida_str = item.get("SAIDA") or item.get("saida")
            if not saida_str:
                continue
            saida_date = parse_date_from_db(saida_str)
            if not saida_date:
                continue
            if isinstance(saida_date, datetime):
                saida_date = saida_date.date()
            if not isinstance(saida_date, date):
                continue
            month_key = f"{saida_date.year}-{saida_date.month:02d}"
            month_names = [
                "jan", "fev", "mar", "abr", "mai", "jun",
                "jul", "ago", "set", "out", "nov", "dez"
            ]
            month_name = f"{month_names[saida_date.month - 1]} {saida_date.year}"
            if month_key not in grouped:
                grouped[month_key] = {"name": month_name, "value": 0, "sort_key": month_key}
            grouped[month_key]["value"] += 1
        except (ValueError, AttributeError, TypeError):
            continue
    result = [
        {"name": item["name"], "value": item["value"]}
        for item in sorted(grouped.values(), key=lambda x: x["sort_key"])
    ]
    return result

# Agrupa processos não organizados total por matéria.
def group_nao_organizados_total_por_mes_LA(org_documentos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa processos não organizados total por matéria."""
    nao_organizados = _filtrar_nao_organizados(org_documentos)
    grouped = {}
    month_names = [
        "jan", "fev", "mar", "abr", "mai", "jun",
        "jul", "ago", "set", "out", "nov", "dez"
    ]
    for item in nao_organizados:
        try:
            entrada_str = item.get("ENTRADA") or item.get("entrada")
            if not entrada_str:
                month_names = "_sem_data"
                if month_names not in grouped:
                    grouped[month_names] = {"name": "Sem data", "value": 0, "sort_key": "9999-99"}
                grouped[month_names]["value"] += 1
                continue
            entrada_date = parse_date_from_db(entrada_str)
            if not entrada_date:
                month_names = "_sem_data"
                if month_names not in grouped:
                    grouped[month_names] = {"name": "Sem data", "value": 0, "sort_key": "9999-99"}
                grouped[month_names]["value"] += 1
                continue
            month_key = f"{entrada_date.year}-{entrada_date.month:02d}"
            month_name = f"{month_names[entrada_date.month - 1]} {entrada_date.year}"
            if month_key not in grouped:
                grouped[month_key] = {"name": month_name, "value": 0, "sort_key": month_key}
            grouped[month_key]["value"] += 1
        except (ValueError, AttributeError, TypeError):
            if "_sem_data" not in grouped:
                grouped["_sem_data"] = {"name": "Sem data", "value": 0, "sort_key": "9999-99"}
            grouped["_sem_data"]["value"] += 1
            continue
    values = list(grouped.values())
    values.sort(key=lambda x: (0 if x["sort_key"] != "9999-99" else 1, x["sort_key"]))
    return [{"name": item["name"], "value": item["value"]} for item in values]

# Agrupa processos resolvidos por dia.
def group_resolvidos_por_dia_LA(org_documentos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    resolvidos = _filtrar_organizados(org_documentos)
    grouped = defaultdict(int)
    for item in resolvidos:
        saida_str = item.get("SAIDA") or item.get("saida")
        if not saida_str:
            continue
        saida_date = parse_date_from_db(saida_str)
        if not saida_date:
            continue
        if isinstance(saida_date, datetime):
            saida_date = saida_date.date()
        dia_str = saida_date.strftime("%Y-%m-%d")   # ← corrigido
        grouped[dia_str] += 1
    sorted_items = sorted(grouped.items(), key=lambda x: x[0])
    return [{"name": dia, "value": count} for dia, count in sorted_items]

# Retorna processos resolvidos por dia por funcionário.
def get_resolvidos_por_dia_por_funcionario_LA(org_documentos: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Retorna processos resolvidos por dia por funcionário."""
    resolvidos = _filtrar_organizados(org_documentos)
    grouped: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for item in resolvidos:
        saida_str = item.get("SAIDA") or item.get("saida")
        if not saida_str:
            continue
        saida_date = parse_date_from_db(saida_str)
        if not saida_date:
            continue
        if isinstance(saida_date, datetime):
            saida_date = saida_date.date()
        dia_str = saida_date.strftime("%Y-%m-%d")   # ← str, não date
        funcionario = item.get("FUNCIONARIO") or "Sem funcionario"
        grouped[dia_str][funcionario] += 1

    dias_ordenados = sorted(grouped.keys())
    funcionarios = sorted(
        set(f for dia_data in grouped.values() for f in dia_data.keys())
    )
    por_funcionario: Dict[str, List[Dict[str, Any]]] = {}
    for func in funcionarios:
        por_funcionario[func] = [
            {"name": dia, "value": grouped[dia].get(func, 0)}
            for dia in dias_ordenados
        ]
    return {"funcionarios": funcionarios, "por_funcionario": por_funcionario}

# -----------------------------------------------------------------------------
# 6 - Funções de comparação
# -----------------------------------------------------------------------------

# Retorna a variação percentual de processos resolvidos (período atual vs anterior).
def get_comparativo_resolvidos_total_LA(
    organizados: List[Dict[str, Any]],
    all_organizados: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    """Variação percentual de processos resolvidos (período atual vs anterior)."""
    dados_para_busca = all_organizados if all_organizados is not None else organizados
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )
    dados_periodo_atual = _filter_by_date_range(organizados, data_inicio_atual, data_fim_atual)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)
    taxa_atual = get_total_organizados_LA(dados_periodo_atual)
    taxa_anterior = get_total_organizados_LA(dados_periodo_anterior)
    if taxa_anterior == 0:
        return 0.0
    variacao = ((taxa_atual - taxa_anterior) / taxa_anterior) * 100
    return round(variacao, 2)

# Retorna a variação percentual de processos organizados manualmente (período atual vs anterior).
def get_comparativo_organizados_manualmente_LA(
    organizados: List[Dict[str, Any]],
    all_organizados: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    """Variação percentual de processos organizados manualmente (período atual vs anterior)."""
    dados_para_busca = all_organizados if all_organizados is not None else organizados
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )
    dados_periodo_atual = _filter_by_date_range(organizados, data_inicio_atual, data_fim_atual)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)
    taxa_atual = get_total_organizados_manualmente_LA(dados_periodo_atual)
    taxa_anterior = get_total_organizados_manualmente_LA(dados_periodo_anterior)
    if taxa_anterior == 0:
        return 0.0
    variacao = ((taxa_atual - taxa_anterior) / taxa_anterior) * 100
    return round(variacao, 2)

# Retorna a variação percentual de processos organizados automaticamente (período atual vs anterior).
def get_comparativo_organizados_automaticamente_LA(
    organizados: List[Dict[str, Any]],
    all_organizados: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    """Variação percentual de processos organizados automaticamente (período atual vs anterior)."""
    dados_para_busca = all_organizados if all_organizados is not None else organizados
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )
    dados_periodo_atual = _filter_by_date_range(organizados, data_inicio_atual, data_fim_atual)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)
    taxa_atual = get_total_organizados_automaticamente_LA(dados_periodo_atual)
    taxa_anterior = get_total_organizados_automaticamente_LA(dados_periodo_anterior)
    if taxa_anterior == 0:
        return 0.0
    variacao = ((taxa_atual - taxa_anterior) / taxa_anterior) * 100
    return round(variacao, 2)

# Retorna a variação percentual de processos retornados para pendência (período atual vs anterior).
def get_comparativo_retorno_pendencia_LA(
    organizados: List[Dict[str, Any]],
    all_organizados: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    """Variação percentual de processos retornados para pendência (período atual vs anterior)."""
    dados_para_busca = all_organizados if all_organizados is not None else organizados
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )
    dados_periodo_atual = _filter_by_date_range(organizados, data_inicio_atual, data_fim_atual)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)
    taxa_atual = get_retorno_pendencia_LA(dados_periodo_atual)
    taxa_anterior = get_retorno_pendencia_LA(dados_periodo_anterior)
    if taxa_anterior == 0:
        return 0.0
    variacao = ((taxa_atual - taxa_anterior) / taxa_anterior) * 100
    return round(variacao, 2)

# Retorna a variação percentual de processos cancelados (período atual vs anterior).
def get_comparativo_cancelados_LA(
    organizados: List[Dict[str, Any]],
    all_organizados: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    """Variação percentual de processos cancelados (período atual vs anterior)."""
    dados_para_busca = all_organizados if all_organizados is not None else organizados
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )
    dados_periodo_atual = _filter_by_date_range(organizados, data_inicio_atual, data_fim_atual)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)
    taxa_atual = get_cancelados_LA(dados_periodo_atual)
    taxa_anterior = get_cancelados_LA(dados_periodo_anterior)
    if taxa_anterior == 0:
        return 0.0
    variacao = ((taxa_atual - taxa_anterior) / taxa_anterior) * 100
    return round (variacao, 2)