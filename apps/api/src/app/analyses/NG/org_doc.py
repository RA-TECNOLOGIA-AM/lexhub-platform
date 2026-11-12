# Funções de analises do setor de organização de documentos

from typing import List, Dict, Any, Optional, Union
from datetime import datetime, date
from collections import defaultdict
from decimal import Decimal
from app.utils import parse_date_from_db, resolver_periodo_comparativo
from app.analyses.NG.comercial_geral import _formatar_nome_atendente
from app.analyses.NG.protocolo import _converter_valor_causa


# -----------------------------------------------------------------------------
# 1 - Funções auxiliares
# -----------------------------------------------------------------------------

# Filtra processos não organizados.
def _filtrar_nao_organizados(organizados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Retorna a lista de não organizados."""
    return [
        p for p in organizados
        if p.get("STATUS") and str(p.get("STATUS", "")).upper() in ["NÃO INICIADO", "EM ANDAMENTO", "RETORNO PET", "RETORNO"]
        and (
            str(p.get("REAJUIZAMENTO", "")).upper() == "FALSE" or
            p.get("REAJUIZAMENTO") is False
        )
    ]

# Filtra processos organização de documentos por intervalo de datas usando a coluna SAIDA.
def _filter_by_date_range(organizados: List[Dict[str, Any]], from_date: date, to_date: date) -> List[Dict[str, Any]]:
    """Filtra dados organização de documentos por intervalo de datas usando a coluna SAIDA."""
    filtered = []
    for item in organizados:
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

# Formata o nome do funcionário.
def _formatar_nome_funcionario(nome_completo: str) -> str:
    """Extrai apenas o primeiro e segundo nome da funcionario."""
    if not nome_completo or nome_completo == "Sem funcionario":
        return nome_completo

    partes = nome_completo.strip().split()
    if len(partes) == 1:
        return partes[0]
    return " ".join(partes[:2])

# Filtra processos organização de documentos resolvidos.
def _filtrar_organizados(organizados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Retorna a lista de processos organizados."""
    return [
        p for p in organizados
        if p.get("STATUS") and str(p.get("STATUS", "")).upper() in ["RESOLVIDO", "PROTOCOLAR"]
        and (
            str(p.get("REAJUIZAMENTO", "")).upper() == "FALSE" or
            p.get("REAJUIZAMENTO") is False
        )
    ]

# Filtra processos organização de documentos de reajuizamento.
def _filtrar_organizados_reajuizamento(organizados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Retorna a lista de processos organizados de reajuizamento."""
    return [
        p for p in organizados
        if p.get("STATUS") and str(p.get("STATUS", "")).upper() in ["RESOLVIDO", "PROTOCOLAR"]
        and (
            str(p.get("REAJUIZAMENTO", "")).upper() == "TRUE" or
            p.get("REAJUIZAMENTO") is True
        )
    ]

# Normaliza a matéria.
def _normalizar_materia(raw: Any) -> str:
    """Extrai a matéria: apenas a parte antes do ' - ' (ex: 'BX_ANT_FIN - BANCO BRADESCO' -> 'BX_ANT_FIN')."""
    if raw is None or raw == "":
        return "Sem materia"
    s = str(raw).strip()
    if " - " in s:
        s = s.split(" - ", 1)[0].strip()
    return s if s else "Sem materia"


def filter_org_doc_por_materia(
    organizados: List[Dict[str, Any]],
    materia: Optional[Union[str, List[str]]] = None,
) -> List[Dict[str, Any]]:
    """
    Mesmo critério de :func:`group_resolvidos_total_por_materia` e
    :func:`group_nao_organizados_total_por_materia` (:func:`_normalizar_materia`).
    """
    valores = materia if isinstance(materia, (list, tuple, set)) else [materia]
    alvos = {_normalizar_materia(v) for v in valores if v is not None and str(v).strip()}
    if not alvos:
        return list(organizados)
    return [p for p in organizados if _normalizar_materia(p.get("MATERIA")) in alvos]


def filter_org_doc_por_funcionario(
    organizados: List[Dict[str, Any]],
    funcionario: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Mesmo critério de :func:`group_resolvidos_por_funcionario` /
    :func:`group_nao_organizados_por_funcionario` (:func:`_formatar_nome_funcionario`).
    """
    if funcionario is None or not str(funcionario).strip():
        return list(organizados)
    alvo = _formatar_nome_funcionario(str(funcionario).strip())
    return [
        p for p in organizados
        if _formatar_nome_funcionario(p.get("FUNCIONARIO")) == alvo
    ]


def filter_org_doc_por_funcionarios(
    organizados: List[Dict[str, Any]],
    funcionarios: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Restringe aos registros de um ou mais funcionários (união — OR)."""
    if not funcionarios:
        return list(organizados)
    alvos = {
        _formatar_nome_funcionario(str(f).strip())
        for f in funcionarios
        if f is not None and str(f).strip()
    }
    if not alvos:
        return list(organizados)
    return [
        p for p in organizados
        if _formatar_nome_funcionario(p.get("FUNCIONARIO")) in alvos
    ]


def _normalizar_uf_org_doc(raw: Any) -> str:
    """Normaliza a UF vinda do banco ou da query para comparação."""
    return str(raw or "").strip().upper()


def list_ufs_org_doc(organizados: List[Dict[str, Any]]) -> List[str]:
    """Lista única de UFs disponíveis no recorte atual de org. documentos."""
    vistos: set[str] = set()
    saida: List[str] = []
    for row in organizados or []:
        uf = _normalizar_uf_org_doc(row.get("UF") or row.get("uf"))
        if not uf or uf in vistos:
            continue
        vistos.add(uf)
        saida.append(uf)
    return sorted(saida)


def filter_org_doc_por_uf(
    organizados: List[Dict[str, Any]],
    uf: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Restringe org. documentos aos registros de uma UF."""
    if uf is None or not str(uf).strip():
        return list(organizados)
    alvo = _normalizar_uf_org_doc(uf)
    return [
        p for p in organizados
        if _normalizar_uf_org_doc(p.get("UF") or p.get("uf")) == alvo
    ]


# -----------------------------------------------------------------------------
# 2 - Funções de Org Documentos
# -----------------------------------------------------------------------------

# Retorna a quantidade de processos não organizados.
def get_nao_organizados(organizados: List[Dict[str, Any]]) -> int:
    """Retorna a quantidade de não organizados."""
    return len(_filtrar_nao_organizados(organizados))

# Retorna a quantidade de processos resolvidos.
def get_resolvidos_total(organizados: List[Dict[str, Any]]) -> int:
    """Resolvidos total."""
    return len(_filtrar_organizados(organizados))

# Retorna a quantidade de processos resolvidos de reajuizamento.
def get_resolvidos_reajuizamento(organizados: List[Dict[str, Any]]) -> int:
    """Resolvidos de reajuizamento."""
    return len(_filtrar_organizados_reajuizamento(organizados))

# Retorna a quantidade de processos organizados manualmente.
def get_organizados_manualmente(organizados: List[Dict[str, Any]]) -> int:
    """Retorna a quantidade de processos organizados manualmente."""
    organizados_manualmente = _filtrar_organizados(organizados)
    organizados_manualmente = [
        p for p in organizados_manualmente
        if p.get("STATUS") and str(p.get("STATUS", "")).upper() == "RESOLVIDO"
    ]
    return len(organizados_manualmente)

# Retorna a quantidade de processos organizados e peticionados automaticamente.
def get_organizados_e_peticionados_automaticamente(organizados: List[Dict[str, Any]]) -> int:
    """Retorna a quantidade de processos organizados e peticionados automaticamente."""
    organizados_e_peticionados_automaticamente = _filtrar_organizados(organizados)
    organizados_e_peticionados_automaticamente = [
        p for p in organizados_e_peticionados_automaticamente
        if p.get("STATUS") and str(p.get("STATUS", "")).upper() == "PROTOCOLAR"
    ]
    return len(organizados_e_peticionados_automaticamente)

# Retorna a quantidade de processos cancelados.
def get_cancelados(organizados: List[Dict[str, Any]]) -> int:
    """Retorna a quantidade de processos cancelados."""
    cancelados = [
        p for p in organizados
        if p.get("STATUS") and str(p.get("STATUS", "")).upper() in ["CANCELADO"]
    ]
    return len(cancelados)

# Retorna a quantidade de processos que retornaram ao setor vindos do Peticionamento.
def get_retorno_pet(organizados: List[Dict[str, Any]]) -> int:
    """Retorna a quantidade de processos que retornaram ao setor vindos do Peticionamento."""
    retornos_ao_setor = [
        p for p in organizados
        if p.get("STATUS") and str(p.get("STATUS", "")).upper() in ["RETORNO PET"]
    ]
    return len(retornos_ao_setor)

# Retorna a quantidade de processos que retornaram ao setor vindos da Pendencia.
def get_retorno_pendencia(organizados: List[Dict[str, Any]]) -> int:
    """Retorna a quantidade de processos que retornaram ao setor vindos da Pendencia."""
    retornos_ao_setor = [
        p for p in organizados
        if p.get("STATUS") and str(p.get("STATUS", "")).upper() in ["RETORNO"]
    ]
    return len(retornos_ao_setor)

_MONTH_NAMES = [
    "jan", "fev", "mar", "abr", "mai", "jun",
    "jul", "ago", "set", "out", "nov", "dez"
]
_SEM_DATA_KEY = "_sem_data"
_SEM_DATA_ENTRY = {"name": "Sem data", "value": 0}
_SEM_DATA_SORT = "9999-99"

# Agrupa processos resolvidos total por mês.
def group_resolvidos_total_por_mes(organizados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa resolvidos total por mês."""
    resolvidos = _filtrar_organizados(organizados)
    grouped: Dict[str, Dict[str, Any]] = {}

    for p in resolvidos:
        try:
            saida_str = p.get("SAIDA") or p.get("saida")
            if not saida_str:
                continue
            
            saida_date = parse_date_from_db(saida_str)
            if not saida_date:
                continue

            month_key = f"{saida_date.year}-{saida_date.month:02d}"

            if month_key not in grouped:
                month_name = f"{_MONTH_NAMES[saida_date.month - 1]} {saida_date.year}"
                grouped[month_key] = {"name": month_name, "value": 0}

            grouped[month_key]["value"] += 1

        except (ValueError, AttributeError, TypeError):
            continue

    return [item for item in sorted(grouped.values(), key=lambda x: x["name"])]

def group_nao_resolvidos_total_por_mes(organizados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa não resolvidos total por mês (usa ENTRADA)."""
    nao_resolvidos = _filtrar_nao_organizados(organizados)
    grouped: Dict[str, Dict[str, Any]] = {}

    def _registrar_sem_data():
        grouped.setdefault(_SEM_DATA_KEY, {"name": "Sem data", "value": 0})
        grouped[_SEM_DATA_KEY]["value"] += 1

    for p in nao_resolvidos:
        try:
            entrada_str = p.get("ENTRADA") or p.get("entrada")
            if not entrada_str:
                _registrar_sem_data()
                continue

            entrada_date = parse_date_from_db(entrada_str)
            if not entrada_date:
                _registrar_sem_data()
                continue

            month_key = f"{entrada_date.year}-{entrada_date.month:02d}"
            if month_key not in grouped:
                month_name = f"{_MONTH_NAMES[entrada_date.month - 1]} {entrada_date.year}"
                grouped[month_key] = {"name": month_name, "value": 0}
            grouped[month_key]["value"] += 1

        except (ValueError, AttributeError, TypeError):
            _registrar_sem_data()

    def _sort_key(item: tuple) -> tuple:
        k, _ = item
        return (1, _SEM_DATA_SORT) if k == _SEM_DATA_KEY else (0, k)

    return [v for _, v in sorted(grouped.items(), key=_sort_key)]

# Agrupa processos resolvidos por dia.
def group_resolvidos_por_dia(organizados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    resolvidos = _filtrar_organizados(organizados)
    grouped = defaultdict(int)
    for p in resolvidos:
        dia = p.get("SAIDA") or p.get("saida")
        if not dia:
            continue
        dt = parse_date_from_db(dia)
        if not dt:
            continue
        dia_key = dt.strftime("%Y-%m-%d")
        grouped[dia_key] += 1
    sorted_items = sorted(grouped.items(), key=lambda x: x[0])
    return [{"name": dia, "value": count} for dia, count in sorted_items]

# -----------------------------------------------------------------------------
# 3 - Funções do comercial
# -----------------------------------------------------------------------------

# Retorna a quantidade de processos não organizados por atendente.
def get_nao_organizados_por_atendente(organizados: List[Dict[str, Any]]) -> Dict[str, int]:
    """Retorna a quantidade de processos não organizados por atendente."""
    organizados = _filtrar_nao_organizados(organizados)
    atendente_counts = defaultdict(int)
    for p in organizados:
        atendente = p.get("ATENDENTE_COMERCIAL") or "Sem atendente"
        atendente_formatado = _formatar_nome_atendente(atendente)
        atendente_counts[atendente_formatado] += 1
    return {name: int(value) for name, value in dict(atendente_counts).items()}


# -----------------------------------------------------------------------------
# 4 - Funções agrupadas por matéria
# -----------------------------------------------------------------------------

# Agrupa processos resolvidos total por matéria.
def group_resolvidos_total_por_materia(organizados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Total de processos resolvidos agrupados por MATERIA. Saída: lista de { name, value }."""
    resolvidos = _filtrar_organizados(organizados)
    grouped = defaultdict(int)
    for item in resolvidos:
        materia = _normalizar_materia(item.get("MATERIA"))
        grouped[materia] += 1
    result = [
        {"name": name, "value": int(qtd)}
        for name, qtd in grouped.items()
    ]
    return sorted(result, key=lambda x: x["value"], reverse=True)

# Agrupa processos não organizados total por matéria.
def group_nao_organizados_total_por_materia(organizados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    nao_organizados = _filtrar_nao_organizados(organizados)
    grouped = defaultdict(int)
    for item in nao_organizados:
        materia = _normalizar_materia(item.get("MATERIA"))
        grouped[materia] += 1
    result = [
        {"name": name, "value": int(qtd)}
        for name, qtd in grouped.items()
    ]
    return sorted(result, key=lambda x: x["value"], reverse=True)


# -----------------------------------------------------------------------------
# 5 - Comparativo
# -----------------------------------------------------------------------------

def get_comparativo_resolvidos_total(
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

    taxa_atual = get_resolvidos_total(dados_periodo_atual)
    taxa_anterior = get_resolvidos_total(dados_periodo_anterior)

    if taxa_anterior == 0:
        return 0.0
    variacao = ((taxa_atual - taxa_anterior) / taxa_anterior) * 100
    return round(variacao, 2)


def get_comparativo_organizados_manualmente(
    organizados: List[Dict[str, Any]],
    all_organizados: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    """Variação percentual de processos organizados manualmente."""
    dados_para_busca = all_organizados if all_organizados is not None else organizados

    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )

    dados_periodo_atual = _filter_by_date_range(organizados, data_inicio_atual, data_fim_atual)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)

    taxa_atual = get_organizados_manualmente(dados_periodo_atual)
    taxa_anterior = get_organizados_manualmente(dados_periodo_anterior)

    if taxa_anterior == 0:
        return 0.0
    variacao = ((taxa_atual - taxa_anterior) / taxa_anterior) * 100
    return round(variacao, 2)


# Retorna a variação percentual de processos organizados e peticionados automaticamente (período atual vs anterior).
def get_comparativo_organizados_e_peticionados_automaticamente(
    organizados: List[Dict[str, Any]],
    all_organizados: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    """Variação percentual de processos organizados e peticionados automaticamente."""
    dados_para_busca = all_organizados if all_organizados is not None else organizados

    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )

    dados_periodo_atual = _filter_by_date_range(organizados, data_inicio_atual, data_fim_atual)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)

    taxa_atual = get_organizados_e_peticionados_automaticamente(dados_periodo_atual)
    taxa_anterior = get_organizados_e_peticionados_automaticamente(dados_periodo_anterior)

    if taxa_anterior == 0:
        return 0.0
    variacao = ((taxa_atual - taxa_anterior) / taxa_anterior) * 100
    return round(variacao, 2)


# Retorna a variação percentual de processos resolvidos de reajuizamento (período atual vs anterior).
def get_comparativo_resolvidos_reajuizamento(
    organizados: List[Dict[str, Any]],
    all_organizados: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    """Variação percentual de processos resolvidos de reajuizamento."""
    dados_para_busca = all_organizados if all_organizados is not None else organizados

    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )

    dados_periodo_atual = _filter_by_date_range(organizados, data_inicio_atual, data_fim_atual)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)

    taxa_atual = get_resolvidos_reajuizamento(dados_periodo_atual)
    taxa_anterior = get_resolvidos_reajuizamento(dados_periodo_anterior)

    if taxa_anterior == 0:
        return 0.0
    variacao = ((taxa_atual - taxa_anterior) / taxa_anterior) * 100
    return round(variacao, 2)

# Retorna a Variação percentual de processos Cancelados do período atual vs anterior.
def get_comparativo_cancelados(
    organizados: List[Dict[str, Any]],
    all_organizados: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    """Variação percentual de processos Cancelados do período atual vs anterior."""
    dados_para_busca = all_organizados if all_organizados is not None else organizados

    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )

    dados_periodo_atual = _filter_by_date_range(organizados, data_inicio_atual, data_fim_atual)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)

    taxa_atual = get_media_tempo_resolvidos(dados_periodo_atual)
    taxa_anterior = get_media_tempo_resolvidos(dados_periodo_anterior)

    if taxa_anterior == 0:
        return 0.0
    variacao = ((taxa_atual - taxa_anterior) / taxa_anterior) * 100
    return round(variacao, 2)


# Retorna a variação percentual de tempo médio de processos resolvidos.
def get_comparativo_tempo_medio_resolvidos_org_doc(
    organizados: List[Dict[str, Any]],
    all_organizados: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    dados_para_busca = all_organizados if all_organizados is not None else organizados

    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )

    dados_periodo_atual = _filter_by_date_range(organizados, data_inicio_atual, data_fim_atual)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)

    dados_periodo_atual = get_media_tempo_resolvidos(dados_periodo_atual)
    dados_periodo_anterior = get_media_tempo_resolvidos(dados_periodo_anterior)

    if dados_periodo_anterior == 0:
        return 0.0
    variacao = ((dados_periodo_atual - dados_periodo_anterior) / dados_periodo_anterior) * 100
    return round(variacao, 2)

# -----------------------------------------------------------------------------
# 6 - Funções agrupadas por funcionários
# -----------------------------------------------------------------------------

# Agrupa processos não organizados por funcionário responsável.
def group_nao_organizados_por_funcionario(organizados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa processos não organizados por funcionario responsavel."""
    nao_organizados = _filtrar_nao_organizados(organizados)
    grouped = defaultdict(int)
    for item in nao_organizados:
        funcionario = _formatar_nome_funcionario(item.get("FUNCIONARIO"))
        grouped[funcionario] += 1
    result = [
        {"name": name, "value": int(qtd)}
        for name, qtd in grouped.items()
    ]
    return sorted(result, key=lambda x: x["value"], reverse=True)


# Agrupa processos resolvidos por funcionário.
def group_resolvidos_por_funcionario(organizados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa processos resolvidos por funcionario."""
    resolvidos = _filtrar_organizados(organizados)
    grouped = defaultdict(int)
    for item in resolvidos:
        funcionario = _formatar_nome_funcionario(item.get("FUNCIONARIO"))
        grouped[funcionario] += 1
    result = [
        {"name": name, "value": int(qtd)}
        for name, qtd in grouped.items()
    ]
    return sorted(result, key=lambda x: x["value"], reverse=True)

# Retorna a média de processos resolvidos por funcionário.
def get_media_resolvidos_por_funcionario(
    organizados: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> List[Dict[str, Any]]:
    """Média de processos resolvidos por FUNCIONARIO."""
    resolvidos = _filtrar_organizados(organizados)
    grouped = defaultdict(lambda: {"total": 0, "dias": set()})
    for item in resolvidos:
        funcionario = _formatar_nome_funcionario(item.get("FUNCIONARIO"))
        saida_str = item.get("SAIDA") or item.get("saida")

        grouped[funcionario]["total"] += 1

        if saida_str:
            try:
                saida_date = parse_date_from_db(saida_str)
                if not saida_date:
                    continue

                data_key = saida_date

                if from_date or to_date:
                    if from_date and to_date:
                        if from_date <= data_key <= to_date:
                            grouped[funcionario]["dias"].add(data_key)
                    elif from_date:
                        if data_key >= from_date:
                            grouped[funcionario]["dias"].add(data_key)
                    elif to_date:
                        if data_key <= to_date:
                            grouped[funcionario]["dias"].add(data_key)
                else:
                    grouped[funcionario]["dias"].add(data_key)
            except (ValueError, AttributeError, TypeError):
                pass

    result = []
    for funcionario, stats in grouped.items():
        total = stats["total"]
        dias = len(stats["dias"])
        if dias > 0:
            media = total / dias
            result.append({
                "name": funcionario,
                "value": round(media, 2)
            })
    return sorted(result, key=lambda x: x["value"], reverse=True)

# Retorna o valor de causa por funcionário.
def get_valor_causa_por_funcionario(organizados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Retorna o valor de causa por funcionario. Para matéria ANP usa DANO_MORAL."""
    resolvidos = _filtrar_organizados(organizados)
    grouped = defaultdict(lambda: {"total": 0, "valor": 0})
    for item in resolvidos:
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
_COMISSAO_POR_RESOLVIDO_MILHAO = Decimal("0.60")
_MILHAO = Decimal("1000000")


def get_comissionamento_por_funcionario(organizados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Comissão = 0,60 × QTD de resolvidos × (valor de causa gerado / 1.000.000).

    Usa as mesmas bases de `group_resolvidos_por_funcionario` e
    `get_valor_causa_por_funcionario` (processos resolvidos/protocolar, sem reajuizamento).

    Retorna linhas com: funcionario, qtd_resolvidos, valor_causa_gerado, valor_comissao.
    """
    por_qtd = {r["name"]: int(r["value"]) for r in group_resolvidos_por_funcionario(organizados)}
    por_valor = {r["name"]: float(r["value"]) for r in get_valor_causa_por_funcionario(organizados)}
    nomes = sorted(set(por_qtd) | set(por_valor))

    linhas: List[Dict[str, Any]] = []
    for nome in nomes:
        qtd = por_qtd.get(nome, 0)
        valor_causa = por_valor.get(nome, 0.0)
        v = Decimal(str(valor_causa))
        q = Decimal(qtd)
        comissao = _COMISSAO_POR_RESOLVIDO_MILHAO * q * (v / _MILHAO)
        comissao_arred = float(comissao.quantize(Decimal("0.01")))
        linhas.append({
            "funcionario": nome,
            "qtd_resolvidos": qtd,
            "valor_causa_gerado": round(valor_causa, 2),
            "valor_comissao": comissao_arred,
        })

    linhas.sort(key=lambda x: (-x["valor_comissao"], x["funcionario"]))
    return linhas


# Retorna processos resolvidos por dia por funcionário.
def get_resolvidos_por_dia_por_funcionario(organizados: List[Dict[str, Any]]) -> Dict[str, Any]:
    resolvidos = _filtrar_organizados(organizados)
    grouped: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for p in resolvidos:
        dia = p.get("SAIDA") or p.get("saida")
        if not dia:
            continue
        dt = parse_date_from_db(dia)
        if dt:
            dia_key = dt.strftime("%Y-%m-%d")
            funcionario = p.get("FUNCIONARIO") or "Sem funcionário"
            grouped[dia_key][funcionario] += 1
    dias_ordenados = sorted(grouped.keys())
    funcionarios = sorted(set(f for dia_data in grouped.values() for f in dia_data.keys()))
    por_funcionario: Dict[str, List[Dict[str, Any]]] = {}
    for func in funcionarios:
        por_funcionario[func] = [
            {"name": dia, "value": grouped[dia].get(func, 0)}
            for dia in dias_ordenados
        ]
    return {"funcionarios": funcionarios, "por_funcionario": por_funcionario}

# -----------------------------------------------------------------------------
# 7 - Funções de Tempo de produção
# -----------------------------------------------------------------------------

# Função auxiliar para extrair os dias
def _extrair_duracoes_dias(organizados: List[Dict[str, Any]]) -> List[float]:
    protocolos_agrupados = _filtrar_organizados(organizados)
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

# Retorna o tempo médio (em dias) para o processo ser resolvido no setor, de forma geral.
def get_media_tempo_resolvidos(organizados: List[Dict[str, Any]]) -> float:
    duracoes = _extrair_duracoes_dias(organizados)

    if not duracoes:
        return 0.0

    return round(sum(duracoes) / len(duracoes), 2)

# Retorna a mediana do tempo (em dias) para o processo ser resolvido no setor, de forma geral.
def get_mediana_tempo_resolvidos(organizados: List[Dict[str, Any]]) -> float:
    duracoes = _extrair_duracoes_dias(organizados)

    if not duracoes:
        return 0.0

    duracoes.sort()
    n = len(duracoes)

    if n % 2 == 1:
        mediana = duracoes[n // 2]
    else:
        mediana = (duracoes[n // 2 - 1] + duracoes[n // 2]) / 2.0

    return round(mediana, 2)