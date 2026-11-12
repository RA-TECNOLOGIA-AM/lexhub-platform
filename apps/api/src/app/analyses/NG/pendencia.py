# Funções de analises do setor de pendencias

from typing import List, Dict, Any, Optional
from datetime import datetime, date
from collections import defaultdict
import statistics
from decimal import Decimal
from app.utils import parse_date_from_db, resolver_periodo_comparativo
from app.analyses.NG.comercial_geral import _formatar_nome_atendente


# -----------------------------------------------------------------------------
# 1 - Funções auxiliares
# -----------------------------------------------------------------------------

# Função auxiliar que retorna a lista de pendencias não resolvidas
def _filtrar_pendencias_nao_resolvidas(pendencias: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        p for p in pendencias
        if p.get("STATUS") and str(p.get("STATUS", "")).upper() in ["EM ANDAMENTO", "PENDÊNCIA"]
        and (
            str(p.get("REAJUIZAMENTO", "")).upper() == "FALSE" or
            p.get("REAJUIZAMENTO") is False
        )
    ]

# Função auxiliar que retorna a lis de Pendencias Não resolvidas de reajuizamento.
def _filtrar_pendencias_nao_resolvidas_reajuizamento(pendencias: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        p for p in pendencias
        if p.get("STATUS") and str(p.get("STATUS", "")).upper() in ["EM ANDAMENTO", "PENDÊNCIA"]
        and (
            str(p.get("REAJUIZAMENTO", "")).upper() == "TRUE" or
            p.get("REAJUIZAMENTO") is True
        )
    ]

# Função auxiliar que retorna a lista de pendencias RESOLVIDAS
def _filtrar_pendencias_resolvidas(pendencias: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        p for p in pendencias
        if p.get("STATUS") and str(p.get("STATUS", "")).upper() in ["RESOLVIDO"]
        and (
            str(p.get("REAJUIZAMENTO", "")).upper() == "FALSE" or
            p.get("REAJUIZAMENTO") is False
        )
    ]

# Função auxiliar que retorna a lista de Pedencias Resolvidas de reajuizamento.
def _filtrar_pendencias_resolvidas_reajuizamento(pendencias: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        p for p in pendencias
        if p.get("STATUS") and str(p.get("STATUS", "")).upper() in ["RESOLVIDO"]
        and (
            str(p.get("REAJUIZAMENTO", "")).upper() == "TRUE" or
            p.get("REAJUIZAMENTO") is True
        )
    ]

# Filtra processos organização de documentos por intervalo de datas usando a coluna ENTRADA.
def _filter_by_date_range(pendencias: List[Dict[str, Any]], from_date: date, to_date: date) -> List[Dict[str, Any]]:
    filtered = []
    for item in pendencias:
        try:
            entrada_str = item.get("ENTRADA") or item.get("entrada")
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


