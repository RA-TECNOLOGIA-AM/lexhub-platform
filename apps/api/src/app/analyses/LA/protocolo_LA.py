# Funções de analises do setor de protocolo LA

from typing import List, Dict, Any, Optional, Union
from datetime import datetime, date
from collections import defaultdict
import statistics
from decimal import Decimal
from app.utils import parse_date_from_db, resolver_periodo_comparativo
from app.analyses.LA.comercial_LA import _formatar_nome_atendente, get_comissao_base_LA

# ------------------- SUMÁRIO ---------------------------------
# 1 - Funções auxiliares
# 2 - Funções de Protocolo
# 3 - Funções do comercial
# 4 - Agrupados por Matéria
# 5 - Agrupados por Funcionários
# 6 - Agrupados por Sistema
# 7 - Tempo de produção
# 8 - Comparativos
# -------------------------------------------------------------

# -----------------------------------------------------------------------------
# 1 - Funções auxiliares
# -----------------------------------------------------------------------------

# Função para converter o valor de causa para float.
def _converter_valor_causa(valor_causa: Any) -> float:
    """
    Converte o valor da causa para float, tratando diferentes tipos de entrada.
    Suporta: Decimal, int, float, string formatada, None.
    """
    # Se o valor for None, retorna 0.0
    if valor_causa is None:
        return 0.0
    
    try:
        # Se for Decimal, converte diretamente para float
        if isinstance(valor_causa, Decimal):
            return float(valor_causa)
        # Se já for número, converte para float
        elif isinstance(valor_causa, (int, float)):
            return float(valor_causa)
        # Se for string, limpa e converte
        elif isinstance(valor_causa, str):
            # Remove espaços e caracteres especiais, mantém apenas números, ponto e vírgula
            valor_limpo = valor_causa.strip().replace(",", ".")
            # Remove qualquer caractere que não seja número ou ponto
            valor_limpo = ''.join(c for c in valor_limpo if c.isdigit() or c == '.')
            if valor_limpo:
                return float(valor_limpo)
            else:
                return 0.0  # String vazia após limpeza
        else:
            # Para outros tipos, tenta converter para string primeiro
            return float(str(valor_causa).replace(",", "."))
    except (ValueError, TypeError, AttributeError):
        # Se não conseguir converter, retorna 0.0
        return 0.0

# Protocolos por ano
def _filtrar_protocolos_por_ano(protocolos: List[Dict[str, Any]], ano: int) -> List[Dict[str, Any]]:
    """Filtra protocolos cuja data de saída (protocolo) está no ano informado."""
    filtered = []
    for p in protocolos:
        try:
            saida_str = p.get("SAIDA") or p.get("saida")
            if not saida_str:
                continue
            saida_date = parse_date_from_db(saida_str)
            if not saida_date:
                continue
            if isinstance(saida_date, datetime):
                saida_date = saida_date.date()
            elif not isinstance(saida_date, date):
                continue
            if saida_date.year == ano:
                filtered.append(p)
        except (ValueError, AttributeError, TypeError):
            continue
    return filtered