def filter_pendencia_por_funcionario(
    pendencias: List[Dict[str, Any]],
    funcionario: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Mesmo critério de :func:`filter_protocolo_por_funcionario` em ``protocolo``
    (:func:`_formatar_nome_funcionario` deste módulo).
    """
    if funcionario is None or not str(funcionario).strip():
        return list(pendencias)
    alvo = _formatar_nome_funcionario(str(funcionario).strip())
    return [
        p for p in pendencias
        if _formatar_nome_funcionario(p.get("FUNCIONARIO")) == alvo
    ]


def filter_pendencia_por_funcionarios(
    pendencias: List[Dict[str, Any]],
    funcionarios: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Restringe aos registros de um ou mais funcionários (união — OR)."""
    if not funcionarios:
        return list(pendencias)
    alvos = {
        _formatar_nome_funcionario(str(f).strip())
        for f in funcionarios
        if f is not None and str(f).strip()
    }
    if not alvos:
        return list(pendencias)
    return [
        p for p in pendencias
        if _formatar_nome_funcionario(p.get("FUNCIONARIO")) in alvos
    ]


def _normalizar_uf_pendencia(raw: Any) -> str:
    """Normaliza a UF vinda do banco ou da query para comparação."""
    return str(raw or "").strip().upper()


def list_ufs_pendencia(pendencias: List[Dict[str, Any]]) -> List[str]:
    """Lista única de UFs disponíveis no recorte atual de pendências."""
    vistos: set[str] = set()
    saida: List[str] = []
    for row in pendencias or []:
        uf = _normalizar_uf_pendencia(row.get("UF") or row.get("uf"))
        if not uf or uf in vistos:
            continue
        vistos.add(uf)
        saida.append(uf)
    return sorted(saida)


def filter_pendencia_por_uf(
    pendencias: List[Dict[str, Any]],
    uf: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Restringe pendências aos registros de uma UF."""
    if uf is None or not str(uf).strip():
        return list(pendencias)
    alvo = _normalizar_uf_pendencia(uf)
    return [
        p for p in pendencias
        if _normalizar_uf_pendencia(p.get("UF") or p.get("uf")) == alvo
    ]


# -----------------------------------------------------------------------------
# Totais gerais (contagens usadas pelo dashboard e pelas funções de comparação)
# -----------------------------------------------------------------------------

# Retorna a quantidade de pendencias não resolvidas.
def get_pendencias_nao_resolvidas(pendencias: List[Dict[str, Any]]) -> int:
    return len(_filtrar_pendencias_nao_resolvidas(pendencias))

# Retorna a quantidade de pendencias não resolvidas de reajuizamento.
def get_pendencias_nao_resolvidas_reajuizamento(pendencias: List[Dict[str, Any]]) -> int:
    return len(_filtrar_pendencias_nao_resolvidas_reajuizamento(pendencias))

# Retorna a quantidade de pendencias NÃO RESOLVIDAS com mais de 5 dias de atraso (a partir da data de entrada).
def get_pendencias_nao_resolvidas_com_atraso(pendencias: List[Dict[str, Any]]) -> int:
    nao_resolvidas = _filtrar_pendencias_nao_resolvidas(pendencias)
    hoje = date.today()
    com_atraso = 0
    for p in nao_resolvidas:
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
            if (hoje - entrada_date).days > 5:
                com_atraso += 1
        except (ValueError, AttributeError, TypeError):
            continue
    return com_atraso

# Retorna a quantidade de pendencias resolvidas.
def get_pendencias_resolvidas(pendencias: List[Dict[str, Any]]) -> int:
    return len(_filtrar_pendencias_resolvidas(pendencias))

# Retorna a quantidade de pendencias resolvidas de reajuizamento.
def get_pendencias_resolvidas_reajuizamento(pendencias: List[Dict[str, Any]]) -> int:
    return len(_filtrar_pendencias_resolvidas_reajuizamento(pendencias))

# Retorna a quantidade de pendencias CANCELADAS.
def get_pendencias_canceladas(pendencias: List[Dict[str, Any]]) -> int:
    cancelados = [
        c for c in pendencias
        if c.get("STATUS") and str(c.get("STATUS", "")).upper() in ["CANCELADO"]
        and (
            str(c.get("REAJUIZAMENTO", "")).upper() == "FALSE" or
            c.get("REAJUIZAMENTO") is False
        )
        and (
            str(c.get("MOTIVO_CANCELAMENTO", "")).upper() not in ["DUPLICADO", "AÇÃO INEXISTENTE"]
        )
    ]
    return len(cancelados)

# Retorna a quantidade de clientes em Triagem.
def get_pendencias_triagem(pendencias: List[Dict[str, Any]]) -> int:
    triagem = [
        t for t in pendencias
        if t.get("STATUS") and str(t.get("STATUS", "")).upper() in ["TRIAGEM"]
    ]
    return len(triagem)

# Retorna o Total de Pendencias.
def get_pendencias_total(pendencias: List[Dict[str, Any]]) -> int:
    total = get_pendencias_nao_resolvidas(pendencias) + get_pendencias_resolvidas(pendencias) + get_pendencias_canceladas(pendencias)
    return total

# Retorna a taxa de pendencias NÃO RESOLVIDOS.
def get_pendencias_taxa_nao_resolvidos(pendencias: List[Dict[str, Any]]) -> Optional[float]:
    total = get_pendencias_total(pendencias)
    if total == 0:
        return 0.0
    return round((get_pendencias_nao_resolvidas(pendencias) / total) * 100, 2)

# Retorna a taxa de pendencias RESOLVIVIDOS.
def get_pendencias_taxa_resolvidos(pendencias: List[Dict[str, Any]]) -> Optional[float]:
    total = get_pendencias_total(pendencias)
    if total == 0:
        return 0.0
    return round((get_pendencias_resolvidas(pendencias) / total) * 100, 2)

# Retorna a taxa de pendencias CANCELADAS.
def get_pendencias_taxa_canceladas(pendencias: List[Dict[str, Any]]) -> Optional[float]:
    total = get_pendencias_total(pendencias)
    if total == 0:
        return 0.0
    return round((get_pendencias_canceladas(pendencias) / total) * 100, 2)

# Função auxiliar para extrair os dias
def _extrair_duracoes_dias(pendencias: List[Dict[str, Any]]) -> List[float]:
    protocolos_agrupados = _filtrar_pendencias_resolvidas(pendencias)
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
def get_media_tempo_resolvidos_pendencia(pendencias: List[Dict[str, Any]]) -> float:
    duracoes = _extrair_duracoes_dias(pendencias)

    if not duracoes:
        return 0.0

    return round(sum(duracoes) / len(duracoes), 2)

# Retorna a mediana do tempo (em dias) para o processo ser resolvido no setor, de forma geral.
def get_mediana_tempo_resolvidos_pendencia(pendencias: List[Dict[str, Any]]) -> float:
    duracoes = _extrair_duracoes_dias(pendencias)

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
# 2 - Funções de análise por atendente
# -----------------------------------------------------------------------------

# Retorna a quantidade de pendencias não resolvidas por atendente.
def get_pendencias_nao_resolvidas_por_atendente(pendencias: List[Dict[str, Any]]) -> Dict[str, int]:
    pendencias = _filtrar_pendencias_nao_resolvidas(pendencias)
    atendente_counts = defaultdict(int)
    for p in pendencias:
        atendente = p.get("ATENDENTE") or "Sem atendente"
        atendente_formatado = _formatar_nome_atendente(atendente)
        atendente_counts[atendente_formatado] += 1
    # Garantir que todos os valores são inteiros (contagem de processos)
    return {name: int(value) for name, value in dict(atendente_counts).items()}

# Retorna a quantidade de pendencias não resolvidos agrupando por ORIGEM.
def get_pendencias_nao_resolvidas_por_origem(pendencias: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    nao_resolvidas = _filtrar_pendencias_nao_resolvidas(pendencias)
    origem_counts = defaultdict(int)
    for p in nao_resolvidas:
        origem = p.get("ORIGEM") or "Sem origem"
        origem_counts[origem] += 1
    result = [
        {"name": name, "value": int(value)}
        for name, value in origem_counts.items()    
    ]
    return sorted(result, key=lambda x: x["value"], reverse=True)

# Agrupa processos resolvidos por mês.
def group_pendencias_resolvidas_por_mes(pendencias: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    resolvidos = _filtrar_pendencias_resolvidas(pendencias)
    grouped = {}
    month_names = [
        "jan", "fev", "mar", "abr", "mai", "jun",
        "jul", "ago", "set", "out", "nov", "dez"
    ]
    for item in resolvidos:
        try:
            data_saida_str = item.get("SAIDA") or item.get("saida")
            if not data_saida_str:
                continue
            data_saida = parse_date_from_db(data_saida_str)
            if not data_saida:
                continue
            
            month_key = f"{data_saida.year}-{data_saida.month:02d}"
            month_names = [
                "jan", "fev", "mar", "abr", "mai", "jun",
                "jul", "ago", "set", "out", "nov", "dez"
            ]
            month_name = f"{month_names[data_saida.month - 1]} {data_saida.year}"
            
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

# -----------------------------------------------------------------------------
# 2 - Funções de análise por Funcionario
# -----------------------------------------------------------------------------

# Agrupa processos resolvidos por funcionário.
def get_media_pendencias_resolvidas_por_funcionario(
    pendencias: List[Dict[str, Any]],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> List[Dict[str, Any]]:
    """Média de processos resolvidos por FUNCIONARIO."""
    resolvidos = _filtrar_pendencias_resolvidas(pendencias)
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

# Agrupa processos resolvidos por dia.
def group_pendencias_resolvidas_por_dia(pendencias: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    resolvidos = _filtrar_pendencias_resolvidas(pendencias)
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

# Retorna processos resolvidos por dia por funcionário.
def get_pendencias_resolvidas_por_dia_por_funcionario(pendencias: List[Dict[str, Any]]) -> Dict[str, Any]:
    resolvidos = _filtrar_pendencias_resolvidas(pendencias)
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


def _filtrar_pendencias_por_funcionario_nome(
    pendencias: List[Dict[str, Any]],
    nome_funcionario: str,
) -> List[Dict[str, Any]]:
    return [
        p for p in pendencias
        if _formatar_nome_funcionario(p.get("FUNCIONARIO") or "Sem funcionário") == nome_funcionario
    ]


def _preco_unitario_pendencia_comissao(
    taxa_resolvido: Optional[float],
    taxa_cancelamento: Optional[float],
) -> Decimal:
    """
    Comissão só se taxa de cancelamento < 5%.
    R$ 3,00 por demanda resolvida se taxa resolvido ≥ 97%; R$ 1,00 se ≥ 85%.
    """
    tc = float(taxa_cancelamento) if taxa_cancelamento is not None else 0.0
    if tc >= 5:
        return Decimal("0")
    tr = float(taxa_resolvido) if taxa_resolvido is not None else 0.0
    if tr >= 97:
        return Decimal("3.00")
    if tr >= 85:
        return Decimal("1.00")
    return Decimal("0")


def get_pendencias_comissionamento_por_funcionario(
    pendencias: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Por funcionário: taxas via funções existentes (`get_pendencias_taxa_resolvidos`,
    `get_pendencias_taxa_canceladas`); comissão sobre qtd resolvida se cancelamento < 5%.
    """
    nomes = {
        _formatar_nome_funcionario(p.get("FUNCIONARIO") or "Sem funcionário")
        for p in pendencias
    }

    linhas: List[Dict[str, Any]] = []
    for nome in sorted(nomes):
        sub = _filtrar_pendencias_por_funcionario_nome(pendencias, nome)
        if get_pendencias_total(sub) == 0:
            continue

        taxa_r = get_pendencias_taxa_resolvidos(sub)
        taxa_c = get_pendencias_taxa_canceladas(sub)
        qtd_r = get_pendencias_resolvidas(sub)

        unit = _preco_unitario_pendencia_comissao(taxa_r, taxa_c)
        qtd_x = (Decimal(qtd_r) * unit).quantize(Decimal("0.01"))
        comissao = float(qtd_x)

        linhas.append({
            "funcionario": nome,
            "taxa_resolvido": taxa_r,
            "taxa_cancelamento": taxa_c,
            "qtd_resolvido": qtd_r,
            "valor": float(unit),
            "qtd_x_valor": float(qtd_x),
            "comissao": comissao,
        })

    linhas.sort(key=lambda x: (-x["comissao"], x["funcionario"]))
    return linhas


# Retorna a variação percentual de pendencias resolvidas.
def get_comparativo_pendencias_resolvidas(
    pendencias: List[Dict[str, Any]],
    all_pendencias: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    dados_para_busca = all_pendencias if all_pendencias is not None else pendencias
    
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )

    dados_periodo_atual = _filter_by_date_range(pendencias, data_inicio_atual, data_fim_atual)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)

    dados_periodo_atual = get_pendencias_resolvidas(dados_periodo_atual)
    dados_periodo_anterior = get_pendencias_resolvidas(dados_periodo_anterior)

    if dados_periodo_anterior == 0:
        return 0.0
    variacao = ((dados_periodo_atual - dados_periodo_anterior) / dados_periodo_anterior) * 100
    return round(variacao, 2)

# Retorna a variação percentual de tempo médio de pendencias resolvidas.
def get_comparativo_tempo_medio_pendencias_resolvidas(
    pendencias: List[Dict[str, Any]],
    all_pendencias: Optional[List[Dict[str, Any]]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> float:
    dados_para_busca = all_pendencias if all_pendencias is not None else pendencias
    
    data_inicio_atual, data_fim_atual, data_inicio_anterior, data_fim_anterior = (
        resolver_periodo_comparativo(from_date, to_date)
    )

    dados_periodo_atual = _filter_by_date_range(pendencias, data_inicio_atual, data_fim_atual)
    dados_periodo_anterior = _filter_by_date_range(dados_para_busca, data_inicio_anterior, data_fim_anterior)

    dados_periodo_atual = get_media_tempo_resolvidos_pendencia(dados_periodo_atual)
    dados_periodo_anterior = get_media_tempo_resolvidos_pendencia(dados_periodo_anterior)

    if dados_periodo_anterior == 0:
        return 0.0
    variacao = ((dados_periodo_atual - dados_periodo_anterior) / dados_periodo_anterior) * 100
    return round(variacao, 2)