# Função auxiliar que retorna a lista filtrada de protocolos resolvidos.
def _filtrar_protocolos_resolvidos(protocolos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filtra e retorna apenas os protocolos resolvidos."""
    return [
        p for p in protocolos
        if p.get("STATUS") and str(p.get("STATUS", "")).upper() == "CONCLUIDO"
        and (
            str(p.get("REAJUIZAMENTO", "")).upper() == "FALSE"
            or p.get("REAJUIZAMENTO") is False
        )
    ]

# Função auxiliar que retorna a lista de não protocolados.
def _filtrar_protocolos_nao_protocolados(protocolos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        p for p in protocolos
        if p.get("STATUS") and str(p.get("STATUS", "")).upper() == "PROTOCOLO"
        and (
            str(p.get("REAJUIZAMENTO", "")).upper() == "FALSE"
            or p.get("REAJUIZAMENTO") is False
        )
    ]

# Meta anual de valor de causa para processos protocolados em 2026 (em reais).
META_VALOR_CAUSA_2026_LA = 240_000_000

# Função para filtrar os dados e crealizar as analises de comparativos entre o periodo atual e o periodo anterior de qualquer outra analise.
def _filter_by_date_range(data: List[Dict[str, Any]], from_date: date, to_date: date) -> List[Dict[str, Any]]:
    filtered = []
    for item in data:
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
        return partes[0].upper()
    return " ".join(partes[:2]).upper()


def _normalizar_materia(raw: Any) -> str:
    """Extrai a matéria: apenas a parte antes do ' - ' (ex: 'BX_ANT_FIN - BANCO BRADESCO' -> 'BX_ANT_FIN')."""
    if raw is None or raw == "":
        return "Sem materia"
    s = str(raw).strip()
    if " - " in s:
        s = s.split(" - ", 1)[0].strip()
    return s if s else "Sem materia"


def filter_protocolo_LA_por_materia(
    protocolos: List[Dict[str, Any]],
    materia: Optional[Union[str, List[str]]] = None,
) -> List[Dict[str, Any]]:
    """
    Mesmo critério de :func:`filter_org_doc_LA_por_materia` em ``org_doc_LA``
    (:func:`_normalizar_materia`).
    """
    valores = materia if isinstance(materia, (list, tuple, set)) else [materia]
    alvos = {_normalizar_materia(v) for v in valores if v is not None and str(v).strip()}
    if not alvos:
        return list(protocolos)
    return [p for p in protocolos if _normalizar_materia(p.get("MATERIA")) in alvos]


def filter_protocolo_LA_por_funcionario(
    protocolos: List[Dict[str, Any]],
    funcionario: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Mesmo critério de :func:`filter_org_doc_LA_por_funcionario` em ``org_doc_LA``
    (:func:`_formatar_nome_funcionario` deste módulo).
    """
    if funcionario is None or not str(funcionario).strip():
        return list(protocolos)
    alvo = _formatar_nome_funcionario(str(funcionario).strip())
    return [
        p for p in protocolos
        if _formatar_nome_funcionario(p.get("FUNCIONARIO")) == alvo
    ]


def filter_protocolo_LA_por_funcionarios(
    protocolos: List[Dict[str, Any]],
    funcionarios: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Restringe aos registros de um ou mais funcionários LA (união — OR)."""
    if not funcionarios:
        return list(protocolos)
    alvos = {
        _formatar_nome_funcionario(str(f).strip())
        for f in funcionarios
        if f is not None and str(f).strip()
    }
    if not alvos:
        return list(protocolos)
    return [
        p for p in protocolos
        if _formatar_nome_funcionario(p.get("FUNCIONARIO")) in alvos
    ]


def filter_protocolo_LA_por_sistema(
    protocolos: List[Dict[str, Any]],
    sistema: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Alinhado ao rótulo de :func:`group_protocolados_por_sistema_LA`
    (``p.get('SISTEMA') or 'Sem sistema'``).
    """
    if sistema is None or not str(sistema).strip():
        return list(protocolos)
    alvo = str(sistema).strip()
    return [
        p for p in protocolos
        if (p.get("SISTEMA") or "Sem sistema") == alvo
    ]


# -----------------------------------------------------------------------------
# 2 - Funções de Protocolo
# -----------------------------------------------------------------------------

# Retorna a quantidade de protocolos Resolvidos.
def get_protocolos_resolvidos_LA(protocolos: List[Dict[str, Any]]) -> int:
    return len(_filtrar_protocolos_resolvidos(protocolos))

# Retorna a quantidade de processos que entraram no período (pela data de ENTRADA)
# e que estão com STATUS = PROTOCOLO ou CONCLUIDO.
def get_entradas_protocolo_LA(
    all_protocolos: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> int:
    """Contagem de processos com ENTRADA dentro do período e STATUS em PROTOCOLO ou CONCLUIDO."""
    all_protocolos = [
        p for p in all_protocolos
        if str(p.get("STATUS") or "").upper() in ("PROTOCOLO", "CONCLUIDO")
    ]
    if from_date is None or to_date is None:
        return len(all_protocolos)
    entradas = 0
    for p in all_protocolos:
        try:
            entrada_str = p.get("ENTRADA") or p.get("entrada")
            if not entrada_str:
                continue
            entrada_date = parse_date_from_db(entrada_str)
            if not entrada_date:
                continue
            if isinstance(entrada_date, datetime):
                entrada_date = entrada_date.date()
            elif not isinstance(entrada_date, date):
                continue
            if from_date <= entrada_date <= to_date:
                entradas += 1
        except (ValueError, AttributeError, TypeError):
            continue
    return entradas

# Retorna a taxa de processos protocolados no período.
def get_taxa_protocolados_LA(
    protocolos: List[Dict[str, Any]],
    all_protocolos: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    """
    Taxa = (processos com SAIDA no período e CONCLUIDO) / (processos com ENTRADA no período e STATUS em PROTOCOLO ou CONCLUIDO) × 100.
    Numerador: já filtrado por SAIDA via _filter_by_date_range → get_protocolos_resolvidos_LA.
    Denominador: contagem de ENTRADA dentro do período usando all_protocolos (dataset completo),
    restrita aos processos com STATUS = PROTOCOLO ou CONCLUIDO.
    """
    saidas = get_protocolos_resolvidos_LA(protocolos)
    dados_entradas = all_protocolos if all_protocolos is not None else protocolos
    entradas = get_entradas_protocolo_LA(dados_entradas, from_date, to_date)

    if entradas == 0:
        return 0.0

    return round((saidas / entradas) * 100, 2)

# Retorna a quantidade de processos represados.
def get_protocolos_represados_LA(protocolos: List[Dict[str, Any]]) -> int:
    return len (_filtrar_protocolos_nao_protocolados(protocolos))

# Retorna a soma do valor da causa para protocolos.
def get_valor_causa_protocolado_LA(protocolos: List[Dict[str, Any]]) -> float:
    total = 0.0
    for p in protocolos:
        # Verifica se atende aos critérios
        status_ok = p.get("STATUS") and str(p.get("STATUS", "")).upper() == "CONCLUIDO"
        reajuizamento_ok = (
            str(p.get("REAJUIZAMENTO", "")).upper() == "FALSE"
            or p.get("REAJUIZAMENTO") is False
        )

        if status_ok and reajuizamento_ok:
            materia = str(p.get("MATERIA") or "").strip().upper()
            # Para matéria ANP, soma o valor da coluna DANO_MORAL; demais matérias usam valor da causa
            if materia == "ANP":
                valor_causa = p.get("DANO_MORAL")
            else:
                valor_causa = p.get("VALOR_DA_CAUSA") or p.get("VALOR_CAUSA")

            # Se o valor for None, pula para o próximo
            if valor_causa is None:
                continue
            
            # Converte o valor usando a função auxiliar
            valor_convertido = _converter_valor_causa(valor_causa)

            # Soma apenas se o valor for válido e maior que zero
            if valor_convertido > 0:
                total += valor_convertido
    
    return round(total, 2)

# Retorna o ticket medio de protocolos resolvidos.
def get_ticket_medio_protocolos_resolvidos_LA(protocolos: List[Dict[str, Any]]) -> float:
    qtd = get_protocolos_resolvidos_LA(protocolos)
    if qtd == 0:
        return 0.0
    valor = get_valor_causa_protocolado_LA(protocolos) / qtd
    return round(valor, 2)

_MONTH_NAMES = [
    "jan", "fev", "mar", "abr", "mai", "jun",
    "jul", "ago", "set", "out", "nov", "dez"
]
_SEM_DATA_KEY = "_sem_data"
_SEM_DATA_ENTRY = {"name": "Sem data", "value": 0}
_SEM_DATA_SORT = "9999-99"

# Agrupados processos protocolados por mês
def group_protocolados_por_mes_LA(protocolos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa processos Protocolados por Mês."""
    protocolos_agrupados = _filtrar_protocolos_resolvidos(protocolos)
    grouped: Dict[str, Dict[str, Any]] = {}

    for p in protocolos_agrupados:
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

    return [item for item in sorted(grouped.values(), key=lambda x: x["name"])]  # ou sort por month_key

# Agrupa o valor de causa dos processos protocolados por mês
def group_valor_causa_protocolados_por_mes_LA(protocolos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa a soma do valor de causa dos processos Protocolados por Mês."""
    protocolos_agrupados = _filtrar_protocolos_resolvidos(protocolos)
    grouped: Dict[str, Dict[str, Any]] = {}

    for p in protocolos_agrupados:
        try:
            saida_str = p.get("SAIDA") or p.get("saida")
            if not saida_str:
                continue

            saida_date = parse_date_from_db(saida_str)
            if not saida_date:
                continue

            materia = str(p.get("MATERIA") or "").strip().upper()
            valor_causa = p.get("DANO_MORAL") if materia == "ANP" else (
                p.get("VALOR_DA_CAUSA") or p.get("VALOR_CAUSA")
            )
            if valor_causa is None:
                continue

            valor_convertido = _converter_valor_causa(valor_causa)
            if valor_convertido <= 0:
                continue

            month_key = f"{saida_date.year}-{saida_date.month:02d}"

            if month_key not in grouped:
                month_name = f"{_MONTH_NAMES[saida_date.month - 1]} {saida_date.year}"
                grouped[month_key] = {"name": month_name, "value": 0.0}

            grouped[month_key]["value"] += valor_convertido

        except (ValueError, AttributeError, TypeError):
            continue

    return [
        {**item, "value": round(item["value"], 2)}
        for item in sorted(grouped.values(), key=lambda x: x["name"])
    ]

# Agrupados processos não protocolados por mês
def group_represados_por_mes_LA(protocolos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa processos não protocolados por Mês."""
    protocolos_agrupados = _filtrar_protocolos_nao_protocolados(protocolos)
    grouped: Dict[str, Dict[str, Any]] = {}

    def _registrar_sem_data():
        grouped.setdefault(_SEM_DATA_KEY, {"name": "Sem data", "value": 0})
        grouped[_SEM_DATA_KEY]["value"] += 1

    for p in protocolos_agrupados:
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

# -----------------------------------------------------------------------------
# 3 - Funções do Comercial
# -----------------------------------------------------------------------------

# Retorna a soma do valor de causa para protocolados em 2026. (METRICA DO COMERCIAL).
def get_valor_causa_protocolado_LA_2026(protocolos: List[Dict[str, Any]]) -> float:
    protocolos_2026 = _filtrar_protocolos_por_ano(protocolos, 2026)
    return get_valor_causa_protocolado_LA(protocolos_2026)

# Retorna a soma do valor de causa do protocolo por atendente.
def get_valor_causa_protocolado_por_atendente_LA(protocolos: List[Dict[str, Any]]) -> Dict[str, float]:
    """Mesma regra de `get_valor_causa_protocolado_LA`, agregada por atendente (inclui ANP → DANO_MORAL)."""
    atendente_values = defaultdict(float)
    for p in protocolos:
        status_ok = p.get("STATUS") and str(p.get("STATUS", "")).upper() == "CONCLUIDO"
        reajuizamento_ok = (
            str(p.get("REAJUIZAMENTO", "")).upper() == "FALSE"
            or p.get("REAJUIZAMENTO") is False
        )

        if status_ok and reajuizamento_ok:
            atendente = p.get("ATENDENTE") or "Sem atendente"
            atendente_formatado = _formatar_nome_atendente(atendente)
            materia = str(p.get("MATERIA") or "").strip().upper()
            if materia == "ANP":
                valor_causa = p.get("DANO_MORAL")
            else:
                valor_causa = p.get("VALOR_DA_CAUSA") or p.get("VALOR_CAUSA")
            if valor_causa is not None:
                valor_convertido = _converter_valor_causa(valor_causa)
                if valor_convertido > 0:
                    atendente_values[atendente_formatado] += valor_convertido
    return dict(atendente_values)

# Retorna a soma do valor de causa não protocolado por atendente.
# Mesma lógica do NG: retorna Dict[atendente, valor] para converter em lista de ChartDataPoint.
def get_valor_causa_nao_protocolado_por_atendente_LA(protocolos: List[Dict[str, Any]]) -> Dict[str, float]:
    protocolos_nao_protocolados = _filtrar_protocolos_nao_protocolados(protocolos)
    atendente_values = defaultdict(float)
    for p in protocolos_nao_protocolados:
        atendente = p.get("ATENDENTE") or "Sem atendente"
        atendente_formatado = _formatar_nome_atendente(atendente)
        valor_causa = p.get("VALOR_DA_CAUSA") or p.get("VALOR_CAUSA")

        if valor_causa is None:
            continue

        valor_convertido = _converter_valor_causa(valor_causa)
        if valor_convertido > 0:
            atendente_values[atendente_formatado] += valor_convertido

    return dict(atendente_values)

# Retorna a quantidade de protocolos resolvidos por atendente.
def get_protocolos_resolvidos_por_atendente_LA(protocolos: List[Dict[str, Any]]) -> Dict[str, int]:
    protocolos_resolvidos = _filtrar_protocolos_resolvidos(protocolos)
    atendente_counts = defaultdict(int)
    for p in protocolos_resolvidos:
        atendente = p.get("ATENDENTE") or "Sem atendente"
        atendente_formatado = _formatar_nome_atendente(atendente)
        atendente_counts[atendente_formatado] += 1
    return dict(atendente_counts)

# Retorna a quantidade de processos não protocolados por atendente.
def get_nao_protocolados_por_atendente_LA(protocolos: List[Dict[str, Any]]) -> Dict[str, int]:
    protocolos_nao_protocolados = _filtrar_protocolos_nao_protocolados(protocolos)
    atendente_counts = defaultdict(int)
    for p in protocolos_nao_protocolados:
        atendente = p.get("ATENDENTE") or "Sem atendente"
        atendente_formatado = _formatar_nome_atendente(atendente)
        atendente_counts[atendente_formatado] += 1
    return dict(atendente_counts)

# -----------------------------------------------------------------------------
# 4 - Agrupados por matéria
# -----------------------------------------------------------------------------
def group_protocolados_por_materia_LA(protocolos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    agrupados = _filtrar_protocolos_resolvidos(protocolos)
    # print(f"[DEBUG] group_protocolados_por_materia_LA — total filtrados: {len(agrupados)}")
    group = defaultdict(int)
    for p in agrupados:
        materia = _normalizar_materia(p.get("MATERIA"))
        group[materia] += 1
    result = [
        {"name": name, "value": int(qtd)}
        for name, qtd in group.items()
    ]
    result = sorted(result, key=lambda x: x["value"], reverse=True)
    # print(f"[DEBUG] group_protocolados_por_materia_LA — resultado ({len(result)} itens): {result[:5]}")
    return result


def group_represados_por_materia_LA(protocolos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    agrupados = _filtrar_protocolos_nao_protocolados(protocolos)
    # print(f"[DEBUG] group_represados_por_materia_LA — total filtrados: {len(agrupados)}")
    group = defaultdict(int)
    for p in agrupados:
        materia = _normalizar_materia(p.get("MATERIA"))
        group[materia] += 1
    result = [
        {"name": name, "value": int(qtd)}
        for name, qtd in group.items()
    ]
    result = sorted(result, key=lambda x: x["value"], reverse=True)
    # print(f"[DEBUG] group_represados_por_materia_LA — resultado ({len(result)} itens): {result[:5]}")
    return result

# -----------------------------------------------------------------------------
# 5 - Agrupados por Funcionários
# -----------------------------------------------------------------------------

# agrupa processos resolvidos por funcionario
def group_protocolados_por_funcionario_LA(protocolos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa processos protocolados por Funcionario."""
    protocolos_agrupados = _filtrar_protocolos_resolvidos(protocolos)
    grouped = defaultdict(int)
    for p in protocolos_agrupados:
        funcionario = _formatar_nome_funcionario(p.get("FUNCIONARIO") or "Sem funcionário")
        grouped[funcionario] += 1
    result = [
        {"name": name, "value": int(qtd)}
        for name, qtd in grouped.items()
    ]
    return sorted(result, key=lambda x: x["value"], reverse=True)

# agrupa processos não resolvidos por funcionario
def group_represados_por_funcionario_LA(protocolos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa processos protocolados por Funcionario."""
    protocolos_agrupados = _filtrar_protocolos_nao_protocolados(protocolos)
    grouped = defaultdict(int)
    for p in protocolos_agrupados:
        funcionario = _formatar_nome_funcionario(p.get("FUNCIONARIO") or "Sem funcionário")
        grouped[funcionario] += 1
    result = [
        {"name": name, "value": int(qtd)}
        for name, qtd in grouped.items()
    ]
    return sorted(result, key=lambda x: x["value"], reverse=True)

# Retorna a soma do valor de causa para protocolos por funcionário.
def get_valor_causa_protocolado_por_funcionario_LA(protocolos: List[Dict[str, Any]]) -> Dict[str, float]:
    funcionario_values = defaultdict(float)
    for p in protocolos:
        status_ok = p.get("STATUS") and str(p.get("STATUS", "")).upper() in ["CONCLUIDO"]
        reajuizamento_ok = (
            str(p.get("REAJUIZAMENTO", "")).upper() == "FALSE" or
            p.get("REAJUIZAMENTO") is False
        )
        if status_ok and reajuizamento_ok:
            funcionario = _formatar_nome_funcionario(p.get("FUNCIONARIO") or "Sem funcionário")
            materia = str(p.get("MATERIA") or "").strip().upper()
            valor_causa = p.get("DANO_MORAL") if materia == "ANP" else (p.get("VALOR_DA_CAUSA") or p.get("VALOR_CAUSA"))
            if valor_causa is not None:
                valor_convertido = _converter_valor_causa(valor_causa)
                if valor_convertido > 0:
                    funcionario_values[funcionario] += valor_convertido
    return dict(funcionario_values)


def _valor_comissao_por_protocolo_LA(taxa: float) -> Decimal:
    """Retorna o valor de comissão por processo protocolado conforme a taxa atingida."""
    if taxa >= 97.0:
        return Decimal("3.00")
    if taxa >= 85.0:
        return Decimal("1.50")
    return Decimal("0.50")


def get_protocolo_comissionamento_por_funcionario_LA(
    protocolos: List[Dict[str, Any]],
    taxa: float = 0.0,
) -> List[Dict[str, Any]]:
    """
    Comissão por processo protocolado (resolvido), escalonada pela taxa:
      ≥ 97% → R$ 3,00 | 85–96% → R$ 1,50 | até 84% → R$ 0,50.

    Retorna linhas com: funcionario, qtd_protocolados, valor_comissao.
    """
    valor_unit = _valor_comissao_por_protocolo_LA(taxa)
    linhas: List[Dict[str, Any]] = []
    for r in group_protocolados_por_funcionario_LA(protocolos):
        nome = r["name"]
        qtd = int(r["value"])
        comissao = (valor_unit * Decimal(qtd)).quantize(Decimal("0.01"))
        linhas.append({
            "funcionario": nome,
            "qtd_protocolados": qtd,
            "comissao_unitaria": float(valor_unit),
            "valor_comissao": float(comissao),
        })

    linhas.sort(key=lambda x: (-x["valor_comissao"], x["funcionario"]))
    return linhas


# Retorna a média de processos resolvidos por funcionário.
def get_media_protocolados_por_funcionario_LA(
    protocolos: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> List[Dict[str, Any]]:
    """Média de processos protocolados por FUNCIONARIO."""
    protocolos_agrupados = _filtrar_protocolos_resolvidos(protocolos)
    grouped = defaultdict(lambda: {"total": 0, "dias": set()})
    for p in protocolos_agrupados:
        funcionario = _formatar_nome_funcionario(p.get("FUNCIONARIO") or "Sem funcionário")
        saida_str = p.get("SAIDA") or p.get("saida")

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

# Retorna processos protocolados por dia por funcionário.
def get_protocolados_por_dia_por_funcionario_LA(protocolos: List[Dict[str, Any]]) -> Dict[str, Any]:
    protocolos_agrupados = _filtrar_protocolos_resolvidos(protocolos)
    # grouped[dia][funcionario] = count
    grouped: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for p in protocolos_agrupados:
        saida_str = p.get("SAIDA") or p.get("saida")
        if not saida_str:
            continue
        dt = parse_date_from_db(saida_str)
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

# agrupa processos protocolados por dia.
def group_protocolados_por_dia_LA(protocolos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa processos protocolados por dia. Retorna lista [{ name, value }, ...] ordenada por data."""
    protocolos_agrupados = _filtrar_protocolos_resolvidos(protocolos)
    grouped = defaultdict(int)
    for p in protocolos_agrupados:
        saida_str = p.get("SAIDA") or p.get("saida")
        if not saida_str:
            continue
        dt = parse_date_from_db(saida_str)
        if dt:
            dia_key = dt.strftime("%Y-%m-%d")
            grouped[dia_key] += 1
    sorted_items = sorted(grouped.items(), key=lambda x: x[0])
    return [{"name": dia, "value": count} for dia, count in sorted_items]


def group_valor_causa_protocolados_por_dia_LA(protocolos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa a soma do valor de causa dos processos protocolados por dia."""
    protocolos_agrupados = _filtrar_protocolos_resolvidos(protocolos)
    grouped = defaultdict(float)
    for p in protocolos_agrupados:
        saida_str = p.get("SAIDA") or p.get("saida")
        if not saida_str:
            continue

        dt = parse_date_from_db(saida_str)
        if not dt:
            continue

        materia = str(p.get("MATERIA") or "").strip().upper()
        valor_causa = p.get("DANO_MORAL") if materia == "ANP" else (
            p.get("VALOR_DA_CAUSA") or p.get("VALOR_CAUSA")
        )
        if valor_causa is None:
            continue

        valor_convertido = _converter_valor_causa(valor_causa)
        if valor_convertido <= 0:
            continue

        dia_key = dt.strftime("%Y-%m-%d")
        grouped[dia_key] += valor_convertido

    sorted_items = sorted(grouped.items(), key=lambda x: x[0])
    return [{"name": dia, "value": round(valor, 2)} for dia, valor in sorted_items]

# -----------------------------------------------------------------------------
# 6 - Agrupados por Sistema
# -----------------------------------------------------------------------------

# Agrupa processos protocolados por Sistema.
def group_protocolados_por_sistema_LA(protocolos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa processos protocolados por Sistema."""
    protocolos_agrupados = _filtrar_protocolos_resolvidos(protocolos)
    grouped = defaultdict(int)
    for p in protocolos_agrupados:
        sistema = p.get("SISTEMA") or "Sem sistema"
        grouped[sistema] += 1
    result = [
        {"name": name, "value": int(qtd)}
        for name, qtd in grouped.items()
    ]
    return sorted(result, key=lambda x: x["value"], reverse=True)

# -----------------------------------------------------------------------------
# 7 - Funções de Tempo de produção
# -----------------------------------------------------------------------------

# Função auxiliar para extrair os dias
def _extrair_duracoes_dias(protocolos: List[Dict[str, Any]]) -> List[float]:
    protocolos_agrupados = _filtrar_protocolos_resolvidos(protocolos)
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

# Retorna o tempo médio (em dias) para o processo protocolado no setor, de forma geral.
def get_media_tempo_protocolado_LA(protocolos: List[Dict[str, Any]]) -> float:
    duracoes = _extrair_duracoes_dias(protocolos)

    if not duracoes:
        return 0.0

    return round(sum(duracoes) / len(duracoes), 2)

# Retorna a mediana do tempo (em dias) para o processo protocolado no setor, de forma geral.
def get_mediana_tempo_protocolado_LA(protocolos: List[Dict[str, Any]]) -> float:
    duracoes = _extrair_duracoes_dias(protocolos)

    if not duracoes:
        return 0.0

    duracoes.sort()
    n = len(duracoes)

    if n % 2 == 1:
        mediana = duracoes[n // 2]
    else:
        mediana = (duracoes[n // 2 - 1] + duracoes[n // 2]) / 2.0

    return round(mediana, 2)

# -----------------------------------------------------------------------------
# 5 - Funções de Comparativos
# -----------------------------------------------------------------------------

def _valor_periodo_anterior_protocolo_LA(
    protocolos: List[Dict[str, Any]],
    all_protocolos: Optional[List[Dict[str, Any]]],
    from_date: Optional[date],
    to_date: Optional[date],
    metrica_fn,
) -> float:
    """
    Valor absoluto da métrica no período anterior (mesmo recorte de calendário
    usado pelas funções ``get_comparativo_*_LA``).

    Necessário porque o Estratégico Geral combina NG+LA+RJ somando os valores
    absolutos de cada escritório antes de calcular UM percentual combinado —
    nunca somando os percentuais de cada escritório entre si (matematicamente
    inválido: dois +30% de bases diferentes não fazem um +60% combinado).
    """
    dados_para_busca = all_protocolos if all_protocolos is not None else protocolos
    _, _, data_inicio_anterior, data_fim_anterior = resolver_periodo_comparativo(from_date, to_date)
    return metrica_fn(
        _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)
    )


def get_protocolos_resolvidos_periodo_anterior_LA(
    protocolos: List[Dict[str, Any]],
    all_protocolos: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    return _valor_periodo_anterior_protocolo_LA(
        protocolos, all_protocolos, from_date, to_date, get_protocolos_resolvidos_LA
    )


def get_valor_causa_protocolado_periodo_anterior_LA(
    protocolos: List[Dict[str, Any]],
    all_protocolos: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> float:
    return _valor_periodo_anterior_protocolo_LA(
        protocolos, all_protocolos, from_date, to_date, get_valor_causa_protocolado_LA
    )


# Retorna o comparativo de protocolos resolvidos.
def get_comparativo_protocolos_resolvidos_LA(
    protocolos: List[Dict[str, Any]],
    all_protocolos: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    # Usar dados não filtrados para calcular período anterior (pode estar fora do filtro atual)
    dados_para_busca = all_protocolos if all_protocolos is not None else protocolos
    
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )

    # Filtrar dados dos períodos atual e anterior
    # Período atual: usar dados filtrados se disponível, senão filtrar dos dados completos
    dados_periodo_atual = _filter_by_date_range(protocolos, data_inicio_atual, data_fim_atual)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)

    # Calcular a quantidade de protocolos resolvidos para cada período
    qtd_atual = get_protocolos_resolvidos_LA(dados_periodo_atual)
    qtd_anterior = get_protocolos_resolvidos_LA(dados_periodo_anterior)
    if qtd_anterior == 0:
        return 0.0

    variacao = ((qtd_atual - qtd_anterior) / qtd_anterior) * 100
    return round(variacao, 2)

# Retorna o comparativo de valor de causa para protocolos resolvidos.
def get_comparativo_valor_causa_protocolado_LA(
    protocolos: List[Dict[str, Any]],
    all_protocolos: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    # Usar dados não filtrados para calcular período anterior (pode estar fora do filtro atual)
    dados_para_busca = all_protocolos if all_protocolos is not None else protocolos
    
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )

    # Filtrar dados dos períodos atual e anterior
    # Período atual: usar dados filtrados se disponível, senão filtrar dos dados completos
    dados_periodo_atual = _filter_by_date_range(protocolos, data_inicio_atual, data_fim_atual)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)

    # Calcular o valor de causa para protocolos resolvidos para cada período
    valor_causa_atual = get_valor_causa_protocolado_LA(dados_periodo_atual)
    valor_causa_anterior = get_valor_causa_protocolado_LA(dados_periodo_anterior)
    if valor_causa_anterior == 0:
        return 0.0

    variacao = ((valor_causa_atual - valor_causa_anterior) / valor_causa_anterior) * 100
    return round(variacao, 2)

# Retorna o comparativo de ticket medio de protocolos resolvidos.
def get_comparativo_ticket_medio_protocolos_resolvidos_LA(
    protocolos: List[Dict[str, Any]],
    all_protocolos: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    # Usar dados não filtrados para calcular período anterior (pode estar fora do filtro atual)
    dados_para_busca = all_protocolos if all_protocolos is not None else protocolos
    
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )

    # Filtrar dados dos períodos atual e anterior
    # Período atual: usar dados filtrados se disponível, senão filtrar dos dados completos
    dados_periodo_atual = _filter_by_date_range(protocolos, data_inicio_atual, data_fim_atual)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)

    # Calcular o ticket medio de protocolos resolvidos para cada período
    ticket_medio_atual = get_ticket_medio_protocolos_resolvidos_LA(dados_periodo_atual)
    ticket_medio_anterior = get_ticket_medio_protocolos_resolvidos_LA(dados_periodo_anterior)
    if ticket_medio_anterior == 0:
        return 0.0

    variacao = ((ticket_medio_atual - ticket_medio_anterior) / ticket_medio_anterior) * 100
    return round(variacao, 2)

# Retorna o comparativo de tempo medio de protocolos resolvidos.
def get_comparativo_tempo_medio_protocolos_resolvidos_LA(
    protocolos: List[Dict[str, Any]],
    all_protocolos: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    # Usar dados não filtrados para calcular período anterior (pode estar fora do filtro atual)
    dados_para_busca = all_protocolos if all_protocolos is not None else protocolos
    
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )

    # Filtrar dados dos períodos atual e anterior
    # Período atual: usar dados filtrados se disponível, senão filtrar dos dados completos
    dados_periodo_atual = _filter_by_date_range(protocolos, data_inicio_atual, data_fim_atual)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)

    # Calcular o ticket medio de protocolos resolvidos para cada período
    tempo_medio_atual = get_media_tempo_protocolado_LA(dados_periodo_atual)
    tempo_medio_anterior = get_media_tempo_protocolado_LA(dados_periodo_anterior)
    if tempo_medio_anterior == 0:
        return 0.0

    variacao = ((tempo_medio_atual - tempo_medio_anterior) / tempo_medio_anterior) * 100
    return round(variacao, 2)

# Retorna o comparativo de mediana de tempo de protocolos resolvidos.
def get_comparativo_mediana_tempo_protocolos_resolvidos_LA(
    protocolos: List[Dict[str, Any]],
    all_protocolos: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    # Usar dados não filtrados para calcular período anterior (pode estar fora do filtro atual)
    dados_para_busca = all_protocolos if all_protocolos is not None else protocolos
    
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )

    # Filtrar dados dos períodos atual e anterior
    # Período atual: usar dados filtrados se disponível, senão filtrar dos dados completos
    dados_periodo_atual = _filter_by_date_range(protocolos, data_inicio_atual, data_fim_atual)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)

    # Calcular o ticket medio de protocolos resolvidos para cada período
    tempo_medio_atual = get_mediana_tempo_protocolado_LA(dados_periodo_atual)
    tempo_medio_anterior = get_mediana_tempo_protocolado_LA(dados_periodo_anterior)
    if tempo_medio_anterior == 0:
        return 0.0

    variacao = ((tempo_medio_atual - tempo_medio_anterior) / tempo_medio_anterior) * 100
    return round(variacao, 2)

# Função auxiliar para extrair os dias desde a contratacao ate o protocolo.
def _extrair_duracoes_dias_pre_protocolo(protocolos: List[Dict[str, Any]]) -> List[float]:
    protocolos_agrupados = _filtrar_protocolos_resolvidos(protocolos)
    duracoes: List[float] = []

    for p in protocolos_agrupados:
        try:
            entrada_str = p.get("DATA_CONTRATACAO") or p.get("data_contratacao")
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


def get_media_tempo_contratacao_protocolado_LA(protocolos: List[Dict[str, Any]]) -> float:
    """Tempo médio (em dias) entre assinatura do contrato (DATA_CONTRATACAO) e protocolo (SAIDA)."""
    duracoes = _extrair_duracoes_dias_pre_protocolo(protocolos)
    if not duracoes:
        return 0.0
    return round(sum(duracoes) / len(duracoes), 2)


def get_mediana_tempo_contratacao_protocolado_LA(protocolos: List[Dict[str, Any]]) -> float:
    """Mediana do tempo (em dias) entre assinatura do contrato (DATA_CONTRATACAO) e protocolo (SAIDA)."""
    duracoes = _extrair_duracoes_dias_pre_protocolo(protocolos)
    if not duracoes:
        return 0.0

    duracoes.sort()
    n = len(duracoes)

    if n % 2 == 1:
        mediana = duracoes[n // 2]
    else:
        mediana = (duracoes[n // 2 - 1] + duracoes[n // 2]) / 2.0

    return round(mediana, 2)

# Retorna o comparativo do tempo médio de contratação até protocolo (vs período anterior equivalente).
def get_comparativo_tempo_medio_contratacao_protocolado_LA(
    protocolos: List[Dict[str, Any]],
    all_protocolos: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    dados_para_busca = all_protocolos if all_protocolos is not None else protocolos

    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )

    dados_periodo_atual = _filter_by_date_range(protocolos, data_inicio_atual, data_fim_atual)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)

    tempo_medio_atual = get_media_tempo_contratacao_protocolado_LA(dados_periodo_atual)
    tempo_medio_anterior = get_media_tempo_contratacao_protocolado_LA(dados_periodo_anterior)

    if tempo_medio_anterior == 0:
        return 0.0
    variacao = ((tempo_medio_atual - tempo_medio_anterior) / tempo_medio_anterior) * 100
    return round(variacao, 2)

# Retorna o comparativo da mediana de tempo de contratação até protocolo (vs período anterior equivalente).
def get_comparativo_mediana_tempo_contratacao_protocolado_LA(
    protocolos: List[Dict[str, Any]],
    all_protocolos: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    dados_para_busca = all_protocolos if all_protocolos is not None else protocolos

    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )

    dados_periodo_atual = _filter_by_date_range(protocolos, data_inicio_atual, data_fim_atual)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)

    mediana_atual = get_mediana_tempo_contratacao_protocolado_LA(dados_periodo_atual)
    mediana_anterior = get_mediana_tempo_contratacao_protocolado_LA(dados_periodo_anterior)

    if mediana_anterior == 0:
        return 0.0
    variacao = ((mediana_atual - mediana_anterior) / mediana_anterior) * 100
    return round(variacao, 2)

# -----------------------------------------------------------------------------
# 2.1 - Medidas de comissão proporcional (DAX -> Python)
# -----------------------------------------------------------------------------

# def _valor_causa_row_protocolo_LA(p: Dict[str, Any]) -> float:
#     """Equivalente ao IF(MATERIA='ANP', DANO_MORAL, VALOR_DA_CAUSA) com fallback."""
#     materia = str(p.get("MATERIA") or "").strip().upper()
#     if materia == "ANP":
#         valor = p.get("DANO_MORAL")
#     else:
#         valor = p.get("VALOR_DA_CAUSA") or p.get("VALOR_CAUSA")
#     return _converter_valor_causa(valor)


def get_valor_causa_protocolo_novo_LA(protocolos: List[Dict[str, Any]]) -> float:
    """
    Valor total de causa do recorte de protocolos (LA).

    Mantém a mesma regra base já usada no arquivo para valor protocolado:
    - STATUS = "CONCLUIDO"
    - REAJUIZAMENTO = False
    - soma por linha: IF(MATERIA="ANP", DANO_MORAL, VALOR_DA_CAUSA)
    """
    # Reaproveita a função existente para garantir consistência no painel.
    return float(get_valor_causa_protocolado_LA(protocolos) or 0.0)


def get_fator_multiplicador_para_atingido_LA(atingido: float) -> float:
    """
    FM (1,0 a 4,0) a partir do valor de causa protocolado (atingido), mesma escada do DAX / NG.
    """
    a = float(atingido or 0.0)
    if a > 4_000_000:
        return 4.0
    if 2_500_000 <= a <= 4_000_000:
        return a / 1_000_000
    return 1.0


def get_fator_multiplicador_LA(protocolos: List[Dict[str, Any]]) -> float:
    """
    FATOR_MULTIPLICADOR (FM) baseado no VALOR_CAUSA_PROTOCOLO global (LA).
    """
    atingido = float(get_valor_causa_protocolo_novo_LA(protocolos) or 0.0)
    return get_fator_multiplicador_para_atingido_LA(atingido)


def get_comissao_com_fm_LA(
    protocolos: List[Dict[str, Any]],
    comercial_geral: List[Dict[str, Any]],
) -> float:
    """
    Pool de comissão após o fator: COMISSAO_BASE (período) × FATOR_MULTIPLICADOR (valor causa protocolo).

    Observação: no LA não usamos as medidas proporcionais por UF aqui; apenas o pool com FM.
    `comercial_geral` deve estar no mesmo recorte de datas usado em `protocolos`.
    """
    fm = float(get_fator_multiplicador_LA(protocolos) or 0.0)
    base = float(get_comissao_base_LA(comercial_geral) or 0.0)
    return round(fm * base, 2)
